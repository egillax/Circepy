from __future__ import annotations

from typing import Any, Optional

from ...build_context import BuildContext
from ...criteria.resolve import (
    concept_id_column_for,
    end_date_column_for,
    primary_key_column_for,
    start_date_column_for,
)
from .spec import BuildState, BuilderSpec


def initial_state(criteria: Any, ctx: BuildContext, spec: BuilderSpec) -> BuildState:
    primary_key = _resolve_primary_key(criteria, spec)
    start_column = _resolve_start_column(criteria, spec)
    end_column = _resolve_end_column(criteria, spec)
    concept_column = _resolve_concept_column(criteria, spec)
    return BuildState(
        table=ctx.table(spec.source_table),
        primary_key=primary_key,
        start_column=start_column,
        end_column=end_column,
        concept_column=concept_column,
    )


def _resolve_primary_key(criteria: Any, spec: BuilderSpec) -> str:
    if spec.primary_key:
        return spec.primary_key
    return primary_key_column_for(criteria)


def _resolve_start_column(criteria: Any, spec: BuilderSpec) -> str:
    if spec.start_column:
        return spec.start_column
    return start_date_column_for(criteria)


def _resolve_end_column(criteria: Any, spec: BuilderSpec) -> str:
    if spec.end_column:
        return spec.end_column
    return end_date_column_for(criteria)


def _resolve_concept_column(criteria: Any, spec: BuilderSpec) -> Optional[str]:
    if spec.concept_column:
        return spec.concept_column
    if spec.concept_from_criteria:
        return concept_id_column_for(criteria)
    return None

