from __future__ import annotations

from typing import Any, Optional


def collect_polars(*, executor: Any, table: Any, params: Optional[dict[str, Any]] = None) -> Any:
    _ = executor
    _ = params
    method = getattr(table, "to_polars", None)
    if not callable(method):
        raise RuntimeError(
            "The returned ibis table does not support to_polars() on this backend."
        )
    try:
        return method()
    except ModuleNotFoundError as exc:
        if getattr(exc, "name", None) == "polars":
            raise RuntimeError(
                "Polars is not installed. Install `ohdsi-circe-python-alpha[polars]`."
            ) from exc
        raise

