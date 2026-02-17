"""Plugin contracts for optional execution outputs.

This module intentionally depends only on the Python stdlib so that the core
package can remain free of optional dataframe / IO dependencies (polars, pyarrow,
etc.). Plugins are discovered lazily via entry points.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional, Protocol

Params = Mapping[str, Any]

COLLECTOR_ENTRYPOINT_GROUP = "circe.execution.collectors"
SINK_ENTRYPOINT_GROUP = "circe.execution.sinks"


def list_collectors() -> list[str]:
    from .plugin_loader import list_plugins

    return list_plugins(COLLECTOR_ENTRYPOINT_GROUP)


def list_sinks() -> list[str]:
    from .plugin_loader import list_plugins

    return list_plugins(SINK_ENTRYPOINT_GROUP)


class Collector(Protocol):
    """Materialize an ibis relation into an in-process object."""

    def __call__(
        self,
        *,
        executor: "IbisExecutor",
        table: Any,
        params: Optional[Params] = None,
    ) -> Any: ...


class Sink(Protocol):
    """Write an ibis relation to an external destination."""

    def __call__(
        self,
        *,
        executor: "IbisExecutor",
        table: Any,
        params: Optional[Params] = None,
    ) -> Any: ...
