"""Adapter registry and selection (explicit ``--format`` or auto-detection)."""

from __future__ import annotations

from .base import FeedAdapter
from .opta_soccer import OptaSoccerAdapter

#: All known adapters, in auto-detection priority order.
_ADAPTERS: list[type[FeedAdapter]] = [OptaSoccerAdapter]


def available_formats() -> list[str]:
    return [a.name for a in _ADAPTERS]


def get_adapter(raw: dict, fmt: str | None = None) -> FeedAdapter:
    """Return an adapter instance.

    If ``fmt`` is given it is used directly; otherwise the first adapter whose
    :meth:`can_parse` recognizes the feed wins.
    """

    if fmt:
        for adapter in _ADAPTERS:
            if adapter.name == fmt:
                return adapter()
        raise ValueError(
            f"Unknown feed format {fmt!r}. Available: {', '.join(available_formats())}"
        )

    for adapter in _ADAPTERS:
        if adapter.can_parse(raw):
            return adapter()
    raise ValueError(
        "Could not auto-detect feed format. "
        f"Pass --format with one of: {', '.join(available_formats())}"
    )


__all__ = ["FeedAdapter", "get_adapter", "available_formats"]
