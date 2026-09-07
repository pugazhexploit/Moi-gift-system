"""Contribution, receipt, and financial state-transition endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Request

from app.core.permissions import get_current_user, request_context, require_csrf, require_roles
from app.models.user import UserRole
from app.schemas.common import SuccessResponse
from app.schemas.pagination import PaginatedData
from app.schemas.transaction import (
    PaymentMethod,
    ReceiptResponse,
    ReceiptVerificationResponse,
    TransactionAction,
    TransactionCreate,
    TransactionCreateData,
    TransactionResponse,
    TransactionStatus,
)
from app.services.transaction_service import TransactionService


router = APIRouter(prefix="/transactions", tags=["Transactions"])
receipts_router = APIRouter(prefix="/receipts", tags=["Receipts"])


@router.get("", response_model=SuccessResponse[PaginatedData[TransactionResponse]])
async def list_transactions(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    event_id: str | None = Query(None, pattern=r"^EVT-\d{6,}$"),
    status: TransactionStatus | None = None,
    payment_method: PaymentMethod | None = None,
    user: dict = Depends(get_current_user),
) -> SuccessResponse[PaginatedData[TransactionResponse]]:
    items, total = await TransactionService(request.app.state.database, request.app.state.settings).list(
        user, page, limit, event_id, status, payment_method.value if payment_method else None
    )
    return SuccessResponse(data=PaginatedData.build(items, page, limit, total))


@router.post("", response_model=SuccessResponse[TransactionCreateData], dependencies=[Depends(require_csrf)])
async def create_transaction(
    payload: TransactionCreate,
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.COLLECTOR)),
) -> SuccessResponse[TransactionCreateData]:
    data = await TransactionService(request.app.state.database, request.app.state.settings).create(
        payload, idempotency_key, user, request_context(request)
    )
    return SuccessResponse(data=data, message="Transaction recorded")


@router.get("/{transaction_id}", response_model=SuccessResponse[TransactionResponse])
async def get_transaction(
    transaction_id: str, request: Request, user: dict = Depends(get_current_user)
) -> SuccessResponse[TransactionResponse]:
    data = await TransactionService(request.app.state.database, request.app.state.settings).get(transaction_id, user)
    return SuccessResponse(data=data)


@router.post(
    "/{transaction_id}/verify",
    response_model=SuccessResponse[TransactionResponse],
    dependencies=[Depends(require_csrf)],
)
async def verify_transaction(
    transaction_id: str,
    action: TransactionAction,
    request: Request,
    user: dict = Depends(require_roles(UserRole.ADMIN)),
) -> SuccessResponse[TransactionResponse]:
    data = await TransactionService(request.app.state.database, request.app.state.settings).verify(
        transaction_id, action, user, request_context(request)
    )
    return SuccessResponse(data=data, message="Transaction verified")


@router.post(
    "/{transaction_id}/reject",
    response_model=SuccessResponse[TransactionResponse],
    dependencies=[Depends(require_csrf)],
)
async def reject_transaction(
    transaction_id: str,
    action: TransactionAction,
    request: Request,
    user: dict = Depends(require_roles(UserRole.ADMIN)),
) -> SuccessResponse[TransactionResponse]:
    data = await TransactionService(request.app.state.database, request.app.state.settings).reject(
        transaction_id, action, user, request_context(request)
    )
    return SuccessResponse(data=data, message="Transaction rejected")


@router.post(
    "/{transaction_id}/lock",
    response_model=SuccessResponse[TransactionResponse],
    dependencies=[Depends(require_csrf)],
)
async def lock_transaction(
    transaction_id: str,
    action: TransactionAction,
    request: Request,
    user: dict = Depends(require_roles(UserRole.ADMIN)),
) -> SuccessResponse[TransactionResponse]:
    data = await TransactionService(request.app.state.database, request.app.state.settings).lock(
        transaction_id, action, user, request_context(request)
    )
    return SuccessResponse(data=data, message="Transaction locked")


@receipts_router.get("/verify/{verification_token}", response_model=SuccessResponse[ReceiptVerificationResponse])
async def verify_receipt(verification_token: str, request: Request) -> SuccessResponse[ReceiptVerificationResponse]:
    data = await TransactionService(request.app.state.database, request.app.state.settings).verify_receipt_token(
        verification_token
    )
    return SuccessResponse(data=data)


@receipts_router.get("/{receipt_id}", response_model=SuccessResponse[ReceiptResponse])
async def get_receipt(
    receipt_id: str, request: Request, user: dict = Depends(get_current_user)
) -> SuccessResponse[ReceiptResponse]:
    data = await TransactionService(request.app.state.database, request.app.state.settings).receipt(receipt_id, user)
    return SuccessResponse(data=data)
