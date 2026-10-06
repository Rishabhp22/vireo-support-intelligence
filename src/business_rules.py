"""Policy constants. Keep all planning assumptions visible and auditable."""
from __future__ import annotations

from datetime import date

ANALYSIS_START = date(2025, 1, 1)
ANALYSIS_END = date(2026, 6, 30)
CURRENT_HELPDESK_START = date(2025, 9, 14)
SLA_HOURS = {"chat": 0.25, "voice": 2.0, "social": 4.0, "email": 8.0}
CONTACT_COSTS = {"chat": 210.0, "email": 260.0, "voice": 520.0, "social": 240.0}
TRANSFER_COST = 305.0
SLA_BREACH_COST = 350.0
REPLACEMENT_SHIPPING_COST = 340.0
AGENT_HOURLY_COST = 165.0
SHIFT_HOURS = 8
DEFAULT_TWO_HIRE_ANNUAL_COST = 900_000.0
DEFAULT_ANNUAL_COST_PER_HIRE = DEFAULT_TWO_HIRE_ANNUAL_COST / 2


def channel_key(value: object) -> str | None:
    """Normalize common channel labels without guessing an unknown channel."""
    text = str(value).strip().lower()
    aliases = {"voice callback": "voice", "phone": "voice", "call": "voice",
               "instagram": "social", "x": "social", "facebook": "social"}
    text = aliases.get(text, text)
    return text if text in SLA_HOURS else None
