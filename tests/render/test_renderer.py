from domain.diff_models import ChangeType, DiffItem, DiffResult
from domain.models import UMLAttribute, UMLClass, UMLMethod, UMLModel
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
                after="id: str",
                before_element=UMLAttribute(name="id", type="int"),
                after_element=UMLAttribute(name="id", type="str")
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
        highlight_rules=(("A", "modified"),)
    )

    puml = render_puml(base_model, pr_model, diff, spec)

    assert "@startuml" in puml
    assert "class \"A\" as A <<modified>>" in puml
    assert "<color:orange>id: str</color>" in puml
    assert "<color:green>new: int</color>" in puml
    assert "@enduml" in puml


def test_renderer_custom_configs() -> None:
    c_base = UMLClass(
        name="com.example.A",
        kind="class",
        attributes=(),
        methods=(
            UMLMethod(name="doSomething", parameters=("param1 : String", "param2 : int"), return_type="void"),
        )
    )
    base_model = UMLModel(module_name="test", classes=())
    pr_model = UMLModel(module_name="test", classes=(c_base,))

    diff = DiffResult(
        module_name="test",
        changes=(
            DiffItem(entity_type="class", entity_name="com.example.A", change_type=ChangeType.ADDED),
        )
    )
    spec = RenderSpec(included_nodes=("com.example.A",), highlight_rules=(("com.example.A", "added"),))

    # Test types_only (should strip params) and ortho lines
    puml = render_puml(base_model, pr_model, diff, spec, layout_orthogonal_lines=True, method_parameter_style="types_only", group_by_package=True)
    assert "skinparam linetype ortho" in puml
    assert "set namespaceSeparator none" not in puml
    assert "doSomething(String, int)" in puml
    assert "param1" not in puml

    # Test names_and_types (should keep params) and curved lines
    puml2 = render_puml(base_model, pr_model, diff, spec, layout_orthogonal_lines=False, method_parameter_style="names_and_types", group_by_package=False)
    assert "skinparam linetype poly" in puml2
    assert "set namespaceSeparator none" in puml2
    assert "doSomething(param1 : String, param2 : int)" in puml2
