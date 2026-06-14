from diff.compute import compute_diff_deepdiff
from diff.serializer import model_to_dict
from domain.diff_models import ChangeType
from domain.models import UMLClass, UMLMethod, UMLModel


def test_hash_stability():
    # Two identical models with classes/methods/attributes in different orders
    m1 = UMLModel(
        module_name="test",
        classes=(
            UMLClass("ClassA", "class"),
            UMLClass("ClassB", "class"),
        ),
        relations=()
    )
    m2 = UMLModel(
        module_name="test",
        classes=(
            UMLClass("ClassB", "class"),
            UMLClass("ClassA", "class"),
        ),
        relations=()
    )

    dict1 = model_to_dict(m1)
    dict2 = model_to_dict(m2)

    # Check that sorting produces identical representations
    assert dict1 == dict2

def test_overloaded_methods_differentiation():
    # Base has process(int)
    # PR has process(int) AND process(String)
    base_m = UMLMethod("process", ("id: int",), "void", "+")
    pr_m1 = UMLMethod("process", ("id: int",), "void", "+")
    pr_m2 = UMLMethod("process", ("name: String",), "void", "+")

    base = UMLModel("test", classes=(UMLClass("User", "class", methods=(base_m,)),), relations=())
    pr = UMLModel("test", classes=(UMLClass("User", "class", methods=(pr_m1, pr_m2)),), relations=())

    diff = compute_diff_deepdiff(base, pr)

    # Should result in exactly 1 ADDED method (process(String))
    assert len(diff.changes) == 1
    assert diff.changes[0].entity_type == "method"
    assert diff.changes[0].change_type == ChangeType.ADDED
    assert diff.changes[0].entity_name == "process(String)"

def test_metric_1_to_1_rename_collision():
    # If 1 method is removed and 2 are added, there is no unambiguous 1:1 rename mapping.
    # Therefore, they should remain independent ADDED/REMOVED changes.
    base_m = UMLMethod("oldName", ("id: int",), "void", "+")
    pr_m1 = UMLMethod("newName1", ("id: int",), "void", "+")
    pr_m2 = UMLMethod("newName2", ("id: int",), "void", "+")

    base = UMLModel("test", classes=(UMLClass("User", "class", methods=(base_m,)),), relations=())
    pr = UMLModel("test", classes=(UMLClass("User", "class", methods=(pr_m1, pr_m2)),), relations=())

    diff = compute_diff_deepdiff(base, pr)

    # Should result in 1 REMOVED and 2 ADDED method changes (no MODIFIED rename)
    assert len([c for c in diff.changes if c.change_type == ChangeType.REMOVED]) == 1
    assert len([c for c in diff.changes if c.change_type == ChangeType.ADDED]) == 2
    assert len([c for c in diff.changes if c.change_type == ChangeType.MODIFIED]) == 0
