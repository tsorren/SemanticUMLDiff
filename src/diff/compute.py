"""
Motor de diff semántico basado en DeepDiff.

Traduce los paths sintácticos de DeepDiff en cambios semánticos de dominio.
"""
import re
from typing import Any, Dict, List, Tuple

from deepdiff import DeepDiff

from domain.diff_models import ChangeType, DiffItem, DiffResult
from domain.models import UMLClass, UMLModel

# Regex para parsear paths de DeepDiff
PATH_RE = re.compile(
    r"root\['(\w+)'\]\['([^']+)'\]"
    r"(?:\['(\w+)'\]\['([^']+)'\])?"
    r"(?:\['(\w+)'\])?"
)

def _parse_deepdiff_path(path: str) -> Dict[str, Any]:
    """
    Parsea un path de DeepDiff y extrae la información semántica.

    Returns: dict con keys: category, entity_name, member_type, member_name, field
    """
    m = PATH_RE.match(path)
    if not m:
        return {}

    groups = m.groups()
    result = {
        "category": groups[0],       # "classes" | "relations"
        "entity_name": groups[1],    # FQN de la clase o clave de relación
    }
    if groups[2]:
        result["member_type"] = groups[2]   # "attributes" | "methods"
    if groups[3]:
        result["member_name"] = groups[3]   # nombre del atributo o firma del método
    if groups[4]:
        result["field"] = groups[4]         # "type" | "visibility" | "return_type" | "kind" ...

    return result

def _resolve_element(model: UMLModel, class_name: str, member_type: str, member_name: str) -> Any:
    """Busca el objeto de dominio original en el modelo."""
    for cls in model.classes:
        if cls.name == class_name:
            if member_type == "attributes":
                for attr in cls.attributes:
                    if attr.name == member_name:
                        return attr
            elif member_type == "methods":
                for method in cls.methods:
                    from diff.serializer import _extract_type_from_parameter
                    types = [_extract_type_from_parameter(p) for p in method.parameters]
                    sig = f"{method.name}({','.join(types)})"
                    if sig == member_name:
                        return method
    return None

def _detect_root_package(base: UMLModel, pr: UMLModel, root_package: str = "") -> str:
    import os
    def get_package(fqn: str) -> str:
        parts = fqn.rsplit(".", 1)
        return parts[0] if len(parts) > 1 else ""

    all_fqns = set(c.name for c in base.classes) | set(c.name for c in pr.classes)
    if not root_package and all_fqns:
        packages = [get_package(fqn) for fqn in all_fqns if get_package(fqn)]
        if packages:
            lcp = os.path.commonprefix(packages)
            if lcp and not lcp.endswith('.') and '.' in lcp:
                if lcp not in packages:
                    lcp = lcp.rsplit('.', 1)[0]
            root_package = lcp.rstrip('.')
    return root_package

def _apply_filters(model: UMLModel, root_package: str) -> UMLModel:
    def get_package(fqn: str) -> str:
        parts = fqn.rsplit(".", 1)
        return parts[0] if len(parts) > 1 else ""

    def is_external(fqn: str) -> bool:
        if not root_package:
            return False
        pkg = get_package(fqn)
        return bool(pkg and not pkg.startswith(root_package))

    classes_filtered = [c for c in model.classes if not is_external(c.name)]
    relations_filtered = [r for r in model.relations if not is_external(r.source) and not is_external(r.target)]

    return UMLModel(
        module_name=model.module_name,
        classes=tuple(classes_filtered),
        relations=tuple(relations_filtered),
        source_hash=model.source_hash
    )

def _compare_packages_legacy(base_filtered: UMLModel, pr_filtered: UMLModel, changes: List[DiffItem]) -> None:
    def get_package(fqn: str) -> str:
        parts = fqn.rsplit(".", 1)
        return parts[0] if len(parts) > 1 else ""

    base_pkgs = set(get_package(c.name) for c in base_filtered.classes if get_package(c.name))
    pr_pkgs = set(get_package(c.name) for c in pr_filtered.classes if get_package(c.name))

    for pkg in pr_pkgs - base_pkgs:
        if pkg:
            changes.append(DiffItem(entity_type="package", entity_name=pkg, change_type=ChangeType.ADDED))

    for pkg in base_pkgs - pr_pkgs:
        if pkg:
            changes.append(DiffItem(entity_type="package", entity_name=pkg, change_type=ChangeType.REMOVED))

    for pkg in pr_pkgs & base_pkgs:
        if not pkg:
            continue
        pkg_changed = False
        for ch in changes:
            if ch.entity_type == "class" and get_package(ch.entity_name) == pkg:
                pkg_changed = True
                break
            if ch.entity_type == "class" and ch.context == "moved" and (get_package(ch.before or "") == pkg or get_package(ch.after or "") == pkg):
                pkg_changed = True
                break
            if ch.entity_type in ("method", "attribute") and get_package(ch.context) == pkg:
                pkg_changed = True
                break
        if pkg_changed:
            changes.append(DiffItem(entity_type="package", entity_name=pkg, change_type=ChangeType.MODIFIED))

def compute_diff_deepdiff(
    base: UMLModel, pr: UMLModel, root_package: str = "", method_parameter_style: str = "types_only",
) -> DiffResult:
    """
    Computa la diferencia semántica entre dos modelos UML usando DeepDiff.
    """
    from dataclasses import replace

    from diff.heuristics import detect_method_renames, detect_moved_classes
    from diff.serializer import model_to_dict

    root_package = _detect_root_package(base, pr, root_package)

    base_filtered = _apply_filters(base, root_package)
    pr_filtered = _apply_filters(pr, root_package)

    base_dict = model_to_dict(base_filtered, method_parameter_style)
    pr_dict = model_to_dict(pr_filtered, method_parameter_style)

    ddiff = DeepDiff(base_dict, pr_dict, ignore_order=True, threshold_to_diff_deeper=0)

    changes: List[DiffItem] = []

    # 1. Dictionary Items Added
    for path in ddiff.get("dictionary_item_added", []):
        info = _parse_deepdiff_path(path)
        if not info:
            continue

        category = info["category"]
        entity_name = info["entity_name"]

        if category == "classes":
            if "member_type" not in info or not info["member_type"]:
                # Class added
                changes.append(DiffItem(
                    entity_type="class",
                    entity_name=entity_name,
                    change_type=ChangeType.ADDED
                ))
            else:
                member_type = info["member_type"]
                member_name = info["member_name"]
                # Member added
                elem = _resolve_element(pr_filtered, entity_name, member_type, member_name)
                changes.append(DiffItem(
                    entity_type=member_type[:-1], # "methods" -> "method", "attributes" -> "attribute"
                    entity_name=member_name,
                    change_type=ChangeType.ADDED,
                    context=entity_name,
                    after_element=elem
                ))
        elif category == "relations":
            # Relation added. The relation key is like "SourceType target"
            # We need to find the relation in pr_filtered to get exact details
            rel = None
            for r in pr_filtered.relations:
                key = f"{r.source} {r.relation_type} {r.target}"
                if key == entity_name:
                    rel = r
                    break
            if rel:
                changes.append(DiffItem(
                    entity_type="relation",
                    entity_name=entity_name,
                    change_type=ChangeType.ADDED
                ))

    # 2. Dictionary Items Removed
    for path in ddiff.get("dictionary_item_removed", []):
        info = _parse_deepdiff_path(path)
        if not info:
            continue

        category = info["category"]
        entity_name = info["entity_name"]

        if category == "classes":
            if "member_type" not in info or not info["member_type"]:
                # Class removed
                changes.append(DiffItem(
                    entity_type="class",
                    entity_name=entity_name,
                    change_type=ChangeType.REMOVED
                ))
            else:
                member_type = info["member_type"]
                member_name = info["member_name"]
                # Member removed
                elem = _resolve_element(base_filtered, entity_name, member_type, member_name)
                changes.append(DiffItem(
                    entity_type=member_type[:-1],
                    entity_name=member_name,
                    change_type=ChangeType.REMOVED,
                    context=entity_name,
                    before_element=elem
                ))
        elif category == "relations":
            # Relation removed
            changes.append(DiffItem(
                entity_type="relation",
                entity_name=entity_name,
                change_type=ChangeType.REMOVED
            ))

    # 3. Values Changed (modified properties)
    # We group changes by member to avoid duplicates
    modified_members: Dict[Tuple[str, str, str], List[Tuple[str, Any]]] = {}
    modified_classes = {}
    modified_relations = {}

    for path, detail in ddiff.get("values_changed", {}).items():
        info = _parse_deepdiff_path(path)
        if not info:
            continue

        category = info["category"]
        entity_name = info["entity_name"]

        if category == "classes":
            if "member_type" not in info or not info["member_type"]:
                # Class property changed (e.g. kind)
                modified_classes[entity_name] = detail
            else:
                member_type = info["member_type"]
                member_name = info["member_name"]
                member_key = (entity_name, member_type, member_name)
                if member_key not in modified_members:
                    modified_members[member_key] = []
                modified_members[member_key].append((info["field"], detail))
        elif category == "relations":
            # Relation property changed (e.g. multiplicity)
            modified_relations[entity_name] = detail

    # Process modified classes
    for class_name, detail in modified_classes.items():
        # Typically class kind changed
        base_cls = next((c for c in base_filtered.classes if c.name == class_name), None)
        pr_cls = next((c for c in pr_filtered.classes if c.name == class_name), None)
        if base_cls and pr_cls:
            changes.append(DiffItem(
                entity_type="class",
                entity_name=class_name,
                change_type=ChangeType.MODIFIED,
                before=base_cls.kind,
                after=pr_cls.kind
            ))

    # Process modified members
    for (entity_name, member_type, member_name), field_changes in modified_members.items():
        base_elem = _resolve_element(base_filtered, entity_name, member_type, member_name)
        pr_elem = _resolve_element(pr_filtered, entity_name, member_type, member_name)

        if member_type == "attributes":
            if base_elem and pr_elem:
                before_str = f"{base_elem.visibility} {base_elem.name}: {base_elem.type}".strip()
                after_str = f"{pr_elem.visibility} {pr_elem.name}: {pr_elem.type}".strip()
                changes.append(DiffItem(
                    entity_type="attribute",
                    entity_name=member_name,
                    change_type=ChangeType.MODIFIED,
                    context=entity_name,
                    before=before_str,
                    after=after_str,
                    before_element=base_elem,
                    after_element=pr_elem
                ))
        elif member_type == "methods":
            if base_elem and pr_elem:
                before_str = f"{base_elem.visibility} {base_elem.name}({','.join(base_elem.parameters)}): {base_elem.return_type}"
                after_str = f"{pr_elem.visibility} {pr_elem.name}({','.join(pr_elem.parameters)}): {pr_elem.return_type}"
                changes.append(DiffItem(
                    entity_type="method",
                    entity_name=member_name,
                    change_type=ChangeType.MODIFIED,
                    context=entity_name,
                    before=before_str.strip(),
                    after=after_str.strip(),
                    before_element=base_elem,
                    after_element=pr_elem
                ))

    # Process modified relations
    for rel_name, detail in modified_relations.items():
        # E.g. key is "SourceType target"
        # Multiplicities or type changed. Legacy compute.py before and after are relation types.
        # Let's find base and pr relations
        base_rel = next((r for r in base_filtered.relations if f"{r.source} {r.relation_type} {r.target}" == rel_name), None)
        pr_rel = next((r for r in pr_filtered.relations if f"{r.source} {r.relation_type} {r.target}" == rel_name), None)
        if base_rel and pr_rel:
            changes.append(DiffItem(
                entity_type="relation",
                entity_name=rel_name,
                change_type=ChangeType.MODIFIED,
                before=base_rel.relation_type,
                after=pr_rel.relation_type
            ))

    # Apply heuristics
    base_classes_dict = {c.name: c for c in base_filtered.classes}
    pr_classes_dict = {c.name: c for c in pr_filtered.classes}

    # 1. Detect Moved Classes
    changes, moved_pairs = detect_moved_classes(
        changes, base_classes_dict, pr_classes_dict, method_parameter_style
    )

    # Compare members of moved classes using DeepDiff recursively on dummy models
    for rm_name, add_name in moved_pairs:
        rm_c = base_classes_dict.get(rm_name)
        add_c = pr_classes_dict.get(add_name)
        if rm_c and add_c:
            rm_c_renamed = replace(rm_c, name=add_name)

            dummy_base = UMLModel(
                module_name=base_filtered.module_name,
                classes=(rm_c_renamed,),
                relations=(),
                source_hash=base_filtered.source_hash
            )
            dummy_pr = UMLModel(
                module_name=pr_filtered.module_name,
                classes=(add_c,),
                relations=(),
                source_hash=pr_filtered.source_hash
            )

            dummy_result = compute_diff_deepdiff(
                dummy_base, dummy_pr, root_package="", method_parameter_style=method_parameter_style
            )

            for ch in dummy_result.changes:
                if ch.entity_type in ("method", "attribute"):
                    changes.append(ch)

    # Map moved class names in base_classes_dict to their original class objects
    # under the new name so that method rename detection can resolve contexts
    base_classes_for_renames = dict(base_classes_dict)
    for rm_name, add_name in moved_pairs:
        rm_c = base_classes_dict.get(rm_name)
        if rm_c:
            base_classes_for_renames[add_name] = rm_c

    # 2. Detect Method Renames and Signature changes
    changes = detect_method_renames(
        changes, base_classes_for_renames, pr_classes_dict, method_parameter_style
    )

    # 4. Package Comparison (Legacy behavior)
    _compare_packages_legacy(base_filtered, pr_filtered, changes)

    return DiffResult(module_name=pr.module_name, changes=tuple(changes))


compute_diff = compute_diff_deepdiff


def _compare_members(base_c: UMLClass, pr_c: UMLClass, context: str, changes: List[DiffItem]) -> None:
    """Función de compatibilidad para pruebas legacy de rename/miembros."""
    base = UMLModel("test", classes=(base_c,), relations=())
    pr = UMLModel("test", classes=(pr_c,), relations=())
    res = compute_diff_deepdiff(base, pr)
    for ch in res.changes:
        if ch.entity_type in ("method", "attribute"):
            changes.append(ch)

