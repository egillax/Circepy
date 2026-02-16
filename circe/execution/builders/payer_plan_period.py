from __future__ import annotations

from ...cohortdefinition.criteria import PayerPlanPeriod
from ..build_context import BuildContext
from .common import (
    apply_codeset_filter,
    apply_interval_range,
    apply_user_defined_period,
)
from .framework import BuilderSpec, BuildState
from .registry import register_framework


def _domain_hook(
    state: BuildState, criteria: PayerPlanPeriod, ctx: BuildContext
) -> BuildState:
    state.table = apply_interval_range(
        state.table,
        "payer_plan_period_start_date",
        "payer_plan_period_end_date",
        criteria.period_length,
    )
    return state


def _post_hook(
    state: BuildState, criteria: PayerPlanPeriod, ctx: BuildContext
) -> BuildState:
    table = state.table
    codeset_filters = (
        ("payer_concept_id", criteria.payer_concept),
        ("plan_concept_id", criteria.plan_concept),
        ("sponsor_concept_id", criteria.sponsor_concept),
        ("stop_reason_concept_id", criteria.stop_reason_concept),
        ("payer_source_concept_id", criteria.payer_source_concept),
        ("plan_source_concept_id", criteria.plan_source_concept),
        ("sponsor_source_concept_id", criteria.sponsor_source_concept),
        ("stop_reason_source_concept_id", criteria.stop_reason_source_concept),
    )
    for column, codeset_id in codeset_filters:
        table = apply_codeset_filter(table, column, codeset_id, ctx)

    table, start_column, end_column = apply_user_defined_period(
        table,
        state.start_column,
        state.end_column,
        criteria.user_defined_period,
    )
    state.table = table
    state.start_column = start_column
    state.end_column = end_column
    return state


register_framework(
    "PayerPlanPeriod",
    spec=BuilderSpec(
        source_table="payer_plan_period",
        primary_key="payer_plan_period_id",
        start_column="payer_plan_period_start_date",
        end_column="payer_plan_period_end_date",
        concept_from_criteria=False,
        codeset_attr=None,
        start_range_attr="period_start_date",
        end_range_attr="period_end_date",
        age_attr=None,
        age_at_start_attr="age_at_start",
        age_at_end_attr="age_at_end",
        gender_attr="gender",
        gender_selection_attr="gender_cs",
        first_position="after_post",
    ),
    domain_hook=_domain_hook,
    post_hook=_post_hook,
)
