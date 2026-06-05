from typing import List, Tuple

from domain.diff_models import ChangeType, DiffItem, DiffResult
from domain.models import UMLClass, UMLModel, UMLRelation


def compute_diff(base: UMLModel, pr: UMLModel) -> DiffResult:
    changes: List[DiffItem] = []

    base_classes = {c.name: c for c in base.classes}
    pr_classes = {c.name: c for c in pr.classes}

    # 1. Compare Classes
    for name, c in pr_classes.items():
        if name not in base_classes:
            changes.append(DiffItem(
                entity_type="class",
                entity_name=name,
                change_type=ChangeType.ADDED
            ))
        else:
            base_c = base_classes[name]
            _compare_members(base_c, c, changes)

    for name, c in base_classes.items():
        if name not in pr_classes:
            changes.append(DiffItem(
                entity_type="class",
                entity_name=name,
                change_type=ChangeType.REMOVED
            ))

    # 2. Compare Relations
    def relation_key(r: UMLRelation) -> Tuple[str, str, str]:
        return (r.source, r.target, r.relation_type)

    base_rels = {relation_key(r): r for r in base.relations}
    pr_rels = {relation_key(r): r for r in pr.relations}

    for key, r in pr_rels.items():
        if key not in base_rels:
            changes.append(DiffItem(
                entity_type="relation",
                entity_name=f"{r.source} {r.relation_type} {r.target}",
                change_type=ChangeType.ADDED
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


def _compare_members(base_c: UMLClass, pr_c: UMLClass, changes: List[DiffItem]) -> None:
    # Compare attributes
    base_attrs = {a.name: a for a in base_c.attributes}
    pr_attrs = {a.name: a for a in pr_c.attributes}

    for name, a in pr_attrs.items():
        if name not in base_attrs:
            changes.append(DiffItem(
                entity_type="attribute",
                entity_name=name,
                change_type=ChangeType.ADDED,
                context=pr_c.name
            ))
        else:
            base_a = base_attrs[name]
            if base_a != a:
                changes.append(DiffItem(
                    entity_type="attribute",
                    entity_name=name,
                    change_type=ChangeType.MODIFIED,
                    context=pr_c.name,
                    before=f"{base_a.visibility} {base_a.name}: {base_a.type}".strip(),
                    after=f"{a.visibility} {a.name}: {a.type}".strip()
                ))

    for name, a in base_attrs.items():
        if name not in pr_attrs:
            changes.append(DiffItem(
                entity_type="attribute",
                entity_name=name,
                change_type=ChangeType.REMOVED,
                context=pr_c.name
            ))

    # Compare methods
    base_methods = {m.name: m for m in base_c.methods}
    pr_methods = {m.name: m for m in pr_c.methods}

    for name, m in pr_methods.items():
        if name not in base_methods:
            changes.append(DiffItem(
                entity_type="method",
                entity_name=name,
                change_type=ChangeType.ADDED,
                context=pr_c.name
            ))
        else:
            base_m = base_methods[name]
            if base_m != m:
                b_sig = f"{base_m.visibility} {base_m.name}({','.join(base_m.parameters)}): {base_m.return_type}"
                a_sig = f"{m.visibility} {m.name}({','.join(m.parameters)}): {m.return_type}"
                changes.append(DiffItem(
                    entity_type="method",
                    entity_name=name,
                    change_type=ChangeType.MODIFIED,
                    context=pr_c.name,
                    before=b_sig.strip(),
                    after=a_sig.strip()
                ))

    for name, m in base_methods.items():
        if name not in pr_methods:
            changes.append(DiffItem(
                entity_type="method",
                entity_name=name,
                change_type=ChangeType.REMOVED,
                context=pr_c.name
            ))
