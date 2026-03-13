import json
import random
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from sqlalchemy.orm import Session  # pyright: ignore[reportMissingImports]

from .config import SAMPLE_POSTS_PATH
from .grok_client import GrokClient
from . import models


def _load_sample_posts(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return list(data)


def _parse_created_at(value) -> datetime:
    """
    Parse an ISO-like datetime string into a datetime object.
    Falls back to datetime.utcnow() if missing or invalid.
    """
    if not value:
        return datetime.utcnow()
    if isinstance(value, datetime):
        return value

    text = str(value)
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    return datetime.utcnow()


def run_refresh_pipeline(db: Session) -> Tuple[int, int]:
    """
    Read posts from the local sample file, pick a fresh subset each refresh,
    cluster via GrokClient, and persist posts + stories + story_posts.

    For this prototype, each refresh fully replaces previously ingested posts
    and previously generated stories so the homepage cleanly reflects the
    latest sampled batch.
    """
    if not SAMPLE_POSTS_PATH.exists():
        raise FileNotFoundError(f"Sample posts file not found at {SAMPLE_POSTS_PATH}")

    raw_posts = _load_sample_posts(SAMPLE_POSTS_PATH)

    if not raw_posts:
        # Clear everything if the sample file is empty
        db.query(models.StoryPost).delete()
        db.query(models.Story).delete()
        db.query(models.Post).delete()
        db.flush()
        return 0, 0

    # Pick a different subset on each refresh so the homepage changes over time.
    # Tweak this number if you want more or fewer posts per refresh.
    sample_size = min(len(raw_posts), 12)
    if len(raw_posts) > sample_size:
        raw_posts = random.sample(raw_posts, sample_size)

    # Replace everything on refresh for a clean demo state.
    db.query(models.StoryPost).delete()
    db.query(models.Story).delete()
    db.query(models.Post).delete()
    db.flush()

    posts_upserted = 0
    normalized_posts = []
    posts_by_x_post_id = {}

    for item in raw_posts:
        x_post_id = str(item.get("id") or item.get("x_post_id") or "").strip()
        if not x_post_id:
            continue

        created_at = _parse_created_at(item.get("created_at"))
        author_handle = item.get("author_handle") or item.get("user", "")
        text = item.get("text", "")

        post = models.Post(
            x_post_id=x_post_id,
            author_handle=author_handle,
            text=text,
            created_at=created_at,
            raw_json=json.dumps(item),
        )
        db.add(post)
        posts_upserted += 1
        posts_by_x_post_id[x_post_id] = post

        normalized_posts.append(
            {
                "x_post_id": x_post_id,
                "author_handle": author_handle,
                "text": text,
            }
        )

    db.flush()

    grok = GrokClient()
    clusters = grok.cluster_posts(normalized_posts)

    stories_created = 0
    for cluster in clusters:
        story = models.Story(
            headline=cluster.headline,
            summary=cluster.summary,
            category=cluster.category,
            story_score=cluster.story_score,
        )
        db.add(story)
        db.flush()

        for x_post_id in cluster.post_ids:
            post = posts_by_x_post_id.get(x_post_id)
            if not post:
                continue

            db.add(
                models.StoryPost(
                    story_id=story.id,
                    post_id=post.id,
                )
            )

        stories_created += 1

    return stories_created, posts_upserted


def get_recent_stories_with_posts(db: Session, limit: int = 10, posts_per_story: int = 3):
    """
    Fetch recent stories with a small subset of representative posts.
    """
    stories = (
        db.query(models.Story)
        .order_by(models.Story.created_at.desc())
        .limit(limit)
        .all()
    )

    result = []
    for story in stories:
        links = (
            db.query(models.StoryPost)
            .filter(models.StoryPost.story_id == story.id)
            .all()
        )
        post_ids = [link.post_id for link in links]

        if not post_ids:
            representative_posts = []
        else:
            representative_posts = (
                db.query(models.Post)
                .filter(models.Post.id.in_(post_ids))
                .order_by(models.Post.created_at.desc())
                .limit(posts_per_story)
                .all()
            )

        result.append((story, representative_posts))

    return result