"""
Configuration for the Tech News Aggregator & Summarizer.
Defines news sources and application settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── OpenAI Configuration ─────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ── Application Settings ─────────────────────────────────────────────────────
MAX_ARTICLES_PER_SOURCE = int(os.getenv("MAX_ARTICLES_PER_SOURCE", "5"))
SUMMARY_MAX_TOKENS = int(os.getenv("SUMMARY_MAX_TOKENS", "300"))
FETCH_TIMEOUT = int(os.getenv("FETCH_TIMEOUT", "15"))

# ── News Sources ──────────────────────────────────────────────────────────────
# Each source has: name, type (rss or api), url, category
NEWS_SOURCES = [
    {
        "name": "TechCrunch",
        "type": "rss",
        "url": "https://techcrunch.com/feed/",
        "category": "General Tech",
        "icon": "🔵",
    },
    {
        "name": "The Verge",
        "type": "rss",
        "url": "https://www.theverge.com/rss/index.xml",
        "category": "General Tech",
        "icon": "🟣",
    },
    {
        "name": "Ars Technica",
        "type": "rss",
        "url": "https://feeds.arstechnica.com/arstechnica/index",
        "category": "Deep Tech",
        "icon": "🟠",
    },
    {
        "name": "Wired",
        "type": "rss",
        "url": "https://www.wired.com/feed/rss",
        "category": "Tech & Culture",
        "icon": "⚫",
    },
    {
        "name": "Hacker News",
        "type": "hackernews",
        "url": "https://hacker-news.firebaseio.com/v0/",
        "category": "Developer & Startups",
        "icon": "🟧",
    },
    {
        "name": "MIT Technology Review",
        "type": "rss",
        "url": "https://www.technologyreview.com/feed/",
        "category": "Research & Innovation",
        "icon": "🔴",
    },
]
