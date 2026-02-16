from __future__ import annotations

from ...cohortdefinition.criteria import VisitOccurrence
from ..build_context import BuildContext
from .common import (
    apply_codeset_filter,
    apply_concept_criteria,
    apply_numeric_range,
    apply_provider_specialty_filter,
    project_event_columns,
)
from .framework import BuilderSpec, BuildState
from .registry import register_framework


def _domain_hook(
    state: BuildState, criteria: VisitOccurrence, ctx: BuildContext
) -> BuildState:
    table = state.table

    table = apply_concept_criteria(
        table,
        column="visit_type_concept_id",
        concepts=criteria.visit_type,
        selection=criteria.visit_type_cs,
        ctx=ctx,
        exclude=bool(criteria.visit_type_exclude),
    )

    table = apply_provider_specialty_filter(
        table,
        criteria.provider_specialty,
        criteria.provider_specialty_cs,
        ctx,
    )
    table = apply_concept_criteria(
        table,
        column="place_of_service_concept_id",
        concepts=criteria.place_of_service,
        selection=criteria.place_of_service_cs,
        ctx=ctx,
    )
    if criteria.visit_length:
        table = apply_numeric_range(table, "visit_length", criteria.visit_length)

    state.table = table
    return state


def _post_hook(
    state: BuildState, criteria: VisitOccurrence, ctx: BuildContext
) -> BuildState:
    table = state.table
    if criteria.visit_source_concept is not None:
        table = apply_codeset_filter(
            table,
            "visit_source_concept_id",
            criteria.visit_source_concept,
            ctx,
        )
    state.table = table
    return state


def _projection_hook(
    state: BuildState, criteria: VisitOccurrence, ctx: BuildContext
) -> BuildState:
    state.table = project_event_columns(
        state.table,
        primary_key=state.primary_key,
        start_column=state.start_column,
        end_column=state.end_column,
        include_visit_occurrence=True,
    )
    return state


register_framework(
    "VisitOccurrence",
    spec=BuilderSpec(
        source_table="visit_occurrence",
        first_position="after_post",
    ),
    domain_hook=_domain_hook,
    post_hook=_post_hook,
    projection_hook=_projection_hook,
)
