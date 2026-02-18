"""Lazy entry point discovery for execution plugins."""

from __future__ import annotations

from importlib import metadata
from typing import Any, Dict, Iterable, List, Optional


class PluginNotFoundError(RuntimeError):
    def __init__(self, *, group: str, name: str, install_hint: Optional[str] = None):
        message = f"No plugin '{name}' installed for entry point group '{group}'."
        if install_hint:
            message = f"{message} {install_hint}"
        super().__init__(message)
        self.group = group
        self.name = name
        self.install_hint = install_hint


_CACHE: Dict[str, Dict[str, metadata.EntryPoint]] = {}


def _iter_entry_points(group: str) -> Iterable[metadata.EntryPoint]:
    eps = metadata.entry_points()
    select = getattr(eps, "select", None)
    if callable(select):
        return eps.select(group=group)
    return eps.get(group, [])


def list_plugins(group: str) -> List[str]:
    return sorted({ep.name for ep in _iter_entry_points(group)})


def load_plugin(group: str, name: str, *, install_hint: Optional[str] = None) -> Any:
    """Load a plugin object via entry points, importing it only when needed."""
    cached_group = _CACHE.get(group)
    if cached_group is None:
        cached_group = {ep.name: ep for ep in _iter_entry_points(group)}
        _CACHE[group] = cached_group

    ep = cached_group.get(name)
    if ep is None:
        raise PluginNotFoundError(group=group, name=name, install_hint=install_hint)
    return ep.load()


def clear_plugin_cache() -> None:
    _CACHE.clear()

