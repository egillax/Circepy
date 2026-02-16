from __future__ import annotations

from ...cohortdefinition.criteria import Observation
from ..build_context import BuildContext
from .common import (
    apply_codeset_filter,
    apply_concept_criteria,
    apply_numeric_range,
    apply_provider_specialty_filter,
    apply_text_filter,
    apply_visit_concept_filters,
)
from .framework import BuilderSpec, BuildState
from .registry import register_framework


def _domain_hook(
    state: BuildState, criteria: Observation, ctx: BuildContext
) -> BuildState:
    table = state.table
    table = apply_concept_criteria(
        table,
        column="observation_type_concept_id",
        concepts=criteria.observation_type,
        selection=criteria.observation_type_cs,
        ctx=ctx,
        exclude=bool(criteria.observation_type_exclude),
    )
    table = apply_concept_criteria(
        table,
        column="qualifier_concept_id",
        concepts=criteria.qualifier,
        selection=criteria.qualifier_cs,
        ctx=ctx,
    )
    table = apply_concept_criteria(
        table,
        column="unit_concept_id",
        concepts=criteria.unit,
        selection=criteria.unit_cs,
        ctx=ctx,
    )
    table = apply_concept_criteria(
        table,
        column="value_as_concept_id",
        concepts=criteria.value_as_concept,
        selection=criteria.value_as_concept_cs,
        ctx=ctx,
    )
    table = apply_numeric_range(table, "value_as_number", criteria.value_as_number)
    table = apply_text_filter(table, "value_as_string", criteria.value_as_string)
    state.table = table
    return state


def _post_hook(
    state: BuildState, criteria: Observation, ctx: BuildContext
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
    if criteria.observation_source_concept is not None:
        table = apply_codeset_filter(
            table,
            "observation_source_concept_id",
            criteria.observation_source_concept,
            ctx,
        )
    state.table = table
    return state


register_framework(
    "Observation",
    spec=BuilderSpec(
        source_table="observation",
        first_position="after_post",
    ),
    domain_hook=_domain_hook,
    post_hook=_post_hook,
)
