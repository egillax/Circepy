from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal, Optional

import ibis.expr.types as ir

from ..build_context import BuildContext
from .common import (
    apply_age_filter,
    apply_codeset_filter,
    apply_date_range,
    apply_first_event,
    apply_gender_filter,
    standardize_output,
)

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
    codeset_attr: Optional[str] = "codeset_id"
    start_range_attr: Optional[str] = "occurrence_start_date"
    end_range_attr: Optional[str] = "occurrence_end_date"
    first_attr: Optional[str] = "first"
    first_position: FirstPosition = "before_dates"
    age_attr: Optional[str] = "age"
    age_column: Optional[str] = None
    age_at_start_attr: Optional[str] = None
    age_at_end_attr: Optional[str] = None
    gender_attr: Optional[str] = "gender"
    gender_selection_attr: Optional[str] = "gender_cs"
    gender_default: Any = None
    correlated_attr: str = "correlated_criteria"


BuildHook = Callable[[BuildState, Any, BuildContext], BuildState]


class FrameworkBuilder:
    """
    Enterprise-style builder orchestrator.

    Common sequencing and output contract live here. Domain modules only provide:
    - a declarative BuilderSpec
    - domain/post/projection hooks for criterion-specific logic.
    """

    def __init__(
        self,
        *,
        spec: BuilderSpec,
        domain_hook: Optional[BuildHook] = None,
        post_hook: Optional[BuildHook] = None,
        projection_hook: Optional[BuildHook] = None,
    ):
        self.spec = spec
        self._domain_hook = domain_hook or _identity_hook
        self._post_hook = post_hook or _identity_hook
        self._projection_hook = projection_hook or _identity_hook

    def __call__(self, criteria: Any, ctx: BuildContext) -> ir.Table:
        self._validate_configured_attrs(criteria)
        state = self._initial_state(criteria, ctx)

        if self.spec.codeset_attr and not state.concept_column:
            raise ValueError(
                f"Builder for {criteria.__class__.__name__} configured `codeset_attr` "
                "but did not resolve a concept column."
            )
        if state.concept_column and self.spec.codeset_attr:
            codeset_id = _attr(criteria, self.spec.codeset_attr)
            state.table = apply_codeset_filter(
                state.table, state.concept_column, codeset_id, ctx
            )

        state = self._maybe_apply_first(state, criteria, when="before_dates")
        state = self._apply_date_filters(state, criteria)

        state = self._domain_hook(state, criteria, ctx)
        state = self._maybe_apply_first(state, criteria, when="after_domain")

        state = self._apply_shared_person_filters(state, criteria, ctx)
        state = self._maybe_apply_first(state, criteria, when="after_shared")

        state = self._post_hook(state, criteria, ctx)
        state = self._maybe_apply_first(state, criteria, when="after_post")

        state = self._projection_hook(state, criteria, ctx)

        events = standardize_output(
            state.table,
            primary_key=state.primary_key,
            start_column=state.start_column,
            end_column=state.end_column,
        )
        from .groups import apply_criteria_group

        correlated = _attr(criteria, self.spec.correlated_attr)
        return apply_criteria_group(events, correlated, ctx)

    def _validate_configured_attrs(self, criteria: Any) -> None:
        configured = {
            name
            for name in (
                self.spec.codeset_attr,
                self.spec.start_range_attr,
                self.spec.end_range_attr,
                self.spec.first_attr,
                self.spec.age_attr,
                self.spec.age_at_start_attr,
                self.spec.age_at_end_attr,
                self.spec.gender_attr,
                self.spec.gender_selection_attr,
                self.spec.correlated_attr,
            )
            if name
        }
        missing = sorted(name for name in configured if not hasattr(criteria, name))
        if missing:
            joined = ", ".join(missing)
            raise ValueError(
                f"{criteria.__class__.__name__} is missing expected criteria "
                f"attribute(s): {joined}"
            )

    def _initial_state(self, criteria: Any, ctx: BuildContext) -> BuildState:
        primary_key = _resolve_primary_key(criteria, self.spec)
        start_column = _resolve_start_column(criteria, self.spec)
        end_column = _resolve_end_column(criteria, self.spec)
        concept_column = _resolve_concept_column(criteria, self.spec)
        return BuildState(
            table=ctx.table(self.spec.source_table),
            primary_key=primary_key,
            start_column=start_column,
            end_column=end_column,
            concept_column=concept_column,
        )

    def _apply_date_filters(self, state: BuildState, criteria: Any) -> BuildState:
        if self.spec.start_range_attr:
            state.table = apply_date_range(
                state.table,
                state.start_column,
                _attr(criteria, self.spec.start_range_attr),
            )
        if self.spec.end_range_attr:
            state.table = apply_date_range(
                state.table,
                state.end_column,
                _attr(criteria, self.spec.end_range_attr),
            )
        return state

    def _apply_shared_person_filters(
        self, state: BuildState, criteria: Any, ctx: BuildContext
    ) -> BuildState:
        if self.spec.age_attr:
            age_range = _attr(criteria, self.spec.age_attr)
            if age_range:
                age_column = self.spec.age_column or state.start_column
                state.table = apply_age_filter(state.table, age_range, ctx, age_column)

        if self.spec.age_at_start_attr:
            age_at_start = _attr(criteria, self.spec.age_at_start_attr)
            if age_at_start:
                state.table = apply_age_filter(
                    state.table, age_at_start, ctx, state.start_column
                )
        if self.spec.age_at_end_attr:
            age_at_end = _attr(criteria, self.spec.age_at_end_attr)
            if age_at_end:
                state.table = apply_age_filter(
                    state.table, age_at_end, ctx, state.end_column
                )

        if self.spec.gender_attr or self.spec.gender_selection_attr:
            genders = (
                _attr(criteria, self.spec.gender_attr)
                if self.spec.gender_attr
                else self.spec.gender_default
            )
            selection = (
                _attr(criteria, self.spec.gender_selection_attr)
                if self.spec.gender_selection_attr
                else None
            )
            state.table = apply_gender_filter(state.table, genders, selection, ctx)
        return state

    def _maybe_apply_first(
        self, state: BuildState, criteria: Any, *, when: FirstPosition
    ) -> BuildState:
        if self.spec.first_position != when:
            return state
        if not self.spec.first_attr:
            return state
        if not _attr(criteria, self.spec.first_attr):
            return state
        state.table = apply_first_event(
            state.table,
            state.start_column,
            state.primary_key,
        )
        return state


def _identity_hook(state: BuildState, criteria: Any, ctx: BuildContext) -> BuildState:
    return state


def _attr(criteria: Any, name: Optional[str]) -> Any:
    if not name:
        return None
    return getattr(criteria, name, None)


def _resolve_primary_key(criteria: Any, spec: BuilderSpec) -> str:
    if spec.primary_key:
        return spec.primary_key
    if hasattr(criteria, "get_primary_key_column"):
        return str(criteria.get_primary_key_column())
    raise ValueError(
        f"Unable to resolve primary key for {criteria.__class__.__name__}. "
        "Set `primary_key` in BuilderSpec."
    )


def _resolve_start_column(criteria: Any, spec: BuilderSpec) -> str:
    if spec.start_column:
        return spec.start_column
    if hasattr(criteria, "get_start_date_column"):
        return str(criteria.get_start_date_column())
    raise ValueError(
        f"Unable to resolve start column for {criteria.__class__.__name__}. "
        "Set `start_column` in BuilderSpec."
    )


def _resolve_end_column(criteria: Any, spec: BuilderSpec) -> str:
    if spec.end_column:
        return spec.end_column
    if hasattr(criteria, "get_end_date_column"):
        return str(criteria.get_end_date_column())
    raise ValueError(
        f"Unable to resolve end column for {criteria.__class__.__name__}. "
        "Set `end_column` in BuilderSpec."
    )


def _resolve_concept_column(criteria: Any, spec: BuilderSpec) -> Optional[str]:
    if spec.concept_column:
        return spec.concept_column
    if spec.concept_from_criteria and hasattr(criteria, "get_concept_id_column"):
        return str(criteria.get_concept_id_column())
    return None
