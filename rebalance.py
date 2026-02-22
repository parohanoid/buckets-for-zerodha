"""
rebalance.py

Given a monthly SIP budget, distributes it across your actual funds
so that each risk bucket receives the proportion demanded by your goals.

Usage (from main.py or standalone):
    from rebalance import compute_rebalance
    plan = compute_rebalance(goal_results, risk_totals, mappings, monthly_budget)
"""


def compute_rebalance(
    goal_results: list,
    risk_totals: dict,
    mappings: dict,
    monthly_budget: float,
) -> dict:
    """
    Step 1 — Aggregate SIP needed per risk bucket across all goals.
    Step 2 — Normalise to the user's actual monthly budget.
    Step 3 — Within each risk bucket, split equally among the mapped funds
              (equal split is the safest default; user can override weights later).

    Returns a dict:
      {
        "total_budget": float,
        "by_risk": {
            "low":    {"sip": float, "funds": [{"name": str, "sip": float}, ...]},
            ...
        },
        "by_fund": {"<tradingsymbol>": float, ...},
      }
    """
    # ── Step 1: raw SIP need per risk bucket ─────────────────────────────────
    raw_need: dict[str, float] = {}
    for g in goal_results:
        for risk, amount in g.get("sip_per_risk", {}).items():
            raw_need[risk] = raw_need.get(risk, 0.0) + amount

    total_raw = sum(raw_need.values())

    # ── Step 2: scale to monthly_budget ──────────────────────────────────────
    if total_raw == 0:
        # All goals already funded — nothing to do
        scaled: dict[str, float] = {risk: 0.0 for risk in mappings}
    else:
        scaled = {
            risk: round((need / total_raw) * monthly_budget, 2)
            for risk, need in raw_need.items()
        }
        # Distribute any budget not yet assigned (from risk categories with no gap)
        # proportionally among the buckets that do have a gap.
        unassigned = monthly_budget - sum(scaled.values())
        if unassigned and scaled:
            # add remainder to highest-need bucket to avoid losing a rupee to rounding
            top_risk = max(scaled, key=lambda r: scaled[r])
            scaled[top_risk] = round(scaled[top_risk] + unassigned, 2)

    # ── Step 3: split each bucket equally among its funds ────────────────────
    by_risk:  dict = {}
    by_fund:  dict = {}

    for risk, budget_for_risk in scaled.items():
        fund_names = mappings.get(risk, [])
        if not fund_names:
            continue

        per_fund = round(budget_for_risk / len(fund_names), 2)
        # Fix rounding remainder on first fund
        remainder = round(budget_for_risk - per_fund * len(fund_names), 2)

        fund_sips = []
        for i, name in enumerate(fund_names):
            amount = per_fund + (remainder if i == 0 else 0.0)
            # Find the tradingsymbol for this fund name
            symbol = _find_symbol(name, risk_totals)
            fund_sips.append({"name": name, "tradingsymbol": symbol, "sip": round(amount, 2)})
            if symbol:
                by_fund[symbol] = by_fund.get(symbol, 0.0) + round(amount, 2)

        by_risk[risk] = {"sip": budget_for_risk, "funds": fund_sips}

    return {
        "total_budget": monthly_budget,
        "by_risk":      by_risk,
        "by_fund":      by_fund,
    }


def _find_symbol(fund_name: str, risk_totals: dict) -> str | None:
    for risk_data in risk_totals.values():
        for f in risk_data["funds"]:
            if f["name"] == fund_name:
                return f["tradingsymbol"]
    return None