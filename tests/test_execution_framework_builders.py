from __future__ import annotations

import datetime as dt

import pytest


def _d(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


def _create_person(conn, ibis) -> None:
    conn.create_table(
        "person",
        obj=ibis.memtable(
            {
                "person_id": [1, 2],
                "year_of_birth": [1980, 1990],
                "gender_concept_id": [0, 0],
            }
        ),
        overwrite=True,
    )


def _create_codesets(conn, ibis, *, rows: list[tuple[int, int]] | None = None) -> None:
    rows = rows or [(0, 0)]
    conn.create_table(
        "codesets",
        obj=ibis.memtable(
            {
                "codeset_id": [r[0] for r in rows],
                "concept_id": [r[1] for r in rows],
            }
        ),
        overwrite=True,
    )


def _ctx(conn):
    from circe.execution.build_context import BuildContext, CohortBuildOptions

    options = CohortBuildOptions(materialize_stages=False, materialize_codesets=False)
    return BuildContext(conn, options, conn.table("codesets"))


@pytest.mark.parametrize(
    "criteria, table_name, row",
    [
        pytest.param(
            "ConditionOccurrence",
            "condition_occurrence",
            {
                "person_id": [1],
                "condition_occurrence_id": [100],
                "condition_concept_id": [111],
                "condition_start_date": [_d("2020-01-01")],
                "condition_end_date": [_d("2020-01-02")],
            },
            id="ConditionOccurrence",
        ),
        pytest.param(
            "ConditionEra",
            "condition_era",
            {
                "person_id": [1],
                "condition_era_id": [101],
                "condition_concept_id": [111],
                "condition_era_start_date": [_d("2020-01-01")],
                "condition_era_end_date": [_d("2020-01-03")],
            },
            id="ConditionEra",
        ),
        pytest.param(
            "DrugExposure",
            "drug_exposure",
            {
                "person_id": [1],
                "drug_exposure_id": [200],
                "drug_concept_id": [222],
                "drug_exposure_start_date": [_d("2020-02-01")],
                "drug_exposure_end_date": [_d("2020-02-10")],
            },
            id="DrugExposure",
        ),
        pytest.param(
            "DrugEra",
            "drug_era",
            {
                "person_id": [1],
                "drug_era_id": [201],
                "drug_concept_id": [222],
                "drug_era_start_date": [_d("2020-02-01")],
                "drug_era_end_date": [_d("2020-02-10")],
            },
            id="DrugEra",
        ),
        pytest.param(
            "DoseEra",
            "dose_era",
            {
                "person_id": [1],
                "dose_era_id": [202],
                "drug_concept_id": [222],
                "dose_era_start_date": [_d("2020-02-01")],
                "dose_era_end_date": [_d("2020-02-10")],
            },
            id="DoseEra",
        ),
        pytest.param(
            "DeviceExposure",
            "device_exposure",
            {
                "person_id": [1],
                "device_exposure_id": [300],
                "device_concept_id": [333],
                "device_exposure_start_date": [_d("2020-03-01")],
                "device_exposure_end_date": [_d("2020-03-02")],
            },
            id="DeviceExposure",
        ),
        pytest.param(
            "Measurement",
            "measurement",
            {
                "person_id": [1],
                "measurement_id": [400],
                "measurement_concept_id": [444],
                "measurement_date": [_d("2020-04-01")],
            },
            id="Measurement",
        ),
        pytest.param(
            "Observation",
            "observation",
            {
                "person_id": [1],
                "observation_id": [500],
                "observation_concept_id": [555],
                "observation_date": [_d("2020-05-01")],
            },
            id="Observation",
        ),
        pytest.param(
            "ProcedureOccurrence",
            "procedure_occurrence",
            {
                "person_id": [1],
                "procedure_occurrence_id": [600],
                "procedure_concept_id": [666],
                "procedure_date": [_d("2020-06-01")],
            },
            id="ProcedureOccurrence",
        ),
        pytest.param(
            "ObservationPeriod",
            "observation_period",
            {
                "person_id": [1],
                "observation_period_id": [700],
                "observation_period_start_date": [_d("2020-01-01")],
                "observation_period_end_date": [_d("2020-12-31")],
            },
            id="ObservationPeriod",
        ),
        pytest.param(
            "PayerPlanPeriod",
            "payer_plan_period",
            {
                "person_id": [1],
                "payer_plan_period_id": [800],
                "payer_concept_id": [777],
                "payer_plan_period_start_date": [_d("2020-01-01")],
                "payer_plan_period_end_date": [_d("2020-12-31")],
            },
            id="PayerPlanPeriod",
        ),
        pytest.param(
            "Specimen",
            "specimen",
            {
                "person_id": [1],
                "specimen_id": [900],
                "specimen_concept_id": [888],
                "specimen_date": [_d("2020-07-01")],
            },
            id="Specimen",
        ),
        pytest.param(
            "VisitOccurrence",
            "visit_occurrence",
            {
                "person_id": [1],
                "visit_occurrence_id": [1000],
                "visit_concept_id": [999],
                "visit_start_date": [_d("2020-08-01")],
                "visit_end_date": [_d("2020-08-02")],
            },
            id="VisitOccurrence",
        ),
        pytest.param(
            "VisitDetail",
            "visit_detail",
            {
                "person_id": [1],
                "visit_detail_id": [1100],
                "visit_occurrence_id": [1000],
                "visit_detail_concept_id": [999],
                "visit_detail_start_date": [_d("2020-08-01")],
                "visit_detail_end_date": [_d("2020-08-01")],
            },
            id="VisitDetail",
        ),
        pytest.param(
            "Death",
            "death",
            {
                "person_id": [1],
                "death_date": [_d("2020-09-01")],
                "cause_concept_id": [111],
                "cause_source_concept_id": [0],
                "death_type_concept_id": [0],
            },
            id="Death",
        ),
    ],
)
def test_framework_builders_smoke_minimal_schema(criteria, table_name, row):
    ibis = pytest.importorskip("ibis")
    _ = pytest.importorskip("duckdb")

    conn = ibis.duckdb.connect()

    # Ensure the execution builder registry is populated.
    from circe.cohortdefinition.criteria import (
        ConditionEra,
        ConditionOccurrence,
        Death,
        DeviceExposure,
        DoseEra,
        DrugEra,
        DrugExposure,
        Measurement,
        Observation,
        ObservationPeriod,
        PayerPlanPeriod,
        ProcedureOccurrence,
        Specimen,
        VisitDetail,
        VisitOccurrence,
    )
    from circe.execution.builders import pipeline as _pipeline  # noqa: F401
    from circe.execution.builders.registry import get_builder

    criteria_map = {
        "ConditionOccurrence": ConditionOccurrence,
        "ConditionEra": ConditionEra,
        "DrugExposure": DrugExposure,
        "DrugEra": DrugEra,
        "DoseEra": DoseEra,
        "DeviceExposure": DeviceExposure,
        "Measurement": Measurement,
        "Observation": Observation,
        "ProcedureOccurrence": ProcedureOccurrence,
        "ObservationPeriod": ObservationPeriod,
        "PayerPlanPeriod": PayerPlanPeriod,
        "Specimen": Specimen,
        "VisitOccurrence": VisitOccurrence,
        "VisitDetail": VisitDetail,
        "Death": Death,
    }

    _create_person(conn, ibis)
    _create_codesets(conn, ibis)
    conn.create_table(table_name, obj=ibis.memtable(row), overwrite=True)

    ctx = _ctx(conn)
    try:
        criteria_obj = criteria_map[criteria]()
        builder = get_builder(criteria_obj)
        events = builder(criteria_obj, ctx)
        result = events.execute()
    finally:
        ctx.close()

    assert set(result.columns) == {
        "person_id",
        "event_id",
        "start_date",
        "end_date",
        "visit_occurrence_id",
    }
    assert len(result) == 1


def test_standardize_output_missing_end_column_raises():
    ibis = pytest.importorskip("ibis")
    _ = pytest.importorskip("duckdb")

    conn = ibis.duckdb.connect()

    from circe.cohortdefinition.criteria import ConditionOccurrence
    from circe.execution.builders import pipeline as _pipeline  # noqa: F401
    from circe.execution.builders.registry import get_builder

    _create_person(conn, ibis)
    _create_codesets(conn, ibis)
    conn.create_table(
        "condition_occurrence",
        obj=ibis.memtable(
            {
                "person_id": [1],
                "condition_occurrence_id": [100],
                "condition_concept_id": [111],
                "condition_start_date": [_d("2020-01-01")],
            }
        ),
        overwrite=True,
    )

    ctx = _ctx(conn)
    try:
        criteria = ConditionOccurrence()
        builder = get_builder(criteria)
        with pytest.raises(
            ValueError, match="Configured end column `condition_end_date`"
        ):
            _ = builder(criteria, ctx).execute()
    finally:
        ctx.close()


def test_death_occurrence_end_date_applies():
    ibis = pytest.importorskip("ibis")
    _ = pytest.importorskip("duckdb")

    from circe.cohortdefinition.core import DateRange
    from circe.cohortdefinition.criteria import Death
    from circe.execution.builders import pipeline as _pipeline  # noqa: F401
    from circe.execution.builders.registry import get_builder

    conn = ibis.duckdb.connect()
    _create_person(conn, ibis)
    _create_codesets(conn, ibis)
    conn.create_table(
        "death",
        obj=ibis.memtable(
            {
                "person_id": [1, 2],
                "death_date": [_d("2020-01-01"), _d("2020-06-01")],
                "cause_concept_id": [111, 111],
                "cause_source_concept_id": [0, 0],
                "death_type_concept_id": [0, 0],
            }
        ),
        overwrite=True,
    )

    ctx = _ctx(conn)
    try:
        criteria = Death(occurrence_end_date=DateRange(op="lt", value="2020-03-01"))
        builder = get_builder(criteria)
        result = builder(criteria, ctx).execute()
    finally:
        ctx.close()

    assert set(result.person_id) == {1}
    assert (result.event_id == result.person_id).all()
    assert result[["person_id", "event_id"]].duplicated().sum() == 0
    assert ((result["end_date"] - result["start_date"]).dt.days == 1).all()


def test_death_cause_source_concept_codeset_filter_applies():
    ibis = pytest.importorskip("ibis")
    _ = pytest.importorskip("duckdb")

    from circe.cohortdefinition.criteria import Death
    from circe.execution.builders import pipeline as _pipeline  # noqa: F401
    from circe.execution.builders.registry import get_builder

    conn = ibis.duckdb.connect()
    try:
        _create_person(conn, ibis)
        _create_codesets(conn, ibis, rows=[(50, 900)])
        conn.create_table(
            "death",
            obj=ibis.memtable(
                {
                    "person_id": [1, 2],
                    "death_date": [_d("2020-01-01"), _d("2020-01-01")],
                    "cause_concept_id": [111, 111],
                    "cause_source_concept_id": [900, 901],
                    "death_type_concept_id": [0, 0],
                }
            ),
            overwrite=True,
        )

        ctx = _ctx(conn)
        try:
            criteria = Death(cause_source_concept=50)
            builder = get_builder(criteria)
            result = builder(criteria, ctx).execute()
        finally:
            ctx.close()
    finally:
        conn.disconnect()

    assert set(result.person_id) == {1}
    assert (result.event_id == result.person_id).all()
    assert result[["person_id", "event_id"]].duplicated().sum() == 0
    assert ((result["end_date"] - result["start_date"]).dt.days == 1).all()


def test_death_empty_cause_source_concept_cs_does_not_override_filter():
    ibis = pytest.importorskip("ibis")
    _ = pytest.importorskip("duckdb")

    from circe.cohortdefinition.core import ConceptSetSelection
    from circe.cohortdefinition.criteria import Death
    from circe.execution.builders import pipeline as _pipeline  # noqa: F401
    from circe.execution.builders.registry import get_builder

    conn = ibis.duckdb.connect()
    try:
        _create_person(conn, ibis)
        _create_codesets(conn, ibis, rows=[(50, 900)])
        conn.create_table(
            "death",
            obj=ibis.memtable(
                {
                    "person_id": [1, 2],
                    "death_date": [_d("2020-01-01"), _d("2020-01-01")],
                    "cause_concept_id": [111, 111],
                    "cause_source_concept_id": [900, 901],
                    "death_type_concept_id": [0, 0],
                }
            ),
            overwrite=True,
        )

        ctx = _ctx(conn)
        try:
            criteria = Death(
                cause_source_concept=50,
                cause_source_concept_cs=ConceptSetSelection(codeset_id=None),
            )
            builder = get_builder(criteria)
            result = builder(criteria, ctx).execute()
        finally:
            ctx.close()
    finally:
        conn.disconnect()

    assert set(result.person_id) == {1}
    assert (result.event_id == result.person_id).all()
    assert result[["person_id", "event_id"]].duplicated().sum() == 0
    assert ((result["end_date"] - result["start_date"]).dt.days == 1).all()


def test_specimen_occurrence_end_date_applies():
    ibis = pytest.importorskip("ibis")
    _ = pytest.importorskip("duckdb")

    from circe.cohortdefinition.core import DateRange
    from circe.cohortdefinition.criteria import Specimen
    from circe.execution.builders import pipeline as _pipeline  # noqa: F401
    from circe.execution.builders.registry import get_builder

    conn = ibis.duckdb.connect()
    _create_person(conn, ibis)
    _create_codesets(conn, ibis)
    conn.create_table(
        "specimen",
        obj=ibis.memtable(
            {
                "person_id": [1, 2],
                "specimen_id": [900, 901],
                "specimen_concept_id": [888, 888],
                "specimen_date": [_d("2020-01-01"), _d("2020-06-01")],
            }
        ),
        overwrite=True,
    )

    ctx = _ctx(conn)
    try:
        criteria = Specimen(occurrence_end_date=DateRange(op="lt", value="2020-03-01"))
        builder = get_builder(criteria)
        result = builder(criteria, ctx).execute()
    finally:
        ctx.close()

    assert set(result.person_id) == {1}
    assert set(result.event_id) == {900}
    assert result[["person_id", "event_id"]].duplicated().sum() == 0
    assert ((result["end_date"] - result["start_date"]).dt.days == 1).all()


def test_apply_date_range_timestamp_between_casts():
    ibis = pytest.importorskip("ibis")
    _ = pytest.importorskip("duckdb")

    from circe.cohortdefinition.core import DateRange
    from circe.execution.builders.common import apply_date_range

    conn = ibis.duckdb.connect()
    try:
        conn.create_table(
            "events",
            obj=ibis.memtable(
                {
                    "event_id": [1, 2, 3, 4],
                    "ts": [
                        dt.datetime(2020, 1, 1, 0, 0, 0),
                        dt.datetime(2020, 1, 2, 0, 0, 0),
                        dt.datetime(2020, 1, 3, 0, 0, 0),
                        dt.datetime(2020, 1, 3, 0, 0, 1),
                    ],
                }
            ),
            overwrite=True,
        )

        table = conn.table("events")
        filtered = apply_date_range(
            table, "ts", DateRange(op="bt", value="2020-01-02", extent="2020-01-03")
        )
        result = filtered.execute()
        assert set(result.event_id) == {2, 3}

        negated = apply_date_range(
            table, "ts", DateRange(op="!bt", value="2020-01-02", extent="2020-01-03")
        )
        negated_result = negated.execute()
        assert set(negated_result.event_id) == {1, 4}
    finally:
        disconnect = getattr(conn, "disconnect", None)
        if disconnect is not None:
            disconnect()
