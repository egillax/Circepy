from __future__ import annotations

from ...cohortdefinition.criteria import ObservationPeriod
from ..build_context import BuildContext
from .common import (
    apply_concept_criteria,
    apply_interval_range,
    apply_user_defined_period,
)
from .framework import BuilderSpec, BuildState
from .registry import register_framework


def _domain_hook(
    state: BuildState, criteria: ObservationPeriod, ctx: BuildContext
) -> BuildState:
    table = state.table
    table = apply_concept_criteria(
        table,
        column="period_type_concept_id",
        concepts=criteria.period_type,
        selection=criteria.period_type_cs,
        ctx=ctx,
    )
    table = apply_interval_range(
        table,
        "observation_period_start_date",
        "observation_period_end_date",
        criteria.period_length,
    )
    state.table = table
    return state


def _post_hook(
    state: BuildState, criteria: ObservationPeriod, ctx: BuildContext
) -> BuildState:
    table, start_column, end_column = apply_user_defined_period(
        state.table,
        state.start_column,
        state.end_column,
        criteria.user_defined_period,
    )
    state.table = table
    state.start_column = start_column
    state.end_column = end_column
    return state


register_framework(
    "ObservationPeriod",
    spec=BuilderSpec(
        source_table="observation_period",
        primary_key="observation_period_id",
        start_column="observation_period_start_date",
        end_column="observation_period_end_date",
        concept_from_criteria=False,
        codeset_attr=None,
        start_range_attr="period_start_date",
        end_range_attr="period_end_date",
        age_attr=None,
        age_at_start_attr="age_at_start",
        age_at_end_attr="age_at_end",
        gender_attr=None,
        gender_selection_attr=None,
        first_position="after_post",
    ),
    domain_hook=_domain_hook,
    post_hook=_post_hook,
)
