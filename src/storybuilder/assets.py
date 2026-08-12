"""Deterministic image selection for pages.

The provided assets are generic stadium/action photos not tied to specific
events, so we map them decoratively and reproducibly: a fixed cover image and a
stable, per-event pick derived from a hash of the event so the same event always
gets the same picture. Missing assets fall back to the placeholder.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from .models import Event

ASSETS_DIR = "assets"
PLACEHOLDER = f"{ASSETS_DIR}/placeholder.png"


class Assets:
    def __init__(self, assets_dir: str | Path = ASSETS_DIR):
        self._dir_label = str(assets_dir).replace("\\", "/").rstrip("/")
        self._images = self._discover(Path(assets_dir))

    def _discover(self, path: Path) -> list[str]:
        if not path.is_dir():
            return []
        names = sorted(
            p.name
            for p in path.iterdir()
            if p.suffix.lower() in {".jpg", ".jpeg", ".png"} and p.stem != "placeholder"
        )
        return [f"{self._dir_label}/{n}" for n in names]

    @property
    def placeholder(self) -> str:
        return f"{self._dir_label}/placeholder.png"

    def cover(self) -> str:
        return self._images[0] if self._images else self.placeholder

    def for_event(self, event: Event) -> str:
        """Pick a stable image for an event (skips the cover image if possible)."""
        pool = self._images[1:] or self._images
        if not pool:
            return self.placeholder
        key = f"{event.raw_id}|{event.type}|{event.minute}".encode("utf-8")
        idx = int(hashlib.sha1(key).hexdigest(), 16) % len(pool)
        return pool[idx]
