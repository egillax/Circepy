from __future__ import annotations

from ...cohortdefinition.criteria import ConditionEra
from ..build_context import BuildContext
from .common import apply_interval_range, apply_numeric_range
from .framework import BuilderSpec, BuildState
from .registry import register_framework


def _domain_hook(
    state: BuildState, criteria: ConditionEra, ctx: BuildContext
) -> BuildState:
    table = state.table
    table = apply_numeric_range(
        table, "condition_occurrence_count", criteria.occurrence_count
    )
    table = apply_interval_range(
        table,
        "condition_era_start_date",
        "condition_era_end_date",
        criteria.era_length,
    )
    state.table = table
    return state


register_framework(
    "ConditionEra",
    spec=BuilderSpec(
        source_table="condition_era",
        primary_key="condition_era_id",
        start_column="condition_era_start_date",
        end_column="condition_era_end_date",
        concept_column="condition_concept_id",
        start_range_attr="era_start_date",
        end_range_attr="era_end_date",
        age_attr=None,
        age_at_start_attr="age_at_start",
        age_at_end_attr="age_at_end",
        first_position="after_shared",
    ),
    domain_hook=_domain_hook,
)
