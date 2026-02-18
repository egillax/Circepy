"""Tests for experimental execution API surface."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from circe import CohortExpression
from circe.cohortdefinition import (
    ConditionOccurrence,
    CustomEraStrategy,
    DateOffsetStrategy,
    DrugExposure,
    PayerPlanPeriod,
    PrimaryCriteria,
    VisitDetail,
)
from circe.execution import ExecutionOptions, IbisExecutor
from circe.execution.criteria.parse import parse_single_criteria
from circe.execution.ibis import write_cohort
from circe.execution.options import schema_to_str
from circe.io import load_expression
from circe.vocabulary import Concept, ConceptSet, ConceptSetExpression, ConceptSetItem


def test_execution_options_defaults():
    options = ExecutionOptions()

    assert options.cdm_schema is None
    assert options.vocabulary_schema is None
    assert options.result_schema is None
    assert options.cohort_id is None
    assert options.materialize_stages is False
    assert options.materialize_codesets is True
    assert options.temp_emulation_schema is None
    assert options.capture_sql is False
    assert options.profile_dir is None
    assert options.trace_steps is False
    assert options.trace_sql is False
    assert options.trace_dir is None
    assert options.probe_empty_primary_events is True


def test_schema_to_str_with_tuple_schema():
    assert schema_to_str(("catalog", "schema")) == "catalog.schema"


def test_load_expression_from_mapping():
    expression = load_expression({"Title": "Mapping Input"})
    assert isinstance(expression, CohortExpression)
    assert expression.title == "Mapping Input"


def test_load_expression_from_path(tmp_path: Path):
    payload = {"Title": "File Input"}
    path = tmp_path / "cohort.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    expression = load_expression(path)
    assert isinstance(expression, CohortExpression)
    assert expression.title == "File Input"


def test_ibis_executor_missing_optional_dependencies(monkeypatch):
    class DummyConn:
        pass

    import builtins
    import sys

    real_import = builtins.__import__
    sys.modules.pop("circe.execution.build_context", None)

    def _import(name, *args, **kwargs):
        if name.endswith("build_context"):
            raise ModuleNotFoundError("No module named 'ibis'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _import)

    executor = IbisExecutor(DummyConn(), ExecutionOptions())

    with pytest.raises(RuntimeError, match="requires optional dependencies"):
        executor.build({"Title": "No Backend"})


def test_criteria_compat_methods_available():
    from circe.execution.criteria.resolve import (
        concept_id_column_for,
        end_date_column_for,
        primary_key_column_for,
        start_date_column_for,
    )

    criteria = DrugExposure()

    assert primary_key_column_for(criteria) == "drug_exposure_id"
    assert start_date_column_for(criteria) == "drug_exposure_start_date"
    assert end_date_column_for(criteria) == "drug_exposure_end_date"
    assert concept_id_column_for(criteria) == "drug_concept_id"



def test_parse_single_criteria_wrapper():
    parsed = parse_single_criteria({"ConditionOccurrence": {"CodesetId": 10}})

    assert isinstance(parsed, ConditionOccurrence)
    assert parsed.codeset_id == 10


def test_parse_single_criteria_wrapper_case_insensitive():
    parsed = parse_single_criteria({"conditionoccurrence": {"CodesetId": 11}})

    assert isinstance(parsed, ConditionOccurrence)
    assert parsed.codeset_id == 11


def test_pipeline_registers_visit_detail_and_payer_plan_period_builders():
    from circe.execution.builders import pipeline as _pipeline  # noqa: F401
    from circe.execution.builders.registry import get_builder

    assert callable(get_builder(VisitDetail()))
    assert callable(get_builder(PayerPlanPeriod()))


def test_coerce_concept_set_selection_rejects_invalid_value():
    from circe.execution.builders.common import coerce_concept_set_selection

    with pytest.raises(ValueError, match="Unsupported concept set selection value"):
        coerce_concept_set_selection(object())


def test_write_rejects_append_and_overwrite_together():
    class DummyConn:
        pass

    executor = IbisExecutor(DummyConn(), ExecutionOptions())

    with pytest.raises(ValueError, match="cannot be used together"):
        executor.write(
            {"Title": "Invalid write options"},
            table="cohort",
            append=True,
            overwrite=True,
            cohort_id=1,
        )


def test_write_cohort_rejects_append_and_overwrite_together():
    class DummyConn:
        pass

    with pytest.raises(ValueError, match="cannot be used together"):
        write_cohort(
            {"Title": "Invalid write options"},
            DummyConn(),
            table="cohort",
            append=True,
            overwrite=True,
            cohort_id=1,
        )


def test_write_requires_cohort_id():
    class DummyConn:
        pass

    executor = IbisExecutor(DummyConn(), ExecutionOptions())

    with pytest.raises(ValueError, match="cohort_id must be set"):
        executor.write(
            {"Title": "Missing cohort id"},
            table="cohort",
        )


def test_write_cohort_requires_cohort_id():
    class DummyConn:
        pass

    with pytest.raises(ValueError, match="cohort_id must be set"):
        write_cohort(
            {"Title": "Missing cohort id"},
            DummyConn(),
            table="cohort",
        )


def test_write_cohort_id_overrides_options(monkeypatch):
    class DummyConn:
        pass

    called: dict[str, object] = {}

    def _fake_build_with_context(self, cohort_expression, cohort_id_override=None):
        called["cohort_id_override"] = cohort_id_override

        class DummyCtx:
            def write_cohort_table(self, *args, **kwargs):
                return None

            def close(self):
                return None

        return object(), DummyCtx()

    monkeypatch.setattr(IbisExecutor, "_build_with_context_native", _fake_build_with_context)

    executor = IbisExecutor(DummyConn(), ExecutionOptions(cohort_id=1))
    executor.write(
        {"Title": "Override cohort id"},
        table="cohort",
        cohort_id=2,
    )

    assert called["cohort_id_override"] == 2


def test_has_end_strategy_handles_polymorphic_models():
    from circe.execution.builders.common import has_end_strategy

    assert has_end_strategy(None) is False
    assert (
        has_end_strategy(DateOffsetStrategy(offset=7, date_field="StartDate")) is True
    )
    assert has_end_strategy(CustomEraStrategy(drug_codeset_id=123)) is True


def test_ibis_executor_build_smoke_duckdb():
    ibis = pytest.importorskip("ibis")
    _ = pytest.importorskip("duckdb")

    conn = ibis.duckdb.connect()

    conn.create_table(
        "concept",
        obj=ibis.memtable(
            {
                "concept_id": [111, 999],
                "invalid_reason": [None, "D"],
            }
        ),
        overwrite=True,
    )
    conn.create_table(
        "concept_ancestor",
        obj=ibis.memtable(
            {
                "ancestor_concept_id": [111],
                "descendant_concept_id": [111],
            }
        ),
        overwrite=True,
    )
    conn.create_table(
        "concept_relationship",
        obj=ibis.memtable(
            {
                "concept_id_1": [111],
                "concept_id_2": [111],
                "relationship_id": ["Maps to"],
                "invalid_reason": [""],
            }
        ),
        overwrite=True,
    )
    conn.create_table(
        "condition_occurrence",
        obj=ibis.memtable(
            {
                "person_id": [1],
                "condition_occurrence_id": [1001],
                "condition_concept_id": [111],
                "condition_start_date": ["2020-01-01"],
                "condition_end_date": ["2020-01-02"],
            }
        ),
        overwrite=True,
    )

    cohort = CohortExpression(
        concept_sets=[
            ConceptSet(
                id=1,
                expression=ConceptSetExpression(
                    items=[ConceptSetItem(concept=Concept(conceptId=111))]
                ),
            )
        ],
        primary_criteria=PrimaryCriteria(
            criteria_list=[ConditionOccurrence(codeset_id=1)],
        ),
    )

    with IbisExecutor(conn, ExecutionOptions(materialize_stages=False)) as executor:
        events = executor.build(cohort)
        result = events.execute()

    assert len(result) == 1
    assert set(result.columns) == {
        "person_id",
        "event_id",
        "start_date",
        "end_date",
        "visit_occurrence_id",
    }


def test_write_append_appends_when_target_exists_duckdb():
    ibis = pytest.importorskip("ibis")
    _ = pytest.importorskip("duckdb")

    conn = ibis.duckdb.connect()

    conn.create_table(
        "concept",
        obj=ibis.memtable(
            {
                "concept_id": [111, 999],
                "invalid_reason": [None, "D"],
            }
        ),
        overwrite=True,
    )
    conn.create_table(
        "concept_ancestor",
        obj=ibis.memtable(
            {
                "ancestor_concept_id": [111],
                "descendant_concept_id": [111],
            }
        ),
        overwrite=True,
    )
    conn.create_table(
        "concept_relationship",
        obj=ibis.memtable(
            {
                "concept_id_1": [111],
                "concept_id_2": [111],
                "relationship_id": ["Maps to"],
                "invalid_reason": [""],
            }
        ),
        overwrite=True,
    )
    conn.create_table(
        "condition_occurrence",
        obj=ibis.memtable(
            {
                "person_id": [1],
                "condition_occurrence_id": [1001],
                "condition_concept_id": [111],
                "condition_start_date": ["2020-01-01"],
                "condition_end_date": ["2020-01-02"],
            }
        ),
        overwrite=True,
    )

    cohort = CohortExpression(
        concept_sets=[
            ConceptSet(
                id=1,
                expression=ConceptSetExpression(
                    items=[ConceptSetItem(concept=Concept(conceptId=111))]
                ),
            )
        ],
        primary_criteria=PrimaryCriteria(
            criteria_list=[ConditionOccurrence(codeset_id=1)],
        ),
    )

    target_table = f"cohort_append_{uuid.uuid4().hex[:8]}"
    options = ExecutionOptions(cohort_id=123, materialize_stages=False)

    with IbisExecutor(conn, options) as executor:
        executor.write(
            cohort,
            table=target_table,
            schema="main",
            overwrite=True,
        )

    with IbisExecutor(conn, options) as executor:
        executor.write(
            cohort,
            table=target_table,
            schema="main",
            append=True,
            overwrite=False,
        )

    result = conn.table(target_table, database="main").execute()
    assert len(result) == 2
    assert set(result["cohort_definition_id"]) == {123}


def test_trace_events_include_pipeline_primary_stage_duckdb():
    ibis = pytest.importorskip("ibis")
    _ = pytest.importorskip("duckdb")

    conn = ibis.duckdb.connect()

    conn.create_table(
        "concept",
        obj=ibis.memtable(
            {
                "concept_id": [111, 999],
                "invalid_reason": [None, "D"],
            }
        ),
        overwrite=True,
    )
    conn.create_table(
        "concept_ancestor",
        obj=ibis.memtable(
            {
                "ancestor_concept_id": [111],
                "descendant_concept_id": [111],
            }
        ),
        overwrite=True,
    )
    conn.create_table(
        "concept_relationship",
        obj=ibis.memtable(
            {
                "concept_id_1": [111],
                "concept_id_2": [111],
                "relationship_id": ["Maps to"],
                "invalid_reason": [""],
            }
        ),
        overwrite=True,
    )
    conn.create_table(
        "condition_occurrence",
        obj=ibis.memtable(
            {
                "person_id": [1],
                "condition_occurrence_id": [1001],
                "condition_concept_id": [111],
                "condition_start_date": ["2020-01-01"],
                "condition_end_date": ["2020-01-02"],
            }
        ),
        overwrite=True,
    )

    cohort = CohortExpression(
        concept_sets=[
            ConceptSet(
                id=1,
                expression=ConceptSetExpression(
                    items=[ConceptSetItem(concept=Concept(conceptId=111))]
                ),
            )
        ],
        primary_criteria=PrimaryCriteria(
            criteria_list=[ConditionOccurrence(codeset_id=1)],
        ),
    )

    with IbisExecutor(
        conn,
        ExecutionOptions(materialize_stages=False, trace_steps=True, trace_sql=False),
    ) as executor:
        executor.build(cohort)
        events = executor.trace_events()

    assert any(event.label.startswith("primary_src_") for event in events)
    assert any(event.label == "primary_events" for event in events)
    assert any(
        event.label == "primary_events" and event.kind == "pipeline" for event in events
    )


def test_probe_empty_primary_events_option_disables_probe_query(monkeypatch):
    ibis = pytest.importorskip("ibis")
    _ = pytest.importorskip("duckdb")
    import ibis.expr.types as ir

    conn = ibis.duckdb.connect()

    conn.create_table(
        "concept",
        obj=ibis.memtable(
            {
                "concept_id": [111],
                "invalid_reason": [""],
            }
        ),
        overwrite=True,
    )
    conn.create_table(
        "concept_ancestor",
        obj=ibis.memtable(
            {
                "ancestor_concept_id": [111],
                "descendant_concept_id": [111],
            }
        ),
        overwrite=True,
    )
    conn.create_table(
        "concept_relationship",
        obj=ibis.memtable(
            {
                "concept_id_1": [111],
                "concept_id_2": [111],
                "relationship_id": ["Maps to"],
                "invalid_reason": [""],
            }
        ),
        overwrite=True,
    )
    conn.create_table(
        "condition_occurrence",
        obj=ibis.memtable(
            {
                "person_id": [1],
                "condition_occurrence_id": [1001],
                "condition_concept_id": [111],
                "condition_start_date": ["2020-01-01"],
                "condition_end_date": ["2020-01-02"],
            }
        ),
        overwrite=True,
    )

    cohort = CohortExpression(
        concept_sets=[
            ConceptSet(
                id=1,
                expression=ConceptSetExpression(
                    items=[ConceptSetItem(concept=Concept(conceptId=111))]
                ),
            )
        ],
        primary_criteria=PrimaryCriteria(
            criteria_list=[ConditionOccurrence(codeset_id=1)],
        ),
    )

    original_execute = ir.Expr.execute
    execute_calls = {"n": 0}

    def _counting_execute(self, *args, **kwargs):
        execute_calls["n"] += 1
        return original_execute(self, *args, **kwargs)

    monkeypatch.setattr(ir.Expr, "execute", _counting_execute)

    with IbisExecutor(
        conn,
        ExecutionOptions(
            materialize_stages=True,
            probe_empty_primary_events=False,
        ),
    ) as executor:
        executor.build(cohort)

    assert execute_calls["n"] == 0


def test_append_insert_runtime_error_is_not_swallowed(monkeypatch):
    ibis = pytest.importorskip("ibis")
    _ = pytest.importorskip("duckdb")

    conn = ibis.duckdb.connect()

    conn.create_table(
        "concept",
        obj=ibis.memtable(
            {
                "concept_id": [111, 999],
                "invalid_reason": [None, "D"],
            }
        ),
        overwrite=True,
    )
    conn.create_table(
        "concept_ancestor",
        obj=ibis.memtable(
            {
                "ancestor_concept_id": [111],
                "descendant_concept_id": [111],
            }
        ),
        overwrite=True,
    )
    conn.create_table(
        "concept_relationship",
        obj=ibis.memtable(
            {
                "concept_id_1": [111],
                "concept_id_2": [111],
                "relationship_id": ["Maps to"],
                "invalid_reason": [""],
            }
        ),
        overwrite=True,
    )
    conn.create_table(
        "condition_occurrence",
        obj=ibis.memtable(
            {
                "person_id": [1],
                "condition_occurrence_id": [1001],
                "condition_concept_id": [111],
                "condition_start_date": ["2020-01-01"],
                "condition_end_date": ["2020-01-02"],
            }
        ),
        overwrite=True,
    )

    cohort = CohortExpression(
        concept_sets=[
            ConceptSet(
                id=1,
                expression=ConceptSetExpression(
                    items=[ConceptSetItem(concept=Concept(conceptId=111))]
                ),
            )
        ],
        primary_criteria=PrimaryCriteria(
            criteria_list=[ConditionOccurrence(codeset_id=1)],
        ),
    )

    target_table = f"cohort_append_{uuid.uuid4().hex[:8]}"
    options = ExecutionOptions(cohort_id=123, materialize_stages=False)

    with IbisExecutor(conn, options) as executor:
        executor.write(
            cohort,
            table=target_table,
            schema="main",
            overwrite=True,
        )

    def _boom(*args, **kwargs):
        raise RuntimeError("insert boom")

    monkeypatch.setattr(conn, "insert", _boom)

    with IbisExecutor(conn, options) as executor:
        with pytest.raises(RuntimeError, match="insert boom"):
            executor.write(
                cohort,
                table=target_table,
                schema="main",
                append=True,
                overwrite=False,
            )
