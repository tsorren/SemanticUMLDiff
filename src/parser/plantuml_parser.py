import hashlib
import re
from typing import Any, Dict, List, Optional

from domain.models import UMLAttribute, UMLClass, UMLMethod, UMLModel, UMLRelation
from parser.preprocessor import preprocess


def split_params_by_comma(s: str) -> List[str]:
    parts = []
    current = []
    depth = 0
    for char in s:
        if char == "<":
            depth += 1
            current.append(char)
        elif char == ">":
            depth -= 1
            current.append(char)
        elif char == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if current or not parts:
        parts.append("".join(current).strip())
    return [p for p in parts if p]


class PlantUMLParser:
    def __init__(self, module_name: str, source_hash: str = "") -> None:
        self.module_name = module_name
        self.source_hash = source_hash
        self.classes: Dict[str, Dict[str, Any]] = {}
        self.relations: List[UMLRelation] = []
        self.current_class: Optional[str] = None

        # Regex compiled
        self.re_entity = re.compile(r'^(abstract\s+class|class|interface|enum)\s+([\w\.]+)(?:\s*\{)?$')
        self.re_method = re.compile(r'^(\w+)\s*\((.*?)\)(?:\s*:\s*(.+))?$')
        self.re_attr = re.compile(r'^(\w+)(?:\s*:\s*(.+))?$')
        # Simple relation regex matching words, namespaces and common UML arrows
        self.re_relation = re.compile(
            r'^([\w\.]+)\s*(?:"(.*?)")?\s*([o\*<\|\-]*[.\-]+[o\*>\|\-]*)\s*(?:"(.*?)")?\s*([\w\.]+)(?:\s*:\s*(.*))?$'
        )

    def parse(self, raw_text: str) -> UMLModel:
        lines = preprocess(raw_text)

        if not self.source_hash:
            self.source_hash = hashlib.sha256(raw_text.encode('utf-8')).hexdigest()

        for line in lines:
            if line == "}":
                self.current_class = None
                continue

            if line == "{":
                continue

            # 1. Check for relation
            rel_match = self.re_relation.match(line)
            if rel_match:
                source, src_mult, arrow, tgt_mult, target, label = rel_match.groups()

                # Determine relation type from arrow
                rel_type = "association"
                if "<|--" in arrow or "--|>" in arrow or "<|.." in arrow or "..|>" in arrow:
                    rel_type = "inheritance"
                elif "*--" in arrow or "--*" in arrow:
                    rel_type = "composition"
                elif "o--" in arrow or "--o" in arrow:
                    rel_type = "aggregation"

                self.relations.append(
                    UMLRelation(
                        source=source,
                        target=target,
                        relation_type=rel_type,
                        multiplicity_source=src_mult or "",
                        multiplicity_target=tgt_mult or ""
                    )
                )
                continue

            # 2. Check for class/interface/enum
            entity_match = self.re_entity.match(line)
            if entity_match:
                kind, name = entity_match.groups()
                kind = " ".join(kind.split())

                self.current_class = name
                if name not in self.classes:
                    self.classes[name] = {
                        "name": name,
                        "kind": kind,
                        "attributes": [],
                        "methods": []
                    }
                else:
                    self.classes[name]["kind"] = kind
                continue

            # 3. Check for methods and attributes
            if self.current_class:
                # Common modifier stripping
                clean_line = line.replace("{method}", "").replace("{field}", "").replace("{static}", "").replace("{abstract}", "").strip()
                vis = ""
                if clean_line and clean_line[0] in "+-#~":
                    vis = clean_line[0]
                    clean_line = clean_line[1:].strip()

                # Check if it has parentheses (method)
                if "(" in clean_line and ")" in clean_line.split("(", 1)[1]:
                    idx_open = clean_line.find("(")
                    idx_close = clean_line.rfind(")")

                    before_paren = clean_line[:idx_open].strip()
                    params_str = clean_line[idx_open+1:idx_close].strip()
                    after_paren = clean_line[idx_close+1:].strip()

                    ret_type = ""
                    if after_paren:
                        if after_paren.startswith(":"):
                            ret_type = after_paren[1:].strip()
                        else:
                            ret_type = after_paren.strip()

                    parts = before_paren.split()
                    if parts:
                        method_name = parts[-1]
                        if len(parts) > 1 and not ret_type:
                            ret_type = " ".join(parts[:-1])

                        params: tuple[str, ...] = ()
                        if params_str:
                            params = tuple(split_params_by_comma(params_str))

                        self.classes[self.current_class]["methods"].append(
                            UMLMethod(
                                name=method_name,
                                parameters=params,
                                return_type=ret_type,
                                visibility=vis or ""
                            )
                        )
                        continue
                else:
                    # Parse as attribute
                    if ":" in clean_line:
                        name_part, rest = clean_line.split(":", 1)
                        name_part = name_part.strip()
                        rest = rest.strip()

                        if "=" in rest:
                            attr_type, default_val = rest.split("=", 1)
                            attr_type = attr_type.strip()
                            default_val = default_val.strip()
                        else:
                            attr_type = rest
                            default_val = ""

                        name_parts = name_part.split()
                        if name_parts:
                            attr_name = name_parts[-1]
                            self.classes[self.current_class]["attributes"].append(
                                UMLAttribute(
                                    name=attr_name,
                                    type=attr_type,
                                    visibility=vis or "",
                                    default_value=default_val
                                )
                            )
                            continue
                    else:
                        if "=" in clean_line:
                            rest, default_val = clean_line.split("=", 1)
                            rest = rest.strip()
                            default_val = default_val.strip()
                        else:
                            rest = clean_line
                            default_val = ""

                        words = rest.split()
                        if words:
                            if len(words) > 1:
                                attr_name = words[-1]
                                attr_type = " ".join(words[:-1])
                            else:
                                attr_name = words[0]
                                attr_type = ""

                            self.classes[self.current_class]["attributes"].append(
                                UMLAttribute(
                                    name=attr_name,
                                    type=attr_type,
                                    visibility=vis or "",
                                    default_value=default_val
                                )
                            )
                            continue

        # Assemble final model
        uml_classes = []
        for cls_name in sorted(self.classes.keys()):
            cls_data = self.classes[cls_name]

            uml_classes.append(
                UMLClass(
                    name=cls_data["name"],
                    kind=cls_data["kind"],
                    attributes=tuple(cls_data["attributes"]),
                    methods=tuple(cls_data["methods"])
                )
            )

        return UMLModel(
            module_name=self.module_name,
            classes=tuple(uml_classes),
            relations=tuple(self.relations),
            source_hash=self.source_hash
        )
