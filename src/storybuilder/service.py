"""Optional HTTP service exposing the builder as an API.

Requires the ``service`` extra (``pip install -e ".[service]"``). It is a thin
shell over :func:`storybuilder.app.build_story_from_feed` - the exact same code
path the CLI uses - so there is no logic duplicated here.

    POST /stories   {feed, squads?, sport?, format?, story_id?}  -> Story JSON
    GET  /healthz                                                -> {"status": "ok"}
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .app import StoryValidationError, build_story_from_feed


class StoryRequest(BaseModel):
    feed: dict[str, Any] = Field(..., description="The raw, JSON-decoded match feed.")
    squads: list[dict[str, Any]] = Field(default_factory=list)
    sport: str | None = None
    format: str | None = Field(default=None, description="Feed adapter name (default: auto-detect).")
    story_id: str | None = None
    # Named ``validate_output`` (not ``validate``) to avoid shadowing a BaseModel attribute.
    validate_output: bool = True


def create_app() -> FastAPI:
    app = FastAPI(title="Storybuilder", version="0.1.0")

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok"}

    @app.post("/stories")
    def create_story(req: StoryRequest) -> dict:
        try:
            return build_story_from_feed(
                req.feed,
                req.squads,
                fmt=req.format,
                sport=req.sport,
                story_id=req.story_id,
                validate=req.validate_output,
            )
        except StoryValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors) from exc
        except ValueError as exc:  # e.g. unknown/undetectable feed format
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


app = create_app()


def run() -> None:  # pragma: no cover - convenience entry point
    import uvicorn

    uvicorn.run("storybuilder.service:app", host="0.0.0.0", port=8080)


if __name__ == "__main__":  # pragma: no cover
    run()
