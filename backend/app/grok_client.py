import json
import re
from dataclasses import dataclass
from typing import Iterable, List, Dict, Any

import requests

from .config import GROK_API_BASE_URL, GROK_MODEL, XAI_API_KEY


@dataclass
class GrokCluster:
    headline: str
    summary: str
    category: str
    story_score: float
    post_ids: List[str]


def _strip_code_fences(text: str) -> str:
    """Remove ``` and ```json fences if present before JSON parsing."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped


class GrokClient:
    """
    Grok client that prefers a real xAI Grok API call but falls back
    to deterministic grouping when necessary to keep the app demoable.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else XAI_API_KEY
        self.base_url = (base_url or GROK_API_BASE_URL).rstrip("/")
        self.model = model or GROK_MODEL

    def cluster_posts(self, posts: Iterable[Dict[str, Any]]) -> List[GrokCluster]:
        posts_list = list(posts)
        if not posts_list:
            return []

        # If no API key is configured, fall back immediately.
        if not self.api_key:
            return self._fallback_clusters(posts_list)

        try:
            clusters = self._call_grok(posts_list)
            if clusters:
                return clusters
        except Exception:
            # Any failure should fall back gracefully.
            pass

        return self._fallback_clusters(posts_list)

    def _call_grok(self, posts: List[Dict[str, Any]]) -> List[GrokCluster]:
        # Prepare compact post payload
        post_payload = [
            {
                "x_post_id": p["x_post_id"],
                "author_handle": p.get("author_handle", ""),
                "text": p.get("text", ""),
            }
            for p in posts
        ]
        valid_ids = {p["x_post_id"] for p in post_payload}

        instructions = (
            "You are clustering recent public X posts into emerging stories for a logged-out homepage.\n"
            "Group posts into coherent stories and respond ONLY with valid JSON using this exact shape:\n"
            '{\"stories\": [{\"headline\": \"string\", \"summary\": \"string\", \"category\": \"string\", '
            '\"story_score\": 0.0, \"post_ids\": [\"string\"]}]}.\n'
            "Rules:\n"
            "- Only include stories with at least 1 post.\n"
            "- Do not invent post IDs. Every post_id must match an x_post_id from the input.\n"
            "- Keep headlines concise and homepage-friendly.\n"
            "- Keep summaries to 1-2 sentences.\n"
            "Here are the posts as JSON:\n"
            f"{json.dumps(post_payload, ensure_ascii=False)}"
        )

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": instructions}],
            "temperature": 0.2,
            "max_tokens": 512,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if not response.ok:
            raise RuntimeError(f"Grok API error: {response.status_code}")

        body = response.json()
        choices = body.get("choices") or []
        if not choices:
            raise ValueError("Grok response missing choices")

        content = choices[0].get("message", {}).get("content") or ""
        content = _strip_code_fences(content)

        parsed = json.loads(content)
        stories_raw = parsed.get("stories")
        if not isinstance(stories_raw, list):
            raise ValueError("Grok response missing 'stories' list")

        clusters: List[GrokCluster] = []
        for story in stories_raw:
            if not isinstance(story, dict):
                continue
            headline = story.get("headline")
            summary = story.get("summary")
            category = story.get("category") or "general"
            score = story.get("story_score")
            post_ids = story.get("post_ids") or []

            if not isinstance(post_ids, list):
                continue

            # Keep only IDs that we actually know about.
            filtered_ids = [pid for pid in post_ids if pid in valid_ids]
            if not filtered_ids:
                continue

            if not isinstance(headline, str) or not isinstance(summary, str):
                continue

            try:
                story_score = float(score) if score is not None else 1.0
            except (TypeError, ValueError):
                story_score = 1.0

            clusters.append(
                GrokCluster(
                    headline=headline.strip(),
                    summary=summary.strip(),
                    category=str(category).strip() or "general",
                    story_score=story_score,
                    post_ids=filtered_ids,
                )
            )

        return clusters

    def _fallback_clusters(self, posts: List[Dict[str, Any]]) -> List[GrokCluster]:
        """
        Deterministic grouping used when Grok is unavailable or fails.
        Produces multiple simple stories when there are enough posts.
        """
        # Stable order by x_post_id for determinism.
        ordered = sorted(posts, key=lambda p: p["x_post_id"])
        cluster_size = 3
        clusters: List[GrokCluster] = []

        for idx in range(0, len(ordered), cluster_size):
            chunk = ordered[idx : idx + cluster_size]
            if not chunk:
                continue

            authors = [p.get("author_handle") or "user" for p in chunk]
            first_author = authors[0]
            other_count = max(len(authors) - 1, 0)

            headline = f"Story {len(clusters) + 1}: @{first_author}" + (
                f" and {other_count} others" if other_count else ""
            )
            summary = (
                "A small cluster of recent posts grouped together for this demo homepage. "
                "Headlines and summaries are synthetic when Grok is unavailable."
            )

            post_ids = [p["x_post_id"] for p in chunk]
            clusters.append(
                GrokCluster(
                    headline=headline,
                    summary=summary,
                    category="general",
                    story_score=1.0,
                    post_ids=post_ids,
                )
            )

        return clusters

