"""
Summarizer Module
Uses OpenAI to provide intelligent summaries of tech news articles.
Implements an agentic workflow: fetch context, reason, and summarize.
"""

from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL, SUMMARY_MAX_TOKENS

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Lazy-init the OpenAI client."""
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


# ── Single-article summary ───────────────────────────────────────────────────

def summarize_article(article: dict) -> str:
    """
    Produce a concise summary for a single article.

    Uses the title, description, and any available content to generate
    a 2-3 sentence summary highlighting key points.
    """
    if not OPENAI_API_KEY:
        return _fallback_summary(article)

    context_parts = [f"Title: {article['title']}"]
    if article.get("description"):
        context_parts.append(f"Description: {article['description'][:1000]}")
    if article.get("content"):
        context_parts.append(f"Content: {article['content'][:2000]}")
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
                        "You are a tech news analyst. Summarize the following article "
                        "in 2-3 concise sentences. Focus on the key facts, impact, and "
                        "why it matters to the tech community. Be objective and informative."
                    ),
                },
                {"role": "user", "content": context},
            ],
            max_tokens=SUMMARY_MAX_TOKENS,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[WARNING] Summarization failed: {e}")
        return _fallback_summary(article)


# ── Mega-summary (all articles) ──────────────────────────────────────────────

def summarize_all(articles: list[dict]) -> str:
    """
    Generate a high-level briefing from a batch of articles.

    This is the *agentic* core: the model receives all headlines + descriptions,
    identifies key themes, and produces a structured executive briefing.
    """
    if not OPENAI_API_KEY:
        return "⚠️ Set your `OPENAI_API_KEY` in the `.env` file to enable AI-powered summaries."

    if not articles:
        return "No articles available to summarize."

    # Build a digest for the model
    digest_lines: list[str] = []
    for i, a in enumerate(articles, 1):
        line = f"{i}. [{a['source']}] {a['title']}"
        if a.get("description"):
            line += f" — {a['description'][:200]}"
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
                        "You are an expert tech news analyst producing a daily briefing. "
                        "Given the following list of today's top tech headlines and descriptions, "
                        "produce a structured summary with the following sections:\n\n"
                        "1. **Top Stories** — The 3-4 most significant stories and why they matter.\n"
                        "2. **Trends & Themes** — Common themes or emerging trends across stories.\n"
                        "3. **Quick Bites** — One-line summaries for remaining noteworthy articles.\n\n"
                        "Use clear, concise language. Be insightful but objective. "
                        "Reference specific articles by number when appropriate."
                    ),
                },
                {"role": "user", "content": digest},
            ],
            max_tokens=1000,
            temperature=0.4,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Failed to generate summary: {e}"


# ── Fallback (no API key) ────────────────────────────────────────────────────

def _fallback_summary(article: dict) -> str:
    """Return the description as-is when no OpenAI key is configured."""
    desc = article.get("description", "")
    if desc:
        sentences = desc.split(". ")
        return ". ".join(sentences[:3]).strip()
    return "No summary available."
