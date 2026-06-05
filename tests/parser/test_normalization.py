from domain.models import UMLAttribute, UMLClass, UMLMethod, UMLModel, UMLRelation
from parser.normalization import normalize_model


def test_normalization_sorting() -> None:
    # Create an intentionally unsorted model
    attr2 = UMLAttribute(name="z_attr")
    attr1 = UMLAttribute(name="a_attr")

    method2 = UMLMethod(name="z_method")
    method1 = UMLMethod(name="a_method")

    cls2 = UMLClass(
        name="ZClass",
        kind="class",
        attributes=(attr2, attr1),
        methods=(method2, method1)
    )

    cls1 = UMLClass(
        name="AClass",
        kind="class"
    )

    rel2 = UMLRelation(source="ZClass", target="AClass", relation_type="association")
    rel1 = UMLRelation(source="AClass", target="ZClass", relation_type="composition")

    unsorted_model = UMLModel(
        module_name="test",
        classes=(cls2, cls1),
        relations=(rel2, rel1)
    )

    normalized = normalize_model(unsorted_model)

    # Verify classes are sorted by name
    assert normalized.classes[0].name == "AClass"
    assert normalized.classes[1].name == "ZClass"

    # Verify relations are sorted by source, target, type
    assert normalized.relations[0].source == "AClass"
    assert normalized.relations[0].target == "ZClass"
    assert normalized.relations[1].source == "ZClass"
    assert normalized.relations[1].target == "AClass"

    # Verify class members are sorted
    zclass = normalized.classes[1]
    assert zclass.attributes[0].name == "a_attr"
    assert zclass.attributes[1].name == "z_attr"

    assert zclass.methods[0].name == "a_method"
    assert zclass.methods[1].name == "z_method"
