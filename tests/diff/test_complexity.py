import os
from unittest import mock

from diff.complexity import calculate_complexity
from domain.diff_models import ChangeType, DiffItem, DiffResult


def test_calculate_complexity_default_weights() -> None:
    # Setup changes representing different entity types
    changes = (
        # Classes: 10 + 10 + 10 + 5 = 35
        DiffItem(entity_type="class", entity_name="NewClass", change_type=ChangeType.ADDED),
        DiffItem(entity_type="class", entity_name="OldClass", change_type=ChangeType.REMOVED),
        DiffItem(entity_type="class", entity_name="MovedClass", change_type=ChangeType.MODIFIED, context="moved"),
        DiffItem(entity_type="class", entity_name="ModifiedClass", change_type=ChangeType.MODIFIED),
        # Relations: 5 * 3 = 15
        DiffItem(entity_type="relation", entity_name="Rel1", change_type=ChangeType.ADDED),
        DiffItem(entity_type="relation", entity_name="Rel2", change_type=ChangeType.REMOVED),
        DiffItem(entity_type="relation", entity_name="Rel3", change_type=ChangeType.MODIFIED),
        # Methods: 3 * 3 = 9
        DiffItem(entity_type="method", entity_name="meth1()", change_type=ChangeType.ADDED),
        DiffItem(entity_type="method", entity_name="meth2()", change_type=ChangeType.REMOVED),
        DiffItem(entity_type="method", entity_name="meth3()", change_type=ChangeType.MODIFIED),
        # Attributes: 1 * 3 = 3
        DiffItem(entity_type="attribute", entity_name="attr1", change_type=ChangeType.ADDED),
        DiffItem(entity_type="attribute", entity_name="attr2", change_type=ChangeType.REMOVED),
        DiffItem(entity_type="attribute", entity_name="attr3", change_type=ChangeType.MODIFIED),
    )
    diff = DiffResult(module_name="test-module", changes=changes)

    # 35 + 15 + 9 + 3 = 62
    score, level = calculate_complexity(diff)
    assert score == 62
    # Baseline: 275, Tolerance: 27.27% -> Lower bound: 200. Score 62 < 200 -> Baja 🟢
    assert level == "Baja 🟢"


@mock.patch.dict(os.environ, {
    "COMPLEXITY_MEDIUM_BASELINE": "100",
    "COMPLEXITY_TOLERANCE": "20.0"
})
def test_calculate_complexity_threshold_classification() -> None:
    # Lower bound = 100 * 0.8 = 80
    # Upper bound = 100 * 1.2 = 120

    # 1. Low: score = 79
    changes_low = (
        [DiffItem(entity_type="class", entity_name="C", change_type=ChangeType.ADDED)] * 7 + # 70
        [DiffItem(entity_type="method", entity_name="m", change_type=ChangeType.ADDED)] * 3 # 9
    )
    diff_low = DiffResult(module_name="test", changes=tuple(changes_low))
    score_l, level_l = calculate_complexity(diff_low)
    assert score_l == 79
    assert level_l == "Baja 🟢"

    # 2. Medium: score = 80 (exactly lower bound)
    changes_med_lower = (
        [DiffItem(entity_type="class", entity_name="C", change_type=ChangeType.ADDED)] * 8 # 80
    )
    diff_med_lower = DiffResult(module_name="test", changes=tuple(changes_med_lower))
    score_ml, level_ml = calculate_complexity(diff_med_lower)
    assert score_ml == 80
    assert level_ml == "Media 🟡"

    # 3. Medium: score = 120 (exactly upper bound)
    changes_med_upper = (
        [DiffItem(entity_type="class", entity_name="C", change_type=ChangeType.ADDED)] * 12 # 120
    )
    diff_med_upper = DiffResult(module_name="test", changes=tuple(changes_med_upper))
    score_mu, level_mu = calculate_complexity(diff_med_upper)
    assert score_mu == 120
    assert level_mu == "Media 🟡"

    # 4. High: score = 121
    changes_high = (
        [DiffItem(entity_type="class", entity_name="C", change_type=ChangeType.ADDED)] * 12 + # 120
        [DiffItem(entity_type="attribute", entity_name="a", change_type=ChangeType.ADDED)] * 1 # 1
    )
    diff_high = DiffResult(module_name="test", changes=tuple(changes_high))
    score_h, level_h = calculate_complexity(diff_high)
    assert score_h == 121
    assert level_h == "Alta 🔴"


@mock.patch.dict(os.environ, {
    "COMPLEXITY_WEIGHTS": '{"class": 20, "relation": 10, "method": 5, "attribute": 2}'
})
def test_calculate_complexity_custom_weights() -> None:
    changes = (
        DiffItem(entity_type="class", entity_name="C1", change_type=ChangeType.ADDED), # 20
        DiffItem(entity_type="class", entity_name="C2", change_type=ChangeType.MODIFIED),  # modified class (not moved) uses 5 pts
        # Wait, in calculate_complexity:
        # class change_type == MODIFIED and context != "moved" -> weight = 5
        # So yes, MODIFIED class is hardcoded to 5.
        # Class added is custom weight = 20.
        DiffItem(entity_type="relation", entity_name="R", change_type=ChangeType.ADDED),  # 10
        DiffItem(entity_type="method", entity_name="M", change_type=ChangeType.ADDED),  # 5
        DiffItem(entity_type="attribute", entity_name="A", change_type=ChangeType.ADDED),  # 2
    )
    diff = DiffResult(module_name="test", changes=changes)
    score, _ = calculate_complexity(diff)

    # 20 + 5 (modified class) + 10 + 5 + 2 = 42
    assert score == 42
