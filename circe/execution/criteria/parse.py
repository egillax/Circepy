from __future__ import annotations

from enum import IntEnum
from typing import Any

from ...cohortdefinition.criteria import (
    ConditionEra,
    ConditionOccurrence,
    CorelatedCriteria,
    Criteria,
    Death,
    DemographicCriteria,
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

CorrelatedCriteria = CorelatedCriteria
DemoGraphicCriteria = DemographicCriteria


class OccurrenceType(IntEnum):
    EXACTLY = 0
    AT_MOST = 1
    AT_LEAST = 2


CRITERIA_TYPE_MAP: dict[str, type[Criteria]] = {
    "ConditionOccurrence": ConditionOccurrence,
    "ConditionEra": ConditionEra,
    "VisitOccurrence": VisitOccurrence,
    "DrugExposure": DrugExposure,
    "DrugEra": DrugEra,
    "DoseEra": DoseEra,
    "ObservationPeriod": ObservationPeriod,
    "Measurement": Measurement,
    "Observation": Observation,
    "Specimen": Specimen,
    "DeviceExposure": DeviceExposure,
    "ProcedureOccurrence": ProcedureOccurrence,
    "Death": Death,
    "VisitDetail": VisitDetail,
    "PayerPlanPeriod": PayerPlanPeriod,
}
CRITERIA_TYPE_MAP_CASEFOLD: dict[str, type[Criteria]] = {
    name.casefold(): model for name, model in CRITERIA_TYPE_MAP.items()
}


def parse_single_criteria(criteria_dict: Any) -> Criteria:
    if isinstance(criteria_dict, Criteria):
        return criteria_dict

    if not isinstance(criteria_dict, dict):
        raise ValueError("Criteria wrapper must be an object.")

    if len(criteria_dict) != 1:
        raise ValueError("Criteria wrapper must contain exactly one criteria type key.")

    criteria_type, criteria_data = next(iter(criteria_dict.items()))
    model_cls = CRITERIA_TYPE_MAP.get(criteria_type)
    if model_cls is None and isinstance(criteria_type, str):
        model_cls = CRITERIA_TYPE_MAP_CASEFOLD.get(criteria_type.casefold())
    if model_cls is None:
        raise ValueError(f"Unsupported criteria type: {criteria_type}")

    if criteria_data is None:
        criteria_data = {}

    if not isinstance(criteria_data, dict):
        raise ValueError(f"Criteria payload for {criteria_type} must be an object.")

    return model_cls.model_validate(criteria_data, strict=False)


def parse_criteria_list(criteria_list_data: Any) -> list[Criteria]:
    if criteria_list_data is None:
        return []

    if not isinstance(criteria_list_data, list):
        raise ValueError("Criteria list must be a list.")

    criteria_instances: list[Criteria] = []
    for idx, criteria_dict in enumerate(criteria_list_data):
        try:
            parsed = parse_single_criteria(criteria_dict)
        except ValueError as exc:
            raise ValueError(f"Invalid criteria wrapper at index {idx}: {exc}") from exc
        criteria_instances.append(parsed)
    return criteria_instances

