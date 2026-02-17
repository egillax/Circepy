"""Experimental ibis execution API."""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import TYPE_CHECKING, Any, List, Optional

from ..io import ExpressionInput, load_expression
from .plugin_loader import PluginNotFoundError, load_plugin
from .plugins import COLLECTOR_ENTRYPOINT_GROUP, SINK_ENTRYPOINT_GROUP
from .options import ExecutionOptions, SchemaName, schema_to_str

if TYPE_CHECKING:
    from .build_context import TraceEvent

logger = logging.getLogger(__name__)


class IbisExecutor:
    """Execute cohort expressions against an ibis backend.

    Notes:
    - This API is experimental.
    - `build()` returns an ibis table expression (lazy relation).
    - Materialization happens in `to_polars()` / `to_pandas()` / `write()`.
    """

    def __init__(self, conn: Any, options: Optional[ExecutionOptions] = None):
        self._conn = conn
        self._options = options or ExecutionOptions()
        self._open_contexts: List[Any] = []

    @property
    def conn(self) -> Any:
        return self._conn

    @property
    def options(self) -> ExecutionOptions:
        return self._options

    def build(self, expression: ExpressionInput) -> Any:
        """Build a lazy ibis relation for the final cohort rows."""
        cohort_expression = load_expression(expression)
        self.close()
        return self._build_native(cohort_expression)

    def _collect(
        self,
        expression: ExpressionInput,
        *,
        name: str,
        fallback_method: str,
        install_hint: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        table = self.build(expression)
        try:
            collector = load_plugin(
                COLLECTOR_ENTRYPOINT_GROUP,
                name,
                install_hint=install_hint,
            )
        except PluginNotFoundError:
            method = getattr(table, fallback_method, None)
            if callable(method):
                return method()
            raise
        return collector(executor=self, table=table, params=params)

    def to_polars(self, expression: ExpressionInput) -> Any:
        """Execute cohort expression and collect to Polars.

        Collection is handled by a collector plugin when installed, otherwise the
        underlying ibis backend's `to_polars()` support is used directly.
        """

        return self._collect(
            expression,
            name="polars",
            fallback_method="to_polars",
            install_hint=(
                "Install `ohdsi-circe-python-alpha[polars]` to enable Polars collection."
            ),
        )

    def to_pandas(self, expression: ExpressionInput) -> Any:
        """Execute cohort expression and collect to pandas.

        Collection is handled by a collector plugin when installed, otherwise the
        underlying ibis backend's `to_pandas()` support is used directly.
        """

        return self._collect(
            expression,
            name="pandas",
            fallback_method="to_pandas",
            install_hint=(
                "Install a pandas collector plugin or ensure your ibis backend "
                "supports to_pandas()."
            ),
        )

    def to_sink(
        self,
        expression: ExpressionInput,
        *,
        name: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Execute cohort expression and write via a named sink plugin."""
        table = self.build(expression)
        sink = load_plugin(
            SINK_ENTRYPOINT_GROUP,
            name,
            install_hint=(
                "Install a sink plugin distribution providing this entry point."
            ),
        )
        return sink(executor=self, table=table, params=params)

    def write(
        self,
        expression: ExpressionInput,
        *,
        table: str,
        schema: Optional[SchemaName] = None,
        overwrite: bool = True,
        append: bool = False,
        cohort_id: Optional[int] = None,
    ) -> Any:
        """Persist cohort rows to a cohort table and return a backend table handle."""
        if append and overwrite:
            raise ValueError(
                "`append=True` and `overwrite=True` cannot be used together."
            )
        effective_cohort_id = (
            cohort_id if cohort_id is not None else self._options.cohort_id
        )
        if effective_cohort_id is None:
            raise ValueError(
                "cohort_id must be set (argument or ExecutionOptions.cohort_id) to write cohort rows."
            )
        cohort_expression = load_expression(expression)
        self.close()
        events, ctx = self._build_with_context_native(
            cohort_expression, cohort_id_override=effective_cohort_id
        )
        self._open_contexts.append(ctx)
        return ctx.write_cohort_table(
            events,
            table_name=table,
            database=schema_to_str(schema)
            or schema_to_str(self._options.result_schema),
            overwrite=overwrite,
            append=append,
        )

    def captured_sql(self) -> List[tuple[str, str]]:
        """Return captured staged SQL snippets when capture_sql is enabled."""
        captured: List[tuple[str, str]] = []
        for ctx in self._open_contexts:
            if hasattr(ctx, "captured_sql"):
                captured.extend(ctx.captured_sql())
        return captured

    def trace_events(self) -> List["TraceEvent"]:
        """Return step-level trace events when trace_steps is enabled."""
        events: List["TraceEvent"] = []
        for ctx in self._open_contexts:
            if hasattr(ctx, "trace_events"):
                events.extend(ctx.trace_events())
        return events

    def close(self) -> None:
        """Release temporary resources held by execution contexts."""
        while self._open_contexts:
            ctx = self._open_contexts.pop()
            try:
                ctx.close()
            except Exception as exc:
                logger.warning("failed to close execution context: %s", exc)

    def __enter__(self) -> "IbisExecutor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _build_native(self, cohort_expression: Any) -> Any:
        events, ctx = self._build_with_context_native(cohort_expression)
        self._open_contexts.append(ctx)
        return events

    def _build_with_context_native(
        self, cohort_expression: Any, cohort_id_override: Optional[int] = None
    ) -> Any:
        try:
            from .build_context import (
                BuildContext,
                CohortBuildOptions,
                compile_codesets,
            )
            from .builders.pipeline import build_primary_events
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Ibis execution requires optional dependencies. "
                "Install `ohdsi-circe-python-alpha[ibis]` plus a backend extra, "
                "for example `[ibis-duckdb]`."
            ) from exc

        backend = self._infer_backend_name(self._conn)
        options = CohortBuildOptions(
            cdm_schema=schema_to_str(self._options.cdm_schema),
            vocabulary_schema=schema_to_str(self._options.vocabulary_schema),
            result_schema=schema_to_str(self._options.result_schema),
            cohort_id=(
                cohort_id_override
                if cohort_id_override is not None
                else self._options.cohort_id
            ),
            materialize_stages=self._options.materialize_stages,
            materialize_codesets=self._options.materialize_codesets,
            temp_emulation_schema=schema_to_str(self._options.temp_emulation_schema),
            profile_dir=self._options.profile_dir,
            capture_sql=self._options.capture_sql,
            trace_steps=self._options.trace_steps,
            trace_sql=self._options.trace_sql,
            trace_dir=self._options.trace_dir,
            backend=backend,
        )
        resource = compile_codesets(
            self._conn, cohort_expression.concept_sets or [], options
        )
        ctx = BuildContext(self._conn, options, resource)
        events = build_primary_events(cohort_expression, ctx)
        if events is None:
            raise RuntimeError(
                "No primary events were generated for the supplied cohort expression."
            )
        return events, ctx

    @staticmethod
    def _infer_backend_name(conn: Any) -> Optional[str]:
        backend_name = getattr(conn, "name", None)
        if isinstance(backend_name, str) and backend_name:
            return backend_name.lower()
        class_name = conn.__class__.__name__.lower()
        if "duckdb" in class_name:
            return "duckdb"
        if "postgres" in class_name:
            return "postgres"
        if "databricks" in class_name:
            return "databricks"
        return None


def build_ibis(
    expression: ExpressionInput,
    conn: Any,
    options: Optional[ExecutionOptions] = None,
) -> Any:
    """Convenience wrapper for IbisExecutor.build()."""
    with IbisExecutor(conn, options) as executor:
        return executor.build(expression)


def to_polars(
    expression: ExpressionInput,
    conn: Any,
    options: Optional[ExecutionOptions] = None,
) -> Any:
    """Convenience wrapper for IbisExecutor.to_polars()."""
    with IbisExecutor(conn, options) as executor:
        return executor.to_polars(expression)


def write_cohort(
    expression: ExpressionInput,
    conn: Any,
    *,
    table: str,
    schema: Optional[SchemaName] = None,
    overwrite: bool = True,
    append: bool = False,
    cohort_id: Optional[int] = None,
    options: Optional[ExecutionOptions] = None,
) -> Any:
    """Convenience wrapper for IbisExecutor.write()."""
    effective_cohort_id = (
        cohort_id if cohort_id is not None else (options.cohort_id if options else None)
    )
    if effective_cohort_id is None:
        raise ValueError(
            "cohort_id must be set (argument or ExecutionOptions.cohort_id) to write cohort rows."
        )
    effective_options = options
    if cohort_id is not None:
        effective_options = replace(options or ExecutionOptions(), cohort_id=cohort_id)

    with IbisExecutor(conn, effective_options) as executor:
        return executor.write(
            expression,
            table=table,
            schema=schema,
            overwrite=overwrite,
            append=append,
            cohort_id=cohort_id,
        )
