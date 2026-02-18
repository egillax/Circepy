from __future__ import annotations

from ...cohortdefinition.criteria import ProcedureOccurrence
from ..build_context import BuildContext
from .common import (
    apply_codeset_filter,
    apply_concept_criteria,
    apply_numeric_range,
    apply_provider_specialty_filter,
    apply_visit_concept_filters,
)
from .framework import BuilderSpec, BuildState
from .registry import register_framework


def _domain_hook(
    state: BuildState, criteria: ProcedureOccurrence, ctx: BuildContext
) -> BuildState:
    table = state.table
    table = apply_concept_criteria(
        table,
        column="procedure_type_concept_id",
        concepts=criteria.procedure_type,
        selection=criteria.procedure_type_cs,
        ctx=ctx,
        exclude=bool(criteria.procedure_type_exclude),
    )
    table = apply_concept_criteria(
        table,
        column="modifier_concept_id",
        concepts=criteria.modifier,
        selection=criteria.modifier_cs,
        ctx=ctx,
    )
    table = apply_numeric_range(table, "quantity", criteria.quantity)
    state.table = table
    return state


def _post_hook(
    state: BuildState, criteria: ProcedureOccurrence, ctx: BuildContext
) -> BuildState:
    table = state.table
    table = apply_provider_specialty_filter(
        table,
        getattr(criteria, "provider_specialty", None),
        getattr(criteria, "provider_specialty_cs", None),
        ctx,
        provider_column="provider_id",
    )
    table = apply_visit_concept_filters(
        table, criteria.visit_type, criteria.visit_type_cs, ctx
    )

    if criteria.procedure_source_concept is not None:
        table = apply_codeset_filter(
            table,
            "procedure_source_concept_id",
            criteria.procedure_source_concept,
            ctx,
        )

    state.table = table
    return state


register_framework(
    "ProcedureOccurrence",
    spec=BuilderSpec(
        source_table="procedure_occurrence",
        first_position="before_dates",
    ),
    domain_hook=_domain_hook,
    post_hook=_post_hook,
)
