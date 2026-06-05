from diff.compute import compute_diff
from domain.diff_models import ChangeType
from domain.models import UMLAttribute, UMLClass, UMLModel


def test_diff_no_changes() -> None:
    c = UMLClass(name="User", kind="class")
    model1 = UMLModel(module_name="test", classes=(c,))
    model2 = UMLModel(module_name="test", classes=(c,))

    result = compute_diff(model1, model2)
    assert len(result.changes) == 0

def test_diff_added_class() -> None:
    c1 = UMLClass(name="User", kind="class")
    c2 = UMLClass(name="Order", kind="class")

    model1 = UMLModel(module_name="test", classes=(c1,))
    model2 = UMLModel(module_name="test", classes=(c1, c2))

    result = compute_diff(model1, model2)
    assert len(result.changes) == 1
    assert result.changes[0].entity_type == "class"
    assert result.changes[0].entity_name == "Order"
    assert result.changes[0].change_type == ChangeType.ADDED

def test_diff_modified_attribute() -> None:
    a1 = UMLAttribute(name="id", type="int", visibility="-")
    a2 = UMLAttribute(name="id", type="str", visibility="+")

    c1 = UMLClass(name="User", kind="class", attributes=(a1,))
    c2 = UMLClass(name="User", kind="class", attributes=(a2,))

    model1 = UMLModel(module_name="test", classes=(c1,))
    model2 = UMLModel(module_name="test", classes=(c2,))

    result = compute_diff(model1, model2)
    assert len(result.changes) == 1

    change = result.changes[0]
    assert change.entity_type == "attribute"
    assert change.entity_name == "id"
    assert change.change_type == ChangeType.MODIFIED
    assert change.context == "User"
    assert change.before is not None
    assert "- id: int" in change.before
    assert change.after is not None
    assert "+ id: str" in change.after
