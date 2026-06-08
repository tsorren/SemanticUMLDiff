import json
import os

from domain.diff_models import ChangeType, DiffResult

DEFAULT_WEIGHTS = {"class": 10, "relation": 5, "method": 3, "attribute": 1}

def calculate_complexity(diff: DiffResult) -> tuple[int, str]:
    # 1. Read configurations
    try:
        baseline = float(os.getenv("COMPLEXITY_MEDIUM_BASELINE", "275"))
    except ValueError:
        baseline = 275.0

    try:
        tolerance = float(os.getenv("COMPLEXITY_TOLERANCE", "27.27"))
    except ValueError:
        tolerance = 27.27

    weights_raw = os.getenv("COMPLEXITY_WEIGHTS")
    weights = dict(DEFAULT_WEIGHTS)
    if weights_raw:
        try:
            custom_weights = json.loads(weights_raw)
            if isinstance(custom_weights, dict):
                for k, v in custom_weights.items():
                    if isinstance(v, (int, float)):
                        weights[k] = int(v)
        except Exception:
            pass

    # 2. Compute score
    score = 0
    for change in diff.changes:
        weight = weights.get(change.entity_type, 0)
        # Handle class-specific weight rules:
        # Class added/removed/moved = class weight (moved is ChangeType.MODIFIED with context == "moved")
        # Class modified (not moved) = 5 pts
        if change.entity_type == "class":
            if change.change_type == ChangeType.MODIFIED and change.context != "moved":
                weight = 5
            else:
                weight = weights.get("class", 10)
        score += weight

    # 3. Classify
    lower_bound = baseline * (1.0 - tolerance / 100.0)
    upper_bound = baseline * (1.0 + tolerance / 100.0)

    # Use tolerance math to handle classification
    if score < lower_bound:
        level = "Baja 🟢"
    elif score <= upper_bound:
        level = "Media 🟡"
    else:
        level = "Alta 🔴"

    return int(score), level
