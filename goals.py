from datetime import date
from utils import months_between


def allocate_goals(goals: list, risk_totals: dict) -> tuple[list, dict]:
    """
    Waterfall allocation in priority order.

    For each goal (sorted by priority):
      - Claim (target × weight) from each risk bucket in the pool.
      - If a bucket is short, the goal gets what's available and records a gap.
      - Any remainder after all goals is returned as unallocated surplus.

    Also computes deadline-based SIP needed if a 'deadline' field is present.

    Returns:
        goal_results  — list of result dicts, one per goal
        pool          — dict of unallocated amounts per risk category
    """
    pool = {risk: data["current"] for risk, data in risk_totals.items()}
    today = date.today()
    results = []

    for goal in sorted(goals, key=lambda g: g["priority"]):
        target     = goal["target"]
        allocation = goal["allocation"]

        breakdown    = {}
        total_funded = 0.0

        for risk, weight in allocation.items():
            needed    = target * weight
            available = pool.get(risk, 0.0)
            funded    = min(needed, available)
            pool[risk] = available - funded

            breakdown[risk] = {
                "needed": round(needed,         2),
                "funded": round(funded,         2),
                "gap":    round(needed - funded, 2),
            }
            total_funded += funded

        gap      = max(target - total_funded, 0.0)
        progress = min((total_funded / target) * 100, 100.0) if target > 0 else 100.0

        # ── deadline & SIP ───────────────────────────────────────────────────
        deadline_str    = goal.get("deadline")
        months_left     = None
        monthly_sip     = None
        sip_per_risk    = {}

        if deadline_str:
            deadline    = date.fromisoformat(deadline_str)
            months_left = months_between(today, deadline)

            if gap > 0:
                monthly_sip = round(gap / months_left, 2)
                # Distribute the monthly SIP across risk buckets by the goal's weights,
                # but only for buckets that still have a gap (so we don't over-invest
                # into already-full buckets).
                remaining_gap = {
                    risk: bd["gap"]
                    for risk, bd in breakdown.items()
                    if bd["gap"] > 0
                }
                gap_total = sum(remaining_gap.values())
                sip_per_risk = {
                    risk: round((gap_val / gap_total) * monthly_sip, 2)
                    for risk, gap_val in remaining_gap.items()
                }
            else:
                monthly_sip  = 0.0
                sip_per_risk = {risk: 0.0 for risk in allocation}

        results.append({
            "name":         goal["name"],
            "priority":     goal["priority"],
            "target":       target,
            "total_funded": round(total_funded, 2),
            "gap":          round(gap, 2),
            "progress_pct": round(progress, 2),
            "breakdown":    breakdown,
            "deadline":     deadline_str,
            "months_left":  months_left,
            "monthly_sip":  monthly_sip,
            "sip_per_risk": sip_per_risk,
        })

    return results, pool