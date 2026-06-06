import hashlib
import re
from typing import Any, Dict, List, Optional

from domain.models import UMLAttribute, UMLClass, UMLMethod, UMLModel, UMLRelation
from parser.preprocessor import preprocess


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
                clean_line = line.replace("{method}", "").replace("{field}", "").strip()
                vis = ""
                if clean_line and clean_line[0] in "+-#~":
                    vis = clean_line[0]
                    clean_line = clean_line[1:].strip()
                clean_line = clean_line.replace("{static}", "").replace("{abstract}", "").strip()

                method_match = self.re_method.match(clean_line)
                if method_match:
                    name, params_str, ret_type = method_match.groups()
                    params: tuple[str, ...] = ()
                    if params_str and params_str.strip():
                        params = tuple(p.strip() for p in params_str.split(","))

                    self.classes[self.current_class]["methods"].append(
                        UMLMethod(
                            name=name,
                            parameters=params,
                            return_type=ret_type.strip() if ret_type else "",
                            visibility=vis or ""
                        )
                    )
                    continue

                attr_match = self.re_attr.match(clean_line)
                if attr_match:
                    name, attr_type = attr_match.groups()
                    self.classes[self.current_class]["attributes"].append(
                        UMLAttribute(
                            name=name,
                            type=attr_type.strip() if attr_type else "",
                            visibility=vis or ""
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
