from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class RefreshResponse(BaseModel):
    status: str
    stories_created: int
    posts_upserted: int


class StoryPostSnippet(BaseModel):
    id: int
    author_handle: str
    text: str
    created_at: datetime


class StorySummary(BaseModel):
    id: int
    headline: str
    summary: str
    category: Optional[str] = None
    story_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    representative_posts: List[StoryPostSnippet]

