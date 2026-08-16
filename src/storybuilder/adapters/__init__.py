"""Adapter registry and selection (explicit ``--format`` or auto-detection).

Adapters are auto-discovered: drop a module in this package with a
``FeedAdapter`` subclass that sets a non-empty ``name`` and it is registered
automatically (mirroring how sport profiles are discovered) - there is no list
to edit. Auto-detection order is by ascending ``priority`` (more specific
adapters set a lower number), then by ``name`` for determinism.
"""

from __future__ import annotations

import importlib
import pkgutil

from .base import FeedAdapter

# Import every submodule so their FeedAdapter subclasses are defined and can be
# discovered below (skip private/dunder modules).
for _mod in pkgutil.iter_modules(__path__):
    if not _mod.name.startswith("_") and _mod.name != "base":
        importlib.import_module(f"{__name__}.{_mod.name}")


def _all_subclasses(cls: type) -> list[type]:
    found: list[type] = []
    for sub in cls.__subclasses__():
        found.append(sub)
        found.extend(_all_subclasses(sub))
    return found


def _adapters() -> list[type[FeedAdapter]]:
    named = [a for a in _all_subclasses(FeedAdapter) if getattr(a, "name", "")]
    return sorted(named, key=lambda a: (getattr(a, "priority", 100), a.name))


def available_formats() -> list[str]:
    return [a.name for a in _adapters()]


def get_adapter(raw: dict, fmt: str | None = None) -> FeedAdapter:
    """Return an adapter instance.

    If ``fmt`` is given it is used directly; otherwise the first adapter whose
    :meth:`can_parse` recognizes the feed wins.
    """
    adapters = _adapters()

    if fmt:
        for adapter in adapters:
            if adapter.name == fmt:
                return adapter()
        raise ValueError(f"Unknown feed format {fmt!r}. Available: {', '.join(available_formats())}")

    for adapter in adapters:
        if adapter.can_parse(raw):
            return adapter()
    raise ValueError(
        "Could not auto-detect feed format. " f"Pass --format with one of: {', '.join(available_formats())}"
    )


__all__ = ["FeedAdapter", "get_adapter", "available_formats"]
