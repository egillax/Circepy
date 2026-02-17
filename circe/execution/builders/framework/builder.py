from __future__ import annotations

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
        state = initial_state(criteria, ctx, spec)

        state = apply_codeset(state, criteria, ctx, spec)

        state = apply_first(state, criteria, when="before_dates", spec=spec)
        state = apply_date_filters(state, criteria, spec=spec)

        state = self._domain_hook(state, criteria, ctx)
        state = apply_first(state, criteria, when="after_domain", spec=spec)

        state = apply_shared_person_filters(state, criteria, ctx, spec=spec)
        state = apply_first(state, criteria, when="after_shared", spec=spec)

        state = self._post_hook(state, criteria, ctx)
        state = apply_first(state, criteria, when="after_post", spec=spec)

        state = self._projection_hook(state, criteria, ctx)

        events = standardize(state)

        correlated = None
        if spec.accessors.correlated is not None:
            correlated = invoke_accessor(
                criteria, spec.accessors.correlated, label="correlated"
            )

        from ..groups import apply_criteria_group

        return apply_criteria_group(events, correlated, ctx)
