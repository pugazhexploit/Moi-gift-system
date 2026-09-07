"""Sensitive contribution workflow: Decimal128, idempotency, receipts, and locking."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.core.config import Settings
from app.core.exceptions import AppError
from app.core.security import generate_csrf_token, hash_receipt_token, utc_now
from app.models.user import UserRole
from app.repositories.collectors import CollectorRepository
from app.repositories.counters import CounterRepository
from app.repositories.guests import GuestRepository
from app.repositories.transactions import TransactionRepository
from app.schemas.transaction import ReceiptResponse, ReceiptVerificationResponse, TransactionAction, TransactionCreate, TransactionCreateData, TransactionResponse, TransactionStatus
from app.services.audit_service import AuditService
from app.services.event_access_service import EventAccessService
from app.utils.money import from_decimal128, to_decimal128


IDEMPOTENCY_KEY = re.compile(r"^[A-Za-z0-9_-]{16,128}$")


class TransactionService:
    def __init__(self, database: Any, settings: Settings) -> None:
        self.database = database
        self.settings = settings
        self.transactions = TransactionRepository(database)
        self.guests = GuestRepository(database)
        self.collectors = CollectorRepository(database)
        self.counters = CounterRepository(database)
        self.audit = AuditService(database)
        self.access = EventAccessService(database)

    async def create(self, payload: TransactionCreate, idempotency_key: str, user: dict[str, Any], context: dict[str, str | None]) -> TransactionCreateData:
        if not IDEMPOTENCY_KEY.fullmatch(idempotency_key):
            raise AppError("VALIDATION_ERROR", "Invalid Idempotency-Key", 422)
        event = await self.access.event_for_user(payload.event_id, user)
        guest = await self.guests.get_by_public_id(payload.guest_id)
        if guest is None or guest["event_id"] != event["_id"]:
            raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        collector = await self._resolve_collector(payload.collector_id, event["_id"], user)
        fingerprint = self._fingerprint(payload, collector["collector_id"])
        existing = await self.transactions.get_by_idempotency_key(event["_id"], idempotency_key)
        if existing is not None:
            return await self._idempotent_result(existing, fingerprint)

        verification_token = generate_csrf_token()
        verification_hash = hash_receipt_token(self.settings, verification_token)
        now = utc_now()

        async def create_transaction(session: Any) -> tuple[dict[str, Any], dict[str, Any], str | None]:
            prior = await self.transactions.get_by_idempotency_key(event["_id"], idempotency_key)
            if prior is not None:
                receipt = await self.transactions.get_receipt_by_transaction_id(prior["_id"])
                if receipt is None:
                    raise AppError("INTEGRITY_ERROR", "Transaction receipt is unavailable", 409)
                return prior, receipt, None
            transaction = {
                "transaction_id": await self.counters.next_id("TXN", session=session),
                "event_id": event["_id"], "event_public_id": event["event_id"],
                "guest_id": guest["_id"], "guest_public_id": guest["guest_id"],
                "collector_id": collector["_id"], "collector_public_id": collector["collector_id"],
                "amount": to_decimal128(payload.amount), "currency": payload.currency,
                "payment_method": payload.payment_method.value, "transaction_type": "contribution",
                "status": TransactionStatus.PENDING.value,
                "notes": payload.notes, "idempotency_key": idempotency_key,
                "request_fingerprint": fingerprint, "created_at": now, "updated_at": now,
                "verified_by": None, "verified_at": None, "locked_at": None,
            }
            if payload.reference_number is not None:
                transaction["reference_number"] = payload.reference_number
            transaction = await self.transactions.create(transaction, session)
            receipt = await self.transactions.create_receipt({"receipt_id": await self.counters.next_id("RCP", session=session), "transaction_id": transaction["_id"], "transaction_public_id": transaction["transaction_id"], "event_id": event["_id"], "event_public_id": event["event_id"], "guest_id": guest["_id"], "collector_id": collector["_id"], "issued_at": now, "verification_status": "valid", "verification_token_hash": verification_hash}, session)
            await self.audit.record(user_id=user["_id"], action="CREATE", request_id=context.get("request_id"), ip_address=context.get("ip_address"), user_agent=context.get("user_agent"), event_id=event["_id"], entity_type="transaction", entity_id=transaction["_id"], new_value={"transaction_id": transaction["transaction_id"], "status": TransactionStatus.PENDING.value}, session=session)
            return transaction, receipt, verification_token

        try:
            transaction, receipt, token = await self._with_transaction(create_transaction)
        except DuplicateKeyError:
            existing = await self.transactions.get_by_idempotency_key(event["_id"], idempotency_key)
            if existing is None:
                raise AppError("DUPLICATE_REFERENCE", "Reference number is already used for this event", 409)
            return await self._idempotent_result(existing, fingerprint)
        return TransactionCreateData(transaction=self.to_response(transaction), receipt=self.receipt_response(receipt), receipt_verification_token=token)

    async def get(self, transaction_id: str, user: dict[str, Any]) -> TransactionResponse:
        return self.to_response(await self._transaction_for_user(transaction_id, user))

    async def list(self, user: dict[str, Any], page: int, limit: int, event_id: str | None, status: TransactionStatus | None, payment_method: str | None) -> tuple[list[TransactionResponse], int]:
        allowed = await self.access.allowed_event_ids(user)
        query: dict[str, Any] = {} if allowed is None else {"event_id": {"$in": allowed}}
        if event_id:
            event = await self.access.event_for_user(event_id, user)
            query["event_id"] = event["_id"]
        if UserRole(user["role"]) is UserRole.COLLECTOR:
            collector = await self.collectors.get_by_user_id(user["_id"])
            if collector is None:
                return [], 0
            query["collector_id"] = collector["_id"]
        if status:
            query["status"] = status.value
        if payment_method:
            query["payment_method"] = payment_method
        transactions, total = await self.transactions.list(query, page, limit)
        return [self.to_response(transaction) for transaction in transactions], total

    async def verify(self, transaction_id: str, action: TransactionAction, user: dict[str, Any], context: dict[str, str | None]) -> TransactionResponse:
        return await self._transition(transaction_id, TransactionStatus.PENDING, {"status": TransactionStatus.VERIFIED.value, "verified_by": user["_id"], "verified_at": utc_now(), "verification_note": action.reason}, "VERIFY", user, context)

    async def reject(self, transaction_id: str, action: TransactionAction, user: dict[str, Any], context: dict[str, str | None]) -> TransactionResponse:
        if not action.reason:
            raise AppError("VALIDATION_ERROR", "A rejection reason is required", 422)
        response = await self._transition(transaction_id, TransactionStatus.PENDING, {"status": TransactionStatus.REJECTED.value, "rejected_by": user["_id"], "rejected_at": utc_now(), "rejection_reason": action.reason}, "REJECT", user, context, invalidate_receipt=True)
        return response

    async def lock(self, transaction_id: str, action: TransactionAction, user: dict[str, Any], context: dict[str, str | None]) -> TransactionResponse:
        return await self._transition(transaction_id, TransactionStatus.VERIFIED, {"status": TransactionStatus.LOCKED.value, "locked_at": utc_now(), "locked_by": user["_id"], "lock_note": action.reason}, "LOCK", user, context)

    async def receipt(self, receipt_id: str, user: dict[str, Any]) -> ReceiptResponse:
        receipt = await self.transactions.get_receipt(receipt_id)
        if receipt is None:
            raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        await self.access.event_for_user(receipt["event_public_id"], user)
        if UserRole(user["role"]) is UserRole.COLLECTOR:
            collector = await self.collectors.get_by_user_id(user["_id"])
            if collector is None or collector["_id"] != receipt["collector_id"]:
                raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        return self.receipt_response(receipt)

    async def verify_receipt_token(self, token: str) -> ReceiptVerificationResponse:
        receipt = await self.transactions.get_receipt_by_token_hash(hash_receipt_token(self.settings, token))
        if receipt is None:
            raise AppError("RESOURCE_NOT_FOUND", "Receipt not found", 404)
        return ReceiptVerificationResponse(receipt_id=receipt["receipt_id"], verification_status=receipt["verification_status"])

    async def _resolve_collector(self, supplied_collector_id: str | None, event_object_id: ObjectId, user: dict[str, Any]) -> dict[str, Any]:
        role = UserRole(user["role"])
        if role is UserRole.COLLECTOR:
            collector = await self.collectors.get_by_user_id(user["_id"])
            if collector is None or (supplied_collector_id and supplied_collector_id != collector["collector_id"]):
                raise AppError("FORBIDDEN", "You are not allowed to use this collector", 403)
        elif role is UserRole.ADMIN:
            if not supplied_collector_id:
                raise AppError("VALIDATION_ERROR", "collector_id is required for administrator entry", 422)
            collector = await self.collectors.get_by_public_id(supplied_collector_id)
            if collector is None:
                raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        else:
            raise AppError("FORBIDDEN", "You are not allowed to create transactions", 403)
        if collector.get("status") != "active" or not await self.collectors.is_assigned(event_object_id, collector["_id"]):
            raise AppError("FORBIDDEN", "Collector is not assigned to this event", 403)
        return collector

    async def _transaction_for_user(self, transaction_id: str, user: dict[str, Any]) -> dict[str, Any]:
        transaction = await self.transactions.get_by_public_id(transaction_id)
        if transaction is None:
            raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        await self.access.event_for_user(transaction["event_public_id"], user)
        if UserRole(user["role"]) is UserRole.COLLECTOR:
            collector = await self.collectors.get_by_user_id(user["_id"])
            if collector is None or collector["_id"] != transaction["collector_id"]:
                raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        return transaction

    async def _transition(self, transaction_id: str, expected: TransactionStatus, changes: dict[str, Any], audit_action: str, user: dict[str, Any], context: dict[str, str | None], invalidate_receipt: bool = False) -> TransactionResponse:
        transaction = await self.transactions.get_by_public_id(transaction_id)
        if transaction is None:
            raise AppError("RESOURCE_NOT_FOUND", "Resource not found", 404)
        now = utc_now()
        async def transition(session: Any) -> dict[str, Any] | None:
            updated = await self.transactions.transition(transaction_id, expected.value, changes, now, session)
            if updated is None:
                return None
            if invalidate_receipt:
                await self.transactions.set_receipt_status(updated["_id"], "invalid", session)
            await self.audit.record(user_id=user["_id"], action=audit_action, request_id=context.get("request_id"), ip_address=context.get("ip_address"), user_agent=context.get("user_agent"), event_id=updated["event_id"], entity_type="transaction", entity_id=updated["_id"], old_value={"status": expected.value}, new_value={"transaction_id": transaction_id, "status": updated["status"]}, session=session)
            return updated
        updated = await self._with_transaction(transition)
        if updated is None:
            raise AppError("INVALID_STATE", f"Transaction is not {expected.value}", 409)
        return self.to_response(updated)

    async def _idempotent_result(self, transaction: dict[str, Any], fingerprint: str) -> TransactionCreateData:
        if transaction.get("request_fingerprint") != fingerprint:
            raise AppError("IDEMPOTENCY_CONFLICT", "Idempotency-Key was already used for a different transaction", 409)
        receipt = await self.transactions.get_receipt_by_transaction_id(transaction["_id"])
        if receipt is None:
            raise AppError("INTEGRITY_ERROR", "Transaction receipt is unavailable", 409)
        return TransactionCreateData(transaction=self.to_response(transaction), receipt=self.receipt_response(receipt), receipt_verification_token=None)

    @staticmethod
    def _fingerprint(payload: TransactionCreate, collector_id: str) -> str:
        fields = {"event_id": payload.event_id, "guest_id": payload.guest_id, "collector_id": collector_id, "amount": str(payload.amount), "currency": payload.currency, "payment_method": payload.payment_method.value, "reference_number": payload.reference_number, "notes": payload.notes}
        return hashlib.sha256(json.dumps(fields, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    async def _with_transaction(self, callback: Any) -> Any:
        session = self.database.client.start_session()
        if hasattr(session, "__await__") and not hasattr(session, "__aenter__"):
            session = await session
        async with session as s:
            return await s.with_transaction(callback)

    @staticmethod
    def to_response(transaction: dict[str, Any]) -> TransactionResponse:
        return TransactionResponse(transaction_id=transaction["transaction_id"], event_id=transaction["event_public_id"], guest_id=transaction["guest_public_id"], collector_id=transaction["collector_public_id"], amount=from_decimal128(transaction["amount"]), currency=transaction["currency"], payment_method=transaction["payment_method"], transaction_type=transaction["transaction_type"], status=transaction["status"], reference_number=transaction.get("reference_number"), notes=transaction.get("notes", ""), created_at=transaction["created_at"], updated_at=transaction["updated_at"], verified_at=transaction.get("verified_at"), locked_at=transaction.get("locked_at"))

    @staticmethod
    def receipt_response(receipt: dict[str, Any]) -> ReceiptResponse:
        return ReceiptResponse(receipt_id=receipt["receipt_id"], transaction_id=receipt.get("transaction_public_id", ""), issued_at=receipt["issued_at"], verification_status=receipt["verification_status"])
