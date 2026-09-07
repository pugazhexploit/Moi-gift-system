"""Authoritative Decimal and Decimal128 conversion helpers."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from bson.decimal128 import Decimal128


MONEY_QUANTUM = Decimal("0.01")


def normalize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def to_decimal128(value: Decimal) -> Decimal128:
    return Decimal128(normalize_money(value))


def from_decimal128(value: Decimal128 | Decimal) -> Decimal:
    return normalize_money(value.to_decimal() if isinstance(value, Decimal128) else value)
