"""Execution options for backend-native cohort execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Union

SchemaName = Union[str, Tuple[str, str]]


@dataclass(frozen=True)
class ExecutionOptions:
    """Runtime options for backend execution via ibis.

    This API is experimental and may evolve while execution parity is built out.
    """

    cdm_schema: Optional[SchemaName] = None
    vocabulary_schema: Optional[SchemaName] = None
    result_schema: Optional[SchemaName] = None

    cohort_id: Optional[int] = None

    materialize_stages: bool = False
    materialize_codesets: bool = True
    temp_emulation_schema: Optional[SchemaName] = None

    capture_sql: bool = False
    profile_dir: Optional[str] = None

    trace_steps: bool = False
    trace_sql: bool = False
    trace_dir: Optional[str] = None
    # Probe `primary_events` with `limit(1)` to short-circuit downstream stages when empty.
    probe_empty_primary_events: bool = True


def schema_to_str(schema: Optional[SchemaName]) -> Optional[str]:
    """Normalize schema names to a string representation."""
    if schema is None:
        return None
    if isinstance(schema, tuple):
        return ".".join(schema)
    return schema
