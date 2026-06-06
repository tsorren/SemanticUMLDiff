from diff.compute import compute_diff
from domain.diff_models import ChangeType
from domain.models import UMLAttribute, UMLClass, UMLMethod, UMLModel


def test_root_package_auto_detection() -> None:
    # 3 classes: com.app.core.A, com.app.core.B, and a third party lib org.lib.Util
    model1 = UMLModel(
        module_name="test",
        classes=(
            UMLClass(name="com.app.core.A", kind="class"),
            UMLClass(name="com.app.core.B", kind="class"),
            UMLClass(name="org.lib.Util", kind="class")
        )
    )
    model2 = UMLModel(
        module_name="test",
        classes=(
            UMLClass(name="com.app.core.A", kind="class"),
            UMLClass(name="com.app.core.B", kind="class"),
            UMLClass(name="com.app.core.C", kind="class"), # added
            UMLClass(name="org.lib.Util", kind="class")
        )
    )
    diff = compute_diff(model1, model2, root_package="com.app.core")
    class_adds = [c for c in diff.changes if c.entity_type == "class" and c.change_type == ChangeType.ADDED]
    assert len(class_adds) == 1
    assert class_adds[0].entity_name == "com.app.core.C"

def test_root_package_filtering() -> None:
    base_model = UMLModel(
        module_name="test",
        classes=(
            UMLClass(name="com.app.core.A", kind="class"),
            UMLClass(name="com.app.core.B", kind="class"),
        )
    )
    pr_model = UMLModel(
        module_name="test",
        classes=(
            UMLClass(name="com.app.core.A", kind="class"),
            UMLClass(name="com.app.core.B", kind="class"),
            UMLClass(name="org.lib.Util", kind="class") # External, shouldn't be diffed
        )
    )
    diff = compute_diff(base_model, pr_model, root_package="com.app.core")

    # org.lib.Util should be filtered out
    class_adds = [c for c in diff.changes if c.entity_type == "class" and c.change_type == ChangeType.ADDED]
    assert len(class_adds) == 0

def test_method_overloading() -> None:
    base_model = UMLModel(
        module_name="test",
        classes=(
            UMLClass(
                name="A", kind="class", methods=(
                    UMLMethod(name="doWork", parameters=(), return_type="void"),
                )
            ),
        )
    )
    pr_model = UMLModel(
        module_name="test",
        classes=(
            UMLClass(
                name="A", kind="class", methods=(
                    UMLMethod(name="doWork", parameters=(), return_type="void"),
                    UMLMethod(name="doWork", parameters=("int x",), return_type="void"),
                )
            ),
        )
    )

    diff = compute_diff(base_model, pr_model)
    method_adds = [c for c in diff.changes if c.entity_type == "method" and c.change_type == ChangeType.ADDED]
    assert len(method_adds) == 1
    assert method_adds[0].entity_name == "doWork(int)"

def test_class_moved() -> None:
    base_model = UMLModel(
        module_name="test",
        classes=(
            UMLClass(
                name="pkg1.A", kind="class", attributes=(
                    UMLAttribute(name="id", type="int"),
                    UMLAttribute(name="name", type="str"),
                    UMLAttribute(name="email", type="str"),
                    UMLAttribute(name="phone", type="str"),
                )
            ),
        )
    )
    pr_model = UMLModel(
        module_name="test",
        classes=(
            UMLClass(
                name="pkg2.A", kind="class", attributes=(
                        UMLAttribute(name="id", type="int"),
                        UMLAttribute(name="name", type="str"),
                        UMLAttribute(name="email", type="str"),
                        UMLAttribute(name="phone", type="str"),
                        UMLAttribute(name="new_id", type="int"),
                )
            ),
        )
    )

    diff = compute_diff(base_model, pr_model)
    class_mods = [c for c in diff.changes if c.entity_type == "class" and c.change_type == ChangeType.MODIFIED and c.context == "moved"]
    assert len(class_mods) == 1
    assert class_mods[0].entity_name == "pkg2.A"
    assert class_mods[0].before == "pkg1.A"
    assert class_mods[0].after == "pkg2.A"

    # And there should be an attribute added
    attr_adds = [c for c in diff.changes if c.entity_type == "attribute" and c.change_type == ChangeType.ADDED]
    assert len(attr_adds) == 1
    assert attr_adds[0].entity_name == "new_id"
    assert attr_adds[0].context == "pkg2.A"
