import re
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from domain.diff_models import DiffResult
    from domain.models import UMLAttribute, UMLClass, UMLMethod

from domain.diff_models import ChangeType
from domain.models import UMLAttribute, UMLMethod


def _clean_type(s: str) -> str:
    if not s:
        return ""
    return re.sub(r'(?:[a-zA-Z_][a-zA-Z0-9_]*\.)+([a-zA-Z_][a-zA-Z0-9_]*)', r'\1', s)


def _get_type(p: str) -> str:
    p = p.strip()
    if ":" in p:
        return p.split(":", 1)[1].strip()
    parts = p.split()
    if len(parts) > 1:
        last_part = parts[-1]
        if any(c in last_part for c in "<>,*&|"):
            return p
        else:
            return " ".join(parts[:-1])
    return p


class MemberFormatter:
    """
    Handles the granular rendering and coloring of UML class members (attributes and methods)
    for semantic diff visualization. Applies SOLID principles by separating this complex
    logic from the main graph structure rendering.
    """

    @staticmethod
    def _format_params(params: tuple[str, ...], method_parameter_style: str) -> list[str]:
        if method_parameter_style == "names_and_types":
            return [_clean_type(p) for p in params]
        # Default: types_only
        types = [_get_type(p) for p in params]
        return [_clean_type(t) for t in types]

    @staticmethod
    def format_attribute(attr: UMLAttribute, is_removed: bool = False, is_added: bool = False, is_enum: bool = False) -> str:
        if is_enum:
            text = attr.name.strip()
            vis_part = ""
        else:
            cleaned_type = _clean_type(attr.type)
            text = f"{attr.name}: {cleaned_type}".strip()
            vis_part = f"{attr.visibility} " if attr.visibility else ""

        if is_removed:
            return f"{vis_part}<color:red>{text}</color>"
        if is_added:
            return f"{vis_part}<color:green>{text}</color>"
        return f"{vis_part}{text}"

    @staticmethod
    def format_modified_attribute(base_attr: UMLAttribute, pr_attr: UMLAttribute, is_enum: bool = False) -> Optional[str]:
        """
        Returns the granularly highlighted string for a modified attribute.
        If there are no visual changes, returns the normal text.
        """
        if is_enum:
            has_change = base_attr.name != pr_attr.name
            text = pr_attr.name
            if has_change:
                return f"<color:orange>{text}</color>".strip()
            return text.strip()

        has_change = (
            base_attr.visibility != pr_attr.visibility or
            base_attr.name != pr_attr.name or
            base_attr.type != pr_attr.type
        )

        vis_part = f"{pr_attr.visibility} " if pr_attr.visibility else ""
        cleaned_type = _clean_type(pr_attr.type)
        text = f"{pr_attr.name}: {cleaned_type}"

        if has_change:
            return f"{vis_part}<color:orange>{text}</color>".strip()
        return f"{vis_part}{text}".strip()

    @staticmethod
    def format_method(method: UMLMethod, method_parameter_style: str, is_removed: bool = False, is_added: bool = False) -> str:
        params = MemberFormatter._format_params(method.parameters, method_parameter_style)
        cleaned_ret = _clean_type(method.return_type)
        text = f"{method.name}({', '.join(params)}): {cleaned_ret}".strip()
        vis_part = f"{method.visibility} " if method.visibility else ""
        if is_removed:
            return f"{vis_part}<color:red>{text}</color>"
        if is_added:
            return f"{vis_part}<color:green>{text}</color>"
        return f"{vis_part}{text}"

    @staticmethod
    def format_modified_method(base_m: UMLMethod, pr_m: UMLMethod, method_parameter_style: str) -> Optional[str]:
        """
        Returns the granularly highlighted string for a modified method.
        Highlights the entire signature after visibility in orange if it changed under the active style.
        If method_parameter_style is types_only, parameter name changes won't trigger an orange highlight.
        """
        base_params = MemberFormatter._format_params(base_m.parameters, method_parameter_style)
        pr_params = MemberFormatter._format_params(pr_m.parameters, method_parameter_style)

        has_change = (
            base_m.visibility != pr_m.visibility or
            base_m.name != pr_m.name or
            base_m.return_type != pr_m.return_type or
            base_params != pr_params
        )

        vis_part = f"{pr_m.visibility} " if pr_m.visibility else ""
        cleaned_name = pr_m.name
        cleaned_ret = _clean_type(pr_m.return_type)
        params_str = ", ".join(pr_params)

        text = f"{cleaned_name}({params_str}): {cleaned_ret}"

        if has_change:
            return f"{vis_part}<color:orange>{text}</color>".strip()
        return f"{vis_part}{text}".strip()


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
                # Scope by class context to avoid name collisions across classes
                member_diffs[(item.context, item.entity_name)] = item

        # Attributes
        if pr_c:
            for a in pr_c.attributes:
                diff_item = member_diffs.get((pr_c.name, a.name))
                if is_added:
                    lines.append(MemberFormatter.format_attribute(a, is_added=True, is_enum=is_enum))
                elif not diff_item:
                    lines.append(MemberFormatter.format_attribute(a, is_enum=is_enum))
                elif diff_item.change_type == ChangeType.ADDED:
                    lines.append(MemberFormatter.format_attribute(a, is_added=True, is_enum=is_enum))
                elif diff_item.change_type == ChangeType.MODIFIED:
                    if diff_item.before_element and diff_item.after_element:
                        fmt = MemberFormatter.format_modified_attribute(diff_item.before_element, diff_item.after_element, is_enum=is_enum)
                        if fmt:
                            lines.append(fmt)
                    else:
                        lines.append(MemberFormatter.format_attribute(a, is_enum=is_enum))
        if base_c:
            for a in base_c.attributes:
                diff_item = member_diffs.get((base_c.name, a.name))
                if is_removed:
                    lines.append(MemberFormatter.format_attribute(a, is_removed=True, is_enum=is_enum))
                elif diff_item and diff_item.change_type == ChangeType.REMOVED:
                    lines.append(MemberFormatter.format_attribute(a, is_removed=True, is_enum=is_enum))

        # Enum spacing
        if is_enum and lines:
            lines.append("==")

        # Methods
        def method_key(m: UMLMethod) -> str:
            types = [_get_type(p) for p in m.parameters]
            return f"{m.name}({','.join(types)})"

        renamed_old_keys = set()
        for item in member_diffs.values():
            if item.entity_type == "method" and item.change_type == ChangeType.MODIFIED and item.before_element and item.after_element:
                if item.before_element.name != item.after_element.name:
                    renamed_old_keys.add((item.context, method_key(item.before_element)))

        if pr_c:
            for m in pr_c.methods:
                key = method_key(m)
                diff_item = member_diffs.get((pr_c.name, key))

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

                if (base_c.name, key) in renamed_old_keys:
                    continue  # Handled as MODIFIED in pr_c

                diff_item = member_diffs.get((base_c.name, key))

                if is_removed:
                    lines.append(MemberFormatter.format_method(m, method_parameter_style, is_removed=True))
                elif diff_item and diff_item.change_type == ChangeType.REMOVED:
                    lines.append(MemberFormatter.format_method(m, method_parameter_style, is_removed=True))

        return lines
