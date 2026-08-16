"""Assemble the final Story dict (cover + highlights + info pages + metrics)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from .assets import Assets
from .models import Match
from .pages import CoverPage, HighlightPage
from .pipeline import final_score, select_highlights
from .profiles.base import SportProfile


def build_story(
    match: Match,
    profile: SportProfile,
    assets: Assets,
    *,
    story_id: str | None = None,
) -> dict:
    final = final_score(match, profile)
    highlights = select_highlights(match, profile)

    pages: list[dict] = []

    # Cover page (image injected here so profiles stay text-only).
    cover_info = profile.cover(match, final)
    pages.append(
        CoverPage(
            headline=cover_info.get("headline", _default_title(match)),
            image=assets.cover(),
            subheadline=cover_info.get("subheadline", ""),
        ).to_dict()
    )

    # Highlight pages, in chronological order.
    for ranked in highlights:
        caption = profile.caption(ranked.event, ranked.score, match)
        pages.append(
            HighlightPage(
                minute=_clamp_minute(ranked.event.minute),
                headline=caption.headline,
                caption=caption.caption,
                image=assets.for_event(ranked.event),
                explanation=caption.explanation,
            ).to_dict()
        )

    # Trailing info/stats pages.
    pages.extend(profile.info_pages(match, final, match.events))

    return {
        "story_id": story_id or f"story-{uuid.uuid4().hex[:12]}",
        "title": _default_title(match),
        "source": match.source or "match_events.json",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": profile.metrics(match, final, match.events),
        "pages": pages,
    }


def _default_title(match: Match) -> str:
    home = match.home.name if match.home else "Home"
    away = match.away.name if match.away else "Away"
    return f"{home} vs {away}"


def _clamp_minute(minute: int) -> int:
    # Schema allows highlight minute 0..130.
    return max(0, min(minute, 130))
