"""
Health Check Module — Ping all external services and report status.
Checks RSS/Atom feeds, Hacker News API, OpenAI API, and Gmail SMTP.
"""

import smtplib
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import feedparser
import requests
from openai import OpenAI

from config import (
    FETCH_TIMEOUT,
    NEWS_SOURCES,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    SMTP_EMAIL,
    SMTP_PASSWORD,
)


def _check_rss(source: dict) -> dict:
    """Ping an RSS/Atom feed and verify it returns entries."""
    start = time.time()
    try:
        feed = feedparser.parse(source["url"])
        latency = round((time.time() - start) * 1000)
        if feed.bozo and not feed.entries:
            return {
                "name": source["name"],
                "type": "RSS" if "rss" in source.get("type", "") else "Atom",
                "url": source["url"],
                "status": "error",
                "message": "Feed returned errors and no entries",
                "latency_ms": latency,
            }
        entry_count = len(feed.entries)
        return {
            "name": source["name"],
            "type": "RSS" if "rss" in source.get("type", "") else "Atom",
            "url": source["url"],
            "status": "healthy",
            "message": f"{entry_count} entries available",
            "latency_ms": latency,
        }
    except Exception as e:
        latency = round((time.time() - start) * 1000)
        return {
            "name": source["name"],
            "type": "RSS/Atom",
            "url": source["url"],
            "status": "error",
            "message": str(e)[:120],
            "latency_ms": latency,
        }


def _check_hackernews(source: dict) -> dict:
    """Ping the Hacker News Firebase API."""
    start = time.time()
    try:
        resp = requests.get(
            f"{source['url']}topstories.json",
            timeout=FETCH_TIMEOUT,
        )
        latency = round((time.time() - start) * 1000)
        resp.raise_for_status()
        ids = resp.json()
        return {
            "name": source["name"],
            "type": "REST API",
            "url": source["url"],
            "status": "healthy",
            "message": f"{len(ids)} stories available",
            "latency_ms": latency,
        }
    except Exception as e:
        latency = round((time.time() - start) * 1000)
        return {
            "name": source["name"],
            "type": "REST API",
            "url": source["url"],
            "status": "error",
            "message": str(e)[:120],
            "latency_ms": latency,
        }


def _check_openai() -> dict:
    """Ping OpenAI API with a minimal request."""
    if not OPENAI_API_KEY:
        return {
            "name": "OpenAI",
            "type": "LLM API",
            "url": "api.openai.com",
            "status": "not_configured",
            "message": "OPENAI_API_KEY not set in .env",
            "latency_ms": 0,
        }
    start = time.time()
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
        )
        latency = round((time.time() - start) * 1000)
        return {
            "name": "OpenAI",
            "type": "LLM API",
            "url": "api.openai.com",
            "status": "healthy",
            "message": f"Model {OPENAI_MODEL} responding",
            "latency_ms": latency,
        }
    except Exception as e:
        latency = round((time.time() - start) * 1000)
        return {
            "name": "OpenAI",
            "type": "LLM API",
            "url": "api.openai.com",
            "status": "error",
            "message": str(e)[:120],
            "latency_ms": latency,
        }


def _check_smtp() -> dict:
    """Verify Gmail SMTP connection and authentication."""
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        return {
            "name": "Gmail SMTP",
            "type": "Email",
            "url": "smtp.gmail.com:587",
            "status": "not_configured",
            "message": "SMTP_EMAIL / SMTP_PASSWORD not set in .env",
            "latency_ms": 0,
        }
    start = time.time()
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
        latency = round((time.time() - start) * 1000)
        return {
            "name": "Gmail SMTP",
            "type": "Email",
            "url": "smtp.gmail.com:587",
            "status": "healthy",
            "message": f"Authenticated as {SMTP_EMAIL}",
            "latency_ms": latency,
        }
    except smtplib.SMTPAuthenticationError:
        latency = round((time.time() - start) * 1000)
        return {
            "name": "Gmail SMTP",
            "type": "Email",
            "url": "smtp.gmail.com:587",
            "status": "error",
            "message": "Authentication failed — check App Password",
            "latency_ms": latency,
        }
    except Exception as e:
        latency = round((time.time() - start) * 1000)
        return {
            "name": "Gmail SMTP",
            "type": "Email",
            "url": "smtp.gmail.com:587",
            "status": "error",
            "message": str(e)[:120],
            "latency_ms": latency,
        }


def run_all_checks() -> list[dict]:
    """Run health checks on all services concurrently.

    Returns a list of result dicts, each with:
      name, type, url, status, message, latency_ms
    """
    results: list[dict] = []

    news_sources = list(NEWS_SOURCES)

    with ThreadPoolExecutor(max_workers=len(news_sources) + 2) as pool:
        futures = {}
        for src in news_sources:
            fn = _check_hackernews if src["type"] == "hackernews" else _check_rss
            futures[pool.submit(fn, src)] = src["name"]

        futures[pool.submit(_check_openai)] = "OpenAI"
        futures[pool.submit(_check_smtp)] = "Gmail SMTP"

        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                results.append({
                    "name": futures[future],
                    "type": "?",
                    "url": "",
                    "status": "error",
                    "message": str(e)[:120],
                    "latency_ms": 0,
                })

    source_order = [s["name"] for s in news_sources] + ["OpenAI", "Gmail SMTP"]
    results.sort(key=lambda r: source_order.index(r["name"]) if r["name"] in source_order else 999)

    return results
