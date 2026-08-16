"""Adapter interface: raw provider feed -> internal :class:`Match`.

An adapter isolates *all* knowledge of a particular feed format (field names,
ordering, string-vs-int quirks, id references). Add support for a new data
provider by writing a new adapter; the rest of the pipeline is untouched.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Match


class FeedAdapter(ABC):
    #: Stable identifier used by ``--format`` and the registry.
    name: str = ""
    #: Auto-detection order (ascending); lower = tried first / more specific.
    priority: int = 100

    @classmethod
    @abstractmethod
    def can_parse(cls, raw: dict) -> bool:
        """Return True if this adapter recognizes the raw feed's shape."""

    @abstractmethod
    def parse(self, raw: dict, squads: list[dict], *, source: str = "") -> Match:
        """Parse a raw feed (already JSON-decoded) into a :class:`Match`."""
