from __future__ import annotations

from typing import Union

from ...cohortdefinition.criteria import Criteria

CriteriaRef = Union[Criteria, type[Criteria]]


_CONCEPT_ID_OVERRIDES: dict[str, str] = {
    "Death": "cause_concept_id",
    "DoseEra": "drug_concept_id",
    "VisitDetail": "visit_detail_concept_id",
}

_PRIMARY_KEY_OVERRIDES: dict[str, str] = {
    "Death": "person_id",
}

_START_DATE_OVERRIDES: dict[str, str] = {
    "ConditionEra": "condition_era_start_date",
    "DrugExposure": "drug_exposure_start_date",
    "Measurement": "measurement_date",
    "Observation": "observation_date",
    "DeviceExposure": "device_exposure_start_date",
    "ProcedureOccurrence": "procedure_date",
    "DrugEra": "drug_era_start_date",
    "DoseEra": "dose_era_start_date",
    "ObservationPeriod": "observation_period_start_date",
    "Specimen": "specimen_date",
    "Death": "death_date",
    "VisitDetail": "visit_detail_start_date",
    "PayerPlanPeriod": "payer_plan_period_start_date",
}

_END_DATE_OVERRIDES: dict[str, str] = {
    "ConditionEra": "condition_era_end_date",
    "DrugExposure": "drug_exposure_end_date",
    "Measurement": "measurement_date",
    "Observation": "observation_date",
    "DeviceExposure": "device_exposure_end_date",
    "ProcedureOccurrence": "procedure_date",
    "DrugEra": "drug_era_end_date",
    "DoseEra": "dose_era_end_date",
    "ObservationPeriod": "observation_period_end_date",
    "Specimen": "specimen_date",
    "Death": "death_date",
    "VisitDetail": "visit_detail_end_date",
    "PayerPlanPeriod": "payer_plan_period_end_date",
}

_SOURCE_CONCEPT_ID_OVERRIDES: dict[str, str] = {
    "Death": "cause_source_concept_id",
}


def _criteria_type(criteria: CriteriaRef) -> type[Criteria]:
    return criteria if isinstance(criteria, type) else type(criteria)


def to_snake_case(name: str) -> str:
    output: list[str] = []
    for idx, char in enumerate(name):
        if char.isupper() and idx > 0:
            output.append("_")
        output.append(char.lower())
    return "".join(output)


def table_name_for(criteria: CriteriaRef) -> str:
    cls = _criteria_type(criteria)
    return to_snake_case(cls.__name__)


def primary_key_column_for(criteria: CriteriaRef) -> str:
    cls_name = _criteria_type(criteria).__name__
    overridden = _PRIMARY_KEY_OVERRIDES.get(cls_name)
    if overridden:
        return overridden
    return f"{table_name_for(criteria)}_id"


def start_date_column_for(criteria: CriteriaRef) -> str:
    cls_name = _criteria_type(criteria).__name__
    overridden = _START_DATE_OVERRIDES.get(cls_name)
    if overridden:
        return overridden
    prefix = table_name_for(criteria).split("_")[0]
    return f"{prefix}_start_date"


def end_date_column_for(criteria: CriteriaRef) -> str:
    cls_name = _criteria_type(criteria).__name__
    overridden = _END_DATE_OVERRIDES.get(cls_name)
    if overridden:
        return overridden
    prefix = table_name_for(criteria).split("_")[0]
    return f"{prefix}_end_date"


def concept_id_column_for(criteria: CriteriaRef) -> str:
    cls_name = _criteria_type(criteria).__name__
    overridden = _CONCEPT_ID_OVERRIDES.get(cls_name)
    if overridden:
        return overridden
    prefix = table_name_for(criteria).split("_")[0]
    return f"{prefix}_concept_id"


def source_concept_id_column_for(criteria: CriteriaRef) -> str:
    candidates = source_concept_id_candidates_for(criteria)
    return candidates[0]


def source_concept_id_candidates_for(criteria: CriteriaRef) -> list[str]:
    """
    Return best-effort candidates for the CDM source concept column.

    This exists because CDM tables are not consistent:
    - most tables use a domain prefix: `drug_source_concept_id`
    - some use full table names: `visit_detail_source_concept_id`
    - Death uses `cause_source_concept_id`
    """

    cls_name = _criteria_type(criteria).__name__
    overridden = _SOURCE_CONCEPT_ID_OVERRIDES.get(cls_name)
    table_name = table_name_for(criteria)
    prefix = table_name.split("_")[0]
    candidates = [
        overridden,
        f"{table_name}_source_concept_id",
        f"{prefix}_source_concept_id",
    ]
    output: list[str] = []
    for name in candidates:
        if not name:
            continue
        if name in output:
            continue
        output.append(name)
    return output
