import os
from typing import List, Tuple

from domain.diff_models import ChangeType, DiffItem, DiffResult
from domain.models import UMLClass, UMLMethod, UMLModel, UMLRelation


def compute_diff(base: UMLModel, pr: UMLModel, root_package: str = "") -> DiffResult:
    changes: List[DiffItem] = []

    def get_package(fqn: str) -> str:
        parts = fqn.rsplit(".", 1)
        return parts[0] if len(parts) > 1 else ""

    def get_short_name(fqn: str) -> str:
        return fqn.rsplit(".", 1)[-1]

    # Auto-detect Root Package
    all_fqns = set(c.name for c in base.classes) | set(c.name for c in pr.classes)
    if not root_package and all_fqns:
        packages = [get_package(fqn) for fqn in all_fqns if get_package(fqn)]
        if packages:
            lcp = os.path.commonprefix(packages)
            # Make sure we don't cut off in the middle of a package name if possible
            if lcp and not lcp.endswith('.') and '.' in lcp:
                # E.g. lcp is "com.app.cor", cut to "com.app"
                # Wait, if all packages are "pkg1" and "pkg2", lcp="pkg", rsplit will break it.
                # If there's a dot, we trim to the last dot unless the LCP exactly matches one of the packages.
                if lcp not in packages:
                    lcp = lcp.rsplit('.', 1)[0]
            root_package = lcp.rstrip('.')

    def is_external(fqn: str) -> bool:
        if not root_package:
            return False
        pkg = get_package(fqn)
        return bool(pkg and not pkg.startswith(root_package))

    base_classes = {c.name: c for c in base.classes if not is_external(c.name)}
    pr_classes = {c.name: c for c in pr.classes if not is_external(c.name)}

    # 1. Compare Classes
    added_classes = {name: c for name, c in pr_classes.items() if name not in base_classes}
    removed_classes = {name: c for name, c in base_classes.items() if name not in pr_classes}

    # Similarity detection for MOVED classes
    moved_classes_target = set()
    moved_classes_source = set()

    for add_name, add_c in list(added_classes.items()):
        short_name = get_short_name(add_name)
        # Find candidates in removed classes
        candidates = [rm_name for rm_name, rm_c in removed_classes.items() if get_short_name(rm_name) == short_name]

        for rm_name in candidates:
            rm_c = removed_classes[rm_name]

            # Simple similarity: matched methods + attrs / total methods + attrs
            add_members = set(f"{m.name}({','.join(m.parameters)})" for m in add_c.methods) | set(a.name for a in add_c.attributes)
            rm_members = set(f"{m.name}({','.join(m.parameters)})" for m in rm_c.methods) | set(a.name for a in rm_c.attributes)

            total = len(add_members | rm_members)
            if total == 0:
                sim = 1.0 # Empty classes with same name
            else:
                sim = len(add_members & rm_members) / total

            if sim >= 0.75:
                # Mark as moved!
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

                # Also compare members so we catch minor changes inside the moved class!
                _compare_members(rm_c, add_c, add_name, changes)

                # Remove from added/removed
                del added_classes[add_name]
                del removed_classes[rm_name]
                break

    for name, c in added_classes.items():
        changes.append(DiffItem(
            entity_type="class",
            entity_name=name,
            change_type=ChangeType.ADDED
        ))

    for name, c in removed_classes.items():
        changes.append(DiffItem(
            entity_type="class",
            entity_name=name,
            change_type=ChangeType.REMOVED
        ))

    # Existing classes comparison
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
            _compare_members(base_c, c, name, changes)

    # 2. Track Packages
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
        # A package is modified if any class inside it was added, removed, or modified
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

    # 3. Compare Relations
    def rel_key(r: UMLRelation) -> Tuple[str, str]:
        return (r.source, r.target)

    # Filter relations if external
    base_relations = [r for r in base.relations if not is_external(r.source) and not is_external(r.target)]
    pr_relations = [r for r in pr.relations if not is_external(r.source) and not is_external(r.target)]

    # Relations between identical source/target but different types will be collapsed or treated as MODIFIED
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

    return DiffResult(
        module_name=pr.module_name,
        changes=tuple(changes)
    )

def _compare_members(base_c: UMLClass, pr_c: UMLClass, context_name: str, changes: List[DiffItem]) -> None:
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
                    after=f"{a.visibility} {a.name}: {a.type}".strip()
                ))

    for name, a in base_attrs.items():
        if name not in pr_attrs:
            changes.append(DiffItem(
                entity_type="attribute",
                entity_name=name,
                change_type=ChangeType.REMOVED,
                context=context_name
            ))

    # Compare methods with FULL signature as key
    def method_key(m: UMLMethod) -> str:
        types = []
        for p in m.parameters:
            if ":" in p:
                types.append(p.split(":", 1)[1].strip())
            else:
                types.append(p.strip())
        return f"{m.name}({','.join(types)})"

    base_methods = {method_key(m): m for m in base_c.methods}
    pr_methods = {method_key(m): m for m in pr_c.methods}

    for key, m in pr_methods.items():
        if key not in base_methods:
            changes.append(DiffItem(
                entity_type="method",
                entity_name=key,
                change_type=ChangeType.ADDED,
                context=context_name
            ))
        else:
            base_m = base_methods[key]
            if base_m.visibility != m.visibility or base_m.return_type != m.return_type:
                b_sig = f"{base_m.visibility} {base_m.name}({','.join(base_m.parameters)}): {base_m.return_type}"
                a_sig = f"{m.visibility} {m.name}({','.join(m.parameters)}): {m.return_type}"
                changes.append(DiffItem(
                    entity_type="method",
                    entity_name=key,
                    change_type=ChangeType.MODIFIED,
                    context=context_name,
                    before=b_sig.strip(),
                    after=a_sig.strip()
                ))

    for key, m in base_methods.items():
        if key not in pr_methods:
            changes.append(DiffItem(
                entity_type="method",
                entity_name=key,
                change_type=ChangeType.REMOVED,
                context=context_name
            ))
