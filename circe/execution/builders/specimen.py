from __future__ import annotations

from ...cohortdefinition.criteria import Specimen
from ..build_context import BuildContext
from .common import (
    apply_codeset_filter,
    apply_concept_criteria,
    apply_numeric_range,
    apply_text_filter,
)
from .framework import BuilderSpec, BuildState
from .registry import register_framework


def _domain_hook(
    state: BuildState, criteria: Specimen, ctx: BuildContext
) -> BuildState:
    table = state.table
    table = apply_concept_criteria(
        table,
        column="specimen_type_concept_id",
        concepts=criteria.specimen_type,
        selection=criteria.specimen_type_cs,
        ctx=ctx,
        exclude=bool(criteria.specimen_type_exclude),
    )

    table = apply_numeric_range(table, "quantity", criteria.quantity)

    table = apply_concept_criteria(
        table,
        column="unit_concept_id",
        concepts=criteria.unit,
        selection=criteria.unit_cs,
        ctx=ctx,
    )

    table = apply_concept_criteria(
        table,
        column="anatomic_site_concept_id",
        concepts=criteria.anatomic_site,
        selection=criteria.anatomic_site_cs,
        ctx=ctx,
    )

    table = apply_concept_criteria(
        table,
        column="disease_status_concept_id",
        concepts=criteria.disease_status,
        selection=criteria.disease_status_cs,
        ctx=ctx,
    )

    table = apply_text_filter(table, "specimen_source_id", criteria.source_id)
    if criteria.specimen_source_concept is not None:
        table = apply_codeset_filter(
            table,
            "specimen_source_concept_id",
            criteria.specimen_source_concept,
            ctx,
        )

    state.table = table
    return state


register_framework(
    "Specimen",
    spec=BuilderSpec(
        source_table="specimen",
        primary_key="specimen_id",
        start_column="specimen_date",
        end_column="specimen_date",
        concept_column="specimen_concept_id",
        age_column="specimen_date",
        first_position="after_post",
    ),
    domain_hook=_domain_hook,
)
