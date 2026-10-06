"""Deterministic metrics. Every result includes the denominator/eligibility used."""
from __future__ import annotations

import pandas as pd
from .business_rules import (CONTACT_COSTS, SLA_HOURS, SLA_BREACH_COST, TRANSFER_COST,
                             REPLACEMENT_SHIPPING_COST, DEFAULT_ANNUAL_COST_PER_HIRE)


class Analytics:
    def __init__(self, tickets: pd.DataFrame):
        self.all = tickets.copy()
        self.t = self.all[self.all["analysis_in_scope"]].copy()

    @staticmethod
    def _records(frame: pd.DataFrame, columns: list[str]) -> list[dict]:
        return frame[columns].where(pd.notna(frame[columns]), None).to_dict("records")

    def team_volume(self) -> dict:
        g = self.t.groupby("assigned_team", dropna=False).size().reset_index(name="tickets").sort_values("tickets", ascending=False)
        return {"metric": "ticket volume", "denominator": len(self.t), "rows": self._records(g, ["assigned_team", "tickets"])}

    def monthly_team_volume(self) -> dict:
        x = self.t.assign(month=self.t["created_at"].dt.to_period("M").astype(str))
        g = x.groupby(["month", "assigned_team"], dropna=False).size().reset_index(name="tickets")
        return {"metric": "monthly ticket volume", "rows": self._records(g.sort_values(["month", "assigned_team"]), ["month", "assigned_team", "tickets"])}

    def category_volume(self) -> dict:
        issue_col = "issue" if "issue" in self.t.columns else "assigned_team"
        g = self.t.groupby(issue_col, dropna=False).size().reset_index(name="tickets").sort_values("tickets", ascending=False)
        return {"metric": "category volume", "denominator": len(self.t), "rows": self._records(g, [issue_col, "tickets"])}

    def monthly_category_volume(self) -> dict:
        issue_col = "issue" if "issue" in self.t.columns else "assigned_team"
        x = self.t.assign(month=self.t["created_at"].dt.to_period("M").astype(str))
        g = x.groupby(["month", issue_col], dropna=False).size().reset_index(name="tickets")
        return {"metric": "monthly category volume", "rows": self._records(g.sort_values(["month", issue_col]), ["month", issue_col, "tickets"])}

    def handle_time(self) -> dict:
        x = self.t.dropna(subset=["first_response_at", "resolved_at"]).copy()
        x["hours"] = (x["resolved_at"] - x["first_response_at"]).dt.total_seconds() / 3600
        x = x[x["hours"] >= 0]
        g = x.groupby("assigned_team")["hours"].agg(observations="count", median_hours="median", average_hours="mean").reset_index()
        return {"metric": "handle time (first response to resolution)", "eligible_tickets": len(x), "rows": self._records(g, list(g.columns))}

    def transfers(self) -> dict:
        x = self.t[self.t["transfers_available"]].copy()
        x["transfers"] = x["transfers"].fillna(0).clip(lower=0)
        g = x.groupby("assigned_team")["transfers"].sum().reset_index()
        g["transfer_cost_inr"] = g["transfers"] * TRANSFER_COST
        return {"metric": "internal transfers (current helpdesk only)", "eligible_tickets": len(x), "excluded_legacy_tickets": int(self.t["is_legacy"].sum()), "rows": self._records(g.sort_values("transfers", ascending=False), list(g.columns))}

    def sla_breaches(self) -> dict:
        x = self.t.dropna(subset=["created_at", "first_response_at", "channel_normalized"]).copy()
        x["response_hours"] = (x["first_response_at"] - x["created_at"]).dt.total_seconds() / 3600
        x = x[x["response_hours"] >= 0]
        x["breach"] = x.apply(lambda r: r.response_hours > SLA_HOURS[r.channel_normalized], axis=1)
        g = x.groupby("assigned_team")["breach"].agg(eligible_tickets="count", breaches="sum").reset_index()
        g["breach_rate"] = g["breaches"] / g["eligible_tickets"]
        g["sla_credit_cost_inr"] = g["breaches"] * SLA_BREACH_COST
        return {"metric": "first-response SLA breaches", "rows": self._records(g, list(g.columns))}

    def csat(self) -> dict:
        x = self.t[self.t["csat"].between(1, 5)].copy()
        g = x.groupby("assigned_team")["csat"].agg(responses="count", average_csat="mean").reset_index()
        return {"metric": "CSAT (blank/no-response excluded)", "eligible_responses": len(x), "rows": self._records(g, list(g.columns))}

    def repeat_contacts(self) -> dict:
        issue_col = "issue" if "issue" in self.t.columns else "assigned_team"
        x = self.t.dropna(subset=["customer_id", "created_at"]).copy().sort_values(["customer_id", issue_col, "created_at"])
        x["is_repeat_contact"] = False
        x["fcr_eligible"] = False
        latest = x["created_at"].max()
        for _, idx in x.groupby(["customer_id", issue_col], dropna=False).groups.items():
            ids = list(idx)
            for pos, ticket_idx in enumerate(ids):
                resolved = x.at[ticket_idx, "resolved_at"] if "resolved_at" in x else pd.NaT
                if pd.notna(resolved) and latest >= resolved + pd.Timedelta(days=30):
                    x.at[ticket_idx, "fcr_eligible"] = True
                    later = x.loc[ids[pos + 1:], "created_at"]
                    if ((later > resolved) & (later <= resolved + pd.Timedelta(days=30))).any():
                        # Attribute repeat status to the later contact too.
                        repeat_idx = later[(later > resolved) & (later <= resolved + pd.Timedelta(days=30))].index
                        x.loc[repeat_idx, "is_repeat_contact"] = True
        x["repeat_contact_cost_inr"] = x["channel_normalized"].map(CONTACT_COSTS).fillna(0) * x["is_repeat_contact"]
        eligible = x[x["fcr_eligible"]]
        return {"metric": "repeat contacts / FCR (same customer and issue within 30 days)", "fcr_denominator": len(eligible), "fcr": None if not len(eligible) else float((~eligible["is_repeat_contact"]).mean()), "repeat_contact_cost_inr": float(x["repeat_contact_cost_inr"].sum()), "repeat_contacts": int(x["is_repeat_contact"].sum())}

    def financial_impact(self, dimension: str = "assigned_team") -> dict:
        x = self.t.copy()
        product_cost = "product_unit_cost" if "product_unit_cost" in x else None
        product_values = x.get(product_cost, pd.Series(0, index=x.index))
        x["replacement_cost_inr"] = x["replacement"] * (pd.to_numeric(product_values, errors="coerce").fillna(0) + REPLACEMENT_SHIPPING_COST)
        g = x.groupby(dimension, dropna=False).agg(tickets=("ticket_id", "count"), refunds_inr=("refund_amount", "sum"), replacements=("replacement", "sum"), replacement_cost_inr=("replacement_cost_inr", "sum")).reset_index()
        g["measured_direct_impact_inr"] = g["refunds_inr"] + g["replacement_cost_inr"]
        return {"metric": f"refund and replacement impact by {dimension}", "caution": "Refunds/replacements are measured impact, not necessarily avoidable cost.", "rows": self._records(g.sort_values("measured_direct_impact_inr", ascending=False), list(g.columns))}

    def staffing_business_case(self, hire_count: int = 2, focus_team: str | None = None) -> dict:
        """Compare measured pressure with a transparent, scalable hiring assumption."""
        if hire_count < 1:
            raise ValueError("hire_count must be at least 1")
        annual_cost = hire_count * DEFAULT_ANNUAL_COST_PER_HIRE
        transfers = self.transfers()["rows"]
        sla = self.sla_breaches()["rows"]
        pressure = {r["assigned_team"]: r.get("transfer_cost_inr", 0) for r in transfers}
        for r in sla:
            pressure[r["assigned_team"]] = pressure.get(r["assigned_team"], 0) + r.get("sla_credit_cost_inr", 0)
        rows = [{"team": k, "observed_transfer_plus_sla_inr": v, "share_of_hiring_cost": v / annual_cost} for k, v in pressure.items()]
        if focus_team:
            rows = [r for r in rows if r["team"].casefold() == focus_team.casefold()]
        return {
            "metric": "staffing decision context",
            "hire_count": hire_count,
            "annual_cost_per_hire_inr": DEFAULT_ANNUAL_COST_PER_HIRE,
            "total_annual_hiring_cost_inr": annual_cost,
            "focus_team": focus_team,
            "interpretation": "Hiring cost is scaled from the Rs 9,00,000 two-hire planning assumption. Observed transfer and SLA costs are a signal, not proof that hires will eliminate them. Compare workload, root causes, and recoverable cost before hiring.",
            "rows": sorted(rows, key=lambda r: r["observed_transfer_plus_sla_inr"], reverse=True),
        }
