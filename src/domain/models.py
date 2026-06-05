import dataclasses
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass(frozen=True)
class UMLAttribute:
    name: str
    type: str = ""
    visibility: str = ""
    default_value: str = ""
    modifiers: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class UMLMethod:
    name: str
    parameters: Tuple[str, ...] = field(default_factory=tuple)
    return_type: str = ""
    visibility: str = ""
    modifiers: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class UMLClass:
    name: str
    kind: str  # e.g., "class", "interface", "enum", "abstract class"
    attributes: Tuple[UMLAttribute, ...] = field(default_factory=tuple)
    methods: Tuple[UMLMethod, ...] = field(default_factory=tuple)
    visibility: str = ""
    modifiers: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class UMLRelation:
    source: str
    target: str
    relation_type: str  # e.g., "association", "inheritance", "composition", "aggregation"
    multiplicity_source: str = ""
    multiplicity_target: str = ""


@dataclass(frozen=True)
class UMLModel:
    module_name: str
    classes: Tuple[UMLClass, ...] = field(default_factory=tuple)
    relations: Tuple[UMLRelation, ...] = field(default_factory=tuple)
    metadata: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    source_hash: str = ""

    def serialize(self) -> str:
        """
        Serializes the model deterministically to a JSON string.
        It uses sort_keys=True to ensure stable field ordering.
        Empty strings and empty tuples are omitted to keep output compact.
        """
        def as_dict_factory(data: List[Tuple[str, Any]]) -> Dict[str, Any]:
            return {k: v for k, v in data if v != "" and v != tuple() and v != []}

        raw_dict = dataclasses.asdict(self, dict_factory=as_dict_factory)
        return json.dumps(raw_dict, sort_keys=True, separators=(",", ":"))
