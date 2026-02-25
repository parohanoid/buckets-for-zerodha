from datetime import date
from itertools import groupby
from utils import months_between


def _allocate_single_goal(goal: dict, pool: dict) -> dict:
    """
    Claim funds from the pool for one goal.
    Mutates pool in place. Returns the breakdown dict.
    """
    target     = goal["target"]
    allocation = goal["allocation"]
    breakdown  = {}
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

    return breakdown, round(total_funded, 2)


def _allocate_tied_goals(goals_in_group: list, pool: dict) -> list[tuple]:
    """
    For goals sharing the same priority, distribute each risk bucket
    proportionally by each goal's 'share' value before claiming.

    Example: Goal A (share=0.6) and Goal B (share=0.4) both need money
    from the low bucket. If low has ₹10,000 available, A gets access to
    ₹6,000 of it and B gets access to ₹4,000 — then each claims
    min(needed, their_slice).

    Returns a list of (goal, breakdown, total_funded) tuples.
    """
    # Normalise shares so they sum to 1.0 within the group
    total_share = sum(g.get("share", 1.0) for g in goals_in_group)
    normalised  = [g.get("share", 1.0) / total_share for g in goals_in_group]

    results = []
    # Track how much each goal actually funds per risk bucket
    funded_matrix = [{} for _ in goals_in_group]

    for risk in pool:
        available = pool[risk]
        total_claimed_from_bucket = 0.0

        for i, (goal, norm_share) in enumerate(zip(goals_in_group, normalised)):
            weight = goal["allocation"].get(risk, 0.0)
            needed = goal["target"] * weight
            # Each goal's slice of the available bucket
            slice_ = available * norm_share
            funded = min(needed, slice_)
            funded_matrix[i][risk] = funded
            total_claimed_from_bucket += funded

        pool[risk] = available - total_claimed_from_bucket

    for i, goal in enumerate(goals_in_group):
        breakdown    = {}
        total_funded = 0.0
        for risk, weight in goal["allocation"].items():
            needed = goal["target"] * weight
            funded = funded_matrix[i].get(risk, 0.0)
            breakdown[risk] = {
                "needed": round(needed,         2),
                "funded": round(funded,         2),
                "gap":    round(needed - funded, 2),
            }
            total_funded += funded
        results.append((goal, breakdown, round(total_funded, 2)))

    return results


def _build_goal_result(goal: dict, breakdown: dict, total_funded: float, today: date) -> dict:
    """Compute progress, deadline, and SIP fields and return the result dict."""
    target   = goal["target"]
    gap      = max(target - total_funded, 0.0)
    progress = min((total_funded / target) * 100, 100.0) if target > 0 else 100.0

    deadline_str = goal.get("deadline")
    months_left  = None
    monthly_sip  = None
    sip_per_risk = {}

    if deadline_str:
        deadline    = date.fromisoformat(deadline_str)
        months_left = months_between(today, deadline)

        if gap > 0:
            monthly_sip = round(gap / months_left, 2)
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
            sip_per_risk = {risk: 0.0 for risk in goal["allocation"]}

    return {
        "name":         goal["name"],
        "priority":     goal["priority"],
        "share":        goal.get("share", 1.0),
        "target":       target,
        "total_funded": total_funded,
        "gap":          round(gap, 2),
        "progress_pct": round(progress, 2),
        "breakdown":    breakdown,
        "deadline":     deadline_str,
        "months_left":  months_left,
        "monthly_sip":  monthly_sip,
        "sip_per_risk": sip_per_risk,
    }


def allocate_goals(goals: list, risk_totals: dict) -> tuple[list, dict]:
    """
    Waterfall allocation in priority order.

    - Goals are processed priority group by priority group (lowest number first).
    - If a priority group has ONE goal, it claims funds directly (simple waterfall).
    - If a priority group has MULTIPLE goals, available funds in each risk bucket
      are first divided by each goal's normalised 'share' before claiming — so
      tied goals compete fairly rather than the first one winning everything.

    'share' lives in goals.json alongside each goal. It is only meaningful
    relative to other goals at the same priority level.
    'allocation' (low/medium/high weights) describes the risk split *within*
    a single goal and must always sum to 1.0.

    Returns:
        goal_results — list of result dicts, one per goal, in priority order
        pool         — dict of unallocated amounts per risk category
    """
    pool  = {risk: data["current"] for risk, data in risk_totals.items()}
    today = date.today()
    results = []

    sorted_goals = sorted(goals, key=lambda g: g["priority"])

    for _priority, group_iter in groupby(sorted_goals, key=lambda g: g["priority"]):
        group = list(group_iter)

        if len(group) == 1:
            breakdown, total_funded = _allocate_single_goal(group[0], pool)
            results.append(_build_goal_result(group[0], breakdown, total_funded, today))
        else:
            for goal, breakdown, total_funded in _allocate_tied_goals(group, pool):
                results.append(_build_goal_result(goal, breakdown, total_funded, today))

    return results, pool