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

# ── Email / SMTP Configuration ────────────────────────────────────────────────
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
DIGEST_RECIPIENT = os.getenv("DIGEST_RECIPIENT", "")

# ── Application Settings ─────────────────────────────────────────────────────
MAX_ARTICLES_PER_SOURCE = int(os.getenv("MAX_ARTICLES_PER_SOURCE", "8"))
SUMMARY_MAX_TOKENS = int(os.getenv("SUMMARY_MAX_TOKENS", "400"))
FETCH_TIMEOUT = int(os.getenv("FETCH_TIMEOUT", "15"))

# ── News Sources ──────────────────────────────────────────────────────────────
NEWS_SOURCES = [
    {
        "name": "TechCrunch",
        "type": "rss",
        "url": "https://techcrunch.com/feed/",
        "category": "General Tech",
        "domain": "techcrunch.com",
    },
    {
        "name": "The Verge",
        "type": "rss",
        "url": "https://www.theverge.com/rss/index.xml",
        "category": "General Tech",
        "domain": "theverge.com",
    },
    {
        "name": "Ars Technica",
        "type": "rss",
        "url": "https://feeds.arstechnica.com/arstechnica/index",
        "category": "Deep Tech",
        "domain": "arstechnica.com",
    },
    {
        "name": "Wired",
        "type": "rss",
        "url": "https://www.wired.com/feed/rss",
        "category": "Tech & Culture",
        "domain": "wired.com",
    },
    {
        "name": "Hacker News",
        "type": "hackernews",
        "url": "https://hacker-news.firebaseio.com/v0/",
        "category": "Developer & Startups",
        "domain": "news.ycombinator.com",
    },
    {
        "name": "MIT Technology Review",
        "type": "rss",
        "url": "https://www.technologyreview.com/feed/",
        "category": "Research & Innovation",
        "domain": "technologyreview.com",
    },
    {
        "name": "VentureBeat",
        "type": "rss",
        "url": "https://venturebeat.com/feed/",
        "category": "AI & Enterprise",
        "domain": "venturebeat.com",
    },
    {
        "name": "The Register",
        "type": "rss",
        "url": "https://www.theregister.com/headlines.atom",
        "category": "Infrastructure & Security",
        "domain": "theregister.com",
    },
]
