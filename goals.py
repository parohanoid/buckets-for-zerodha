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
