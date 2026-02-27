"""
News Fetcher Module
Fetches tech news articles from RSS feeds and the Hacker News API.
Includes deduplication, reading-time estimation, and concurrent fetching.
"""

import math
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote_plus, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

from config import FETCH_TIMEOUT, MAX_ARTICLES_PER_SOURCE, NEWS_SOURCES


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_date(entry: dict) -> Optional[datetime]:
    for key in ("published_parsed", "updated_parsed"):
        tp = entry.get(key)
        if tp:
            try:
                return datetime(*tp[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def _clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)[:3000]


def _reading_time(text: str) -> int:
    """Estimate reading time in minutes (avg 200 wpm)."""
    words = len(re.findall(r"\w+", text or ""))
    return max(1, math.ceil(words / 200))


def _extract_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def _normalize(title: str) -> str:
    """Lowercase, strip punctuation for dedup comparison."""
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()


# ── RSS Fetcher ───────────────────────────────────────────────────────────────

def _fetch_rss(source: dict) -> list[dict]:
    articles = []
    try:
        feed = feedparser.parse(source["url"])
        for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
            description = ""
            if hasattr(entry, "summary"):
                description = _clean_html(entry.summary)
            elif hasattr(entry, "description"):
                description = _clean_html(entry.description)

            content = ""
            if hasattr(entry, "content") and entry.content:
                content = _clean_html(entry.content[0].get("value", ""))

            full_text = content or description
            url = entry.get("link", "")

            articles.append({
                "title": entry.get("title", "Untitled"),
                "url": url,
                "description": description,
                "content": full_text,
                "published": _parse_date(entry),
                "source": source["name"],
                "category": source["category"],
                "domain": source.get("domain", _extract_domain(url)),
                "reading_time": _reading_time(full_text),
            })
    except Exception as e:
        print(f"[WARNING] Failed to fetch RSS from {source['name']}: {e}")
    return articles


# ── Hacker News Fetcher ──────────────────────────────────────────────────────

def _fetch_hackernews(source: dict) -> list[dict]:
    articles = []
    base_url = source["url"]
    try:
        resp = requests.get(f"{base_url}topstories.json", timeout=FETCH_TIMEOUT)
        resp.raise_for_status()
        story_ids = resp.json()[:MAX_ARTICLES_PER_SOURCE]

        for sid in story_ids:
            try:
                r = requests.get(f"{base_url}item/{sid}.json", timeout=FETCH_TIMEOUT)
                r.raise_for_status()
                item = r.json()
                if item and item.get("type") == "story" and item.get("url"):
                    published = None
                    if item.get("time"):
                        published = datetime.fromtimestamp(item["time"], tz=timezone.utc)
                    url = item.get("url", "")
                    text = item.get("text", "") or ""
                    articles.append({
                        "title": item.get("title", "Untitled"),
                        "url": url,
                        "description": text[:500],
                        "content": text[:3000],
                        "published": published,
                        "source": source["name"],
                        "category": source["category"],
                        "domain": source.get("domain", _extract_domain(url)),
                        "reading_time": _reading_time(text),
                        "score": item.get("score", 0),
                        "comments": item.get("descendants", 0),
                    })
            except Exception:
                continue
    except Exception as e:
        print(f"[WARNING] Failed to fetch Hacker News: {e}")
    return articles


# ── Article body fetcher ─────────────────────────────────────────────────────

def fetch_article_body(url: str) -> str:
    try:
        resp = requests.get(
            url, timeout=FETCH_TIMEOUT,
            headers={"User-Agent": "TechNewsAggregator/2.0"},
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:4000]
    except Exception:
        return ""


# ── Web news search (Google News RSS) ─────────────────────────────────────────

def search_web_news(query: str, max_results: int = 5) -> list[dict]:
    """Search Google News RSS for recent articles about a topic (last 48 hours)."""
    try:
        search_url = (
            f"https://news.google.com/rss/search?"
            f"q={quote_plus(query)}+when:2d&hl=en-US&gl=US&ceid=US:en"
        )
        feed = feedparser.parse(search_url)
        results = []
        for entry in feed.entries[:max_results]:
            source_name = ""
            if hasattr(entry, "source"):
                source_name = entry.source.get("title", "")

            title = entry.get("title", "Untitled")
            if source_name and title.endswith(f" - {source_name}"):
                title = title[: -len(f" - {source_name}")]

            results.append({
                "title": title,
                "url": entry.get("link", ""),
                "description": _clean_html(entry.get("summary", "")),
                "source": source_name,
                "published": _parse_date(entry),
            })
        return results
    except Exception as e:
        print(f"[WARNING] Web news search failed: {e}")
        return []


# ── Deduplication ─────────────────────────────────────────────────────────────

def _deduplicate(articles: list[dict]) -> list[dict]:
    """Remove near-duplicate articles by normalized title similarity."""
    seen: set[str] = set()
    unique: list[dict] = []
    for a in articles:
        norm = _normalize(a["title"])
        # Check for exact or prefix match
        is_dup = False
        for s in seen:
            # If titles share >70 % of words, consider duplicate
            words_a = set(norm.split())
            words_s = set(s.split())
            if not words_a or not words_s:
                continue
            overlap = len(words_a & words_s) / min(len(words_a), len(words_s))
            if overlap > 0.7:
                is_dup = True
                break
        if not is_dup:
            seen.add(norm)
            unique.append(a)
    return unique


# ── Main entry point ─────────────────────────────────────────────────────────

def fetch_all_news(
    sources: list[dict] | None = None,
    selected_sources: list[str] | None = None,
) -> list[dict]:
    """
    Fetch news from all configured sources concurrently.
    Returns deduplicated articles sorted by date (newest first).
    """
    if sources is None:
        sources = NEWS_SOURCES

    targets = [
        s for s in sources
        if not selected_sources or s["name"] in selected_sources
    ]

    all_articles: list[dict] = []

    # Concurrent fetch for speed
    with ThreadPoolExecutor(max_workers=len(targets) or 1) as pool:
        futures = {}
        for src in targets:
            fn = _fetch_hackernews if src["type"] == "hackernews" else _fetch_rss
            futures[pool.submit(fn, src)] = src["name"]

        for future in as_completed(futures):
            try:
                all_articles.extend(future.result())
            except Exception as e:
                print(f"[WARNING] {futures[future]}: {e}")

    # Deduplicate
    all_articles = _deduplicate(all_articles)

    # Sort newest first
    all_articles.sort(
        key=lambda a: a.get("published") or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return all_articles
