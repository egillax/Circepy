from __future__ import annotations

from ...cohortdefinition.criteria import DrugEra
from ..build_context import BuildContext
from .common import apply_interval_range, apply_numeric_range
from .framework import BuilderSpec, BuildState, CriteriaAccessors, attr
from .registry import register_framework


def _domain_hook(state: BuildState, criteria: DrugEra, ctx: BuildContext) -> BuildState:
    table = state.table
    table = apply_numeric_range(table, "drug_exposure_count", criteria.occurrence_count)
    table = apply_numeric_range(table, "gap_days", criteria.gap_days)
    table = apply_interval_range(
        table,
        "drug_era_start_date",
        "drug_era_end_date",
        criteria.era_length,
    )
    state.table = table
    return state


register_framework(
    "DrugEra",
    spec=BuilderSpec(
        source_table="drug_era",
        primary_key="drug_era_id",
        start_column="drug_era_start_date",
        end_column="drug_era_end_date",
        concept_column="drug_concept_id",
        accessors=CriteriaAccessors(
            start_range=attr("era_start_date"),
            end_range=attr("era_end_date"),
            age=None,
            age_at_start=attr("age_at_start"),
            age_at_end=attr("age_at_end"),
        ),
        first_position="after_shared",
    ),
    domain_hook=_domain_hook,
)
