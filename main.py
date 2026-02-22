from auth import get_kite_client
from portfolio import build_risk_totals
from goals import allocate_goals
from display import print_portfolio, print_goal_allocations
from utils import load_json, validate_goals
import json

def main():
    print("Excited to see you managing your own finances!\n")

    if input("Fetch fresh holdings from Zerodha? [y/N]: ").strip().lower() == "y":
        kite = get_kite_client()
        with open("funds.json", "w") as f:
            json.dump(kite.mf_holdings(), f, indent=4)

    funds    = load_json("funds.json")
    goals    = load_json("goals.json")
    mappings = load_json("mappings.json")

    validate_goals(goals)

    risk_totals            = build_risk_totals(funds, mappings)
    goal_results, surplus  = allocate_goals(goals, risk_totals)

    print_portfolio(risk_totals)
    print_goal_allocations(goal_results, surplus)

if __name__ == "__main__":
    main()