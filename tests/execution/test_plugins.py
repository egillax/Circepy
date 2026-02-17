from __future__ import annotations

import pytest

from circe.execution.ibis import IbisExecutor
from circe.execution.plugin_loader import PluginNotFoundError
from circe.execution.plugins import COLLECTOR_ENTRYPOINT_GROUP


def test_to_polars_falls_back_to_backend_method(monkeypatch):
    class DummyTable:
        def to_polars(self):
            return "polars-result"

    executor = IbisExecutor(object())
    monkeypatch.setattr(executor, "build", lambda _: DummyTable())

    def _no_plugin(*args, **kwargs):
        raise PluginNotFoundError(group=COLLECTOR_ENTRYPOINT_GROUP, name="polars")

    monkeypatch.setattr("circe.execution.ibis.load_plugin", _no_plugin)

    assert executor.to_polars({"Title": "dummy"}) == "polars-result"


def test_to_polars_uses_plugin_when_installed(monkeypatch):
    class DummyTable:
        def to_polars(self):
            raise AssertionError("backend fallback should not be used")

    executor = IbisExecutor(object())
    monkeypatch.setattr(executor, "build", lambda _: DummyTable())

    def _collector(*, executor, table, params=None):
        assert params is None
        assert hasattr(table, "to_polars")
        return "plugin-polars"

    monkeypatch.setattr("circe.execution.ibis.load_plugin", lambda *a, **k: _collector)

    assert executor.to_polars({"Title": "dummy"}) == "plugin-polars"


def test_to_polars_raises_when_no_plugin_and_no_backend_support(monkeypatch):
    class DummyTable:
        pass

    executor = IbisExecutor(object())
    monkeypatch.setattr(executor, "build", lambda _: DummyTable())

    def _no_plugin(*args, **kwargs):
        raise PluginNotFoundError(
            group=COLLECTOR_ENTRYPOINT_GROUP, name="polars", install_hint="install it"
        )

    monkeypatch.setattr("circe.execution.ibis.load_plugin", _no_plugin)

    with pytest.raises(PluginNotFoundError, match="No plugin 'polars' installed"):
        executor.to_polars({"Title": "dummy"})

