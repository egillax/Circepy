from __future__ import annotations

from ...cohortdefinition.criteria import DeviceExposure
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
    state: BuildState, criteria: DeviceExposure, ctx: BuildContext
) -> BuildState:
    table = state.table

    table = apply_concept_criteria(
        table,
        column="device_type_concept_id",
        concepts=criteria.device_type,
        selection=criteria.device_type_cs,
        ctx=ctx,
        exclude=bool(criteria.device_type_exclude),
    )
    table = apply_numeric_range(table, "quantity", criteria.quantity)
    table = apply_text_filter(
        table,
        "unique_device_id",
        getattr(criteria, "unique_device_id", None),
    )
    state.table = table
    return state


def _post_hook(
    state: BuildState, criteria: DeviceExposure, ctx: BuildContext
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
    if criteria.device_source_concept is not None:
        table = apply_codeset_filter(
            table,
            "device_source_concept_id",
            criteria.device_source_concept,
            ctx,
        )

    state.table = table
    return state


register_framework(
    "DeviceExposure",
    spec=BuilderSpec(
        source_table="device_exposure",
        first_position="after_post",
    ),
    domain_hook=_domain_hook,
    post_hook=_post_hook,
)
