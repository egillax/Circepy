from __future__ import annotations

import json

import pytest


def _context(*, trace_steps: bool, trace_sql: bool, capture_sql: bool):
    ibis = pytest.importorskip("ibis")
    _ = pytest.importorskip("duckdb")

    from circe.execution.build_context import BuildContext, CohortBuildOptions

    conn = ibis.duckdb.connect()
    conn.create_table(
        "codesets",
        obj=ibis.memtable({"codeset_id": [0], "concept_id": [0]}),
        overwrite=True,
    )
    ctx = BuildContext(
        conn,
        CohortBuildOptions(
            materialize_stages=False,
            materialize_codesets=False,
            trace_steps=trace_steps,
            trace_sql=trace_sql,
            capture_sql=capture_sql,
        ),
        conn.table("codesets"),
    )
    return ibis, conn, ctx


def test_capture_sql_does_not_compile_in_trace_step(monkeypatch):
    ibis, conn, ctx = _context(trace_steps=True, trace_sql=False, capture_sql=True)

    calls = {"n": 0}

    def _compile(_expr):
        calls["n"] += 1
        return "SELECT 1"

    monkeypatch.setattr(conn, "compile", _compile)

    expr = ibis.memtable({"x": [1]})
    traced = ctx.trace_step(expr, label="capture_only_step")
    assert traced is expr
    assert calls["n"] == 0

    events = ctx.trace_events()
    assert len(events) == 1
    assert events[0].label == "capture_only_step"
    assert events[0].step_key == "capture_only_step"
    assert events[0].sql is None


def test_trace_sql_compiles_in_trace_step(monkeypatch):
    ibis, conn, ctx = _context(trace_steps=True, trace_sql=True, capture_sql=False)

    calls = {"n": 0}

    def _compile(_expr):
        calls["n"] += 1
        return "SELECT 1"

    monkeypatch.setattr(conn, "compile", _compile)

    expr = ibis.memtable({"x": [1]})
    traced = ctx.trace_step(expr, label="trace_sql_step")
    assert traced is expr
    assert calls["n"] == 1

    events = ctx.trace_events()
    assert len(events) == 1
    assert events[0].label == "trace_sql_step"
    assert events[0].step_key == "trace_sql_step"
    assert events[0].sql == "SELECT 1"


def test_trace_file_payload_contains_step_key_and_label(tmp_path):
    ibis = pytest.importorskip("ibis")
    _ = pytest.importorskip("duckdb")

    from circe.execution.build_context import BuildContext, CohortBuildOptions

    conn = ibis.duckdb.connect()
    conn.create_table(
        "codesets",
        obj=ibis.memtable({"codeset_id": [0], "concept_id": [0]}),
        overwrite=True,
    )
    ctx = BuildContext(
        conn,
        CohortBuildOptions(
            materialize_stages=False,
            materialize_codesets=False,
            trace_steps=True,
            trace_dir=str(tmp_path),
        ),
        conn.table("codesets"),
    )

    expr = ibis.memtable({"x": [1]})
    ctx.trace_step(expr, label="payload_step")

    trace_files = sorted(tmp_path.glob("ibis_trace_*.jsonl"))
    assert len(trace_files) == 1
    payload = json.loads(trace_files[0].read_text(encoding="utf-8").splitlines()[0])
    assert payload["label"] == "payload_step"
    assert payload["step_key"] == "payload_step"
