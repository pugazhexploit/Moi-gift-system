"""Development seed script for GiftLedger.

Creates development-only accounts, events, guests, transactions, and gifts.
DO NOT RUN IN PRODUCTION.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import uuid
from bson import Decimal128, ObjectId

from app.core.config import get_settings
from app.core.database import database_manager
from app.core.security import hash_password, hash_receipt_token, utc_now
from app.models.user import UserRole, UserStatus


async def seed() -> None:
    settings = get_settings()
    await database_manager.connect(settings)
    db = database_manager.db

    print("--- Seeding GiftLedger Database ---")
    now = utc_now()

    # Clear existing collections for a clean dev seed
    collections = [
        "users", "events", "guests", "collectors", "event_collectors",
        "transactions", "gifts", "receipts", "reconciliations",
        "audit_logs", "counters", "refresh_tokens"
    ]
    for col in collections:
        await db[col].delete_many({})

    # 1. Counters initialization
    await db["counters"].insert_many([
        {"_id": "EVT", "seq": 2},
        {"_id": "GST", "seq": 20},
        {"_id": "COL", "seq": 2},
        {"_id": "TXN", "seq": 50},
        {"_id": "RCP", "seq": 50},
        {"_id": "GFT", "seq": 10},
        {"_id": "REC", "seq": 1},
    ])

    # 2. Users (1 Admin, 2 Collectors, 1 Viewer)
    admin_hash = hash_password("Admin@GiftLedger123!")
    col1_hash = hash_password("Collector1@123!")
    col2_hash = hash_password("Collector2@123!")
    viewer_hash = hash_password("Viewer@123!")

    admin_user = {
        "_id": ObjectId(),
        "username": "admin",
        "username_normalized": "admin",
        "email": "admin@giftledger.dev",
        "email_normalized": "admin@giftledger.dev",
        "password_hash": admin_hash,
        "role": UserRole.ADMIN.value,
        "status": UserStatus.ACTIVE.value,
        "failed_login_attempts": 0,
        "locked_until": None,
        "last_login_at": now,
        "created_at": now,
        "updated_at": now,
    }
    col1_user = {
        "_id": ObjectId(),
        "username": "collector1",
        "username_normalized": "collector1",
        "email": "collector1@giftledger.dev",
        "email_normalized": "collector1@giftledger.dev",
        "password_hash": col1_hash,
        "role": UserRole.COLLECTOR.value,
        "status": UserStatus.ACTIVE.value,
        "failed_login_attempts": 0,
        "locked_until": None,
        "last_login_at": now,
        "created_at": now,
        "updated_at": now,
    }
    col2_user = {
        "_id": ObjectId(),
        "username": "collector2",
        "username_normalized": "collector2",
        "email": "collector2@giftledger.dev",
        "email_normalized": "collector2@giftledger.dev",
        "password_hash": col2_hash,
        "role": UserRole.COLLECTOR.value,
        "status": UserStatus.ACTIVE.value,
        "failed_login_attempts": 0,
        "locked_until": None,
        "last_login_at": now,
        "created_at": now,
        "updated_at": now,
    }
    viewer_user = {
        "_id": ObjectId(),
        "username": "viewer",
        "username_normalized": "viewer",
        "email": "viewer@giftledger.dev",
        "email_normalized": "viewer@giftledger.dev",
        "password_hash": viewer_hash,
        "role": UserRole.VIEWER.value,
        "status": UserStatus.ACTIVE.value,
        "failed_login_attempts": 0,
        "locked_until": None,
        "last_login_at": now,
        "created_at": now,
        "updated_at": now,
    }
    await db["users"].insert_many([admin_user, col1_user, col2_user, viewer_user])
    print("[+] Users created: 1 Admin, 2 Collectors, 1 Viewer")

    # 3. Collectors
    collector1_doc = {
        "_id": ObjectId(),
        "collector_id": "COL-000001",
        "user_id": col1_user["_id"],
        "name": "Jane Collector",
        "phone": "+919876543211",
        "employee_code": "EMP-001",
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }
    collector2_doc = {
        "_id": ObjectId(),
        "collector_id": "COL-000002",
        "user_id": col2_user["_id"],
        "name": "David Collector",
        "phone": "+919876543212",
        "employee_code": "EMP-002",
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }
    await db["collectors"].insert_many([collector1_doc, collector2_doc])
    print("[+] Collector profiles created: COL-000001, COL-000002")

    # 4. Events (2 Events)
    event1 = {
        "_id": ObjectId(),
        "event_id": "EVT-000001",
        "event_name": "Kavitha & Arvind Wedding Reception",
        "event_type": "wedding",
        "description": "Grand wedding celebration of Kavitha and Arvind",
        "venue": "Grand Palace Hall, Chennai",
        "event_date": now + timedelta(days=1),
        "start_time": "18:00",
        "end_time": "23:00",
        "status": "active",
        "created_by": admin_user["_id"],
        "assigned_viewers": [viewer_user["_id"]],
        "created_at": now,
        "updated_at": now,
    }
    event2 = {
        "_id": ObjectId(),
        "event_id": "EVT-000002",
        "event_name": "Anand 50th Birthday Celebration",
        "event_type": "birthday",
        "description": "Family and friends milestone birthday gathering",
        "venue": "Emerald Banquet, Bangalore",
        "event_date": now + timedelta(days=5),
        "start_time": "19:00",
        "end_time": "22:30",
        "status": "active",
        "created_by": admin_user["_id"],
        "assigned_viewers": [viewer_user["_id"]],
        "created_at": now,
        "updated_at": now,
    }
    await db["events"].insert_many([event1, event2])
    print("[+] Events created: EVT-000001, EVT-000002")

    # Event Collectors assignments
    await db["event_collectors"].insert_many([
        {"_id": ObjectId(), "event_id": event1["_id"], "collector_id": collector1_doc["_id"], "assigned_at": now, "status": "active"},
        {"_id": ObjectId(), "event_id": event1["_id"], "collector_id": collector2_doc["_id"], "assigned_at": now, "status": "active"},
        {"_id": ObjectId(), "event_id": event2["_id"], "collector_id": collector1_doc["_id"], "assigned_at": now, "status": "active"},
    ])

    # 5. Guests (20 Guests: 10 per event)
    guest_names = [
        ("Rajesh Sharma", "Bride Uncle", "Sharma Family"),
        ("Priya Nair", "Friend", "Nair Family"),
        ("Suresh Kumar", "Groom Cousin", "Kumar Family"),
        ("Lakshmi Venkatesh", "Aunt", "Venkatesh Family"),
        ("Arun Patel", "Colleague", "Patel Family"),
        ("Meena Sundaram", "Family Friend", "Sundaram Family"),
        ("Karthik Raman", "School Friend", "Raman Family"),
        ("Ananya Iyer", "Bride Sister", "Iyer Family"),
        ("Girish Reddy", "Business Partner", "Reddy Family"),
        ("Deepa Menon", "Neighbor", "Menon Family"),
        ("Vikram Singh", "Cousin", "Singh Family"),
        ("Sunita Joshi", "Aunt", "Joshi Family"),
        ("Manoj Gupta", "Friend", "Gupta Family"),
        ("Kavita Rao", "Colleague", "Rao Family"),
        ("Ramesh Verma", "Uncle", "Verma Family"),
        ("Pooja Bhat", "College Friend", "Bhat Family"),
        ("Siddharth Das", "Groom Friend", "Das Family"),
        ("Bhavna Shah", "Friend", "Shah Family"),
        ("Naveen Prasad", "Neighbor", "Prasad Family"),
        ("Divya Pillai", "Cousin", "Pillai Family"),
    ]

    guest_docs = []
    for i, (name, rel, fam) in enumerate(guest_names, start=1):
        target_event = event1 if i <= 10 else event2
        g_id = f"GST-{i:06d}"
        guest_docs.append({
            "_id": ObjectId(),
            "guest_id": g_id,
            "event_id": target_event["_id"],
            "full_name": name,
            "phone": f"+9198000{i:05d}",
            "email": f"guest{i}@example.dev",
            "address": {
                "line_1": f"{i*12} Blossom Avenue",
                "line_2": "Suite 3",
                "city": "Chennai" if i <= 10 else "Bangalore",
                "district": "Central",
                "state": "Tamil Nadu" if i <= 10 else "Karnataka",
                "postal_code": "600001" if i <= 10 else "560001",
                "country": "India",
            },
            "relationship": rel,
            "family_name": fam,
            "notes": "VIP Table" if i % 3 == 0 else "Confirmed RSVP",
            "qr_token": str(uuid.uuid4()),
            "created_at": now - timedelta(days=2),
            "updated_at": now - timedelta(days=2),
        })
    await db["guests"].insert_many(guest_docs)
    print(f"[+] Guests created: {len(guest_docs)} guests")

    # 6. Transactions (50 Transactions) & Receipts
    amounts = [
        1001, 2001, 5001, 10001, 2500, 5000, 10000, 1500, 2000, 3000,
        500, 1000, 2100, 5100, 11000, 7500, 25000, 15000, 1000, 2000
    ]
    methods = ["cash", "upi", "cash", "bank_transfer", "cash", "upi"]
    txn_docs = []
    receipt_docs = []

    for idx in range(1, 51):
        target_event = event1 if idx <= 35 else event2
        target_collector = collector1_doc if idx % 2 == 0 else collector2_doc
        target_guest = guest_docs[(idx - 1) % len(guest_docs)]
        amount_val = amounts[(idx - 1) % len(amounts)]
        method = methods[(idx - 1) % len(methods)]
        status = "locked" if idx <= 15 else ("verified" if idx <= 35 else "pending")
        txn_id = f"TXN-{idx:06d}"
        rcp_id = f"RCP-{idx:06d}"

        txn_oid = ObjectId()
        txn_time = now - timedelta(hours=(51 - idx) * 2)

        txn_doc = {
            "_id": txn_oid,
            "transaction_id": txn_id,
            "event_id": target_event["_id"],
            "event_public_id": target_event["event_id"],
            "guest_id": target_guest["_id"],
            "guest_public_id": target_guest["guest_id"],
            "collector_id": target_collector["_id"],
            "collector_public_id": target_collector["collector_id"],
            "amount": Decimal128(Decimal(str(amount_val))),
            "currency": "INR",
            "payment_method": method,
            "transaction_type": "contribution",
            "status": status,
            "reference_number": f"REF-{100000+idx}" if method != "cash" else None,
            "idempotency_key": f"seed-key-{idx}",
            "notes": "Blessings and best wishes" if idx % 2 == 0 else "",
            "created_at": txn_time,
            "updated_at": txn_time,
            "verified_by": admin_user["_id"] if status in ("verified", "locked") else None,
            "verified_at": txn_time + timedelta(minutes=15) if status in ("verified", "locked") else None,
            "locked_at": txn_time + timedelta(hours=1) if status == "locked" else None,
        }
        txn_docs.append(txn_doc)

        v_token = str(uuid.uuid4())
        v_hash = hash_receipt_token(settings, v_token)
        receipt_doc = {
            "_id": ObjectId(),
            "receipt_id": rcp_id,
            "transaction_id": txn_oid,
            "transaction_public_id": txn_id,
            "event_id": target_event["_id"],
            "event_public_id": target_event["event_id"],
            "guest_id": target_guest["_id"],
            "collector_id": target_collector["_id"],
            "verification_token_hash": v_hash,
            "issued_at": txn_time,
            "verification_status": "valid",
        }
        receipt_docs.append(receipt_doc)

    await db["transactions"].insert_many(txn_docs)
    await db["receipts"].insert_many(receipt_docs)
    print(f"[+] Transactions & Receipts created: {len(txn_docs)} records")

    # 7. Gifts (10 Physical Gifts)
    gift_items = [
        ("Prestige Mixer Grinder 750W", "household_item", 1, 3800),
        ("Pure Silver Diya Lamp Set", "decorative", 2, 8500),
        ("Kanchipuram Silk Saree", "clothing", 1, 14000),
        ("Philips Air Fryer 4.1L", "electronics", 1, 6200),
        ("Wonderchef Non-Stick Cookware Set", "household_item", 1, 4500),
        ("Titan Couple Wrist Watch Set", "accessories", 1, 11500),
        ("Brass Radha Krishna Idol", "decorative", 1, 5400),
        ("Morphy Richards Microwave Oven", "electronics", 1, 8900),
        ("Tupperware Executive Dinner Set", "household_item", 1, 3200),
        ("Gold Plated Pooja Thali Set", "decorative", 1, 4000),
    ]

    gift_docs = []
    for g_idx, (desc, g_type, qty, val) in enumerate(gift_items, start=1):
        target_event = event1 if g_idx <= 7 else event2
        target_guest = guest_docs[g_idx - 1]
        target_collector = collector1_doc if g_idx % 2 == 0 else collector2_doc
        gift_docs.append({
            "_id": ObjectId(),
            "gift_id": f"GFT-{g_idx:06d}",
            "event_id": target_event["_id"],
            "guest_id": target_guest["_id"],
            "collector_id": target_collector["_id"],
            "gift_type": g_type,
            "description": desc,
            "quantity": qty,
            "estimated_value": Decimal128(Decimal(str(val))),
            "currency": "INR",
            "notes": "Delivered with gift wrapping",
            "status": "received",
            "created_at": now - timedelta(hours=g_idx * 3),
        })
    await db["gifts"].insert_many(gift_docs)
    print(f"[+] Physical Gifts created: {len(gift_docs)} items")

    # 8. Sample Reconciliation
    recon_doc = {
        "_id": ObjectId(),
        "reconciliation_id": "REC-000001",
        "event_id": event1["_id"],
        "collector_id": collector1_doc["_id"],
        "expected_cash": Decimal128(Decimal("45000.00")),
        "actual_cash": Decimal128(Decimal("45000.00")),
        "difference": Decimal128(Decimal("0.00")),
        "reason": "Shift 1 cash drawer balance verified exactly",
        "status": "verified",
        "submitted_by": col1_user["_id"],
        "submitted_at": now - timedelta(hours=2),
        "verified_by": admin_user["_id"],
        "verified_at": now - timedelta(hours=1),
    }
    await db["reconciliations"].insert_one(recon_doc)
    print("[+] Sample Reconciliation created: REC-000001")

    # 9. Audit Logs (Initial entries)
    await db["audit_logs"].insert_many([
        {
            "_id": ObjectId(),
            "user_id": admin_user["_id"],
            "event_id": event1["_id"],
            "action": "CREATE",
            "entity_type": "event",
            "entity_id": event1["_id"],
            "old_value": {},
            "new_value": {"event_name": event1["event_name"]},
            "ip_address": "127.0.0.1",
            "user_agent": "SeedScript/1.0",
            "request_id": "seed-req-001",
            "timestamp": now - timedelta(days=2),
        },
        {
            "_id": ObjectId(),
            "user_id": admin_user["_id"],
            "event_id": event1["_id"],
            "action": "LOCK",
            "entity_type": "transaction",
            "entity_id": txn_docs[0]["_id"],
            "old_value": {"status": "verified"},
            "new_value": {"status": "locked"},
            "ip_address": "127.0.0.1",
            "user_agent": "SeedScript/1.0",
            "request_id": "seed-req-002",
            "timestamp": now - timedelta(hours=1),
        }
    ])
    print("[+] Audit logs initialized")

    print("\n--- Development Credentials ---")
    print("Admin:     admin / Admin@GiftLedger123!   (email: admin@giftledger.dev)")
    print("Collector: collector1 / Collector1@123!   (email: collector1@giftledger.dev)")
    print("Collector: collector2 / Collector2@123!   (email: collector2@giftledger.dev)")
    print("Viewer:    viewer / Viewer@123!           (email: viewer@giftledger.dev)")
    print("---------------------------------")
    await database_manager.close()


if __name__ == "__main__":
    asyncio.run(seed())
