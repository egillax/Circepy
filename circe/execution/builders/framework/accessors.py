from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional


def attr(name: str, default: Any = None) -> Callable[[Any], Any]:
    return lambda criteria: getattr(criteria, name, default)


def flag(name: str) -> Callable[[Any], bool]:
    return lambda criteria: bool(getattr(criteria, name, False))


@dataclass(frozen=True)
class CriteriaAccessors:
    codeset_id: Optional[Callable[[Any], Optional[int]]] = attr("codeset_id")
    start_range: Optional[Callable[[Any], Any]] = attr("occurrence_start_date")
    end_range: Optional[Callable[[Any], Any]] = attr("occurrence_end_date")
    first: Optional[Callable[[Any], bool]] = flag("first")
    age: Optional[Callable[[Any], Any]] = attr("age")
    age_at_start: Optional[Callable[[Any], Any]] = None
    age_at_end: Optional[Callable[[Any], Any]] = None
    gender: Optional[Callable[[Any], Any]] = attr("gender")
    gender_selection: Optional[Callable[[Any], Any]] = attr("gender_cs")
    correlated: Optional[Callable[[Any], Any]] = attr("correlated_criteria")


def invoke_accessor(criteria: Any, accessor: Callable[[Any], Any], *, label: str) -> Any:
    try:
        return accessor(criteria)
    except (AttributeError, TypeError) as exc:
        raise ValueError(
            f"{criteria.__class__.__name__} failed criteria accessor `{label}`"
        ) from exc

