from __future__ import annotations

import ibis

from ...cohortdefinition.criteria import Death
from ..build_context import BuildContext
from .common import apply_codeset_filter, apply_concept_criteria
from .framework import BuilderSpec, BuildState
from .registry import register_framework


def _domain_hook(state: BuildState, criteria: Death, ctx: BuildContext) -> BuildState:
    table = state.table
    table = apply_concept_criteria(
        table,
        column="death_type_concept_id",
        concepts=criteria.death_type,
        selection=criteria.death_type_cs,
        ctx=ctx,
        exclude=bool(getattr(criteria, "death_type_exclude", False)),
    )
    if getattr(criteria, "death_source_concept", None) is not None:
        table = apply_codeset_filter(
            table,
            "cause_source_concept_id",
            int(criteria.death_source_concept),
            ctx,
        )
    order_by = [table.death_date]
    for column in (
        "cause_concept_id",
        "death_type_concept_id",
        "cause_source_concept_id",
    ):
        if column in table.columns:
            order_by.append(ibis.coalesce(table[column], ibis.literal(-1)))
    window = ibis.window(group_by=table.person_id, order_by=order_by)
    table = table.mutate(death_event_id=(ibis.row_number().over(window) + 1))
    state.table = table
    return state


register_framework(
    "Death",
    spec=BuilderSpec(
        source_table="death",
        primary_key="death_event_id",
        start_column="death_date",
        end_column="death_date",
        concept_column="cause_concept_id",
        start_range_attr="occurrence_start_date",
        end_range_attr=None,
        first_attr=None,
        first_position="never",
        age_attr="age",
    ),
    domain_hook=_domain_hook,
)
