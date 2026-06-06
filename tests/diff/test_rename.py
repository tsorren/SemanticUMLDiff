from typing import List

from diff.compute import _compare_members
from domain.diff_models import ChangeType, DiffItem
from domain.models import UMLClass, UMLMethod


def test_rename_detection_single() -> None:
    base_c = UMLClass("A", "class", attributes=(), methods=(
        UMLMethod("oldName", ("int a",), "void", "+"),
    ))
    pr_c = UMLClass("A", "class", attributes=(), methods=(
        UMLMethod("newName", ("int a",), "void", "+"),
    ))
    changes: List[DiffItem] = []
    _compare_members(base_c, pr_c, "A", changes)

    assert len(changes) == 1
    assert changes[0].change_type == ChangeType.MODIFIED
    assert changes[0].entity_name == "newName(int)"

def test_rename_detection_collision() -> None:
    # Two identical methods removed, two added -> collision fallback
    base_c = UMLClass("A", "class", attributes=(), methods=(
        UMLMethod("oldName1", ("int a",), "void", "+"),
        UMLMethod("oldName2", ("int a",), "void", "+"),
    ))
    pr_c = UMLClass("A", "class", attributes=(), methods=(
        UMLMethod("newName1", ("int a",), "void", "+"),
        UMLMethod("newName2", ("int a",), "void", "+"),
    ))
    changes: List[DiffItem] = []
    _compare_members(base_c, pr_c, "A", changes)

    assert len(changes) == 4
    types = [c.change_type for c in changes]
    assert types.count(ChangeType.ADDED) == 2
    assert types.count(ChangeType.REMOVED) == 2

def test_granular_modified_method_diff() -> None:
    base_c = UMLClass("A", "class", attributes=(), methods=(
        UMLMethod("name", ("int a",), "void", "+"),
    ))
    pr_c = UMLClass("A", "class", attributes=(), methods=(
        UMLMethod("name", ("String a",), "void", "-"),
    ))
    changes: List[DiffItem] = []
    _compare_members(base_c, pr_c, "A", changes)

    assert len(changes) == 1
    assert changes[0].change_type == ChangeType.MODIFIED
