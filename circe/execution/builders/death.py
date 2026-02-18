from __future__ import annotations

import logging

from ...cohortdefinition.criteria import Death
from ..build_context import BuildContext
from .common import (
    apply_concept_criteria,
    apply_concept_set_selection,
    coerce_concept_set_selection,
)
from .framework import BuilderSpec, BuildState, CriteriaAccessors
from .registry import register_framework

logger = logging.getLogger(__name__)


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

    # Align with Circe/SQL builder semantics:
    # - `DeathSourceConcept` is a codeset applied to `cause_source_concept_id`.
    # - Some payloads also supply `CauseSourceConcept` / `CauseSourceConceptCS`; treat them
    #   as equivalent, preferring the explicit ConceptSetSelection when present.
    def _normalize_selection(field: str, value: object | None):
        try:
            selection = coerce_concept_set_selection(value)
        except ValueError as exc:
            raise ValueError(
                f"Death.{field} must be a ConceptSetSelection or codeset identifier; got {value!r}"
            ) from exc
        if selection is not None and getattr(selection, "codeset_id", None) is None:
            return None
        return selection

    selection_cs = _normalize_selection(
        "cause_source_concept_cs", getattr(criteria, "cause_source_concept_cs", None)
    )
    selection_concept = _normalize_selection(
        "cause_source_concept", getattr(criteria, "cause_source_concept", None)
    )
    selection_death_source = _normalize_selection(
        "death_source_concept", getattr(criteria, "death_source_concept", None)
    )

    provided = [
        name
        for name, value in (
            ("cause_source_concept_cs", selection_cs),
            ("cause_source_concept", selection_concept),
            ("death_source_concept", selection_death_source),
        )
        if value is not None
    ]
    if len(provided) > 1:
        logger.warning(
            "Death criteria contains multiple cause-source fields (%s); "
            "using precedence cause_source_concept_cs → cause_source_concept → death_source_concept.",
            ", ".join(provided),
        )

    selection = selection_cs or selection_concept or selection_death_source
    if selection is not None:
        table = apply_concept_set_selection(
            table,
            "cause_source_concept_id",
            selection,
            ctx,
        )

    state.table = table
    return state


register_framework(
    "Death",
    spec=BuilderSpec(
        source_table="death",
        primary_key="person_id",
        start_column="death_date",
        end_column="death_date",
        concept_column="cause_concept_id",
        accessors=CriteriaAccessors(first=None),
        first_position="never",
    ),
    domain_hook=_domain_hook,
)
