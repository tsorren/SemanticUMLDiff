from typing import List, Optional

from domain.diff_models import ChangeType, DiffResult
from domain.models import UMLClass, UMLModel, UMLRelation
from domain.render_models import RenderSpec

COLOR_ADDED = "#D4EDDA"
COLOR_REMOVED = "#F8D7DA"
COLOR_MODIFIED = "#FFF3CD"

ARROW_COLOR_ADDED = "[#green]"
ARROW_COLOR_REMOVED = "[#red]"


def render_puml(
    base: UMLModel,
    pr: UMLModel,
    diff: DiffResult,
    spec: RenderSpec,
    layout_orthogonal_lines: bool = False,
    method_parameter_style: str = "types_only",
    group_by_package: bool = True
) -> str:
    lines: List[str] = []
    lines.append("@startuml")
    lines.append("left to right direction")
    
    if layout_orthogonal_lines:
        lines.append("skinparam linetype ortho")
    else:
        lines.append("skinparam linetype poly")
        
    if not group_by_package:
        lines.append("set namespaceSeparator none")
    lines.append("skinparam nodesep 60")
    lines.append("skinparam ranksep 60")
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
            is_added=(color == "green"),
            method_parameter_style=method_parameter_style
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
    is_added: bool,
    method_parameter_style: str
) -> List[str]:
    lines: List[str] = []
    member_diffs = [
        d for d in diff.changes
        if d.context == class_name and d.entity_type in ("attribute", "method")
    ]

    import re
    def _clean_type(s: str) -> str:
        return re.sub(r'(?:[a-zA-Z_][a-zA-Z0-9_]*\.)+([a-zA-Z_][a-zA-Z0-9_]*)', r'\1', s)

    # Attributes
    if pr_c:
        for a in pr_c.attributes:
            sig = _clean_type(f"{a.visibility} {a.name}: {a.type}".strip())
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
                        lines.append(f"  <color:red>{_clean_type(diff_item.before)}</color>")
                    if diff_item.after:
                        lines.append(f"  <color:green>{_clean_type(diff_item.after)}</color>")

    if base_c:
        for a in base_c.attributes:
            diff_item = next(
                (d for d in member_diffs if d.entity_type == "attribute" and d.entity_name == a.name),
                None
            )
            sig = _clean_type(f"{a.visibility} {a.name}: {a.type}".strip())
            if is_removed:
                lines.append(f"  <color:red>{sig}</color>")
            elif diff_item and diff_item.change_type == ChangeType.REMOVED:
                lines.append(f"  <color:red>{sig}</color>")

    # Methods
    def _format_params(params: List[str]) -> str:
        formatted = []
        for p in params:
            if method_parameter_style == "types_only" and ":" in p:
                formatted.append(p.split(":", 1)[1].strip())
            else:
                formatted.append(p.strip())
        return ", ".join(formatted)

    if pr_c:
        for m in pr_c.methods:
            sig = _clean_type(f"{m.visibility} {m.name}({_format_params(m.parameters)}): {m.return_type}".strip())
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
                        lines.append(f"  <color:red>{_clean_type(diff_item.before)}</color>")
                    if diff_item.after:
                        lines.append(f"  <color:green>{_clean_type(diff_item.after)}</color>")

    if base_c:
        for m in base_c.methods:
            diff_item = next(
                (d for d in member_diffs if d.entity_type == "method" and d.entity_name == m.name),
                None
            )
            sig = _clean_type(f"{m.visibility} {m.name}({_format_params(m.parameters)}): {m.return_type}".strip())
            if is_removed:
                lines.append(f"  <color:red>{sig}</color>")
            elif diff_item and diff_item.change_type == ChangeType.REMOVED:
                lines.append(f"  <color:red>{sig}</color>")

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
