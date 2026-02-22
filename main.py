import logging
import json
import os
import webbrowser
from dotenv import load_dotenv
from kiteconnect import KiteConnect


# ── helpers ───────────────────────────────────────────────────────────────────

def load_json(path: str) -> dict | list:
    with open(path) as f:
        return json.load(f)


def build_risk_totals(funds: list, mappings: dict) -> dict:
    """Return cost-basis and current-value totals grouped by risk category."""
    totals = {risk: {"cost": 0.0, "current": 0.0, "funds": []} for risk in mappings}

    for fund in funds:
        name = fund["fund"]
        cost_value    = fund["quantity"] * fund["average_price"]
        current_value = fund["quantity"] * fund["last_price"] if fund["last_price"] else cost_value

        for risk, fund_list in mappings.items():
            if name in fund_list:
                totals[risk]["cost"]    += cost_value
                totals[risk]["current"] += current_value
                totals[risk]["funds"].append({
                    "name": name,
                    "quantity": fund["quantity"],
                    "avg_price": fund["average_price"],
                    "last_price": fund["last_price"],
                    "cost_value": cost_value,
                    "current_value": current_value,
                })

    return totals


def allocate_goals(goals: list, risk_totals: dict) -> list:
    """
    Waterfall allocation: goals are funded in priority order.
    Within each goal the risk allocation weights determine how much
    of each risk bucket is consumed.
    Returns a list of result dicts, one per goal.
    """
    # mutable pool of what's still available per risk category
    pool = {risk: data["current"] for risk, data in risk_totals.items()}

    results = []
    for goal in sorted(goals, key=lambda g: g["priority"]):
        target     = goal["target"]
        allocation = goal["allocation"]  # e.g. {"low": 0.7, "medium": 0.2, "high": 0.1}

        breakdown  = {}
        total_funded = 0.0

        for risk, weight in allocation.items():
            needed    = target * weight
            available = pool.get(risk, 0.0)
            funded    = min(needed, available)
            pool[risk] = available - funded

            breakdown[risk] = {
                "needed":  round(needed, 2),
                "funded":  round(funded, 2),
                "gap":     round(needed - funded, 2),
            }
            total_funded += funded

        progress = min((total_funded / target) * 100, 100.0) if target > 0 else 100.0

        results.append({
            "name":          goal["name"],
            "priority":      goal["priority"],
            "target":        target,
            "total_funded":  round(total_funded, 2),
            "progress_pct":  round(progress, 2),
            "breakdown":     breakdown,
        })

    return results, pool   # pool now holds unallocated remainder


# ── display ───────────────────────────────────────────────────────────────────

def print_portfolio(risk_totals: dict) -> None:
    bar = "─" * 60
    print(f"\n{'═'*60}")
    print(f"  PORTFOLIO SUMMARY")
    print(f"{'═'*60}")

    grand_cost    = sum(d["cost"]    for d in risk_totals.values())
    grand_current = sum(d["current"] for d in risk_totals.values())
    grand_gain    = grand_current - grand_cost
    grand_gain_pct = (grand_gain / grand_cost * 100) if grand_cost else 0

    for risk, data in risk_totals.items():
        print(f"\n  [{risk.upper()} RISK]")
        for f in data["funds"]:
            gain     = f["current_value"] - f["cost_value"]
            gain_pct = (gain / f["cost_value"] * 100) if f["cost_value"] else 0
            sign     = "+" if gain >= 0 else ""
            print(f"    {f['name']}")
            print(f"      Qty: {f['quantity']:.3f}  |  Avg: ₹{f['avg_price']:.3f}  |  LTP: ₹{f['last_price']:.3f}")
            print(f"      Cost: ₹{f['cost_value']:,.2f}  →  Current: ₹{f['current_value']:,.2f}  ({sign}{gain_pct:.2f}%)")
        print(f"  {bar[:50]}")
        print(f"  {risk.upper()} subtotal  →  ₹{data['current']:,.2f}  (cost ₹{data['cost']:,.2f})")

    sign = "+" if grand_gain >= 0 else ""
    print(f"\n{'─'*60}")
    print(f"  TOTAL  →  ₹{grand_current:,.2f}  (cost ₹{grand_cost:,.2f})  {sign}{grand_gain_pct:.2f}%")
    print(f"{'═'*60}\n")


def progress_bar(pct: float, width: int = 30) -> str:
    filled = int(width * pct / 100)
    return f"[{'█' * filled}{'░' * (width - filled)}] {pct:.1f}%"


def print_goal_allocations(goal_results: list, unallocated: dict) -> None:
    print(f"{'═'*60}")
    print(f"  GOAL ALLOCATIONS  (priority order)")
    print(f"{'═'*60}")

    for g in goal_results:
        gap = g["target"] - g["total_funded"]
        print(f"\n  [{g['priority']}] {g['name'].upper()}")
        print(f"      Target  : ₹{g['target']:,.2f}")
        print(f"      Funded  : ₹{g['total_funded']:,.2f}")
        print(f"      Gap     : ₹{gap:,.2f}" if gap > 0.01 else "      Gap     : ✓ Fully funded")
        print(f"      Progress: {progress_bar(g['progress_pct'])}")
        print(f"      Risk breakdown:")
        for risk, bd in g["breakdown"].items():
            print(f"        {risk:8s}  needed ₹{bd['needed']:>10,.2f}  |  funded ₹{bd['funded']:>10,.2f}  |  gap ₹{bd['gap']:>10,.2f}")

    print(f"\n{'─'*60}")
    print(f"  UNALLOCATED (surplus after all goals):")
    total_surplus = 0.0
    for risk, amount in unallocated.items():
        print(f"    {risk:8s}  ₹{amount:,.2f}")
        total_surplus += amount
    print(f"    {'TOTAL':8s}  ₹{total_surplus:,.2f}")
    print(f"{'═'*60}\n")


# ── auth ──────────────────────────────────────────────────────────────────────

def get_kite_client() -> KiteConnect:
    load_dotenv()
    kite = KiteConnect(api_key=os.getenv("zerodha_api_key"))
    url  = kite.login_url()
    print(f"Opening login URL: {url}")
    if not webbrowser.open(url):
        print("Could not open browser automatically. Please open the URL above manually.")
    request_token = input("Paste the request_token from the redirect URL: ").strip()
    data = kite.generate_session(
        request_token=request_token,
        api_secret=os.getenv("zerodha_api_secret"),
    )
    kite.set_access_token(data["access_token"])
    return kite


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    logging.basicConfig(level=logging.WARNING)   # flip to DEBUG when needed
    print("Excited to see you managing your own finances!\n")

    # ── fetch or load funds ──────────────────────────────────────────────────
    refresh = input("Fetch fresh holdings from Zerodha? [y/N]: ").strip().lower()
    if refresh == "y":
        kite = get_kite_client()
        holdings = kite.mf_holdings()
        with open("funds.json", "w") as f:
            json.dump(holdings, f, indent=4)
        print("funds.json updated.\n")

    funds    = load_json("funds.json")
    goals    = load_json("user_defined/goals.json")
    mappings = load_json("user_defined/mappings.json")

    # ── validate allocations sum to 1 ────────────────────────────────────────
    for goal in goals:
        total_weight = sum(goal["allocation"].values())
        if abs(total_weight - 1.0) > 0.001:
            print(f"  ⚠  Goal '{goal['name']}' allocation weights sum to {total_weight:.3f}, not 1.0. Please fix goals.json.")

    # ── compute & display ────────────────────────────────────────────────────
    risk_totals          = build_risk_totals(funds, mappings)
    goal_results, surplus = allocate_goals(goals, risk_totals)

    print_portfolio(risk_totals)
    print_goal_allocations(goal_results, surplus)


if __name__ == "__main__":
    main()