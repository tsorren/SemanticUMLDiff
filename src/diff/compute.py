import os
from typing import List, Tuple

from domain.diff_models import ChangeType, DiffItem, DiffResult
from domain.models import UMLClass, UMLMethod, UMLModel, UMLRelation


def _detect_root_package(base: UMLModel, pr: UMLModel, root_package: str = "") -> str:
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


def _filter_internal_classes(classes: Tuple[UMLClass, ...] | List[UMLClass], root_package: str) -> dict[str, UMLClass]:
    def get_package(fqn: str) -> str:
        parts = fqn.rsplit(".", 1)
        return parts[0] if len(parts) > 1 else ""

    def is_external(fqn: str) -> bool:
        if not root_package:
            return False
        pkg = get_package(fqn)
        return bool(pkg and not pkg.startswith(root_package))

    return {c.name: c for c in classes if not is_external(c.name)}


def _detect_moved_classes(
    added_classes: dict[str, UMLClass],
    removed_classes: dict[str, UMLClass],
    changes: List[DiffItem],
    method_parameter_style: str
) -> Tuple[set[str], set[str]]:
    def get_short_name(fqn: str) -> str:
        return fqn.rsplit(".", 1)[-1]

    moved_classes_target = set()
    moved_classes_source = set()

    for add_name, add_c in list(added_classes.items()):
        short_name = get_short_name(add_name)
        candidates = [rm_name for rm_name, rm_c in removed_classes.items() if get_short_name(rm_name) == short_name]

        for rm_name in candidates:
            rm_c = removed_classes[rm_name]

            add_members = set(f"{m.name}({','.join(m.parameters)})" for m in add_c.methods) | set(a.name for a in add_c.attributes)
            rm_members = set(f"{m.name}({','.join(m.parameters)})" for m in rm_c.methods) | set(a.name for a in rm_c.attributes)

            total = len(add_members | rm_members)
            if total == 0:
                sim = 1.0
            else:
                sim = len(add_members & rm_members) / total

            add_member_names = set(m.name for m in add_c.methods) | set(a.name for a in add_c.attributes)
            rm_member_names = set(m.name for m in rm_c.methods) | set(a.name for a in rm_c.attributes)
            total_names = len(add_member_names | rm_member_names)
            sim_names = len(add_member_names & rm_member_names) / total_names if total_names > 0 else 1.0

            is_moved = False
            if sim >= 0.75:
                is_moved = True
            elif len(candidates) == 1 and sim_names >= 0.50:
                is_moved = True

            if is_moved:
                changes.append(DiffItem(
                    entity_type="class",
                    entity_name=add_name,
                    change_type=ChangeType.MODIFIED,
                    context="moved",
                    before=rm_name,
                    after=add_name
                ))
                moved_classes_target.add(add_name)
                moved_classes_source.add(rm_name)

                _compare_members(rm_c, add_c, add_name, changes, method_parameter_style)

                del added_classes[add_name]
                del removed_classes[rm_name]
                break

    return moved_classes_target, moved_classes_source


def _compare_class_additions_removals(
    added_classes: dict[str, UMLClass],
    removed_classes: dict[str, UMLClass],
    changes: List[DiffItem]
) -> None:
    for name in added_classes:
        changes.append(DiffItem(
            entity_type="class",
            entity_name=name,
            change_type=ChangeType.ADDED
        ))

    for name in removed_classes:
        changes.append(DiffItem(
            entity_type="class",
            entity_name=name,
            change_type=ChangeType.REMOVED
        ))


def _compare_existing_classes_members(
    base_classes: dict[str, UMLClass],
    pr_classes: dict[str, UMLClass],
    changes: List[DiffItem],
    method_parameter_style: str
) -> None:
    for name, c in pr_classes.items():
        if name in base_classes:
            base_c = base_classes[name]
            if base_c.kind != c.kind:
                changes.append(DiffItem(
                    entity_type="class",
                    entity_name=name,
                    change_type=ChangeType.MODIFIED,
                    before=base_c.kind,
                    after=c.kind
                ))
            _compare_members(base_c, c, name, changes, method_parameter_style)


def _compare_packages(
    base_classes: dict[str, UMLClass],
    pr_classes: dict[str, UMLClass],
    changes: List[DiffItem]
) -> None:
    def get_package(fqn: str) -> str:
        parts = fqn.rsplit(".", 1)
        return parts[0] if len(parts) > 1 else ""

    base_pkgs = set(get_package(name) for name in base_classes if get_package(name))
    pr_pkgs = set(get_package(name) for name in pr_classes if get_package(name))

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


def _compare_relations(
    base: UMLModel,
    pr: UMLModel,
    root_package: str,
    changes: List[DiffItem]
) -> None:
    def get_package(fqn: str) -> str:
        parts = fqn.rsplit(".", 1)
        return parts[0] if len(parts) > 1 else ""

    def is_external(fqn: str) -> bool:
        if not root_package:
            return False
        pkg = get_package(fqn)
        return bool(pkg and not pkg.startswith(root_package))

    def rel_key(r: UMLRelation) -> Tuple[str, str]:
        return (r.source, r.target)

    base_relations = [r for r in base.relations if not is_external(r.source) and not is_external(r.target)]
    pr_relations = [r for r in pr.relations if not is_external(r.source) and not is_external(r.target)]

    base_rels = {rel_key(r): r for r in base_relations}
    pr_rels = {rel_key(r): r for r in pr_relations}

    for key, r in pr_rels.items():
        if key not in base_rels:
            changes.append(DiffItem(
                entity_type="relation",
                entity_name=f"{r.source} {r.relation_type} {r.target}",
                change_type=ChangeType.ADDED
            ))
        else:
            base_r = base_rels[key]
            if base_r.relation_type != r.relation_type or \
               base_r.multiplicity_source != r.multiplicity_source or \
               base_r.multiplicity_target != r.multiplicity_target:
                changes.append(DiffItem(
                    entity_type="relation",
                    entity_name=f"{r.source} {r.relation_type} {r.target}",
                    change_type=ChangeType.MODIFIED,
                    before=f"{base_r.relation_type}",
                    after=f"{r.relation_type}"
                ))

    for key, r in base_rels.items():
        if key not in pr_rels:
            changes.append(DiffItem(
                entity_type="relation",
                entity_name=f"{r.source} {r.relation_type} {r.target}",
                change_type=ChangeType.REMOVED
            ))


def compute_diff(base: UMLModel, pr: UMLModel, root_package: str = "", method_parameter_style: str = "types_only") -> DiffResult:
    changes: List[DiffItem] = []

    # 1. Detect Root Package and Filter Classes
    root_package = _detect_root_package(base, pr, root_package)
    base_classes = _filter_internal_classes(base.classes, root_package)
    pr_classes = _filter_internal_classes(pr.classes, root_package)

    added_classes = {name: c for name, c in pr_classes.items() if name not in base_classes}
    removed_classes = {name: c for name, c in base_classes.items() if name not in pr_classes}

    # 2. Detect Moved Classes
    _detect_moved_classes(added_classes, removed_classes, changes, method_parameter_style)

    # 3. Compare Class Additions/Removals
    _compare_class_additions_removals(added_classes, removed_classes, changes)

    # 4. Compare Existing Classes and Members
    _compare_existing_classes_members(base_classes, pr_classes, changes, method_parameter_style)

    # 5. Compare Packages
    _compare_packages(base_classes, pr_classes, changes)

    # 6. Compare Relations
    _compare_relations(base, pr, root_package, changes)

    return DiffResult(
        module_name=pr.module_name,
        changes=tuple(changes)
    )


def _compare_members(base_c: UMLClass, pr_c: UMLClass, context_name: str, changes: List[DiffItem], method_parameter_style: str = "types_only") -> None:
    def _get_parameter_types(parameters: Tuple[str, ...] | List[str]) -> List[str]:
        types = []
        for p in parameters:
            if ":" in p:
                types.append(p.split(":", 1)[1].strip())
            else:
                parts = p.strip().split()
                if len(parts) > 1:
                    types.append(" ".join(parts[:-1]))
                else:
                    types.append(p.strip())
        return types

    # Compare attributes
    base_attrs = {a.name: a for a in base_c.attributes}
    pr_attrs = {a.name: a for a in pr_c.attributes}

    for name, a in pr_attrs.items():
        if name not in base_attrs:
            changes.append(DiffItem(
                entity_type="attribute",
                entity_name=name,
                change_type=ChangeType.ADDED,
                context=context_name
            ))
        else:
            base_a = base_attrs[name]
            if base_a != a:
                changes.append(DiffItem(
                    entity_type="attribute",
                    entity_name=name,
                    change_type=ChangeType.MODIFIED,
                    context=context_name,
                    before=f"{base_a.visibility} {base_a.name}: {base_a.type}".strip(),
                    after=f"{a.visibility} {a.name}: {a.type}".strip(),
                    before_element=base_a,
                    after_element=a
                ))

    for name, a in base_attrs.items():
        if name not in pr_attrs:
            changes.append(DiffItem(
                entity_type="attribute",
                entity_name=name,
                change_type=ChangeType.REMOVED,
                context=context_name,
                before_element=a
            ))

    # Compare methods with FULL signature as key
    def method_key(m: UMLMethod) -> str:
        types = []
        for p in m.parameters:
            if ":" in p:
                types.append(p.split(":", 1)[1].strip())
            else:
                parts = p.strip().split()
                if len(parts) > 1:
                    types.append(" ".join(parts[:-1]))
                else:
                    types.append(p.strip())
        return f"{m.name}({','.join(types)})"

    def method_sig(m: UMLMethod) -> str:
        types = []
        for p in m.parameters:
            if ":" in p:
                types.append(p.split(":", 1)[1].strip())
            else:
                parts = p.strip().split()
                if len(parts) > 1:
                    types.append(" ".join(parts[:-1]))
                else:
                    types.append(p.strip())
        return f"({','.join(types)}):{m.return_type}"

    base_methods = {method_key(m): m for m in base_c.methods}
    pr_methods = {method_key(m): m for m in pr_c.methods}

    added_keys = set(pr_methods.keys()) - set(base_methods.keys())
    removed_keys = set(base_methods.keys()) - set(pr_methods.keys())
    common_keys = set(pr_methods.keys()) & set(base_methods.keys())

    # Detect Parameter/Return Type Changes (Same Name, different signature)
    from collections import defaultdict
    added_by_name = defaultdict(list)
    removed_by_name = defaultdict(list)

    for k in added_keys:
        m = pr_methods[k]
        added_by_name[m.name].append(m)
    for k in removed_keys:
        m = base_methods[k]
        removed_by_name[m.name].append(m)

    for name in list(added_by_name.keys()):
        if name in removed_by_name:
            if len(added_by_name[name]) == 1 and len(removed_by_name[name]) == 1:
                add_m = added_by_name[name][0]
                rm_m = removed_by_name[name][0]

                changes.append(DiffItem(
                    entity_type="method",
                    entity_name=method_key(add_m),
                    change_type=ChangeType.MODIFIED,
                    context=context_name,
                    before_element=rm_m,
                    after_element=add_m
                ))

                added_keys.remove(method_key(add_m))
                removed_keys.remove(method_key(rm_m))

    # Detect Renames (Same Signature, different name)
    added_by_sig = defaultdict(list)
    removed_by_sig = defaultdict(list)

    for k in added_keys:
        m = pr_methods[k]
        added_by_sig[method_sig(m)].append(m)
    for k in removed_keys:
        m = base_methods[k]
        removed_by_sig[method_sig(m)].append(m)

    import difflib
    for sig in list(added_by_sig.keys()):
        if sig in removed_by_sig:
            if len(added_by_sig[sig]) == 1 and len(removed_by_sig[sig]) == 1:
                add_m = added_by_sig[sig][0]
                rm_m = removed_by_sig[sig][0]

                name_sim = difflib.SequenceMatcher(None, add_m.name, rm_m.name).ratio()
                is_rename = False
                if name_sim >= 0.70:
                    is_rename = True
                elif len(base_methods) == 1 and len(pr_methods) == 1:
                    is_rename = True
                elif len(added_keys) == 1 and len(removed_keys) == 1:
                    is_rename = True

                if is_rename:
                    changes.append(DiffItem(
                        entity_type="method",
                        entity_name=method_key(add_m),
                        change_type=ChangeType.MODIFIED,
                        context=context_name,
                        before_element=rm_m,
                        after_element=add_m
                    ))

                    added_keys.remove(method_key(add_m))
                    removed_keys.remove(method_key(rm_m))

    for key in added_keys:
        changes.append(DiffItem(
            entity_type="method",
            entity_name=key,
            change_type=ChangeType.ADDED,
            context=context_name,
            after_element=pr_methods[key]
        ))

    for key in common_keys:
        base_m = base_methods[key]
        m = pr_methods[key]

        if method_parameter_style == "types_only":
            params_changed = _get_parameter_types(base_m.parameters) != _get_parameter_types(m.parameters)
        else:
            params_changed = base_m.parameters != m.parameters

        if base_m.visibility != m.visibility or base_m.return_type != m.return_type or params_changed:
            b_sig = f"{base_m.visibility} {base_m.name}({','.join(base_m.parameters)}): {base_m.return_type}"
            a_sig = f"{m.visibility} {m.name}({','.join(m.parameters)}): {m.return_type}"
            changes.append(DiffItem(
                entity_type="method",
                entity_name=key,
                change_type=ChangeType.MODIFIED,
                context=context_name,
                before=b_sig.strip(),
                after=a_sig.strip(),
                before_element=base_m,
                after_element=m
            ))

    for key in removed_keys:
        changes.append(DiffItem(
            entity_type="method",
            entity_name=key,
            change_type=ChangeType.REMOVED,
            context=context_name,
            before_element=base_methods[key]
        ))
