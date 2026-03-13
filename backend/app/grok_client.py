from dataclasses import dataclass
from typing import Iterable, List, Dict, Any


@dataclass
class GrokCluster:
    headline: str
    summary: str
    category: str
    story_score: float
    post_ids: List[str]


class GrokClient:
    """
    Stubbed Grok client.

    In a real implementation, this would call Grok's API with the posts and
    return clusters. For this take-home scaffold, we simply group everything
    into a single mock cluster to keep things demoable.
    """

    def cluster_posts(self, posts: Iterable[Dict[str, Any]]) -> List[GrokCluster]:
        post_ids = [p["x_post_id"] for p in posts]
        if not post_ids:
            return []

        # Simple, deterministic stub: one cluster containing all posts.
        return [
            GrokCluster(
                headline="Today on X",
                summary="A collection of recent posts from X.",
                category="general",
                story_score=1.0,
                post_ids=post_ids,
            )
        ]

