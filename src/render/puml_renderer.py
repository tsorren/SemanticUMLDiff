import re
from typing import Dict, List, Optional

from domain.diff_models import ChangeType, DiffResult
from domain.models import UMLClass, UMLModel, UMLRelation
from domain.render_models import RenderSpec
from render.member_renderer import MemberFormatter
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
    lines.append("skinparam packagePadding 8")
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

    # Filter nodes within each package to only those that actually exist in the model
    # (either in base_classes if status is removed, or in pr_classes otherwise)
    filtered_packages: Dict[str, List[str]] = {}
    for pkg, nodes in packages.items():
        valid_nodes = []
        for class_name in nodes:
            status = highlight_dict.get(class_name)
            if status == "removed":
                c = base_classes.get(class_name)
            else:
                c = pr_classes.get(class_name)
            if c:
                valid_nodes.append(class_name)
        if valid_nodes:
            filtered_packages[pkg] = valid_nodes

    # Detect package status
    package_status: Dict[str, str] = {}
    for pkg in filtered_packages.keys():
        if pkg:
            diff_item = next((d for d in diff.changes if d.entity_type == "package" and d.entity_name == pkg), None)
            if diff_item:
                if diff_item.change_type == ChangeType.ADDED:
                    package_status[pkg] = "package_added"
                elif diff_item.change_type == ChangeType.REMOVED:
                    package_status[pkg] = "package_removed"
                elif diff_item.change_type == ChangeType.MODIFIED:
                    package_status[pkg] = "package_modified"

    for pkg, nodes in filtered_packages.items():
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
    is_removed: bool = False,
    is_added: bool = False,
    method_parameter_style: str = "types_only",
    is_enum: bool = False
) -> List[str]:
    # Use the separated MemberFormatter class to respect SOLID principles
    lines = MemberFormatter.render_class_members(
        base_c=base_c,
        pr_c=pr_c,
        diff=diff,
        is_removed=is_removed,
        is_added=is_added,
        method_parameter_style=method_parameter_style,
        is_enum=is_enum
    )

    # Prepend indentation as expected by puml_renderer
    return [f"  {line}" for line in lines]
