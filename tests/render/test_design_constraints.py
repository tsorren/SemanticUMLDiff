from domain.diff_models import ChangeType, DiffItem, DiffResult
from domain.models import UMLAttribute, UMLMethod, UMLModel
from domain.render_models import RenderSpec
from render.member_renderer import MemberFormatter
from render.puml_renderer import render_puml


def test_visibility_outside_color_tags() -> None:
    # Test that visibility is outside color tags for added and removed members
    attr_add = UMLAttribute("name", "String", "+")
    attr_rm = UMLAttribute("name", "String", "-")

    res_add = MemberFormatter.format_attribute(attr_add, is_added=True)
    res_rm = MemberFormatter.format_attribute(attr_rm, is_removed=True)

    assert res_add == "+ <color:green>name: String</color>"
    assert res_rm == "- <color:red>name: String</color>"
    assert "strike" not in res_rm

    method_add = UMLMethod("doWork", (), "void", "+")
    method_rm = UMLMethod("doWork", (), "void", "-")

    res_m_add = MemberFormatter.format_method(method_add, "types_only", is_added=True)
    res_m_rm = MemberFormatter.format_method(method_rm, "types_only", is_removed=True)

    assert res_m_add == "+ <color:green>doWork(): void</color>"
    assert res_m_rm == "- <color:red>doWork(): void</color>"
    assert "strike" not in res_m_rm

def test_enum_member_rendering_constraints() -> None:
    # Test that enum attributes are rendered without visibility and without colons
    enum_attr = UMLAttribute("NEW_VALUE", "", "+")

    res_norm = MemberFormatter.format_attribute(enum_attr, is_enum=True)
    res_add = MemberFormatter.format_attribute(enum_attr, is_added=True, is_enum=True)
    res_rm = MemberFormatter.format_attribute(enum_attr, is_removed=True, is_enum=True)

    assert res_norm == "NEW_VALUE"
    assert res_add == "<color:green>NEW_VALUE</color>"
    assert res_rm == "<color:red>NEW_VALUE</color>"
    assert "+" not in res_norm
    assert ":" not in res_norm

def test_omit_empty_packages() -> None:
    # Test that package blocks without visible classes are completely omitted
    base_model = UMLModel(module_name="test", classes=())
    pr_model = UMLModel(module_name="test", classes=())

    # Packge "com.empty" has a deleted package change, but no class nodes are in the spec
    diff = DiffResult(
        module_name="test",
        changes=(
            DiffItem(entity_type="package", entity_name="com.empty", change_type=ChangeType.REMOVED),
        )
    )
    spec = RenderSpec(included_nodes=(), highlight_rules=())

    puml = render_puml(base_model, pr_model, diff, spec, group_by_package=True)
    assert 'package "' not in puml
