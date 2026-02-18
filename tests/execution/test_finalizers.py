from __future__ import annotations

import gc
import weakref

import pytest

from circe.execution.build_context import (
    BuildContext,
    CohortBuildOptions,
    compile_codesets,
)


def test_build_context_finalizer_does_not_keep_context_alive():
    ibis = pytest.importorskip("ibis")
    _ = pytest.importorskip("duckdb")

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
    ref = weakref.ref(ctx)
    del ctx

    gc.collect()
    gc.collect()

    assert ref() is None


def test_codeset_resource_finalizer_does_not_keep_resource_alive():
    ibis = pytest.importorskip("ibis")
    _ = pytest.importorskip("duckdb")

    conn = ibis.duckdb.connect()
    conn.create_table(
        "concept",
        obj=ibis.memtable({"concept_id": [1], "invalid_reason": [""]}),
        overwrite=True,
    )
    conn.create_table(
        "concept_ancestor",
        obj=ibis.memtable({"ancestor_concept_id": [1], "descendant_concept_id": [1]}),
        overwrite=True,
    )
    conn.create_table(
        "concept_relationship",
        obj=ibis.memtable(
            {
                "concept_id_1": [1],
                "concept_id_2": [1],
                "relationship_id": ["Maps to"],
                "invalid_reason": [""],
            }
        ),
        overwrite=True,
    )

    resource = compile_codesets(
        conn,
        [],
        CohortBuildOptions(materialize_codesets=True),
    )
    ref = weakref.ref(resource)
    del resource

    gc.collect()
    gc.collect()

    assert ref() is None
