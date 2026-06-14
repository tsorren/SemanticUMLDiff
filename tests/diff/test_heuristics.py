from diff.compute import compute_diff_deepdiff
from domain.diff_models import ChangeType
from domain.models import UMLAttribute, UMLClass, UMLMethod, UMLModel


def test_moved_class_jaccard_similarity():
    # Base class: a.b.C1 with x, y attributes and m1() method
    base_class = UMLClass(
        name="a.b.C1",
        kind="class",
        attributes=(UMLAttribute("x", "int", "+"), UMLAttribute("y", "String", "+")),
        methods=(UMLMethod("m1", (), "void", "+"),)
    )
    # PR class: a.c.C1 with exact same attributes and methods
    pr_class = UMLClass(
        name="a.c.C1",
        kind="class",
        attributes=(UMLAttribute("x", "int", "+"), UMLAttribute("y", "String", "+")),
        methods=(UMLMethod("m1", (), "void", "+"),)
    )

    base = UMLModel("test", classes=(base_class,), relations=())
    pr = UMLModel("test", classes=(pr_class,), relations=())

    diff = compute_diff_deepdiff(base, pr)

    # Filter for non-package changes
    non_pkg_changes = [ch for ch in diff.changes if ch.entity_type != "package"]
    assert len(non_pkg_changes) == 1
    ch = non_pkg_changes[0]
    assert ch.entity_type == "class"
    assert ch.entity_name == "a.c.C1"
    assert ch.change_type == ChangeType.MODIFIED
    assert ch.context == "moved"
    assert ch.before == "a.b.C1"
    assert ch.after == "a.c.C1"

def test_moved_class_unique_candidate():
    # Base class: a.b.C1
    base_class = UMLClass(
        name="a.b.C1",
        kind="class",
        attributes=(UMLAttribute("x", "int", "+"), UMLAttribute("y", "String", "+")),
        methods=(UMLMethod("m1", (), "void", "+"),)
    )
    # PR class: a.c.C1 with y removed (similarity is 2/3 = 66.6% but it's the unique candidate)
    pr_class = UMLClass(
        name="a.c.C1",
        kind="class",
        attributes=(UMLAttribute("x", "int", "+"),),
        methods=(UMLMethod("m1", (), "void", "+"),)
    )

    base = UMLModel("test", classes=(base_class,), relations=())
    pr = UMLModel("test", classes=(pr_class,), relations=())

    diff = compute_diff_deepdiff(base, pr)

    # Should detect the move, AND detect the removal of attribute 'y'
    non_pkg_changes = [ch for ch in diff.changes if ch.entity_type != "package"]
    assert len(non_pkg_changes) == 2

    move_ch = next(c for c in non_pkg_changes if c.entity_type == "class")
    assert move_ch.change_type == ChangeType.MODIFIED
    assert move_ch.context == "moved"
    assert move_ch.before == "a.b.C1"
    assert move_ch.after == "a.c.C1"

    attr_ch = next(c for c in non_pkg_changes if c.entity_type == "attribute")
    assert attr_ch.change_type == ChangeType.REMOVED
    assert attr_ch.entity_name == "y"
    assert attr_ch.context == "a.c.C1"

def test_moved_class_rejected():
    # Base class: a.b.C1
    base_class = UMLClass(
        name="a.b.C1",
        kind="class",
        attributes=(UMLAttribute("x", "int", "+"),),
        methods=()
    )
    # PR class: a.c.C1 with totally different attributes (0% similarity)
    pr_class = UMLClass(
        name="a.c.C1",
        kind="class",
        attributes=(UMLAttribute("z", "String", "+"),),
        methods=()
    )

    base = UMLModel("test", classes=(base_class,), relations=())
    pr = UMLModel("test", classes=(pr_class,), relations=())

    diff = compute_diff_deepdiff(base, pr)

    # Move should be rejected, so we should get ADDED and REMOVED changes for classes and members
    classes_changed = [c for c in diff.changes if c.entity_type == "class"]
    assert len(classes_changed) == 2
    assert any(c.change_type == ChangeType.ADDED and c.entity_name == "a.c.C1" for c in classes_changed)
    assert any(c.change_type == ChangeType.REMOVED and c.entity_name == "a.b.C1" for c in classes_changed)

def test_method_rename_ratio():
    # SequenceMatcher ratio for "sendMessage" -> "sendMsg" is 14/20 = 70%
    base_m = UMLMethod("sendMessage", ("data: String",), "void", "+")
    pr_m = UMLMethod("sendMsg", ("data: String",), "void", "+")

    base = UMLModel("test", classes=(UMLClass("User", "class", methods=(base_m,)),), relations=())
    pr = UMLModel("test", classes=(UMLClass("User", "class", methods=(pr_m,)),), relations=())

    diff = compute_diff_deepdiff(base, pr)

    assert len(diff.changes) == 1
    ch = diff.changes[0]
    assert ch.entity_type == "method"
    assert ch.change_type == ChangeType.MODIFIED
    assert ch.before_element == base_m
    assert ch.after_element == pr_m

def test_method_rename_rejected():
    # SequenceMatcher ratio for "sendMessage" -> "post" is very low
    # But since it is not the only added/removed method in the class, it won't match as a rename
    base_m1 = UMLMethod("sendMessage", ("data: String",), "void", "+")
    base_m2 = UMLMethod("receiveMessage", ("data: String",), "void", "+")
    pr_m1 = UMLMethod("post", ("data: String",), "void", "+")
    pr_m2 = UMLMethod("fetch", ("data: String",), "void", "+")

    base = UMLModel("test", classes=(UMLClass("User", "class", methods=(base_m1, base_m2)),), relations=())
    pr = UMLModel("test", classes=(UMLClass("User", "class", methods=(pr_m1, pr_m2)),), relations=())

    diff = compute_diff_deepdiff(base, pr)

    # We should get separate ADDED and REMOVED method changes
    added_methods = [c for c in diff.changes if c.change_type == ChangeType.ADDED]
    removed_methods = [c for c in diff.changes if c.change_type == ChangeType.REMOVED]
    assert len(added_methods) == 2
    assert len(removed_methods) == 2

def test_method_parameter_type_changed():
    # Same name, different parameter signature
    base_m = UMLMethod("process", ("id: int",), "void", "+")
    pr_m = UMLMethod("process", ("id: String",), "void", "+")

    base = UMLModel("test", classes=(UMLClass("User", "class", methods=(base_m,)),), relations=())
    pr = UMLModel("test", classes=(UMLClass("User", "class", methods=(pr_m,)),), relations=())

    diff = compute_diff_deepdiff(base, pr)

    assert len(diff.changes) == 1
    ch = diff.changes[0]
    assert ch.entity_type == "method"
    assert ch.change_type == ChangeType.MODIFIED
    assert ch.before_element == base_m
    assert ch.after_element == pr_m
