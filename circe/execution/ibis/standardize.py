from __future__ import annotations

import ibis

from ..plan.events import EventSource
from ..plan.schema import (
    CONCEPT_ID,
    CRITERION_INDEX,
    CRITERION_TYPE,
    DAYS_SUPPLY,
    DOMAIN,
    DURATION,
    END_DATE,
    EVENT_ID,
    GAP_DAYS,
    OCCURRENCE_COUNT,
    PERSON_ID,
    QUANTITY,
    RANGE_HIGH,
    RANGE_LOW,
    REFILLS,
    SOURCE_CONCEPT_ID,
    SOURCE_TABLE,
    START_DATE,
    UNIT_CONCEPT_ID,
    VALUE_AS_NUMBER,
    VISIT_DETAIL_ID,
    VISIT_OCCURRENCE_ID,
)


def _typed_optional_column(table, column_name: str | None, dtype: str):
    if column_name and column_name in table.columns:
        return table[column_name].cast(dtype)
    return ibis.null().cast(dtype)


def _duration_expr(table, *, source: EventSource):
    if source.table_name in {"measurement", "observation"}:
        return ibis.null().cast("int64")
    if source.table_name in {"death", "specimen"}:
        return ibis.literal(1, type="int64")

    start_expr = table[source.start_date_column].cast("date")
    end_expr = table[source.end_date_column].cast("date")
    return end_expr.delta(start_expr, unit="day").cast("int64")


def _supplemental_exprs(table, *, source: EventSource) -> dict[str, object]:
    value_as_number_expr = _typed_optional_column(table, "value_as_number", "float64")
    if source.table_name == "dose_era" and "dose_value" in table.columns:
        value_as_number_expr = table["dose_value"].cast("float64")

    unit_concept_expr = _typed_optional_column(table, "unit_concept_id", "int64")
    if source.table_name == "drug_exposure" and "dose_unit_concept_id" in table.columns:
        unit_concept_expr = table["dose_unit_concept_id"].cast("int64")

    occurrence_count_expr = ibis.null().cast("int64")
    if "occurrence_count" in table.columns:
        occurrence_count_expr = table["occurrence_count"].cast("int64")
    elif "condition_occurrence_count" in table.columns:
        occurrence_count_expr = table["condition_occurrence_count"].cast("int64")
    elif "drug_exposure_count" in table.columns:
        occurrence_count_expr = table["drug_exposure_count"].cast("int64")

    return {
        QUANTITY: _typed_optional_column(table, "quantity", "float64"),
        DAYS_SUPPLY: _typed_optional_column(table, "days_supply", "float64"),
        REFILLS: _typed_optional_column(table, "refills", "float64"),
        RANGE_LOW: _typed_optional_column(table, "range_low", "float64"),
        RANGE_HIGH: _typed_optional_column(table, "range_high", "float64"),
        VALUE_AS_NUMBER: value_as_number_expr,
        UNIT_CONCEPT_ID: unit_concept_expr,
        VISIT_DETAIL_ID: _typed_optional_column(table, "visit_detail_id", "int64"),
        OCCURRENCE_COUNT: occurrence_count_expr,
        GAP_DAYS: _typed_optional_column(table, "gap_days", "int64"),
        DURATION: _duration_expr(table, source=source),
    }


def standardize_event_table(
    table,
    *,
    source: EventSource,
    criterion_type: str,
    criterion_index: int,
):
    concept_expr = ibis.null().cast("int64")
    if source.concept_column and source.concept_column in table.columns:
        concept_expr = table[source.concept_column].cast("int64")

    source_concept_expr = ibis.null().cast("int64")
    if source.source_concept_column and source.source_concept_column in table.columns:
        source_concept_expr = table[source.source_concept_column].cast("int64")

    visit_occ_expr = ibis.null().cast("int64")
    if source.visit_occurrence_column and source.visit_occurrence_column in table.columns:
        visit_occ_expr = table[source.visit_occurrence_column].cast("int64")

    supplemental_exprs = _supplemental_exprs(table, source=source)
    standardized = table.select(
        table[source.person_id_column].cast("int64").name(PERSON_ID),
        table[source.event_id_column].cast("int64").name(EVENT_ID),
        table[source.start_date_column].cast("date").name(START_DATE),
        table[source.end_date_column].cast("date").name(END_DATE),
        ibis.literal(source.domain).name(DOMAIN),
        concept_expr.name(CONCEPT_ID),
        source_concept_expr.name(SOURCE_CONCEPT_ID),
        visit_occ_expr.name(VISIT_OCCURRENCE_ID),
        supplemental_exprs[VISIT_DETAIL_ID].name(VISIT_DETAIL_ID),
        supplemental_exprs[QUANTITY].name(QUANTITY),
        supplemental_exprs[DAYS_SUPPLY].name(DAYS_SUPPLY),
        supplemental_exprs[REFILLS].name(REFILLS),
        supplemental_exprs[RANGE_LOW].name(RANGE_LOW),
        supplemental_exprs[RANGE_HIGH].name(RANGE_HIGH),
        supplemental_exprs[VALUE_AS_NUMBER].name(VALUE_AS_NUMBER),
        supplemental_exprs[UNIT_CONCEPT_ID].name(UNIT_CONCEPT_ID),
        supplemental_exprs[OCCURRENCE_COUNT].name(OCCURRENCE_COUNT),
        supplemental_exprs[GAP_DAYS].name(GAP_DAYS),
        supplemental_exprs[DURATION].name(DURATION),
        ibis.literal(int(criterion_index), type="int64").name(CRITERION_INDEX),
        ibis.literal(criterion_type).name(CRITERION_TYPE),
        ibis.literal(source.table_name).name(SOURCE_TABLE),
    )
    return standardized
