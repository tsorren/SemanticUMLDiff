from domain.diff_models import ChangeType, DiffItem, DiffResult
from domain.models import UMLAttribute, UMLClass, UMLModel
from domain.render_models import RenderSpec
from render.puml_renderer import render_puml


def test_render_modified_class() -> None:
    c_base = UMLClass(
        name="A",
        kind="class",
        attributes=(UMLAttribute(name="id", type="int"),)
    )
    c_pr = UMLClass(
        name="A",
        kind="class",
        attributes=(
            UMLAttribute(name="id", type="str"),
            UMLAttribute(name="new", type="int")
        )
    )

    base_model = UMLModel(module_name="test", classes=(c_base,))
    pr_model = UMLModel(module_name="test", classes=(c_pr,))

    diff = DiffResult(
        module_name="test",
        changes=(
            DiffItem(
                entity_type="attribute",
                entity_name="id",
                change_type=ChangeType.MODIFIED,
                context="A",
                before="id: int",
                after="id: str"
            ),
            DiffItem(
                entity_type="attribute",
                entity_name="new",
                change_type=ChangeType.ADDED,
                context="A"
            )
        )
    )

    spec = RenderSpec(
        included_nodes=("A",),
        highlight_rules=(("A", "yellow"),)
    )

    puml = render_puml(base_model, pr_model, diff, spec)

    assert "@startuml" in puml
    assert "class A #FFF3CD" in puml
    assert "<color:red><s:red>id: int</s></color>" in puml
    assert "<color:green>id: str</color>" in puml
    assert "<color:green>new: int</color>" in puml
    assert "@enduml" in puml
