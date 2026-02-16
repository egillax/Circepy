from __future__ import annotations

from ...cohortdefinition.criteria import DoseEra
from ..build_context import BuildContext
from .common import apply_concept_criteria, apply_interval_range, apply_numeric_range
from .framework import BuilderSpec, BuildState
from .registry import register_framework


def _domain_hook(state: BuildState, criteria: DoseEra, ctx: BuildContext) -> BuildState:
    table = state.table
    table = apply_concept_criteria(
        table,
        column="unit_concept_id",
        concepts=criteria.unit,
        selection=criteria.unit_cs,
        ctx=ctx,
    )
    table = apply_numeric_range(table, "dose_value", criteria.dose_value)
    table = apply_interval_range(
        table,
        "dose_era_start_date",
        "dose_era_end_date",
        criteria.era_length,
    )
    state.table = table
    return state


register_framework(
    "DoseEra",
    spec=BuilderSpec(
        source_table="dose_era",
        primary_key="dose_era_id",
        start_column="dose_era_start_date",
        end_column="dose_era_end_date",
        concept_column="drug_concept_id",
        start_range_attr="era_start_date",
        end_range_attr="era_end_date",
        age_attr=None,
        age_at_start_attr="age_at_start",
        age_at_end_attr="age_at_end",
        first_position="after_shared",
    ),
    domain_hook=_domain_hook,
)
