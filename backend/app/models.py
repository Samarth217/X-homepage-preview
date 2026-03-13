from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .db import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    x_post_id = Column(String, unique=True, index=True, nullable=False)
    author_handle = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    raw_json = Column(Text, nullable=True)

    story_links = relationship("StoryPost", back_populates="post")


class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    headline = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    category = Column(String, nullable=True)
    story_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    posts = relationship("StoryPost", back_populates="story", cascade="all, delete-orphan")


class StoryPost(Base):
    __tablename__ = "story_posts"

    story_id = Column(Integer, ForeignKey("stories.id"), primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"), primary_key=True)

    story = relationship("Story", back_populates="posts")
    post = relationship("Post", back_populates="story_links")

    __table_args__ = (
        UniqueConstraint("story_id", "post_id", name="uq_story_post"),
    )

