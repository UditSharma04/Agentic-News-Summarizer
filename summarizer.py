"""
Summarizer Module — Agentic AI Core
Uses OpenAI for intelligent summaries, trending-topic extraction,
sentiment analysis, chat, and structured executive briefings.
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


# ── Sentiment Analysis ───────────────────────────────────────────────────────

def analyze_sentiment(articles: list[dict]) -> dict[str, str]:
    """
    Analyze sentiment for a batch of articles.
    Returns {title: "positive" | "negative" | "neutral"} for each article.
    """
    if not OPENAI_API_KEY or not articles:
        return _fallback_sentiment(articles)

    titles = [a["title"] for a in articles[:50]]
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles))

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Classify the sentiment of each tech news headline as exactly one of: "
                        '"positive", "negative", or "neutral".\n'
                        "Return ONLY a JSON object mapping headline number (as string) to sentiment.\n"
                        'Example: {"1": "positive", "2": "negative", "3": "neutral"}\n'
                        "No explanation. Just the JSON."
                    ),
                },
                {"role": "user", "content": numbered},
            ],
            max_tokens=500,
            temperature=0.1,
        )
        raw = response.choices[0].message.content.strip()
        parsed = json.loads(raw)
        result: dict[str, str] = {}
        for i, t in enumerate(titles):
            s = parsed.get(str(i + 1), "neutral")
            if s not in ("positive", "negative", "neutral"):
                s = "neutral"
            result[t] = s
        return result
    except Exception:
        return _fallback_sentiment(articles)


# ── Web search fallback for chat ──────────────────────────────────────────────

def _enrich_from_web(
    client: OpenAI,
    user_question: str,
    fallback_response: str,
) -> tuple[list[dict], str]:
    """Search Google News for the topic and build a response from real results.

    Returns (web_results, response_text).
    """
    from news_fetcher import search_web_news

    web_results_raw = search_web_news(user_question, max_results=5)
    if not web_results_raw:
        return [], fallback_response

    web_context = "\n".join(
        f"- [{r['source']}] {r['title']}: {r['description'][:250]}"
        for r in web_results_raw
    )

    try:
        web_resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a tech news assistant. The user asked about a topic "
                        "not covered in the local article feed. Below are real search "
                        "results from Google News (last 48 hours):\n\n"
                        f"{web_context}\n\n"
                        "Write a concise, factual summary paragraph based ONLY on "
                        "these search results. Reference specific findings. If the "
                        "results are not relevant to the user's question, say so "
                        "honestly and briefly explain what the results do cover."
                    ),
                },
                {"role": "user", "content": user_question},
            ],
            max_tokens=600,
            temperature=0.3,
        )
        response_text = web_resp.choices[0].message.content.strip()
    except Exception:
        response_text = fallback_response

    web_results = [
        {"title": r["title"], "url": r["url"], "source": r["source"]}
        for r in web_results_raw
    ]
    return web_results, response_text


# ── Chat about the news ──────────────────────────────────────────────────────

def chat_about_news(
    articles: list[dict],
    user_question: str,
    history: list[dict],
) -> dict:
    """
    Answer a user question about today's news using fetched articles as context.
    Returns a dict with: found, matched_articles, brief, response.
    """
    empty_result = {
        "found": False, "matched_articles": [], "web_results": [],
        "brief": "", "response": "",
    }

    if not OPENAI_API_KEY:
        empty_result["response"] = (
            "Set your OPENAI_API_KEY in the .env file to use the chat feature."
        )
        return empty_result

    context_lines: list[str] = []
    for i, a in enumerate(articles[:40], 1):
        line = f"{i}. [{a['source']}] {a['title']}"
        desc = a.get("description", "")
        if desc:
            line += f" -- {desc[:200]}"
        context_lines.append(line)
    context = "\n".join(context_lines)

    system_msg = (
        "You are a helpful tech news assistant. The user can ask questions about "
        "today's tech news. Below are the articles available today:\n\n"
        f"{context}\n\n"
        "You MUST respond in valid JSON with exactly these fields:\n"
        "{\n"
        '  "found_in_articles": true or false,\n'
        '  "article_numbers": [1-indexed numbers of relevant articles],\n'
        '  "brief": "1-2 sentence summary of the matched news",\n'
        '  "response": "Your full detailed response"\n'
        "}\n\n"
        "Rules:\n"
        "- If the user's question relates to ANY of the listed articles, set "
        "found_in_articles to true, list ALL matching article_numbers, write a "
        "concise brief, and give an insightful response.\n"
        "- If the topic is NOT covered by any listed article, set found_in_articles "
        "to false, article_numbers to [], brief to \"\", and in the response field "
        "provide a helpful, informative paragraph about the topic based on your "
        "knowledge. Focus strictly on developments from the last 48 hours. Be "
        "factual and current.\n"
        "- Always return valid JSON only, no markdown code fences."
    )

    messages = [{"role": "system", "content": system_msg}]
    for h in history[-20:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_question})

    try:
        client = _get_client()
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=800,
            temperature=0.4,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content.strip()
        parsed = json.loads(raw)

        found = parsed.get("found_in_articles", False)
        article_nums = parsed.get("article_numbers", [])
        brief = parsed.get("brief", "")
        response_text = parsed.get("response", "")

        matched_articles = []
        for n in article_nums:
            if isinstance(n, int) and 1 <= n <= len(articles):
                a = articles[n - 1]
                matched_articles.append({
                    "title": a["title"],
                    "url": a["url"],
                    "source": a["source"],
                    "description": a.get("description", "")[:300],
                    "content": a.get("content", ""),
                    "category": a.get("category", ""),
                })

        if not found:
            web_results, response_text = _enrich_from_web(
                client, user_question, response_text,
            )
            return {
                "found": False,
                "matched_articles": [],
                "web_results": web_results,
                "brief": "",
                "response": response_text,
            }

        return {
            "found": True,
            "matched_articles": matched_articles,
            "web_results": [],
            "brief": brief,
            "response": response_text,
        }
    except Exception as e:
        empty_result["response"] = f"Failed to get response: {e}"
        return empty_result


# ── Fallbacks ─────────────────────────────────────────────────────────────────

def _fallback_summary(article: dict) -> str:
    desc = article.get("description", "")
    if desc:
        sentences = desc.split(". ")
        return ". ".join(sentences[:3]).strip()
    return "No summary available."


def _fallback_topics(articles: list[dict]) -> list[str]:
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
            clean = w.strip(".,!?:;\"'()-\u2014").capitalize()
            if len(clean) > 2 and clean.lower() not in stopwords:
                words.append(clean)
    return [w for w, _ in Counter(words).most_common(8)]


def _fallback_sentiment(articles: list[dict]) -> dict[str, str]:
    """Simple keyword-based fallback sentiment."""
    positive_words = {"launch", "growth", "profit", "raise", "fund", "breakthrough",
                      "success", "win", "award", "record", "boost", "gain", "partner",
                      "innovation", "upgrade", "improve", "milestone"}
    negative_words = {"hack", "breach", "layoff", "cut", "loss", "crash", "fail",
                      "sue", "lawsuit", "fine", "ban", "risk", "threat", "attack",
                      "vulnerability", "decline", "drop", "warning", "fraud"}
    result: dict[str, str] = {}
    for a in articles:
        words = set(a["title"].lower().split())
        pos = len(words & positive_words)
        neg = len(words & negative_words)
        if pos > neg:
            result[a["title"]] = "positive"
        elif neg > pos:
            result[a["title"]] = "negative"
        else:
            result[a["title"]] = "neutral"
    return result
