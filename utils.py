import json
from collections import defaultdict
from datetime import date


def load_json(path: str) -> dict | list:
    with open(path) as f:
        return json.load(f)


def validate_goals(goals: list) -> None:
    """
    Raises ValueError if:
      - Any goal's allocation weights (low/medium/high) don't sum to 1.0
      - Any tied-priority group is missing 'share' on some but not all goals
        (all-missing is fine — they default to equal shares)
    """
    for goal in goals:
        total = sum(goal["allocation"].values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(
                f"Goal '{goal['name']}' allocation weights sum to {total:.3f}, not 1.0. "
                f"Please fix goals.json."
            )

    # Group by priority and warn if share is defined for some but not all in a tie
    by_priority = defaultdict(list)
    for goal in goals:
        by_priority[goal["priority"]].append(goal)

    for priority, group in by_priority.items():
        if len(group) > 1:
            has_share = [("share" in g) for g in group]
            if any(has_share) and not all(has_share):
                names = [g["name"] for g in group]
                raise ValueError(
                    f"Priority {priority} has tied goals {names} but only some define 'share'. "
                    f"Either add 'share' to all of them or remove it from all (equal split will be used)."
                )


def months_between(start: date, end: date) -> int:
    """Return the number of whole months from start to end (minimum 1)."""
    months = (end.year - start.year) * 12 + (end.month - start.month)
    return max(months, 1)