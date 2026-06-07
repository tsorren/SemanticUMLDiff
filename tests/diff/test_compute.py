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

def test_diff_matching_order_prioritizes_name() -> None:
    from domain.models import UMLMethod

    m_base_validar = UMLMethod(name="validarNecesidadRecurrente", parameters=(), return_type="void", visibility="-")
    m_base_set = UMLMethod(name="setFechaPeriodo", parameters=("LocalDate",), return_type="void", visibility="+")
    c_base = UMLClass(name="NecesidadRecurrente", kind="class", methods=(m_base_validar, m_base_set))

    m_pr_validar = UMLMethod(name="validarNecesidadRecurrente", parameters=("LocalDate",), return_type="void", visibility="-")
    c_pr = UMLClass(name="NecesidadRecurrente", kind="class", methods=(m_pr_validar,))

    model1 = UMLModel(module_name="test", classes=(c_base,))
    model2 = UMLModel(module_name="test", classes=(c_pr,))

    result = compute_diff(model1, model2)

    modified_methods = [ch for ch in result.changes if ch.entity_type == "method" and ch.change_type == ChangeType.MODIFIED]
    removed_methods = [ch for ch in result.changes if ch.entity_type == "method" and ch.change_type == ChangeType.REMOVED]

    assert len(modified_methods) == 1
    assert modified_methods[0].entity_name == "validarNecesidadRecurrente(LocalDate)"
    assert modified_methods[0].before_element == m_base_validar
    assert modified_methods[0].after_element == m_pr_validar

    assert len(removed_methods) == 1
    assert removed_methods[0].entity_name == "setFechaPeriodo(LocalDate)"
    assert removed_methods[0].before_element == m_base_set

