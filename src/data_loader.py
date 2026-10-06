"""Load Vireo source files, normalize column names, and retain audit flags."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import pandas as pd

from .business_rules import ANALYSIS_START, ANALYSIS_END, CURRENT_HELPDESK_START, channel_key

REQUIRED = ("tickets", "orders", "customers", "products", "agents")
ALIASES = {
    "ticket_id": ("ticketid", "id", "case_id"), "customer_id": ("customerid", "customer"),
    "order_id": ("orderid", "order"), "agent_id": ("agentid", "resolved_by", "resolver_id"),
    "product_id": ("productid", "sku_id", "sku", "product_sku"), "assigned_team": ("assignedteam", "initial_team"),
    "channel": ("contact_channel", "source_channel"), "created_at": ("created", "created_date"),
    "first_response_at": ("first_response", "firstreply_at", "first_reply_at"),
    "resolved_at": ("resolved", "resolution_at", "closed_at"), "transfers": ("transfer_count",),
    "csat": ("csat_score", "satisfaction"), "status": ("ticket_status",),
    "issue": ("issue_type", "reason", "category"), "refund_amount": ("refund", "refund_value", "refund_amount_inr"),
    "replacement": ("is_replacement", "replacement_flag", "replacement_issued"), "unit_cost": ("cost", "product_cost", "unit_cost_inr"),
}


def _snake(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")


def _normalise_columns(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out.columns = [_snake(c) for c in out.columns]
    for canonical, aliases in ALIASES.items():
        if canonical in out.columns:
            continue
        match = next((a for a in aliases if a in out.columns), None)
        if match:
            out = out.rename(columns={match: canonical})
    return out


def _read_csv(path: Path) -> pd.DataFrame:
    # utf-8-sig handles Excel exports; fallback covers older Windows exports.
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin-1")


def _parse_timestamp(values: pd.Series) -> pd.Series:
    """Preserve naive IST exports; convert explicitly offset API values to IST."""
    parsed = pd.to_datetime(values, errors="coerce")
    if isinstance(parsed.dtype, pd.DatetimeTZDtype):
        return parsed.dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    return parsed


@dataclass
class VireoData:
    tickets: pd.DataFrame
    orders: pd.DataFrame
    customers: pd.DataFrame
    products: pd.DataFrame
    agents: pd.DataFrame
    quality_notes: list[str]


def load_data(data_dir: str | Path) -> VireoData:
    root = Path(data_dir)
    found: dict[str, pd.DataFrame] = {}
    missing: list[str] = []
    for name in REQUIRED:
        path = root / f"{name}.csv"
        if path.exists():
            found[name] = _normalise_columns(_read_csv(path))
        else:
            missing.append(path.name)
    if missing:
        raise FileNotFoundError(f"Missing required source files in {root}: {', '.join(missing)}")

    tickets = found["tickets"].copy()
    required_ticket_columns = {"ticket_id", "customer_id", "created_at", "assigned_team", "channel"}
    absent = required_ticket_columns - set(tickets.columns)
    if absent:
        raise ValueError(f"tickets.csv is missing required columns: {', '.join(sorted(absent))}")
    for col in ("created_at", "first_response_at", "resolved_at"):
        if col in tickets:
            tickets[col] = _parse_timestamp(tickets[col])
    tickets["channel_normalized"] = tickets["channel"].map(channel_key)
    tickets["analysis_in_scope"] = tickets["created_at"].dt.date.between(ANALYSIS_START, ANALYSIS_END)
    tickets["is_legacy"] = tickets["created_at"].dt.date < CURRENT_HELPDESK_START
    tickets["transfers_available"] = ~tickets["is_legacy"] & tickets.get("transfers", pd.Series(index=tickets.index)).notna()
    tickets["transfers"] = pd.to_numeric(tickets.get("transfers", 0), errors="coerce")
    tickets.loc[tickets["is_legacy"], "transfers"] = pd.NA  # Not zero: unavailable by policy.
    tickets["csat"] = pd.to_numeric(tickets.get("csat", pd.Series(pd.NA, index=tickets.index)), errors="coerce")
    tickets["refund_amount"] = pd.to_numeric(tickets.get("refund_amount", 0), errors="coerce").fillna(0)
    tickets["replacement"] = tickets.get("replacement", pd.Series(False, index=tickets.index)).astype(str).str.lower().isin(["1", "true", "yes", "y"])

    products = found["products"].copy()
    notes = []
    # Re-imported legacy exports can repeat a case. Keep the most complete/latest row
    # rather than silently double-counting a ticket in every metric.
    duplicate_count = int(tickets.duplicated("ticket_id", keep=False).sum())
    if duplicate_count:
        tickets["_completeness"] = tickets.notna().sum(axis=1)
        sort_columns = ["ticket_id", "_completeness"] + (["resolved_at"] if "resolved_at" in tickets else [])
        tickets = tickets.sort_values(sort_columns, ascending=[True, False] + ([False] if "resolved_at" in tickets else []), na_position="last")
        tickets = tickets.drop_duplicates("ticket_id", keep="first").drop(columns="_completeness")
        notes.append(f"Deduplicated {duplicate_count} repeated ticket-id rows, keeping the most complete record.")
    legacy_count = int((tickets["created_at"].dt.date < ANALYSIS_START).sum())
    if legacy_count:
        notes.append(f"{legacy_count} pre-2025 legacy rows are excluded from primary analysis.")
    if tickets["channel_normalized"].isna().any():
        notes.append("Tickets with unknown channels are excluded from channel-based SLA/contact-cost metrics.")
    if "product_id" in tickets and "product_id" in products:
        if products["product_id"].duplicated().any():
            raise ValueError("products.csv has duplicate product_id values; resolve them before joining to avoid duplicated ticket metrics.")
        before = len(tickets)
        tickets = tickets.merge(products.add_prefix("product_"), how="left", left_on="product_id", right_on="product_product_id")
        notes.append(f"Product join retained all {before} ticket rows.")
    return VireoData(tickets, found["orders"], found["customers"], products, found["agents"], notes)
