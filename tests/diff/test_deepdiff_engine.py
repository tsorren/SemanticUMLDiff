import pytest
from domain.models import UMLModel, UMLClass, UMLAttribute, UMLMethod, UMLRelation
from domain.diff_models import ChangeType
from diff.deepdiff_engine import compute_diff_deepdiff

def test_deepdiff_no_changes():
    base = UMLModel("test", classes=(UMLClass("User", "class"),), relations=())
    pr = UMLModel("test", classes=(UMLClass("User", "class"),), relations=())
    diff = compute_diff_deepdiff(base, pr)
    assert len(diff.changes) == 0

def test_deepdiff_class_added():
    base = UMLModel("test", classes=(), relations=())
    pr = UMLModel("test", classes=(UMLClass("User", "class"),), relations=())
    diff = compute_diff_deepdiff(base, pr)
    assert len(diff.changes) == 1
    assert diff.changes[0].entity_type == "class"
    assert diff.changes[0].entity_name == "User"
    assert diff.changes[0].change_type == ChangeType.ADDED

def test_deepdiff_class_removed():
    base = UMLModel("test", classes=(UMLClass("User", "class"),), relations=())
    pr = UMLModel("test", classes=(), relations=())
    diff = compute_diff_deepdiff(base, pr)
    assert len(diff.changes) == 1
    assert diff.changes[0].entity_type == "class"
    assert diff.changes[0].entity_name == "User"
    assert diff.changes[0].change_type == ChangeType.REMOVED

def test_deepdiff_attribute_modified():
    attr_base = UMLAttribute("age", "int", "+")
    attr_pr = UMLAttribute("age", "String", "+")
    base = UMLModel("test", classes=(UMLClass("User", "class", attributes=(attr_base,)),), relations=())
    pr = UMLModel("test", classes=(UMLClass("User", "class", attributes=(attr_pr,)),), relations=())
    diff = compute_diff_deepdiff(base, pr)
    # We should have 1 attribute modification
    assert len(diff.changes) == 1
    ch = diff.changes[0]
    assert ch.entity_type == "attribute"
    assert ch.entity_name == "age"
    assert ch.change_type == ChangeType.MODIFIED
    assert ch.context == "User"
    assert ch.before == "+ age: int"
    assert ch.after == "+ age: String"
    assert ch.before_element == attr_base
    assert ch.after_element == attr_pr

def test_deepdiff_method_added():
    method = UMLMethod("save", (), "void", "+")
    base = UMLModel("test", classes=(UMLClass("User", "class"),), relations=())
    pr = UMLModel("test", classes=(UMLClass("User", "class", methods=(method,)),), relations=())
    diff = compute_diff_deepdiff(base, pr)
    assert len(diff.changes) == 1
    ch = diff.changes[0]
    assert ch.entity_type == "method"
    assert ch.entity_name == "save()"
    assert ch.change_type == ChangeType.ADDED
    assert ch.context == "User"
    assert ch.after_element == method

def test_deepdiff_method_parameter_name_ignored():
    # In types_only mode, param name changes should be ignored.
    m_base = UMLMethod("send", ("msg: String",), "void", "+")
    m_pr = UMLMethod("send", ("path: String",), "void", "+")
    base = UMLModel("test", classes=(UMLClass("User", "class", methods=(m_base,)),), relations=())
    pr = UMLModel("test", classes=(UMLClass("User", "class", methods=(m_pr,)),), relations=())
    diff = compute_diff_deepdiff(base, pr, method_parameter_style="types_only")
    assert len(diff.changes) == 0

def test_deepdiff_relation_added():
    rel = UMLRelation("User", "Order", "association", "1", "*")
    base = UMLModel("test", classes=(), relations=())
    pr = UMLModel("test", classes=(), relations=(rel,))
    diff = compute_diff_deepdiff(base, pr)
    assert len(diff.changes) == 1
    ch = diff.changes[0]
    assert ch.entity_type == "relation"
    assert ch.entity_name == "User association Order"
    assert ch.change_type == ChangeType.ADDED
