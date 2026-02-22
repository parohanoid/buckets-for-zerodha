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
