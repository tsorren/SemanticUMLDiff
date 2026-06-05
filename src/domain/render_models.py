from dataclasses import dataclass, field
from typing import Tuple

from domain.models import UMLRelation


@dataclass(frozen=True)
class RenderSpec:
    included_nodes: Tuple[str, ...] = field(default_factory=tuple)
    highlight_rules: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    included_edges: Tuple[UMLRelation, ...] = field(default_factory=tuple)
