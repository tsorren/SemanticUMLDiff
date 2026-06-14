import hashlib
from typing import Any, List, Tuple

import lark
from lark import Token, Transformer, Tree

from domain.models import UMLAttribute, UMLClass, UMLMethod, UMLModel, UMLRelation
from parser.lark_grammar import PLANTUML_GRAMMAR
from parser.preprocessor import preprocess


class UMLType(str):
    """Subclase de str para diferenciar tipos de nombres en el CST/AST."""
    pass

class PlantUMLTransformer(Transformer[Any, Any]):
    """Traduce el Parse Tree de Lark a objetos inmutables del dominio."""

    def start(self, items: List[Any]) -> Any:
        return items[0]

    def document(self, items: List[Any]) -> Tuple[List[UMLClass], List[UMLRelation]]:
        classes: List[UMLClass] = []
        relations: List[UMLRelation] = []

        for item in items:
            if isinstance(item, UMLClass):
                classes.append(item)
            elif isinstance(item, UMLRelation):
                relations.append(item)
            elif isinstance(item, list):  # Sub-elements from package or block
                for sub in item:
                    if isinstance(sub, UMLClass):
                        classes.append(sub)
                    elif isinstance(sub, UMLRelation):
                        relations.append(sub)
        return classes, relations

    def package_decl(self, items: List[Any]) -> List[Any]:
        pkg_name = str(items[0]).strip('"')
        children: List[Any] = []
        for item in items[1:]:
            if isinstance(item, UMLClass):
                fqn = f"{pkg_name}.{item.name}" if "." not in item.name else item.name
                children.append(UMLClass(
                    name=fqn, kind=item.kind,
                    attributes=item.attributes, methods=item.methods,
                    visibility=item.visibility, modifiers=item.modifiers
                ))
            elif isinstance(item, UMLRelation):
                children.append(item)
            elif isinstance(item, list):
                children.extend(item)
        return children

    def class_kind(self, items: List[Any]) -> Tree[Any]:
        return Tree("class_kind", items)

    def interface_kind(self, items: List[Any]) -> Tree[Any]:
        return Tree("interface_kind", items)

    def element_simple(self, items: List[Any]) -> UMLClass:
        kind_node = items[0]
        name_token = items[1]

        kind_str = "class"
        is_abstract = False
        if isinstance(kind_node, Tree) and kind_node.data == "class_kind":
            # If ABSTRACT token is present (len == 2, or child is ABSTRACT token)
            if len(kind_node.children) == 2 or (len(kind_node.children) > 0 and getattr(kind_node.children[0], "type", None) == "ABSTRACT"):
                kind_str = "abstract class"
                is_abstract = True
            else:
                kind_str = "class"
        elif isinstance(kind_node, Tree) and kind_node.data == "interface_kind":
            kind_str = "interface"

        attrs = []
        methods = []
        for item in items[2:]:
            if isinstance(item, UMLAttribute):
                attrs.append(item)
            elif isinstance(item, UMLMethod):
                methods.append(item)
            elif isinstance(item, list):
                for sub in item:
                    if isinstance(sub, UMLAttribute):
                        attrs.append(sub)
                    elif isinstance(sub, UMLMethod):
                        methods.append(sub)

        modifiers = ("abstract",) if is_abstract else ()
        return UMLClass(
            name=str(name_token),
            kind=kind_str,
            attributes=tuple(attrs),
            methods=tuple(methods),
            modifiers=modifiers
        )

    def element_fqn(self, items: List[Any]) -> UMLClass:
        kind_node = items[0]
        quoted_name = str(items[1]).strip('"')

        # Check alias
        alias = None
        current_idx = 2
        if current_idx < len(items) and isinstance(items[current_idx], Token) and items[current_idx].type == "IDENTIFIER":
            alias = str(items[current_idx])
            current_idx += 1

        kind_str = "class"
        is_abstract = False
        if isinstance(kind_node, Tree) and kind_node.data == "class_kind":
            if len(kind_node.children) == 2 or (len(kind_node.children) > 0 and getattr(kind_node.children[0], "type", None) == "ABSTRACT"):
                kind_str = "abstract class"
                is_abstract = True
            else:
                kind_str = "class"
        elif isinstance(kind_node, Tree) and kind_node.data == "interface_kind":
            kind_str = "interface"

        attrs = []
        methods = []
        for item in items[current_idx:]:
            if isinstance(item, UMLAttribute):
                attrs.append(item)
            elif isinstance(item, UMLMethod):
                methods.append(item)
            elif isinstance(item, list):
                for sub in item:
                    if isinstance(sub, UMLAttribute):
                        attrs.append(sub)
                    elif isinstance(sub, UMLMethod):
                        methods.append(sub)

        modifiers = ("abstract",) if is_abstract else ()
        return UMLClass(
            name=alias if alias else quoted_name,
            kind=kind_str,
            attributes=tuple(attrs),
            methods=tuple(methods),
            modifiers=modifiers
        )

    def enum_simple(self, items: List[Any]) -> UMLClass:
        name_token = items[1] # items[0] is ENUM token

        attrs = []
        methods = []
        for item in items[2:]:
            if isinstance(item, UMLAttribute):
                attrs.append(item)
            elif isinstance(item, UMLMethod):
                methods.append(item)
            elif isinstance(item, list):
                for sub in item:
                    if isinstance(sub, UMLAttribute):
                        attrs.append(sub)
                    elif isinstance(sub, UMLMethod):
                        methods.append(sub)

        return UMLClass(
            name=str(name_token),
            kind="enum",
            attributes=tuple(attrs),
            methods=tuple(methods)
        )

    def enum_fqn(self, items: List[Any]) -> UMLClass:
        quoted_name = str(items[1]).strip('"')

        alias = None
        current_idx = 2
        if current_idx < len(items) and isinstance(items[current_idx], Token) and items[current_idx].type == "IDENTIFIER":
            alias = str(items[current_idx])
            current_idx += 1

        attrs = []
        methods = []
        for item in items[current_idx:]:
            if isinstance(item, UMLAttribute):
                attrs.append(item)
            elif isinstance(item, UMLMethod):
                methods.append(item)
            elif isinstance(item, list):
                for sub in item:
                    if isinstance(sub, UMLAttribute):
                        attrs.append(sub)
                    elif isinstance(sub, UMLMethod):
                        methods.append(sub)

        return UMLClass(
            name=alias if alias else quoted_name,
            kind="enum",
            attributes=tuple(attrs),
            methods=tuple(methods)
        )

    def vis_public(self, items: List[Any]) -> str: return "+"
    def vis_private(self, items: List[Any]) -> str: return "-"
    def vis_protected(self, items: List[Any]) -> str: return "#"
    def vis_package(self, items: List[Any]) -> str: return "~"

    def mod_static(self, items: List[Any]) -> str: return "static"
    def mod_abstract(self, items: List[Any]) -> str: return "abstract"
    def mod_method(self, items: List[Any]) -> str: return "method"
    def mod_field(self, items: List[Any]) -> str: return "field"

    def member_modifier(self, items: List[Any]) -> Any:
        return items[0]

    def name(self, items: List[Any]) -> str:
        return str(items[0])

    def value(self, items: List[Any]) -> str:
        return str(items[0])

    def enum_value(self, items: List[Any]) -> UMLAttribute:
        name_str = str(items[-1])
        visibility = ""
        for item in items[:-1]:
            if item in ("+", "-", "#", "~"):
                visibility = item
        return UMLAttribute(name=name_str, type="", visibility=visibility)

    def member(self, items: List[Any]) -> Any:
        return items[0] if items else None

    def enum_member(self, items: List[Any]) -> Any:
        return items[0] if items else None

    def method_decl(self, items: List[Any]) -> UMLMethod:
        visibility = ""
        modifiers = []

        current_idx = 0
        while current_idx < len(items):
            item = items[current_idx]
            if isinstance(item, str) and item in ("+", "-", "#", "~"):
                visibility = item
                current_idx += 1
            elif isinstance(item, str) and item in ("static", "abstract", "method", "field"):
                if item in ("static", "abstract"):
                    modifiers.append(item)
                current_idx += 1
            else:
                break

        remaining = items[current_idx:]

        ret_type = ""
        name_str = ""
        params = []

        params_node = None
        for item in remaining:
            if isinstance(item, Tree) and item.data == "parameters":
                params_node = item
                break

        if params_node is not None:
            params_idx = remaining.index(params_node)
            before_params = remaining[:params_idx]
            after_params = remaining[params_idx+1:]

            for param_tree in params_node.children:
                if param_tree.data == "param_colon":
                    p_name = str(param_tree.children[0].children[0]) if isinstance(param_tree.children[0], Tree) else str(param_tree.children[0])
                    p_type = str(param_tree.children[1])
                    params.append(f"{p_name}: {p_type}")
                elif param_tree.data == "param_type_first":
                    p_type = str(param_tree.children[0])
                    p_name = str(param_tree.children[1].children[0]) if isinstance(param_tree.children[1], Tree) else str(param_tree.children[1])
                    params.append(f"{p_type} {p_name}")
                elif param_tree.data == "param_type_only":
                    params.append(str(param_tree.children[0]))
        else:
            before_params = remaining
            after_params = []
            # Now we parse before_params and after_params:
        # type is UMLType, name is str (but NOT UMLType)
        for item in before_params:
            if isinstance(item, UMLType):
                ret_type = item
            elif isinstance(item, str):
                name_str = item

        # Suffix type is in after_params
        for item in after_params:
            if isinstance(item, UMLType):
                ret_type = item

        return UMLMethod(
            name=name_str,
            parameters=tuple(params),
            return_type=str(ret_type),
            visibility=visibility,
            modifiers=tuple(modifiers)
        )

    def attribute_colon(self, items: List[Any]) -> UMLAttribute:
        visibility = ""
        modifiers = []

        current_idx = 0
        while current_idx < len(items):
            item = items[current_idx]
            if isinstance(item, str) and item in ("+", "-", "#", "~"):
                visibility = item
                current_idx += 1
            elif isinstance(item, str) and item in ("static", "abstract", "method", "field"):
                if item in ("static", "abstract"):
                    modifiers.append(item)
                current_idx += 1
            else:
                break

        name_str = str(items[current_idx])
        current_idx += 1

        attr_type = str(items[current_idx])
        current_idx += 1

        default_val = ""
        if current_idx < len(items) and items[current_idx] is not None:
            default_val = str(items[current_idx]).strip('"').strip()

        return UMLAttribute(
            name=name_str,
            type=attr_type,
            visibility=visibility,
            default_value=default_val,
            modifiers=tuple(modifiers)
        )

    def attribute_type_first(self, items: List[Any]) -> UMLAttribute:
        visibility = ""
        modifiers = []

        current_idx = 0
        while current_idx < len(items):
            item = items[current_idx]
            if isinstance(item, str) and item in ("+", "-", "#", "~"):
                visibility = item
                current_idx += 1
            elif isinstance(item, str) and item in ("static", "abstract", "method", "field"):
                if item in ("static", "abstract"):
                    modifiers.append(item)
                current_idx += 1
            else:
                break

        attr_type = str(items[current_idx])
        current_idx += 1

        name_str = str(items[current_idx])
        current_idx += 1

        default_val = ""
        if current_idx < len(items) and items[current_idx] is not None:
            default_val = str(items[current_idx]).strip('"').strip()

        return UMLAttribute(
            name=name_str,
            type=attr_type,
            visibility=visibility,
            default_value=default_val,
            modifiers=tuple(modifiers)
        )

    def generic_type(self, items: List[Any]) -> UMLType:
        base = str(items[0].children[0]) if isinstance(items[0], Tree) else str(items[0])
        if len(items) > 1:
            args = ", ".join(str(a) for a in items[1:])
            return UMLType(f"{base}<{args}>")
        return UMLType(base)

    def relationship_decl(self, items: List[Any]) -> UMLRelation:
        source = str(items[0])

        src_mult = ""
        current_idx = 1
        if isinstance(items[current_idx], Token) and items[current_idx].type == "ESCAPED_STRING":
            src_mult = str(items[current_idx]).strip('"')
            current_idx += 1

        arrow = str(items[current_idx])
        current_idx += 1

        tgt_mult = ""
        if isinstance(items[current_idx], Token) and items[current_idx].type == "ESCAPED_STRING":
            tgt_mult = str(items[current_idx]).strip('"')
            current_idx += 1

        target = str(items[current_idx])
        current_idx += 1

        label = ""
        if current_idx < len(items) and items[current_idx] is not None:
            label = str(items[current_idx]).strip()

        # Determine relation type from arrow
        rel_type = "association"
        if "<|--" in arrow or "--|>" in arrow or "<|.." in arrow or "..|>" in arrow:
            rel_type = "inheritance"
        elif "*--" in arrow or "--*" in arrow:
            rel_type = "composition"
        elif "o--" in arrow or "--o" in arrow:
            rel_type = "aggregation"

        return UMLRelation(
            source=source,
            target=target,
            relation_type=rel_type,
            multiplicity_source=src_mult,
            multiplicity_target=tgt_mult,
            label=label
        )



class LarkPlantUMLParser:
    """Parser PlantUML basado en Lark LALR(1)."""

    def __init__(self, module_name: str, source_hash: str = "") -> None:
        self.module_name = module_name
        self.source_hash = source_hash
        self._parser = lark.Lark(
            PLANTUML_GRAMMAR,
            start="start",
            parser="lalr",
            maybe_placeholders=False,
        )

    def parse_tree(self, raw_text: str) -> lark.Tree[Any]:
        """Genera el Parse Tree (CST) sin transformar a modelos de dominio."""
        clean_lines = preprocess(raw_text)
        clean_text = "@startuml\n" + "\n".join(clean_lines) + "\n@enduml"
        return self._parser.parse(clean_text)

    def _validate_relations(self, model: UMLModel) -> UMLModel:
        """Valida que los extremos de cada relación referencien clases existentes."""
        class_names = {c.name for c in model.classes}
        valid_relations = []
        for rel in model.relations:
            if rel.source in class_names and rel.target in class_names:
                valid_relations.append(rel)
            else:
                import logging
                logging.getLogger(__name__).warning(
                    f"Relación {rel.source} -> {rel.target}: "
                    f"al menos un extremo no existe en el modelo"
                )
                valid_relations.append(rel)
        return UMLModel(
            module_name=model.module_name,
            classes=model.classes,
            relations=tuple(valid_relations),
            source_hash=model.source_hash,
        )

    def parse(self, raw_text: str) -> UMLModel:
        """Pipeline completo: preprocesado -> CST -> AST -> UMLModel normalizado."""
        import logging

        from lark.exceptions import UnexpectedCharacters, UnexpectedToken
        logger = logging.getLogger(__name__)

        if not self.source_hash:
            self.source_hash = hashlib.sha256(raw_text.encode('utf-8')).hexdigest()

        try:
            tree = self.parse_tree(raw_text)
            classes, relations = PlantUMLTransformer().transform(tree)

            # Normalización determinista (sorting canónico)
            sorted_classes = tuple(sorted(classes, key=lambda c: c.name))
            sorted_relations = tuple(sorted(
                relations, key=lambda r: (r.source, r.target, r.relation_type)
            ))

            model = UMLModel(
                module_name=self.module_name,
                classes=sorted_classes,
                relations=sorted_relations,
                source_hash=self.source_hash,
            )
            return self._validate_relations(model)
        except (UnexpectedToken, UnexpectedCharacters) as e:
            logger.error(
                f"Error sintáctico en módulo '{self.module_name}': "
                f"Línea {getattr(e, 'line', '?')}, Columna {getattr(e, 'column', '?')}. "
                f"Token inesperado: {getattr(e, 'token', e)!r}. "
                f"Tokens esperados: {getattr(e, 'expected', '?')}"
            )
            # Degradación elegante: retornar modelo vacío (P-05)
            return UMLModel(
                module_name=self.module_name,
                classes=(),
                relations=(),
                source_hash=self.source_hash,
            )


PlantUMLParser = LarkPlantUMLParser



