import json
from datetime import date


def load_json(path: str) -> dict | list:
    with open(path) as f:
        return json.load(f)


def validate_goals(goals: list) -> None:
    """Raise if any goal's allocation weights don't sum to 1.0."""
    for goal in goals:
        total = sum(goal["allocation"].values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(
                f"Goal '{goal['name']}' allocation weights sum to {total:.3f}, not 1.0. "
                f"Please fix goals.json."
            )


def months_between(start: date, end: date) -> int:
    """Return the number of whole months from start to end (minimum 1)."""
    months = (end.year - start.year) * 12 + (end.month - start.month)
    return max(months, 1)