from typing import List

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from .db import get_db, init_db
from . import schemas
from .services import run_refresh_pipeline, get_recent_stories_with_posts


app = FastAPI(title="X Homepage Backend", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health", response_model=schemas.HealthResponse)
def health() -> schemas.HealthResponse:
    return schemas.HealthResponse(status="ok")


@app.post("/refresh", response_model=schemas.RefreshResponse)
def refresh(db: Session = Depends(get_db)) -> schemas.RefreshResponse:
    try:
        stories_created, posts_upserted = run_refresh_pipeline(db)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return schemas.RefreshResponse(
        status="ok",
        stories_created=stories_created,
        posts_upserted=posts_upserted,
    )


@app.get("/stories", response_model=List[schemas.StorySummary])
def list_stories(
    limit: int = 10,
    db: Session = Depends(get_db),
) -> List[schemas.StorySummary]:
    story_rows = get_recent_stories_with_posts(db, limit=limit)
    response: List[schemas.StorySummary] = []

    for story, posts in story_rows:
        representative_posts = [
            schemas.StoryPostSnippet(
                id=p.id,
                author_handle=p.author_handle,
                text=p.text,
                created_at=p.created_at,
            )
            for p in posts
        ]
        response.append(
            schemas.StorySummary(
                id=story.id,
                headline=story.headline,
                summary=story.summary,
                category=story.category,
                story_score=story.story_score,
                created_at=story.created_at,
                updated_at=story.updated_at,
                representative_posts=representative_posts,
            )
        )

    return response

