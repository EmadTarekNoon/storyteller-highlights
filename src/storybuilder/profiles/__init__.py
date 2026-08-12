"""Profile registry: auto-discovers every SportProfile in this package.

To add a sport you only need to drop a new module in this package with a
`SportProfile` subclass that sets a non-empty ``handles``. It is imported and
registered automatically here - there is no list to edit.
"""

from __future__ import annotations

import importlib
import pkgutil

from .base import SportProfile
from .generic import GenericProfile

# Import every submodule so their SportProfile subclasses are defined and can be
# discovered below (skip private/dunder modules).
for _mod in pkgutil.iter_modules(__path__):
    if not _mod.name.startswith("_"):
        importlib.import_module(f"{__name__}.{_mod.name}")


def _all_subclasses(cls: type) -> list[type]:
    found: list[type] = []
    for sub in cls.__subclasses__():
        found.append(sub)
        found.extend(_all_subclasses(sub))
    return found


def _registry() -> dict[str, type[SportProfile]]:
    reg: dict[str, type[SportProfile]] = {}
    for cls in _all_subclasses(SportProfile):
        for name in getattr(cls, "handles", ()):  # generic (no handles) is skipped
            reg[name.lower()] = cls
    return reg


def available_sports() -> list[str]:
    return sorted(_registry().keys())


def get_profile(sport: str | None) -> SportProfile:
    """Return a profile for ``sport`` (case-insensitive), else the generic one."""
    key = (sport or "").strip().lower()
    cls = _registry().get(key)
    return cls() if cls else GenericProfile()


__all__ = ["SportProfile", "get_profile", "available_sports"]
