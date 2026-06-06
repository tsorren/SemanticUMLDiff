import re
from typing import Dict, List, Optional

from domain.diff_models import ChangeType, DiffResult
from domain.models import UMLClass, UMLMethod, UMLModel, UMLRelation
from domain.render_models import RenderSpec
from render.themes import get_theme


def _get_relation_arrow(r: UMLRelation) -> str:
    arrow = "-->"
    if r.relation_type == "inheritance":
        arrow = "--|>"
    elif r.relation_type == "composition":
        arrow = "*--"
    elif r.relation_type == "aggregation":
        arrow = "o--"
    return arrow


def _clean_type(s: str) -> str:
    return re.sub(r'(?:[a-zA-Z_][a-zA-Z0-9_]*\.)+([a-zA-Z_][a-zA-Z0-9_]*)', r'\1', s)


def render_puml(
    base: UMLModel,
    pr: UMLModel,
    diff: DiffResult,
    spec: RenderSpec,
    layout_orthogonal_lines: bool = False,
    method_parameter_style: str = "types_only",
    group_by_package: bool = True,
    theme: str = "modern",
    diagram_spacing: int = 30
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

    lines.append(f"skinparam nodesep {diagram_spacing}")
    lines.append(f"skinparam ranksep {diagram_spacing}")
    lines.append("")

    # Inject Theme CSS
    theme_css = get_theme(theme)
    if theme_css:
        lines.append(theme_css)
        lines.append("")

    base_classes = {c.name: c for c in base.classes}
    pr_classes = {c.name: c for c in pr.classes}
    highlight_dict = dict(spec.highlight_rules)

    # Helper to determine if a class is an enum
    def is_enum(c: Optional[UMLClass]) -> bool:
        return bool(c and c.kind == "enum")

    # Group by package if needed
    packages: Dict[str, List[str]] = {}
    if group_by_package:
        for node in spec.included_nodes:
            parts = node.rsplit(".", 1)
            pkg = parts[0] if len(parts) > 1 else ""
            packages.setdefault(pkg, []).append(node)
    else:
        packages[""] = list(spec.included_nodes)

    # Detect package status
    package_status: Dict[str, str] = {}
    for pkg in packages.keys():
        if pkg:
            diff_item = next((d for d in diff.changes if d.entity_type == "package" and d.entity_name == pkg), None)
            if diff_item:
                if diff_item.change_type == ChangeType.ADDED:
                    package_status[pkg] = "package_added"
                elif diff_item.change_type == ChangeType.REMOVED:
                    package_status[pkg] = "package_removed"
                elif diff_item.change_type == ChangeType.MODIFIED:
                    package_status[pkg] = "package_modified"

    for pkg, nodes in packages.items():
        if pkg:
            stereo = f" <<{package_status[pkg]}>>" if pkg in package_status else ""
            lines.append(f'package "{pkg}"{stereo} {{')

        for class_name in nodes:
            status = highlight_dict.get(class_name)
            if status == "removed":
                c = base_classes.get(class_name)
            else:
                c = pr_classes.get(class_name)

            if not c:
                continue

            stereo_str = f" <<{status}>>" if status else ""

            # Short name for class block if grouping by package
            display_name = class_name.rsplit(".", 1)[-1] if pkg else class_name

            lines.append(f'{c.kind} "{display_name}" as {class_name}{stereo_str} {{')

            base_c = base_classes.get(class_name)
            pr_c = pr_classes.get(class_name)

            # Check if this class was moved
            if status == "moved":
                diff_item = next((d for d in diff.changes if d.entity_type == "class" and d.entity_name == class_name and d.context == "moved"), None)
                if diff_item and diff_item.before:
                    lines.append(f"  .. (moved from: {diff_item.before}) ..")

            members_lines = _render_members(
                base_c, pr_c, class_name, diff,
                is_removed=(status == "removed"),
                is_added=(status == "added"),
                method_parameter_style=method_parameter_style,
                is_enum=is_enum(c)
            )
            for mline in members_lines:
                lines.append(mline)
            lines.append("}")

        if pkg:
            lines.append("}")
            lines.append("")

    for r in spec.included_edges:
        arrow = _get_relation_arrow(r)
        rel_sig = f"{r.source} {r.relation_type} {r.target}"

        arrow_color = ""
        status = "neutral"
        for change in diff.changes:
            if change.entity_type == "relation" and change.entity_name == rel_sig:
                if change.change_type == ChangeType.ADDED:
                    arrow_color = "[#green]"
                elif change.change_type == ChangeType.REMOVED:
                    arrow_color = "[#red]"
                elif change.change_type == ChangeType.MODIFIED:
                    arrow_color = "[#orange]"
                break

        if arrow_color:
            if arrow.startswith("--"):
                arrow = f"-{arrow_color}-{arrow[2:]}"
            elif arrow.startswith("-"):
                arrow = f"-{arrow_color}{arrow[1:]}"
            elif arrow.startswith(".."):
                arrow = f".{arrow_color}.{arrow[2:]}"

        # Render relationship
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
    method_parameter_style: str,
    is_enum: bool
) -> List[str]:
    lines: List[str] = []
    member_diffs = [
        d for d in diff.changes
        if d.context == class_name and d.entity_type in ("attribute", "method")
    ]

    def _format_member(vis: str, text: str, color: str = "") -> str:
        if is_enum:
            vis = ""
            text = text.split(":")[0].strip()

        vis_part = f"{vis} " if vis else ""
        if color:
            return f"  {vis_part}<color:{color}>{text}</color>"
        return f"  {vis_part}{text}"

    # Attributes
    if pr_c:
        for a in pr_c.attributes:
            text = _clean_type(f"{a.name}: {a.type}".strip())
            diff_item = next(
                (d for d in member_diffs if d.entity_type == "attribute" and d.entity_name == a.name),
                None
            )

            if is_added:
                lines.append(_format_member(a.visibility, text, "green"))
            else:
                if not diff_item:
                    lines.append(_format_member(a.visibility, text))
                elif diff_item.change_type == ChangeType.ADDED:
                    lines.append(_format_member(a.visibility, text, "green"))
                elif diff_item.change_type == ChangeType.MODIFIED:
                    lines.append(_format_member(a.visibility, text, "orange"))

    if base_c:
        for a in base_c.attributes:
            diff_item = next(
                (d for d in member_diffs if d.entity_type == "attribute" and d.entity_name == a.name),
                None
            )
            text = _clean_type(f"{a.name}: {a.type}".strip())
            if is_removed:
                lines.append(_format_member(a.visibility, text, "red"))
            elif diff_item and diff_item.change_type == ChangeType.REMOVED:
                lines.append(_format_member(a.visibility, text, "red"))
            elif diff_item and diff_item.change_type == ChangeType.MODIFIED:
                pass

    # Methods
    def _format_params(params: tuple[str, ...]) -> str:
        formatted = []
        for p in params:
            if method_parameter_style != "names_and_types" and ":" in p:
                formatted.append(p.split(":", 1)[1].strip())
            else:
                formatted.append(p.strip())
        return ", ".join(formatted)

    def method_key(m: UMLMethod) -> str:
        return f"{m.name}({','.join(m.parameters)})"

    if pr_c:
        for m in pr_c.methods:
            text = _clean_type(f"{m.name}({_format_params(m.parameters)}): {m.return_type}".strip())
            diff_item = next(
                (d for d in member_diffs if d.entity_type == "method" and d.entity_name == method_key(m)),
                None
            )

            if is_added:
                lines.append(_format_member(m.visibility, text, "green"))
            else:
                if not diff_item:
                    lines.append(_format_member(m.visibility, text))
                elif diff_item.change_type == ChangeType.ADDED:
                    lines.append(_format_member(m.visibility, text, "green"))
                elif diff_item.change_type == ChangeType.MODIFIED:
                    lines.append(_format_member(m.visibility, text, "orange"))

    if base_c:
        for m in base_c.methods:
            diff_item = next(
                (d for d in member_diffs if d.entity_type == "method" and d.entity_name == method_key(m)),
                None
            )
            text = _clean_type(f"{m.name}({_format_params(m.parameters)}): {m.return_type}".strip())
            if is_removed:
                lines.append(_format_member(m.visibility, text, "red"))
            elif diff_item and diff_item.change_type == ChangeType.REMOVED:
                lines.append(_format_member(m.visibility, text, "red"))
            elif diff_item and diff_item.change_type == ChangeType.MODIFIED:
                pass

    return lines
