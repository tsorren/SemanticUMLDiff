from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Tuple


class ChangeType(Enum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    MODIFIED = "MODIFIED"


@dataclass(frozen=True)
class DiffItem:
    entity_type: str  # class, attribute, method, relation
    entity_name: str
    change_type: ChangeType
    context: str = ""  # Parent class name if applicable
    before: Optional[str] = None
    after: Optional[str] = None
    before_element: Any = field(default=None, compare=False, hash=False)
    after_element: Any = field(default=None, compare=False, hash=False)


@dataclass(frozen=True)
class DiffResult:
    module_name: str
    changes: Tuple[DiffItem, ...] = field(default_factory=tuple)
    complexity_score: Optional[int] = None
    complexity_level: Optional[str] = None
