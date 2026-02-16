from __future__ import annotations

from ...cohortdefinition.criteria import DrugExposure
from ..build_context import BuildContext
from .common import (
    apply_concept_criteria,
    apply_numeric_range,
    apply_provider_specialty_filter,
    apply_text_filter,
    apply_visit_concept_filters,
    coerce_concept_set_selection,
)
from .framework import BuilderSpec, BuildState
from .registry import register_framework


def _domain_hook(
    state: BuildState, criteria: DrugExposure, ctx: BuildContext
) -> BuildState:
    table = state.table

    table = apply_concept_criteria(
        table,
        column="drug_type_concept_id",
        concepts=criteria.drug_type,
        selection=criteria.drug_type_cs,
        ctx=ctx,
        exclude=bool(getattr(criteria, "drug_type_exclude", False)),
    )
    table = apply_concept_criteria(
        table,
        column="route_concept_id",
        concepts=criteria.route_concept,
        selection=criteria.route_concept_cs,
        ctx=ctx,
    )
    table = apply_concept_criteria(
        table,
        column="dose_unit_concept_id",
        concepts=getattr(criteria, "dose_unit", []),
        selection=getattr(criteria, "dose_unit_cs", None),
        ctx=ctx,
    )

    table = apply_numeric_range(table, "quantity", criteria.quantity)
    table = apply_numeric_range(table, "days_supply", criteria.days_supply)
    table = apply_numeric_range(table, "refills", criteria.refills)
    table = apply_text_filter(
        table, "stop_reason", getattr(criteria, "stop_reason", None)
    )
    table = apply_text_filter(
        table, "lot_number", getattr(criteria, "lot_number", None)
    )

    state.table = table
    return state


def _post_hook(
    state: BuildState, criteria: DrugExposure, ctx: BuildContext
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

    source_filter = getattr(criteria, "drug_source_concept", None)
    selection = coerce_concept_set_selection(source_filter)
    if selection is not None:
        table = apply_concept_criteria(
            table,
            column="drug_source_concept_id",
            concepts=None,
            selection=selection,
            ctx=ctx,
        )

    state.table = table
    return state


register_framework(
    "DrugExposure",
    spec=BuilderSpec(
        source_table="drug_exposure",
        first_position="before_dates",
    ),
    domain_hook=_domain_hook,
    post_hook=_post_hook,
)
