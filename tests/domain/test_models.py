import json
from dataclasses import FrozenInstanceError

import pytest

from domain.models import UMLAttribute, UMLClass, UMLMethod, UMLModel, UMLRelation


def test_immutability() -> None:
    attr = UMLAttribute(name="id", type="int")
    with pytest.raises(FrozenInstanceError):
        attr.name = "new_id"  # type: ignore[misc]

    method = UMLMethod(name="save")
    with pytest.raises(FrozenInstanceError):
        method.visibility = "+"  # type: ignore[misc]

    cls = UMLClass(name="User", kind="class")
    with pytest.raises(FrozenInstanceError):
        cls.kind = "interface"  # type: ignore[misc]

    rel = UMLRelation(source="A", target="B", relation_type="association")
    with pytest.raises(FrozenInstanceError):
        rel.target = "C"  # type: ignore[misc]

    model = UMLModel(module_name="auth")
    with pytest.raises(FrozenInstanceError):
        model.module_name = "core"  # type: ignore[misc]

def test_deterministic_serialization_simple() -> None:
    model1 = UMLModel(module_name="auth", source_hash="123")
    model2 = UMLModel(module_name="auth", source_hash="123")

    assert model1.serialize() == model2.serialize()

    # Verify omitted fields
    data = json.loads(model1.serialize())
    assert "module_name" in data
    assert "source_hash" in data
    assert "classes" not in data  # Empty tuple omitted

def test_deterministic_serialization_complex() -> None:
    attr1 = UMLAttribute(name="id", type="int", visibility="-")
    attr2 = UMLAttribute(name="name", type="str", visibility="-")

    method1 = UMLMethod(name="getId", return_type="int", visibility="+")

    cls1 = UMLClass(
        name="User",
        kind="class",
        attributes=(attr1, attr2),
        methods=(method1,)
    )

    cls2 = UMLClass(
        name="Order",
        kind="class"
    )

    rel1 = UMLRelation(
        source="User",
        target="Order",
        relation_type="association",
        multiplicity_source="1",
        multiplicity_target="*"
    )

    model = UMLModel(
        module_name="domain",
        classes=(cls1, cls2),
        relations=(rel1,),
        source_hash="abc"
    )

    serialized1 = model.serialize()
    serialized2 = model.serialize()

    assert serialized1 == serialized2

    # The output should not change based on dict ordering internals, because we use sort_keys=True
    parsed = json.loads(serialized1)

    assert parsed["module_name"] == "domain"
    assert parsed["source_hash"] == "abc"
    assert len(parsed["classes"]) == 2
    assert parsed["classes"][0]["name"] == "User"
    assert parsed["classes"][0]["attributes"][0]["name"] == "id"
    assert parsed["classes"][1]["name"] == "Order"
    assert len(parsed["relations"]) == 1
    assert parsed["relations"][0]["source"] == "User"
