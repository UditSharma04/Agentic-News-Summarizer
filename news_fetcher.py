"""
News Fetcher Module
Fetches tech news articles from RSS feeds and the Hacker News API.
"""

import time
from datetime import datetime, timezone
from typing import Optional

import feedparser
import requests
from bs4 import BeautifulSoup

from config import FETCH_TIMEOUT, MAX_ARTICLES_PER_SOURCE, NEWS_SOURCES


def _parse_date(entry: dict) -> Optional[datetime]:
    """Try to extract a datetime from a feed entry."""
    for key in ("published_parsed", "updated_parsed"):
        tp = entry.get(key)
        if tp:
            try:
                return datetime(*tp[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def _clean_html(raw_html: str) -> str:
    """Strip HTML tags and return plain text."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)[:2000]


def _fetch_rss(source: dict) -> list[dict]:
    """Fetch articles from an RSS feed."""
    articles = []
    try:
        feed = feedparser.parse(source["url"])
        for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
            # Get description / summary text
            description = ""
            if hasattr(entry, "summary"):
                description = _clean_html(entry.summary)
            elif hasattr(entry, "description"):
                description = _clean_html(entry.description)

            # Try to get full content
            content = ""
            if hasattr(entry, "content") and entry.content:
                content = _clean_html(entry.content[0].get("value", ""))

            articles.append(
                {
                    "title": entry.get("title", "Untitled"),
                    "url": entry.get("link", ""),
                    "description": description,
                    "content": content or description,
                    "published": _parse_date(entry),
                    "source": source["name"],
                    "category": source["category"],
                    "icon": source["icon"],
                }
            )
    except Exception as e:
        print(f"[WARNING] Failed to fetch RSS from {source['name']}: {e}")
    return articles


def _fetch_hackernews(source: dict) -> list[dict]:
    """Fetch top stories from the Hacker News API."""
    articles = []
    base_url = source["url"]
    try:
        resp = requests.get(
            f"{base_url}topstories.json", timeout=FETCH_TIMEOUT
        )
        resp.raise_for_status()
        story_ids = resp.json()[:MAX_ARTICLES_PER_SOURCE]

        for sid in story_ids:
            try:
                item_resp = requests.get(
                    f"{base_url}item/{sid}.json", timeout=FETCH_TIMEOUT
                )
                item_resp.raise_for_status()
                item = item_resp.json()
                if item and item.get("type") == "story" and item.get("url"):
                    published = None
                    if item.get("time"):
                        published = datetime.fromtimestamp(
                            item["time"], tz=timezone.utc
                        )
                    articles.append(
                        {
                            "title": item.get("title", "Untitled"),
                            "url": item.get("url", ""),
                            "description": item.get("text", "")[:500] if item.get("text") else "",
                            "content": item.get("text", "")[:2000] if item.get("text") else "",
                            "published": published,
                            "source": source["name"],
                            "category": source["category"],
                            "icon": source["icon"],
                            "score": item.get("score", 0),
                        }
                    )
            except Exception:
                continue
    except Exception as e:
        print(f"[WARNING] Failed to fetch Hacker News: {e}")
    return articles


def fetch_article_body(url: str) -> str:
    """Attempt to fetch the full body text of an article URL."""
    try:
        resp = requests.get(
            url,
            timeout=FETCH_TIMEOUT,
            headers={"User-Agent": "TechNewsAggregator/1.0"},
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove scripts, styles, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        return text[:3000]
    except Exception:
        return ""


def fetch_all_news(
    sources: list[dict] | None = None,
    selected_sources: list[str] | None = None,
) -> list[dict]:
    """
    Fetch news from all configured sources.

    Args:
        sources: List of source configs. Defaults to NEWS_SOURCES.
        selected_sources: Optional filter — only fetch from these source names.

    Returns:
        List of article dicts sorted by published date (newest first).
    """
    if sources is None:
        sources = NEWS_SOURCES

    all_articles: list[dict] = []
    for source in sources:
        if selected_sources and source["name"] not in selected_sources:
            continue

        if source["type"] == "rss":
            all_articles.extend(_fetch_rss(source))
        elif source["type"] == "hackernews":
            all_articles.extend(_fetch_hackernews(source))

    # Sort by date (newest first), put None-dated last
    all_articles.sort(
        key=lambda a: a.get("published") or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return all_articles
