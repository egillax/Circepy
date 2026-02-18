from __future__ import annotations

from dataclasses import replace
from typing import Any

import ibis.expr.types as ir

from ...build_context import BuildContext
from ..common import (
    apply_age_filter,
    apply_codeset_filter,
    apply_date_range,
    apply_first_event,
    apply_gender_filter,
    standardize_output,
)
from .accessors import invoke_accessor
from .spec import BuildState, BuilderSpec, FirstPosition


def apply_codeset(
    state: BuildState,
    criteria: Any,
    ctx: BuildContext,
    spec: BuilderSpec,
) -> BuildState:
    accessor = spec.accessors.codeset_id
    if accessor is None:
        return state
    if not state.concept_column:
        raise ValueError(
            f"Builder for {criteria.__class__.__name__} configured `codeset_id` accessor "
            "but did not resolve a concept column."
        )
    codeset_id = invoke_accessor(criteria, accessor, label="codeset_id")
    table = apply_codeset_filter(state.table, state.concept_column, codeset_id, ctx)
    return replace(state, table=table)


def apply_first(
    state: BuildState,
    criteria: Any,
    *,
    when: FirstPosition,
    spec: BuilderSpec,
) -> BuildState:
    if spec.first_position != when:
        return state
    accessor = spec.accessors.first
    if accessor is None:
        return state
    if not invoke_accessor(criteria, accessor, label="first"):
        return state
    table = apply_first_event(state.table, state.start_column, state.primary_key)
    return replace(state, table=table)


def apply_date_filters(
    state: BuildState,
    criteria: Any,
    *,
    spec: BuilderSpec,
) -> BuildState:
    table = state.table
    if spec.accessors.start_range is not None:
        table = apply_date_range(
            table,
            state.start_column,
            invoke_accessor(criteria, spec.accessors.start_range, label="start_range"),
        )
    if spec.accessors.end_range is not None:
        table = apply_date_range(
            table,
            state.end_column,
            invoke_accessor(criteria, spec.accessors.end_range, label="end_range"),
        )
    return replace(state, table=table)


def apply_shared_person_filters(
    state: BuildState, criteria: Any, ctx: BuildContext, *, spec: BuilderSpec
) -> BuildState:
    table = state.table

    if spec.accessors.age is not None:
        age_range = invoke_accessor(criteria, spec.accessors.age, label="age")
        if age_range:
            age_column = spec.age_column or state.start_column
            table = apply_age_filter(table, age_range, ctx, age_column)

    if spec.accessors.age_at_start is not None:
        age_at_start = invoke_accessor(
            criteria, spec.accessors.age_at_start, label="age_at_start"
        )
        if age_at_start:
            table = apply_age_filter(table, age_at_start, ctx, state.start_column)

    if spec.accessors.age_at_end is not None:
        age_at_end = invoke_accessor(
            criteria, spec.accessors.age_at_end, label="age_at_end"
        )
        if age_at_end:
            table = apply_age_filter(table, age_at_end, ctx, state.end_column)

    if spec.accessors.gender is not None or spec.accessors.gender_selection is not None:
        if spec.accessors.gender is not None:
            genders = invoke_accessor(criteria, spec.accessors.gender, label="gender")
        else:
            genders = spec.gender_default

        selection = None
        if spec.accessors.gender_selection is not None:
            selection = invoke_accessor(
                criteria, spec.accessors.gender_selection, label="gender_selection"
            )

        table = apply_gender_filter(table, genders, selection, ctx)

    return replace(state, table=table)


def standardize(state: BuildState) -> ir.Table:
    return standardize_output(
        state.table,
        primary_key=state.primary_key,
        start_column=state.start_column,
        end_column=state.end_column,
    )
