import json

def load_json(path: str) -> dict | list:
    with open(path) as f:
        return json.load(f)

def validate_goals(goals: list) -> None:
    for goal in goals:
        total = sum(goal["allocation"].values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(
                f"Goal '{goal['name']}' allocation weights sum to {total:.3f}, not 1.0"
            )