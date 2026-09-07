"""MongoDB aggregation pipelines for authoritative reporting."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from bson.decimal128 import Decimal128


VALID_TRANSACTION_STATUSES = ["pending", "verified", "locked"]


class ReportRepository:
    def __init__(self, database: Any) -> None:
        self.events = database["events"]
        self.guests = database["guests"]
        self.transactions = database["transactions"]
        self.gifts = database["gifts"]
        self.collectors = database["collectors"]
        self.assignments = database["event_collectors"]
        self.reconciliations = database["reconciliations"]

    @staticmethod
    def _event_match(event_ids: list[Any] | None) -> dict[str, Any]:
        return {} if event_ids is None else {"event_id": {"$in": event_ids}}

    @staticmethod
    def _date_match(start_at: datetime | None, end_at: datetime | None) -> dict[str, Any]:
        bounds: dict[str, Any] = {}
        if start_at is not None:
            bounds["$gte"] = start_at
        if end_at is not None:
            bounds["$lte"] = end_at
        return {"created_at": bounds} if bounds else {}

    async def dashboard(
        self, event_ids: list[Any] | None, start_at: datetime | None, end_at: datetime | None
    ) -> dict[str, Any]:
        transaction_match = {
            **self._event_match(event_ids),
            **self._date_match(start_at, end_at),
        }
        cursor = self.transactions.aggregate(
            [
                {"$match": transaction_match},
                {
                    "$facet": {
                        "totals": [
                            {
                                "$group": {
                                    "_id": None,
                                    "total_contributions": {
                                        "$sum": {
                                            "$cond": [
                                                {"$in": ["$status", VALID_TRANSACTION_STATUSES]},
                                                "$amount",
                                                Decimal128("0.00"),
                                            ]
                                        }
                                    },
                                    "total_cash": {
                                        "$sum": {
                                            "$cond": [
                                                {
                                                    "$and": [
                                                        {"$eq": ["$payment_method", "cash"]},
                                                        {"$in": ["$status", VALID_TRANSACTION_STATUSES]},
                                                    ]
                                                },
                                                "$amount",
                                                Decimal128("0.00"),
                                            ]
                                        }
                                    },
                                    "total_online": {
                                        "$sum": {
                                            "$cond": [
                                                {
                                                    "$and": [
                                                        {"$ne": ["$payment_method", "cash"]},
                                                        {"$in": ["$status", VALID_TRANSACTION_STATUSES]},
                                                    ]
                                                },
                                                "$amount",
                                                Decimal128("0.00"),
                                            ]
                                        }
                                    },
                                    "verified_amount": {
                                        "$sum": {
                                            "$cond": [
                                                {"$in": ["$status", ["verified", "locked"]]},
                                                "$amount",
                                                Decimal128("0.00"),
                                            ]
                                        }
                                    },
                                    "pending_amount": {
                                        "$sum": {
                                            "$cond": [
                                                {"$eq": ["$status", "pending"]},
                                                "$amount",
                                                Decimal128("0.00"),
                                            ]
                                        }
                                    },
                                }
                            }
                        ],
                        "cash_vs_online": [
                            {"$match": {"status": {"$in": VALID_TRANSACTION_STATUSES}}},
                            {
                                "$group": {
                                    "_id": {
                                        "$cond": [
                                            {"$eq": ["$payment_method", "cash"]},
                                            "cash",
                                            "online",
                                        ]
                                    },
                                    "amount": {"$sum": "$amount"},
                                }
                            }
                        ],
                        "contributions_over_time": [
                            {"$match": {"status": {"$in": VALID_TRANSACTION_STATUSES}}},
                            {
                                "$group": {
                                    "_id": {
                                        "$dateToString": {
                                            "format": "%Y-%m-%d",
                                            "date": "$created_at",
                                            "timezone": "UTC",
                                        }
                                    },
                                    "amount": {"$sum": "$amount"},
                                }
                            },
                            {"$sort": {"_id": 1}},
                        ],
                        "hourly_collection": [
                            {"$match": {"status": {"$in": VALID_TRANSACTION_STATUSES}}},
                            {
                                "$group": {
                                    "_id": {"$hour": {"date": "$created_at", "timezone": "UTC"}},
                                    "amount": {"$sum": "$amount"},
                                }
                            },
                            {"$sort": {"_id": 1}},
                        ],
                        "transaction_status": [
                            {
                                "$group": {
                                    "_id": "$status",
                                    "transactions": {"$sum": 1},
                                    "amount": {"$sum": "$amount"},
                                }
                            },
                            {"$sort": {"_id": 1}},
                        ],
                        "collector_wise_collection": [
                            {"$match": {"status": {"$in": VALID_TRANSACTION_STATUSES}}},
                            {
                                "$group": {
                                    "_id": "$collector_id",
                                    "transactions": {"$sum": 1},
                                    "amount": {"$sum": "$amount"},
                                }
                            },
                            {
                                "$lookup": {
                                    "from": "collectors",
                                    "localField": "_id",
                                    "foreignField": "_id",
                                    "as": "collector",
                                }
                            },
                            {"$unwind": {"path": "$collector", "preserveNullAndEmptyArrays": True}},
                            {
                                "$project": {
                                    "_id": 0,
                                    "collector_id": "$collector.collector_id",
                                    "collector_name": {"$ifNull": ["$collector.name", "Unknown collector"]},
                                    "transactions": 1,
                                    "amount": 1,
                                }
                            },
                            {"$sort": {"amount": -1}},
                        ],
                    }
                },
            ]
        )
        transaction_data = await self._first(cursor, {})
        guest_match = {**self._event_match(event_ids), **self._date_match(start_at, end_at)}
        total_guests = await self.guests.count_documents(guest_match)
        gift_cursor = self.gifts.aggregate(
            [
                {
                    "$match": {
                        **self._event_match(event_ids),
                        **self._date_match(start_at, end_at),
                        "status": "received",
                    }
                },
                {
                    "$facet": {
                        "totals": [{"$group": {"_id": None, "quantity": {"$sum": "$quantity"}}}],
                        "categories": [
                            {"$group": {"_id": "$gift_type", "quantity": {"$sum": "$quantity"}}},
                            {"$sort": {"quantity": -1, "_id": 1}},
                        ],
                    }
                },
            ]
        )
        gift_data = await self._first(gift_cursor, {})
        collector_match = {**self._event_match(event_ids), "status": "active"}
        collector_count = await self.assignments.count_documents(collector_match)
        reconciliation_cursor = self.reconciliations.aggregate(
            [
                {
                    "$match": {
                        **self._event_match(event_ids),
                        "status": "mismatch",
                    }
                },
                {"$group": {"_id": None, "amount": {"$sum": {"$abs": "$difference"}}}},
            ]
        )
        unreconciled = await self._first(reconciliation_cursor, {})
        return {
            "transactions": transaction_data,
            "total_guests": total_guests,
            "gifts": gift_data,
            "collectors": collector_count,
            "unreconciled_amount": unreconciled.get("amount", Decimal128("0.00")),
        }

    async def collector_report(
        self, collector_id: Any, event_ids: list[Any] | None
    ) -> dict[str, Any]:
        cursor = self.transactions.aggregate(
            [
                {"$match": {**self._event_match(event_ids), "collector_id": collector_id}},
                {
                    "$group": {
                        "_id": None,
                        "transactions": {"$sum": 1},
                        "cash": {
                            "$sum": {
                                "$cond": [
                                    {
                                        "$and": [
                                            {"$eq": ["$payment_method", "cash"]},
                                            {"$in": ["$status", VALID_TRANSACTION_STATUSES]},
                                        ]
                                    },
                                    "$amount",
                                    Decimal128("0.00"),
                                ]
                            }
                        },
                        "online": {
                            "$sum": {
                                "$cond": [
                                    {
                                        "$and": [
                                            {"$ne": ["$payment_method", "cash"]},
                                            {"$in": ["$status", VALID_TRANSACTION_STATUSES]},
                                        ]
                                    },
                                    "$amount",
                                    Decimal128("0.00"),
                                ]
                            }
                        },
                        "total": {
                            "$sum": {
                                "$cond": [
                                    {"$in": ["$status", VALID_TRANSACTION_STATUSES]},
                                    "$amount",
                                    Decimal128("0.00"),
                                ]
                            }
                        },
                        "pending": {
                            "$sum": {
                                "$cond": [
                                    {"$eq": ["$status", "pending"]},
                                    "$amount",
                                    Decimal128("0.00"),
                                ]
                            }
                        },
                    }
                },
            ]
        )
        transaction_data = await self._first(cursor, {})
        reconciliation_cursor = self.reconciliations.aggregate(
            [
                {"$match": {**self._event_match(event_ids), "collector_id": collector_id, "status": "mismatch"}},
                {"$group": {"_id": None, "mismatch": {"$sum": {"$abs": "$difference"}}}},
            ]
        )
        reconciliation_data = await self._first(reconciliation_cursor, {})
        return {**transaction_data, "mismatch": reconciliation_data.get("mismatch", Decimal128("0.00"))}

    async def guest_report(
        self, event_ids: list[Any] | None, page: int, limit: int
    ) -> tuple[list[dict[str, Any]], int]:
        pipeline: list[dict[str, Any]] = [
            {"$match": self._event_match(event_ids)},
            {
                "$facet": {
                    "items": [
                        {"$sort": {"full_name": 1, "guest_id": 1}},
                        {"$skip": (page - 1) * limit},
                        {"$limit": limit},
                        {
                            "$lookup": {
                                "from": "transactions",
                                "let": {"guest_id": "$_id"},
                                "pipeline": [
                                    {
                                        "$match": {
                                            "$expr": {"$eq": ["$guest_id", "$$guest_id"]},
                                            "status": {"$in": VALID_TRANSACTION_STATUSES},
                                        }
                                    },
                                    {"$group": {"_id": None, "contribution": {"$sum": "$amount"}}},
                                ],
                                "as": "contributions",
                            }
                        },
                        {
                            "$lookup": {
                                "from": "gifts",
                                "let": {"guest_id": "$_id"},
                                "pipeline": [
                                    {
                                        "$match": {
                                            "$expr": {"$eq": ["$guest_id", "$$guest_id"]},
                                            "status": "received",
                                        }
                                    },
                                    {
                                        "$group": {
                                            "_id": None,
                                            "gift_items": {"$sum": "$quantity"},
                                            "gift_estimated_value": {
                                                "$sum": {"$ifNull": ["$estimated_value", Decimal128("0.00")]}
                                            },
                                        }
                                    },
                                ],
                                "as": "gifts",
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "guest_id": 1,
                                "full_name": 1,
                                "family_name": 1,
                                "relationship": 1,
                                "contribution": {
                                    "$ifNull": [
                                        {"$arrayElemAt": ["$contributions.contribution", 0]},
                                        Decimal128("0.00"),
                                    ]
                                },
                                "gift_items": {
                                    "$ifNull": [{"$arrayElemAt": ["$gifts.gift_items", 0]}, 0]
                                },
                                "gift_estimated_value": {
                                    "$ifNull": [
                                        {"$arrayElemAt": ["$gifts.gift_estimated_value", 0]},
                                        Decimal128("0.00"),
                                    ]
                                },
                            }
                        },
                    ],
                    "meta": [{"$count": "total"}],
                }
            },
        ]
        cursor = self.guests.aggregate(pipeline)
        result = await self._first(cursor, {"items": [], "meta": []})
        return result["items"], result["meta"][0]["total"] if result["meta"] else 0

    async def reconciliation_report(
        self, event_ids: list[Any] | None, page: int, limit: int
    ) -> tuple[list[dict[str, Any]], int]:
        cursor = self.reconciliations.aggregate(
            [
                {"$match": self._event_match(event_ids)},
                {
                    "$facet": {
                        "items": [
                            {"$sort": {"submitted_at": -1}},
                            {"$skip": (page - 1) * limit},
                            {"$limit": limit},
                            {
                                "$lookup": {
                                    "from": "collectors",
                                    "localField": "collector_id",
                                    "foreignField": "_id",
                                    "as": "collector",
                                }
                            },
                            {"$unwind": {"path": "$collector", "preserveNullAndEmptyArrays": True}},
                            {
                                "$project": {
                                    "_id": 0,
                                    "reconciliation_id": 1,
                                    "event_public_id": 1,
                                    "collector_public_id": 1,
                                    "collector_name": {"$ifNull": ["$collector.name", "Unknown collector"]},
                                    "expected_cash": 1,
                                    "actual_cash": 1,
                                    "difference": 1,
                                    "status": 1,
                                    "submitted_at": 1,
                                    "verified_at": 1,
                                    "resolved_at": 1,
                                }
                            },
                        ],
                        "meta": [{"$count": "total"}],
                    }
                },
            ]
        )
        result = await self._first(cursor, {"items": [], "meta": []})
        return result["items"], result["meta"][0]["total"] if result["meta"] else 0

    @staticmethod
    async def _first(cursor: Any, default: dict[str, Any]) -> dict[str, Any]:
        async for document in cursor:
            return document
        return default
