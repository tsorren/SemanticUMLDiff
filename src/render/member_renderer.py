from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from domain.diff_models import DiffResult
    from domain.models import UMLAttribute, UMLClass, UMLMethod

from domain.diff_models import ChangeType
from domain.models import UMLAttribute, UMLMethod


class MemberFormatter:
    """
    Handles the granular rendering and coloring of UML class members (attributes and methods)
    for semantic diff visualization. Applies SOLID principles by separating this complex
    logic from the main graph structure rendering.
    """

    @staticmethod
    def _format_params(params: tuple[str, ...], method_parameter_style: str) -> list[str]:
        if method_parameter_style == "names_and_types":
            return list(params)
        # Default: types_only
        types = []
        for p in params:
            if ":" in p:
                types.append(p.split(":", 1)[1].strip())
            else:
                parts = p.strip().split()
                if len(parts) > 1:
                    types.append(" ".join(parts[:-1]))
                else:
                    types.append(p.strip())
        return types

    @staticmethod
    def format_attribute(attr: UMLAttribute, is_removed: bool = False, is_added: bool = False) -> str:
        text = f"{attr.visibility} {attr.name}: {attr.type}".strip()
        if is_removed:
            return f"<color:red><strike>{text}</strike></color>"
        if is_added:
            return f"<color:green>{text}</color>"
        return text

    @staticmethod
    def format_modified_attribute(base_attr: UMLAttribute, pr_attr: UMLAttribute) -> Optional[str]:
        """
        Returns the granularly highlighted string for a modified attribute.
        If there are no visual changes, returns the normal text.
        """
        vis = pr_attr.visibility if pr_attr.visibility == base_attr.visibility else f"<color:orange>{pr_attr.visibility}</color>"
        name = pr_attr.name if pr_attr.name == base_attr.name else f"<color:orange>{pr_attr.name}</color>"
        typ = pr_attr.type if pr_attr.type == base_attr.type else f"<color:orange>{pr_attr.type}</color>"

        return f"{vis} {name}: {typ}".strip()

    @staticmethod
    def format_method(method: UMLMethod, method_parameter_style: str, is_removed: bool = False, is_added: bool = False) -> str:
        params = MemberFormatter._format_params(method.parameters, method_parameter_style)
        text = f"{method.visibility} {method.name}({', '.join(params)}): {method.return_type}".strip()
        if is_removed:
            return f"<color:red><strike>{text}</strike></color>"
        if is_added:
            return f"<color:green>{text}</color>"
        return text

    @staticmethod
    def format_modified_method(base_m: UMLMethod, pr_m: UMLMethod, method_parameter_style: str) -> Optional[str]:
        """
        Returns the granularly highlighted string for a modified method.
        Highlights only the specific parts (visibility, name, specific parameters, return type) that changed.
        If method_parameter_style is types_only, parameter name changes won't trigger an orange highlight.
        """
        vis = pr_m.visibility if pr_m.visibility == base_m.visibility else f"<color:orange>{pr_m.visibility}</color>"
        name = pr_m.name if pr_m.name == base_m.name else f"<color:orange>{pr_m.name}</color>"
        ret = pr_m.return_type if pr_m.return_type == base_m.return_type else f"<color:orange>{pr_m.return_type}</color>"

        # Handle parameters
        base_params_full = base_m.parameters
        pr_params_full = pr_m.parameters

        base_params_display = MemberFormatter._format_params(base_params_full, method_parameter_style)
        pr_params_display = MemberFormatter._format_params(pr_params_full, method_parameter_style)

        formatted_params = []
        # If the number of parameters changed, it's safer to just highlight all changed/new ones
        max_len = max(len(base_params_display), len(pr_params_display))
        for i in range(max_len):
            if i >= len(base_params_display):
                # Added parameter
                formatted_params.append(f"<color:orange>{pr_params_display[i]}</color>")
            elif i >= len(pr_params_display):
                # Removed parameter - we don't show removed parameters in the PR method signature,
                # but their removal makes the method MODIFIED (which is handled by other changes or we just skip)
                pass
            else:
                # Compare parameter
                if base_params_display[i] != pr_params_display[i]:
                    formatted_params.append(f"<color:orange>{pr_params_display[i]}</color>")
                else:
                    formatted_params.append(pr_params_display[i])

        params_str = ", ".join(formatted_params)
        text = f"{vis} {name}({params_str}): {ret}".strip()

        # If after styling there are no color tags, and we know it was modified
        # (e.g. only parameter names changed but style is types_only), we return standard format.
        return text

    @staticmethod
    def render_class_members(
        base_c: Optional['UMLClass'],
        pr_c: Optional['UMLClass'],
        diff: 'DiffResult',
        is_removed: bool,
        is_added: bool,
        method_parameter_style: str,
        is_enum: bool
    ) -> list[str]:
        lines: list[str] = []

        member_diffs = {}
        for item in diff.changes:
            if item.entity_type in ("attribute", "method"):
                member_diffs[item.entity_name] = item

        # Attributes
        if pr_c:
            for a in pr_c.attributes:
                diff_item = member_diffs.get(a.name)
                if is_added:
                    lines.append(MemberFormatter.format_attribute(a, is_added=True))
                elif not diff_item:
                    lines.append(MemberFormatter.format_attribute(a))
                elif diff_item.change_type == ChangeType.ADDED:
                    lines.append(MemberFormatter.format_attribute(a, is_added=True))
                elif diff_item.change_type == ChangeType.MODIFIED:
                    if diff_item.before_element and diff_item.after_element:
                        fmt = MemberFormatter.format_modified_attribute(diff_item.before_element, diff_item.after_element)
                        if fmt:
                            lines.append(fmt)
                    else:
                        lines.append(MemberFormatter.format_attribute(a))
        if base_c:
            for a in base_c.attributes:
                diff_item = member_diffs.get(a.name)
                if is_removed:
                    lines.append(MemberFormatter.format_attribute(a, is_removed=True))
                elif diff_item and diff_item.change_type == ChangeType.REMOVED:
                    lines.append(MemberFormatter.format_attribute(a, is_removed=True))

        # Enum spacing
        if is_enum and lines:
            lines.append("==")

        # Methods
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

        renamed_old_keys = set()
        for item in member_diffs.values():
            if item.entity_type == "method" and item.change_type == ChangeType.MODIFIED and item.before_element and item.after_element:
                if item.before_element.name != item.after_element.name:
                    renamed_old_keys.add(method_key(item.before_element))

        if pr_c:
            for m in pr_c.methods:
                key = method_key(m)
                diff_item = member_diffs.get(key)

                if is_added:
                    lines.append(MemberFormatter.format_method(m, method_parameter_style, is_added=True))
                elif not diff_item:
                    lines.append(MemberFormatter.format_method(m, method_parameter_style))
                elif diff_item.change_type == ChangeType.ADDED:
                    lines.append(MemberFormatter.format_method(m, method_parameter_style, is_added=True))
                elif diff_item.change_type == ChangeType.MODIFIED:
                    if diff_item.before_element and diff_item.after_element:
                        fmt = MemberFormatter.format_modified_method(diff_item.before_element, diff_item.after_element, method_parameter_style)
                        if fmt:
                            lines.append(fmt)
                    else:
                        lines.append(MemberFormatter.format_method(m, method_parameter_style))

        if base_c:
            for m in base_c.methods:
                key = method_key(m)

                if key in renamed_old_keys:
                    continue  # Handled as MODIFIED in pr_c

                diff_item = member_diffs.get(key)

                if is_removed:
                    lines.append(MemberFormatter.format_method(m, method_parameter_style, is_removed=True))
                elif diff_item and diff_item.change_type == ChangeType.REMOVED:
                    lines.append(MemberFormatter.format_method(m, method_parameter_style, is_removed=True))

        return lines
