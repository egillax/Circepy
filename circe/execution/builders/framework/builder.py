from __future__ import annotations

from dataclasses import replace
from typing import Any, Optional

import ibis.expr.types as ir

from ...build_context import BuildContext
from .accessors import invoke_accessor
from .resolve import initial_state
from .spec import BuildHook, BuilderSpec, BuildState
from .steps import (
    apply_codeset,
    apply_date_filters,
    apply_first,
    apply_shared_person_filters,
    standardize,
)


def _identity_hook(state: BuildState, criteria: Any, ctx: BuildContext) -> BuildState:
    return state


class FrameworkBuilder:
    """
    Enterprise-style builder orchestrator.

    Common sequencing and output contract live here. Domain modules only provide:
    - a declarative BuilderSpec
    - domain/post/projection hooks for criterion-specific logic.
    """

    def __init__(
        self,
        *,
        spec: BuilderSpec,
        domain_hook: Optional[BuildHook] = None,
        post_hook: Optional[BuildHook] = None,
        projection_hook: Optional[BuildHook] = None,
    ):
        self.spec = spec
        self._domain_hook = domain_hook or _identity_hook
        self._post_hook = post_hook or _identity_hook
        self._projection_hook = projection_hook or _identity_hook

    def __call__(self, criteria: Any, ctx: BuildContext) -> ir.Table:
        spec = self.spec
        criteria_label = criteria.__class__.__name__
        state = initial_state(criteria, ctx, spec)

        state = apply_codeset(state, criteria, ctx, spec)
        state = replace(
            state,
            table=ctx.trace_step(
                state.table, label=f"{criteria_label}.codeset", kind="filter"
            ),
        )

        state = apply_first(state, criteria, when="before_dates", spec=spec)
        state = replace(
            state,
            table=ctx.trace_step(
                state.table, label=f"{criteria_label}.first.before_dates", kind="first"
            ),
        )
        state = apply_date_filters(state, criteria, spec=spec)
        state = replace(
            state,
            table=ctx.trace_step(
                state.table, label=f"{criteria_label}.date_range", kind="filter"
            ),
        )

        state = self._domain_hook(state, criteria, ctx)
        state = replace(
            state,
            table=ctx.trace_step(
                state.table, label=f"{criteria_label}.domain", kind="domain"
            ),
        )
        state = apply_first(state, criteria, when="after_domain", spec=spec)
        state = replace(
            state,
            table=ctx.trace_step(
                state.table, label=f"{criteria_label}.first.after_domain", kind="first"
            ),
        )

        state = apply_shared_person_filters(state, criteria, ctx, spec=spec)
        state = replace(
            state,
            table=ctx.trace_step(
                state.table, label=f"{criteria_label}.shared", kind="filter"
            ),
        )
        state = apply_first(state, criteria, when="after_shared", spec=spec)
        state = replace(
            state,
            table=ctx.trace_step(
                state.table, label=f"{criteria_label}.first.after_shared", kind="first"
            ),
        )

        state = self._post_hook(state, criteria, ctx)
        state = replace(
            state,
            table=ctx.trace_step(
                state.table, label=f"{criteria_label}.post", kind="post"
            ),
        )
        state = apply_first(state, criteria, when="after_post", spec=spec)
        state = replace(
            state,
            table=ctx.trace_step(
                state.table, label=f"{criteria_label}.first.after_post", kind="first"
            ),
        )

        state = self._projection_hook(state, criteria, ctx)
        state = replace(
            state,
            table=ctx.trace_step(
                state.table, label=f"{criteria_label}.projection", kind="projection"
            ),
        )

        events = standardize(state)
        events = ctx.trace_step(
            events,
            label=f"{criteria_label}.standardize",
            kind="standardize",
        )

        correlated = None
        if spec.accessors.correlated is not None:
            correlated = invoke_accessor(
                criteria, spec.accessors.correlated, label="correlated"
            )

        from ..groups import apply_criteria_group

        events = apply_criteria_group(events, correlated, ctx)
        return ctx.trace_step(
            events, label=f"{criteria_label}.correlated_group", kind="group"
        )
