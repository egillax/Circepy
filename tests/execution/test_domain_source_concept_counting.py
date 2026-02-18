from __future__ import annotations

import pytest

from circe.cohortdefinition.criteria import CriteriaColumn, Specimen, VisitDetail
from circe.execution.build_context import BuildContext, CohortBuildOptions
from circe.execution.builders.groups import _attach_count_columns


def _ctx_with_codesets(conn, ibis) -> BuildContext:
    conn.create_table(
        "codesets",
        obj=ibis.memtable({"codeset_id": [0], "concept_id": [0]}),
        overwrite=True,
    )
    return BuildContext(
        conn,
        CohortBuildOptions(materialize_stages=False, materialize_codesets=False),
        conn.table("codesets"),
    )


def test_attach_count_columns_picks_visit_detail_source_column():
    ibis = pytest.importorskip("ibis")
    _ = pytest.importorskip("duckdb")

    conn = ibis.duckdb.connect()
    ctx = _ctx_with_codesets(conn, ibis)

    conn.create_table(
        "visit_detail",
        obj=ibis.memtable(
            {
                "visit_detail_id": [1],
                "visit_detail_source_concept_id": [100],
                "visit_source_concept_id": [999],
            }
        ),
        overwrite=True,
    )

    events = ibis.memtable({"person_id": [1], "event_id": [1]})

    augmented = _attach_count_columns(
        events,
        VisitDetail(),
        ctx,
        count_column_name="_corr_domain_source_concept_id",
        count_column_enum=CriteriaColumn.DOMAIN_SOURCE_CONCEPT,
    )

    result = augmented.execute().to_dict(orient="list")
    assert result["_corr_domain_source_concept_id"] == [100]


def test_attach_count_columns_raises_when_source_concept_missing():
    ibis = pytest.importorskip("ibis")
    _ = pytest.importorskip("duckdb")

    conn = ibis.duckdb.connect()
    ctx = _ctx_with_codesets(conn, ibis)

    conn.create_table(
        "specimen",
        obj=ibis.memtable(
            {
                "specimen_id": [1],
            }
        ),
        overwrite=True,
    )

    events = ibis.memtable({"person_id": [1], "event_id": [1]})

    with pytest.raises(ValueError, match="DOMAIN_SOURCE_CONCEPT"):
        _attach_count_columns(
            events,
            Specimen(),
            ctx,
            count_column_name="_corr_domain_source_concept_id",
            count_column_enum=CriteriaColumn.DOMAIN_SOURCE_CONCEPT,
        )
