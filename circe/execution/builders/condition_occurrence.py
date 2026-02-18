from __future__ import annotations

from ...cohortdefinition.criteria import ConditionOccurrence
from ..build_context import BuildContext
from .common import (
    apply_concept_criteria,
    apply_visit_concept_filters,
    coerce_concept_set_selection,
)
from .framework import BuilderSpec, BuildState
from .registry import register_framework


def _domain_hook(
    state: BuildState, criteria: ConditionOccurrence, ctx: BuildContext
) -> BuildState:
    table = state.table
    table = apply_concept_criteria(
        table,
        column="condition_type_concept_id",
        concepts=criteria.condition_type,
        selection=criteria.condition_type_cs,
        ctx=ctx,
        exclude=bool(criteria.condition_type_exclude),
    )
    table = apply_concept_criteria(
        table,
        column="condition_status_concept_id",
        concepts=getattr(criteria, "condition_status", None),
        selection=None,
        ctx=ctx,
    )
    state.table = table
    return state


def _post_hook(
    state: BuildState, criteria: ConditionOccurrence, ctx: BuildContext
) -> BuildState:
    table = state.table

    source_filter = getattr(criteria, "condition_source_concept", None)
    selection = coerce_concept_set_selection(source_filter)
    if selection is not None:
        table = apply_concept_criteria(
            table,
            column="condition_source_concept_id",
            concepts=None,
            selection=selection,
            ctx=ctx,
        )

    visit_source = getattr(criteria, "visit_source_concept", None)
    needs_visit_filters = bool(
        criteria.visit_type or criteria.visit_type_cs or visit_source is not None
    )
    if needs_visit_filters:
        visit = ctx.table("visit_occurrence").select(
            "person_id",
            "visit_occurrence_id",
            "visit_concept_id",
            "visit_source_concept_id",
        )
        table = table.join(
            visit,
            (table.visit_occurrence_id == visit.visit_occurrence_id)
            & (table.person_id == visit.person_id),
        )
        table = apply_visit_concept_filters(
            table, criteria.visit_type, criteria.visit_type_cs, ctx
        )
        if visit_source is not None:
            table = table.filter(table.visit_source_concept_id == int(visit_source))

    state.table = table
    return state


register_framework(
    "ConditionOccurrence",
    spec=BuilderSpec(
        source_table="condition_occurrence",
        first_position="before_dates",
    ),
    domain_hook=_domain_hook,
    post_hook=_post_hook,
)
