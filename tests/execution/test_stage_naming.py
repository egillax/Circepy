from __future__ import annotations

import re


def test_make_stage_name_portable_and_unique():
    import ibis

    from circe.execution.build_context import BuildContext, CohortBuildOptions

    conn = ibis.duckdb.connect()
    conn.create_table(
        "codesets",
        obj=ibis.memtable({"codeset_id": [0], "concept_id": [0]}),
        overwrite=True,
    )

    ctx = BuildContext(
        conn,
        CohortBuildOptions(materialize_stages=False, materialize_codesets=False),
        conn.table("codesets"),
    )

    names = [ctx.make_stage_name("DrugExposure.date_range") for _ in range(5)]
    assert len(set(names)) == len(names)
    assert all(len(name) <= 30 for name in names)
    assert all(re.match(r"^[a-z0-9_]+$", name) for name in names)

