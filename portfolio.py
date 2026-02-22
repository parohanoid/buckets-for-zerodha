def build_risk_totals(funds: list, mappings: dict) -> dict:
    """
    Group funds by risk category and compute cost-basis + current-value totals.
    Returns a dict keyed by risk level (e.g. "low", "medium", "high").
    """
    totals = {risk: {"cost": 0.0, "current": 0.0, "funds": []} for risk in mappings}

    for fund in funds:
        name          = fund["fund"]
        cost_value    = fund["quantity"] * fund["average_price"]
        current_value = fund["quantity"] * fund["last_price"] if fund["last_price"] else cost_value

        for risk, fund_list in mappings.items():
            if name in fund_list:
                totals[risk]["cost"]    += cost_value
                totals[risk]["current"] += current_value
                totals[risk]["funds"].append({
                    "name":          name,
                    "tradingsymbol": fund["tradingsymbol"],
                    "quantity":      fund["quantity"],
                    "avg_price":     fund["average_price"],
                    "last_price":    fund["last_price"],
                    "cost_value":    cost_value,
                    "current_value": current_value,
                })

    return totals