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
            key = name.lower()
            existing = reg.get(key)
            if existing is not None and existing is not cls:
                raise RuntimeError(
                    f"Duplicate sport handle {key!r}: {existing.__name__} and "
                    f"{cls.__name__} both claim it. Handles must be unique."
                )
            reg[key] = cls
    return reg


def available_sports() -> list[str]:
    return sorted(_registry().keys())


def get_profile(sport: str | None, config_dir: str | None = None) -> SportProfile:
    """Return a profile for ``sport`` (case-insensitive), else the generic one.

    If a ``config/<sport>.json`` (or a file named after one of the profile's
    ``handles``) exists under ``config_dir`` (defaults to the repo's ``config/``),
    its values override the profile's declarative defaults. Pass an explicit
    ``config_dir`` to point at a different config set (e.g. per-customer tuning).
    """
    from ..config import DEFAULT_CONFIG_DIR, load_config

    key = (sport or "").strip().lower()
    cls = _registry().get(key)
    profile_cls = cls or GenericProfile

    cfg_dir = config_dir if config_dir is not None else DEFAULT_CONFIG_DIR
    candidates = [key, *getattr(profile_cls, "handles", ())]
    raw = None
    for name in candidates:
        raw = load_config(name, cfg_dir)
        if raw is not None:
            break

    return profile_cls(config=raw)


__all__ = ["SportProfile", "get_profile", "available_sports"]
