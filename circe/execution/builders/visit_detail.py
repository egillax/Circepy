from __future__ import annotations

from ...cohortdefinition.criteria import VisitDetail
from ..build_context import BuildContext
from .common import (
    apply_care_site_filter,
    apply_codeset_filter,
    apply_concept_set_selection,
    apply_interval_range,
    apply_location_region_filter,
    apply_provider_specialty_filter,
    project_event_columns,
)
from .framework import BuilderSpec, BuildState
from .registry import register_framework


def _domain_hook(
    state: BuildState, criteria: VisitDetail, ctx: BuildContext
) -> BuildState:
    table = state.table
    table = apply_concept_set_selection(
        table,
        "visit_detail_type_concept_id",
        criteria.visit_detail_type_cs,
        ctx,
    )
    if criteria.visit_detail_source_concept is not None:
        table = apply_codeset_filter(
            table,
            "visit_detail_source_concept_id",
            criteria.visit_detail_source_concept,
            ctx,
        )
    table = apply_interval_range(
        table,
        "visit_detail_start_date",
        "visit_detail_end_date",
        criteria.visit_detail_length,
    )
    state.table = table
    return state


def _post_hook(
    state: BuildState, criteria: VisitDetail, ctx: BuildContext
) -> BuildState:
    table = state.table
    table = apply_provider_specialty_filter(
        table,
        None,
        criteria.provider_specialty_cs,
        ctx,
    )
    table = apply_care_site_filter(table, criteria.place_of_service_cs, ctx)
    table = apply_location_region_filter(
        table,
        care_site_column="care_site_id",
        location_codeset_id=criteria.place_of_service_location,
        start_column="visit_detail_start_date",
        end_column="visit_detail_end_date",
        ctx=ctx,
    )
    state.table = table
    return state


def _projection_hook(
    state: BuildState, criteria: VisitDetail, ctx: BuildContext
) -> BuildState:
    state.table = project_event_columns(
        state.table,
        primary_key=state.primary_key,
        start_column=state.start_column,
        end_column=state.end_column,
        include_visit_occurrence=True,
    )
    return state


register_framework(
    "VisitDetail",
    spec=BuilderSpec(
        source_table="visit_detail",
        primary_key="visit_detail_id",
        start_column="visit_detail_start_date",
        end_column="visit_detail_end_date",
        concept_column="visit_detail_concept_id",
        start_range_attr="visit_detail_start_date",
        end_range_attr="visit_detail_end_date",
        age_column="visit_detail_end_date",
        gender_attr=None,
        gender_selection_attr="gender_cs",
        gender_default=[],
        first_position="before_dates",
    ),
    domain_hook=_domain_hook,
    post_hook=_post_hook,
    projection_hook=_projection_hook,
)
