from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Optional

import ibis.expr.types as ir

from ...build_context import BuildContext
from .accessors import CriteriaAccessors

FirstPosition = Literal[
    "before_dates",
    "after_domain",
    "after_shared",
    "after_post",
    "never",
]


@dataclass
class BuildState:
    table: ir.Table
    primary_key: str
    start_column: str
    end_column: str
    concept_column: Optional[str]


@dataclass(frozen=True)
class BuilderSpec:
    source_table: str
    primary_key: Optional[str] = None
    start_column: Optional[str] = None
    end_column: Optional[str] = None
    concept_column: Optional[str] = None
    concept_from_criteria: bool = True
    accessors: CriteriaAccessors = field(default_factory=CriteriaAccessors)
    first_position: FirstPosition = "before_dates"
    age_column: Optional[str] = None
    gender_default: Any = None


BuildHook = Callable[[BuildState, Any, BuildContext], BuildState]

