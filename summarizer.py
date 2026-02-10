"""
Summarizer Module — Agentic AI Core
Uses OpenAI for intelligent summaries, trending-topic extraction,
and structured executive briefings.
"""

import json
from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL, SUMMARY_MAX_TOKENS

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


# ── Single-article summary ───────────────────────────────────────────────────

def summarize_article(article: dict) -> str:
    """
    Produce a rich summary for a single article.
    Includes key facts, impact assessment, and a 'why it matters' line.
    """
    if not OPENAI_API_KEY:
        return _fallback_summary(article)

    context_parts = [f"Title: {article['title']}"]
    if article.get("description"):
        context_parts.append(f"Description: {article['description'][:1200]}")
    if article.get("content"):
        context_parts.append(f"Content: {article['content'][:2500]}")
    context_parts.append(f"Source: {article['source']}")

    context = "\n".join(context_parts)

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior tech news analyst. Given an article, produce a summary "
                        "in this exact format:\n\n"
                        "**Summary:** 2-3 sentences covering the key facts.\n\n"
                        "**Why it matters:** 1 sentence on the broader impact for the tech industry.\n\n"
                        "**Key players:** Mention companies or people involved (comma-separated).\n\n"
                        "Be concise, objective, and insightful."
                    ),
                },
                {"role": "user", "content": context},
            ],
            max_tokens=SUMMARY_MAX_TOKENS,
            temperature=0.25,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[WARNING] Summarization failed: {e}")
        return _fallback_summary(article)


# ── Executive briefing ───────────────────────────────────────────────────────

def summarize_all(articles: list[dict]) -> str:
    """
    Generate a structured executive briefing from a batch of articles.
    Identifies top stories, trends, market signals, and quick bites.
    """
    if not OPENAI_API_KEY:
        return "Set your OPENAI_API_KEY in the .env file to enable AI-powered summaries."

    if not articles:
        return "No articles available to summarize."

    digest_lines: list[str] = []
    for i, a in enumerate(articles, 1):
        line = f"{i}. [{a['source']}] {a['title']}"
        if a.get("description"):
            line += f" -- {a['description'][:250]}"
        digest_lines.append(line)

    digest = "\n".join(digest_lines)

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert tech news analyst producing a daily executive briefing. "
                        "Given today's top tech headlines and descriptions, produce a structured "
                        "briefing with these sections:\n\n"
                        "**TOP STORIES** -- The 3-4 most significant stories. For each, give a "
                        "2-sentence summary and explain why it matters.\n\n"
                        "**TRENDS & THEMES** -- 2-3 emerging patterns or themes across the stories. "
                        "Connect the dots between related articles.\n\n"
                        "**MARKET SIGNALS** -- Any implications for investors, startups, or the "
                        "broader tech ecosystem.\n\n"
                        "**QUICK BITES** -- One-line summaries for remaining noteworthy articles.\n\n"
                        "Use clear, direct language. Reference articles by number. Be insightful."
                    ),
                },
                {"role": "user", "content": digest},
            ],
            max_tokens=1200,
            temperature=0.35,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Failed to generate briefing: {e}"


# ── Trending Topics Extraction ───────────────────────────────────────────────

def extract_trending_topics(articles: list[dict]) -> list[str]:
    """
    Extract 6-10 trending topic keywords/phrases from article headlines.
    Returns a list of short topic strings.
    """
    if not OPENAI_API_KEY or not articles:
        return _fallback_topics(articles)

    headlines = " | ".join(a["title"] for a in articles[:40])

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract 8-10 trending topic tags from these tech news headlines. "
                        "Return ONLY a JSON array of short strings (1-3 words each). "
                        'Example: ["AI Regulation", "Apple Vision Pro", "Cybersecurity"]. '
                        "Focus on specific technologies, companies, and themes. No explanation."
                    ),
                },
                {"role": "user", "content": headlines},
            ],
            max_tokens=150,
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()
        topics = json.loads(raw)
        if isinstance(topics, list):
            return [str(t) for t in topics[:10]]
    except Exception:
        pass
    return _fallback_topics(articles)


# ── Fallbacks ─────────────────────────────────────────────────────────────────

def _fallback_summary(article: dict) -> str:
    desc = article.get("description", "")
    if desc:
        sentences = desc.split(". ")
        return ". ".join(sentences[:3]).strip()
    return "No summary available."


def _fallback_topics(articles: list[dict]) -> list[str]:
    """Extract simple topics from titles when no API key."""
    from collections import Counter
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
        "to", "for", "of", "and", "or", "but", "with", "from", "by",
        "how", "why", "what", "its", "it", "that", "this", "has", "have",
        "new", "will", "can", "may", "could", "about", "just", "not", "be",
        "your", "you", "now", "up", "out", "all", "get", "more", "than",
        "into", "over", "as", "after", "says", "said", "do", "no", "yes",
    }
    words: list[str] = []
    for a in articles:
        for w in a["title"].split():
            clean = w.strip(".,!?:;\"'()-—").capitalize()
            if len(clean) > 2 and clean.lower() not in stopwords:
                words.append(clean)
    return [w for w, _ in Counter(words).most_common(8)]
