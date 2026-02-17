from __future__ import annotations

import pytest


def test_capture_sql_does_not_fail_when_compile_fails(monkeypatch):
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
            materialize_stages=True,
            materialize_codesets=False,
            capture_sql=True,
        ),
        conn.table("codesets"),
    )

    def _boom(_expr):
        raise RuntimeError("compile failed")

    monkeypatch.setattr(conn, "compile", _boom)

    expr = ibis.memtable({"x": [1]})
    table = ctx.materialize(expr, label="compile_fail_test", analyze=False)

    assert table is not None
    assert ctx.captured_sql() == []

