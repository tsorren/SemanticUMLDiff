from typing import List, Optional

from domain.diff_models import ChangeType, DiffResult
from domain.models import UMLClass, UMLModel, UMLRelation
from domain.render_models import RenderSpec

COLOR_ADDED = "#D4EDDA"
COLOR_REMOVED = "#F8D7DA"
COLOR_MODIFIED = "#FFF3CD"

ARROW_COLOR_ADDED = "[#green]"
ARROW_COLOR_REMOVED = "[#red]"


def render_puml(base: UMLModel, pr: UMLModel, diff: DiffResult, spec: RenderSpec) -> str:
    lines: List[str] = []
    lines.append("@startuml")
    lines.append("skinparam classBackgroundColor transparent")
    lines.append("skinparam classHeaderBackgroundColor transparent")
    lines.append("skinparam shadowing false")
    lines.append("skinparam defaultFontName Arial")
    lines.append("")

    base_classes = {c.name: c for c in base.classes}
    pr_classes = {c.name: c for c in pr.classes}
    highlight_dict = dict(spec.highlight_rules)

    for class_name in spec.included_nodes:
        color = highlight_dict.get(class_name)
        if color == "red":
            c = base_classes.get(class_name)
            bg_color = COLOR_REMOVED
        else:
            c = pr_classes.get(class_name)
            bg_color = (
                COLOR_ADDED if color == "green"
                else (COLOR_MODIFIED if color == "yellow" else "")
            )

        if not c:
            continue

        color_str = f" {bg_color}" if bg_color else ""
        lines.append(f"{c.kind} {c.name}{color_str} {{")

        base_c = base_classes.get(class_name)
        pr_c = pr_classes.get(class_name)
        members_lines = _render_members(
            base_c, pr_c, class_name, diff,
            is_removed=(color == "red"),
            is_added=(color == "green")
        )
        lines.extend(members_lines)
        lines.append("}")
        lines.append("")

    for r in spec.included_edges:
        arrow = _get_relation_arrow(r)
        rel_sig = f"{r.source} {r.relation_type} {r.target}"

        arrow_color = ""
        for change in diff.changes:
            if change.entity_type == "relation" and change.entity_name == rel_sig:
                if change.change_type == ChangeType.ADDED:
                    arrow_color = ARROW_COLOR_ADDED
                elif change.change_type == ChangeType.REMOVED:
                    arrow_color = ARROW_COLOR_REMOVED
                break

        if arrow_color:
            if arrow.startswith("--"):
                arrow = f"-{arrow_color}-{arrow[2:]}"
            elif arrow.startswith("-"):
                arrow = f"-{arrow_color}{arrow[1:]}"
            elif arrow.startswith(".."):
                arrow = f".{arrow_color}.{arrow[2:]}"

        lines.append(f"{r.source} {arrow} {r.target}")

    lines.append("@enduml")
    return "\n".join(lines)


def _render_members(
    base_c: Optional[UMLClass],
    pr_c: Optional[UMLClass],
    class_name: str,
    diff: DiffResult,
    is_removed: bool,
    is_added: bool
) -> List[str]:
    lines: List[str] = []
    member_diffs = [
        d for d in diff.changes
        if d.context == class_name and d.entity_type in ("attribute", "method")
    ]

    # Attributes
    if pr_c:
        for a in pr_c.attributes:
            sig = f"{a.visibility} {a.name}: {a.type}".strip()
            diff_item = next(
                (d for d in member_diffs if d.entity_type == "attribute" and d.entity_name == a.name),
                None
            )

            if is_added:
                lines.append(f"  <color:green>{sig}</color>")
            else:
                if not diff_item:
                    lines.append(f"  {sig}")
                elif diff_item.change_type == ChangeType.ADDED:
                    lines.append(f"  <color:green>{sig}</color>")
                elif diff_item.change_type == ChangeType.MODIFIED:
                    if diff_item.before:
                        lines.append(f"  <color:red><s:red>{diff_item.before}</s></color>")
                    if diff_item.after:
                        lines.append(f"  <color:green>{diff_item.after}</color>")

    if base_c:
        for a in base_c.attributes:
            diff_item = next(
                (d for d in member_diffs if d.entity_type == "attribute" and d.entity_name == a.name),
                None
            )
            sig = f"{a.visibility} {a.name}: {a.type}".strip()
            if is_removed:
                lines.append(f"  <color:red><s:red>{sig}</s></color>")
            elif diff_item and diff_item.change_type == ChangeType.REMOVED:
                lines.append(f"  <color:red><s:red>{sig}</s></color>")

    # Methods
    if pr_c:
        for m in pr_c.methods:
            sig = f"{m.visibility} {m.name}({','.join(m.parameters)}): {m.return_type}".strip()
            diff_item = next(
                (d for d in member_diffs if d.entity_type == "method" and d.entity_name == m.name),
                None
            )

            if is_added:
                lines.append(f"  <color:green>{sig}</color>")
            else:
                if not diff_item:
                    lines.append(f"  {sig}")
                elif diff_item.change_type == ChangeType.ADDED:
                    lines.append(f"  <color:green>{sig}</color>")
                elif diff_item.change_type == ChangeType.MODIFIED:
                    if diff_item.before:
                        lines.append(f"  <color:red><s:red>{diff_item.before}</s></color>")
                    if diff_item.after:
                        lines.append(f"  <color:green>{diff_item.after}</color>")

    if base_c:
        for m in base_c.methods:
            diff_item = next(
                (d for d in member_diffs if d.entity_type == "method" and d.entity_name == m.name),
                None
            )
            sig = f"{m.visibility} {m.name}({','.join(m.parameters)}): {m.return_type}".strip()
            if is_removed:
                lines.append(f"  <color:red><s:red>{sig}</s></color>")
            elif diff_item and diff_item.change_type == ChangeType.REMOVED:
                lines.append(f"  <color:red><s:red>{sig}</s></color>")

    return lines


def _get_relation_arrow(r: UMLRelation) -> str:
    mapping = {
        "association": "-->",
        "composition": "*--",
        "aggregation": "o--",
        "inheritance": "--|>",
        "realization": "..|>",
        "dependency": "..>"
    }
    return mapping.get(r.relation_type, "-->")
