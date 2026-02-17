from __future__ import annotations

from circe.cohortdefinition.criteria import Death, DoseEra, VisitDetail
from circe.execution.criteria.resolve import (
    concept_id_column_for,
    end_date_column_for,
    primary_key_column_for,
    start_date_column_for,
    table_name_for,
)


def test_resolver_table_name():
    assert table_name_for(VisitDetail) == "visit_detail"


def test_resolver_primary_key_overrides():
    assert primary_key_column_for(Death) == "person_id"


def test_resolver_concept_overrides():
    assert concept_id_column_for(Death) == "cause_concept_id"
    assert concept_id_column_for(DoseEra) == "drug_concept_id"
    assert concept_id_column_for(VisitDetail) == "visit_detail_concept_id"


def test_resolver_date_overrides():
    assert start_date_column_for(Death) == "death_date"
    assert end_date_column_for(Death) == "death_date"
    assert start_date_column_for(VisitDetail) == "visit_detail_start_date"
    assert end_date_column_for(VisitDetail) == "visit_detail_end_date"

