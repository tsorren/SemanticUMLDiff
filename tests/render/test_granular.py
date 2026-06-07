from domain.models import UMLMethod
from render.member_renderer import MemberFormatter


def test_format_modified_method_visibility() -> None:
    base_m = UMLMethod("name", ("int a",), "void", "+")
    pr_m = UMLMethod("name", ("int a",), "void", "-")

    text = MemberFormatter.format_modified_method(base_m, pr_m, "types_only")
    assert text == "- <color:orange>name(int): void</color>"

def test_format_modified_method_name() -> None:
    base_m = UMLMethod("oldName", ("int a",), "void", "+")
    pr_m = UMLMethod("newName", ("int a",), "void", "+")

    text = MemberFormatter.format_modified_method(base_m, pr_m, "types_only")
    assert text == "+ <color:orange>newName(int): void</color>"

def test_format_modified_method_return_type() -> None:
    base_m = UMLMethod("name", ("int a",), "int", "+")
    pr_m = UMLMethod("name", ("int a",), "void", "+")

    text = MemberFormatter.format_modified_method(base_m, pr_m, "types_only")
    assert text == "+ <color:orange>name(int): void</color>"

def test_format_modified_method_param_type_changed() -> None:
    base_m = UMLMethod("name", ("int a",), "void", "+")
    pr_m = UMLMethod("name", ("String a",), "void", "+")

    text = MemberFormatter.format_modified_method(base_m, pr_m, "types_only")
    assert text == "+ <color:orange>name(String): void</color>"

def test_format_modified_method_param_name_changed_types_only() -> None:
    base_m = UMLMethod("name", ("int a",), "void", "+")
    pr_m = UMLMethod("name", ("int b",), "void", "+")

    # Under types_only, the parameter format is identical, so no orange is applied
    text = MemberFormatter.format_modified_method(base_m, pr_m, "types_only")
    assert text == "+ name(int): void"

def test_format_modified_method_param_name_changed_names_and_types() -> None:
    base_m = UMLMethod("name", ("int a",), "void", "+")
    pr_m = UMLMethod("name", ("int b",), "void", "+")

    # Under names_and_types, the string is different so it highlights
    text = MemberFormatter.format_modified_method(base_m, pr_m, "names_and_types")
    assert text == "+ <color:orange>name(int b): void</color>"

def test_format_modified_method_param_added() -> None:
    base_m = UMLMethod("name", ("int a",), "void", "+")
    pr_m = UMLMethod("name", ("int a", "String b"), "void", "+")

    text = MemberFormatter.format_modified_method(base_m, pr_m, "types_only")
    assert text == "+ <color:orange>name(int, String): void</color>"

