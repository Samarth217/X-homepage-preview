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
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts)

    return str(content or "")


def _extract_json_text(text: str) -> str:
    """
    Try hard to extract a JSON object from model output.
    """
    cleaned = _strip_code_fences(text)

    # Best case: already valid JSON
    try:
        json.loads(cleaned)
        return cleaned
    except Exception:
        pass

    # Common case: model wraps JSON with extra explanation
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        candidate = match.group(0)
        json.loads(candidate)  # validate
        return candidate

    raise ValueError("Could not extract valid JSON from Grok response")


def _truncate(text: str, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _guess_category(texts: List[str]) -> str:
    blob = " ".join(texts).lower()

    if any(word in blob for word in ["ai", "model", "inference", "llm", "open-source"]):
        return "Technology"
    if any(word in blob for word in ["stock", "market", "trader", "rates", "valuation", "semis"]):
        return "Markets"
    if any(word in blob for word in ["game", "coach", "fans", "shot", "sports", "season"]):
        return "Sports"
    if any(word in blob for word in ["trailer", "studio", "movie", "franchise", "entertainment"]):
        return "Culture"
    if any(word in blob for word in ["airline", "airport", "travel", "bag fees", "flying"]):
        return "Travel"

    return "General"


class GrokClient:
    """
    Tries full Grok clustering first.
    If that fails, falls back to deterministic grouping.
    Even in fallback mode, it still tries to use Grok to write
    the headline/summary for each chunk so the output looks real.
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

        if not self.api_key:
            print("[grok] no API key found; using fallback")
            return self._fallback_clusters(posts_list)

        try:
            print(f"[grok] calling {self.base_url}/chat/completions with model={self.model}")
            clusters = self._call_grok(posts_list)
            if clusters:
                print(f"[grok] success: returned {len(clusters)} clusters from API")
                return clusters
            print("[grok] API returned no usable clusters; using fallback")
        except Exception as e:
            print(f"[grok] full clustering failed: {e}")

        return self._fallback_clusters(posts_list)

    def _call_grok(self, posts: List[Dict[str, Any]]) -> List[GrokCluster]:
        post_payload = [
            {
                "x_post_id": p["x_post_id"],
                "author_handle": p.get("author_handle", ""),
                "text": p.get("text", ""),
            }
            for p in posts
        ]
        valid_ids = {p["x_post_id"] for p in post_payload}

        system_prompt = (
            "You are clustering recent public X posts into emerging homepage stories. "
            "Return only valid JSON."
        )

        user_prompt = (
            "Group these posts into coherent stories for a desktop logged-out homepage.\n\n"
            "Return ONLY valid JSON with this exact shape:\n"
            '{"stories":[{"headline":"string","summary":"string","category":"string","story_score":1.0,"post_ids":["string"]}]}\n\n'
            "Rules:\n"
            "- Every post_ids entry must exactly match an input x_post_id.\n"
            "- Use concise, homepage-friendly headlines.\n"
            "- Summaries should be 1-2 sentences.\n"
            "- Do not include markdown or explanation.\n\n"
            f"Posts:\n{json.dumps(post_payload, ensure_ascii=False)}"
        )

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
            "max_tokens": 900,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if not response.ok:
            raise RuntimeError(
                f"Grok API error: {response.status_code} {response.text[:400]}"
            )

        body = response.json()
        choices = body.get("choices") or []
        if not choices:
            raise ValueError("Grok response missing choices")

        raw_content = choices[0].get("message", {}).get("content")
        content = _content_to_text(raw_content)
        json_text = _extract_json_text(content)
        parsed = json.loads(json_text)

        stories_raw = parsed.get("stories")
        if not isinstance(stories_raw, list):
            raise ValueError("Grok response missing 'stories' list")

        clusters: List[GrokCluster] = []
        for story in stories_raw:
            if not isinstance(story, dict):
                continue

            headline = story.get("headline")
            summary = story.get("summary")
            category = story.get("category") or "General"
            score = story.get("story_score")
            post_ids = story.get("post_ids") or []

            if not isinstance(headline, str) or not headline.strip():
                continue
            if not isinstance(summary, str) or not summary.strip():
                continue
            if not isinstance(post_ids, list):
                continue

            filtered_ids = [str(pid) for pid in post_ids if str(pid) in valid_ids]
            if not filtered_ids:
                continue

            try:
                story_score = float(score) if score is not None else 1.0
            except Exception:
                story_score = 1.0

            clusters.append(
                GrokCluster(
                    headline=_truncate(headline.strip(), 90),
                    summary=_truncate(summary.strip(), 220),
                    category=str(category).strip() or "General",
                    story_score=story_score,
                    post_ids=filtered_ids,
                )
            )

        return clusters

    def _call_grok_for_story_copy(self, chunk: List[Dict[str, Any]]) -> tuple[str, str, str]:
        post_payload = [
            {
                "author_handle": p.get("author_handle", ""),
                "text": p.get("text", ""),
            }
            for p in chunk
        ]

        system_prompt = (
            "You write homepage headlines and summaries for clusters of public X posts. "
            "Return only valid JSON."
        )

        user_prompt = (
            "Given these related posts, write a concise homepage headline and short summary.\n\n"
            'Return ONLY valid JSON with this exact shape: {"headline":"string","summary":"string","category":"string"}\n\n'
            "Rules:\n"
            "- Headline should feel like a real news/front-page headline.\n"
            "- Summary should be 1-2 sentences.\n"
            "- Category should be short, like Technology, Markets, Sports, Culture, Travel, or General.\n"
            "- Do not include markdown or explanation.\n\n"
            f"Posts:\n{json.dumps(post_payload, ensure_ascii=False)}"
        )

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 220,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if not response.ok:
            raise RuntimeError(
                f"Grok story-copy error: {response.status_code} {response.text[:300]}"
            )

        body = response.json()
        choices = body.get("choices") or []
        if not choices:
            raise ValueError("Grok story-copy response missing choices")

        raw_content = choices[0].get("message", {}).get("content")
        content = _content_to_text(raw_content)
        json_text = _extract_json_text(content)
        parsed = json.loads(json_text)

        headline = _truncate(str(parsed.get("headline") or "").strip(), 90)
        summary = _truncate(str(parsed.get("summary") or "").strip(), 220)
        category = str(parsed.get("category") or "").strip() or "General"

        if not headline or not summary:
            raise ValueError("Grok story-copy response missing headline/summary")

        return headline, summary, category

    def _heuristic_story_copy(self, chunk: List[Dict[str, Any]]) -> tuple[str, str, str]:
        texts = [p.get("text", "").strip() for p in chunk if p.get("text")]
        headline = _truncate(texts[0] if texts else "What people are talking about right now", 90)

        summary = _truncate(" ".join(texts[:2]), 220)
        if not summary:
            summary = "Recent public posts are driving this conversation on X."

        category = _guess_category(texts)

        return headline, summary, category

    def _fallback_clusters(self, posts: List[Dict[str, Any]]) -> List[GrokCluster]:
        ordered = sorted(posts, key=lambda p: p["x_post_id"])
        cluster_size = 3
        clusters: List[GrokCluster] = []

        for idx in range(0, len(ordered), cluster_size):
            chunk = ordered[idx : idx + cluster_size]
            if not chunk:
                continue

            try:
                headline, summary, category = self._call_grok_for_story_copy(chunk)
                print("[grok] used Grok for fallback story copy")
            except Exception as e:
                print(f"[grok] fallback story-copy call failed: {e}")
                headline, summary, category = self._heuristic_story_copy(chunk)

            post_ids = [p["x_post_id"] for p in chunk]

            clusters.append(
                GrokCluster(
                    headline=headline,
                    summary=summary,
                    category=category,
                    story_score=1.0,
                    post_ids=post_ids,
                )
            )

        return clusters