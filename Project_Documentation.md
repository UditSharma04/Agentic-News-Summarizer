# Tech News Aggregator & Summarizer

### Project Documentation

**Author:** _[Your Name]_
**Date:** February 2026
**Version:** 1.0

---

## 1. Executive Summary

The **Tech News Aggregator & Summarizer** is an AI-powered web application that consolidates tech news from eight trusted sources into a single, intelligent dashboard. It fetches articles concurrently, removes cross-source duplicates, classifies headline sentiment, extracts trending topics, and generates executive-level daily briefings -- all powered by OpenAI's GPT models.

The application was built using Python and Streamlit as a rapid-prototype agentic AI tool. It demonstrates practical use of large language models for real-time information synthesis, moving beyond simple chatbot interactions into a system that autonomously fetches, processes, analyzes, and presents structured intelligence from unstructured web data.

---

## 2. Problem Statement

Technology professionals -- engineers, product managers, and leadership -- need to stay current with the rapidly evolving tech landscape. This currently requires manually visiting multiple news outlets (TechCrunch, Hacker News, Wired, The Verge, etc.), reading through dozens of articles, and mentally synthesizing patterns and trends.

**Core pain points:**

- **Fragmented sources** -- Important stories are scattered across 8+ websites with no unified view.
- **Duplicate coverage** -- The same story appears on multiple outlets, wasting reading time.
- **No intelligent analysis** -- Manual reading provides no automated sentiment tracking, trend detection, or executive summaries.
- **Time-intensive** -- A thorough daily news review can take 30-60 minutes with no structured output to share with a team.

There is no existing lightweight tool that aggregates, deduplicates, summarizes, and enables conversational Q&A over tech news in a single interface.

---

## 3. Project Goal

Build a self-contained web application that **automatically aggregates tech news from 8 curated sources** and applies AI to transform raw articles into actionable intelligence -- summaries, sentiment scores, trending topics, executive briefings, and a conversational Q&A interface -- all accessible through a modern dashboard.

### Objectives

1. Fetch articles from 8 sources concurrently with parallel network calls.
2. Remove duplicate stories across sources using title-similarity matching.
3. Classify headline sentiment (positive / negative / neutral) via GPT.
4. Extract trending topics from the current news cycle.
5. Generate on-demand per-article summaries and daily executive briefings.
6. Provide a chat interface for asking questions grounded in the day's articles.
7. Display interactive analytics charts for the news landscape.
8. Persist briefing history for later review.
9. Operate gracefully without an API key via keyword-based fallbacks.

---

## 4. Tech Stack & Tools

### 4.1 Runtime Stack

| Layer | Technology | Why |
|-------|------------|-----|
| Language | Python 3.10+ | Ecosystem for AI/ML, rapid prototyping |
| Web Framework | Streamlit | No frontend code needed, reactive widgets, hot reload |
| AI / LLM | OpenAI GPT (`gpt-4o-mini` default) | Cost-effective, fast, strong summarization quality |
| Charts | Altair + Pandas | Declarative, interactive visualizations from DataFrames |
| RSS Parsing | feedparser | Industry-standard RSS/Atom parser |
| HTTP Client | requests | Simple, reliable HTTP for API calls and page fetches |
| HTML Parsing | BeautifulSoup4 | Extract clean text from raw HTML |
| Concurrency | ThreadPoolExecutor | Simple parallel I/O for fetching 8 sources simultaneously |
| Config | python-dotenv | Load secrets and settings from `.env` file |
| Storage | Local JSON file | Lightweight briefing history, no database needed |

### 4.2 Development Tools

| Tool | Role in This Project |
|------|---------------------|
| **VS Code / Cursor IDE** | Primary development environment |
| **GitHub Copilot** | AI pair-programming assistant used throughout development |
| **OpenAI API** | Powers all runtime AI features (summaries, sentiment, chat, topics) |
| **Git + GitHub** | Version control and remote repository hosting |
| **Python venv** | Isolated dependency management |
| **Terminal (zsh)** | Running dev server, package installs, git operations |

---

## 5. System Architecture

The application follows a **modular pipeline architecture** with five Python modules, each responsible for a single concern:

```
┌─────────────────────────────────────────────────────────┐
│                    USER (Browser)                        │
│               http://localhost:8501                      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  app.py  —  Streamlit UI Layer                           │
│  5 Tabs: AI Briefing | Articles | Analytics | Chat | How │
│  Custom CSS (dark glassmorphism theme)                   │
│  Sidebar filters, stats bar, card grid, charts           │
└────┬──────────┬──────────────┬──────────────┬────────────┘
     │          │              │              │
     ▼          ▼              ▼              ▼
┌─────────┐ ┌──────────┐ ┌─────────┐ ┌────────────┐
│ news_   │ │summarizer│ │history  │ │ config.py  │
│fetcher  │ │  .py     │ │  .py    │ │            │
│  .py    │ │          │ │         │ │ .env vars  │
│         │ │ OpenAI   │ │ JSON    │ │ 8 source   │
│ RSS +   │ │ GPT calls│ │ read/   │ │ definitions│
│ HN API  │ │ fallbacks│ │ write   │ │            │
└────┬────┘ └────┬─────┘ └────┬────┘ └────────────┘
     │           │             │
     ▼           ▼             ▼
  8 News      OpenAI       briefing_
  Sources     API          history.json
```

| Module | Lines | Responsibility |
|--------|-------|----------------|
| `app.py` | 743 | UI rendering, tabs, CSS styling, user interaction handling |
| `news_fetcher.py` | 222 | Concurrent fetching from RSS feeds and Hacker News API, HTML cleaning, deduplication |
| `summarizer.py` | 292 | All OpenAI GPT interactions: summaries, briefings, sentiment, topics, chat; fallback logic |
| `history.py` | 42 | Read/write briefing history to local JSON (capped at 20 entries) |
| `config.py` | 79 | Environment variable loading, news source definitions |

---

## 6. Application Workflow

### Phase 1: Data Acquisition

When the app loads, `news_fetcher.py` spawns a **ThreadPoolExecutor** that fetches all 8 sources in parallel:

- **7 RSS/Atom sources** are parsed using `feedparser.parse(url)` -- each returns a list of entries with title, link, description, and publish date.
- **Hacker News** uses the Firebase REST API -- first fetches `/topstories.json` for story IDs, then fetches `/item/{id}.json` for each story's details.

For every article, the fetcher normalizes the data into a consistent structure (title, URL, description, content, source name, category, domain, UTC publish time, estimated reading time). HTML tags are stripped using BeautifulSoup. Results are cached for 10 minutes to avoid hammering sources on Streamlit reruns.

### Phase 2: Deduplication

The same breaking story often appears on multiple outlets. The deduplication algorithm normalizes each title to lowercase, strips punctuation, and computes **word-set overlap** between every pair of titles. If two titles share more than **70% of their words**, the later one is discarded. This threshold was tuned to catch true duplicates without accidentally merging related-but-distinct stories.

### Phase 3: AI Analysis

Two batch GPT calls process all headlines at once (cached for 10 minutes):

1. **Sentiment classification** -- All headlines are sent in a single prompt; GPT returns `positive`, `negative`, or `neutral` for each. A colored border on each article card reflects the result.
2. **Trending topics** -- Headlines are sent to GPT which extracts 8-10 topic tags (e.g., "AI Regulation", "Apple Vision Pro", "Cybersecurity"). These appear as clickable pills in the UI.

If no API key is configured, fallback methods activate: keyword matching against positive/negative word lists for sentiment, and word-frequency analysis for topics.

### Phase 4: Display & Interaction

The Streamlit UI renders five tabs:

| Tab | What It Shows |
|-----|---------------|
| **AI Briefing** | Generate/view executive daily briefings with top stories, trends, market signals |
| **All Articles** | 2-column card grid with filters (source, category, search), sort options, per-article summaries |
| **Analytics** | 4 Altair charts: articles by source, category distribution, hourly timeline, sentiment by source |
| **Ask AI** | Chat interface where GPT answers questions using all articles as context |
| **How It Works** | Architecture diagram and step-by-step explanation |

### Phase 5: On-Demand AI Features

- **Article Summary**: User clicks "Summarize" on a card. If the article body is too short, the full page is fetched. GPT returns a structured summary with key facts, impact analysis ("why it matters"), and key players mentioned.
- **Executive Briefing**: User clicks "Generate Briefing". All headlines and descriptions are sent to GPT with an executive briefing prompt. The output is structured into Top Stories, Trends & Themes, Market Signals, and Quick Bites. It is automatically saved to `briefing_history.json`.
- **AI Chat**: The user types a question. All fetched articles are injected into the system prompt as context. GPT responds with article-grounded answers. Conversation history (last 20 exchanges) is maintained in session state.

---

## 7. External APIs & Data Sources

| Service | Endpoint | Authentication | Usage |
|---------|----------|---------------|-------|
| OpenAI Chat Completions | `api.openai.com/v1/chat/completions` | API Key (Bearer token) | Summaries, sentiment, topics, chat |
| Hacker News (Firebase) | `hacker-news.firebaseio.com/v0/` | None | Top stories and item details |
| TechCrunch | `techcrunch.com/feed/` | None | RSS feed (General Tech) |
| The Verge | `theverge.com/rss/index.xml` | None | Atom feed (General Tech) |
| Ars Technica | `feeds.arstechnica.com/arstechnica/index` | None | RSS feed (Deep Tech) |
| Wired | `wired.com/feed/rss` | None | RSS feed (Tech & Culture) |
| MIT Technology Review | `technologyreview.com/feed/` | None | RSS feed (Research & Innovation) |
| VentureBeat | `venturebeat.com/feed/` | None | RSS feed (AI & Enterprise) |
| The Register | `theregister.com/headlines.atom` | None | Atom feed (Infrastructure & Security) |
| Google Favicons | `google.com/s2/favicons?sz=32&domain=...` | None | Source logos in article cards |

---

## 8. Key Features

- **Multi-source concurrent aggregation** from 8 trusted tech outlets
- **AI executive briefings** with top stories, trends, market signals, and quick bites
- **Per-article AI summaries** with key facts, impact, and key players
- **Batch sentiment analysis** classifying every headline as positive, negative, or neutral
- **Trending topic extraction** showing 8-10 real-time topic tags
- **Interactive AI chat** for asking questions grounded in the day's news
- **Analytics dashboard** with 4 interactive Altair charts
- **Keyword alert system** with configurable watchlist and alert badges
- **Smart filtering & sorting** by source, category, search query, date, reading time
- **Cross-source deduplication** using 70% word-overlap threshold
- **Briefing history** auto-saved to local JSON for review
- **Fallback mode** that works fully without an OpenAI API key

---

## 9. Design Decisions & Trade-offs

| Decision | Rationale |
|----------|-----------|
| Streamlit over Flask/Django | No frontend code needed; Python-only reactive UI; built-in caching and session state; ideal for data-centric rapid prototyping |
| ThreadPoolExecutor over asyncio | Simpler model sufficient for I/O-bound RSS/API fetches; no async complexity for 8 concurrent tasks |
| `gpt-4o-mini` as default model | Best cost-to-quality ratio -- cheap enough for batch calls (sentiment on 40+ headlines), smart enough for quality summaries |
| Local JSON for briefing history | No database setup overhead; append-only, capped at 20 entries; sufficient for a single-user tool |
| 10-minute cache TTL | Balances freshness against rate-limiting; news doesn't change minute-to-minute |
| 70% dedup threshold | Empirically tuned -- catches "same story, different outlet" without false merges on related topics |
| Fallback mode (no API key) | Makes the app fully demoable and testable without any cost or key setup |

---

## 10. Future Scope

1. **Email/Slack delivery** -- Schedule daily briefings to be sent automatically to a team channel or email inbox.
2. **Persistent database** -- Replace local JSON with SQLite or PostgreSQL for multi-user support and search over historical briefings.
3. **Custom source management** -- Let users add/remove RSS feeds and API sources through the UI.
4. **User authentication** -- Add login so multiple users can have personalized keyword alerts and chat histories.
5. **Summarization of full articles** -- Use web scraping to fetch and summarize complete article bodies instead of just headlines and descriptions.
6. **Deployment** -- Containerize with Docker and deploy to a cloud platform (Streamlit Cloud, AWS, or GCP) for team-wide access.

---

## 11. Conclusion

This project demonstrates a practical application of agentic AI -- a system that autonomously fetches, cleans, deduplicates, analyzes, and synthesizes information from multiple unstructured web sources into structured, actionable intelligence. It combines concurrent data pipelines, large language model integration, and a modern web interface to solve a real productivity problem for tech professionals.

The modular architecture (5 focused Python files, ~1,400 lines total) keeps the codebase maintainable, and the fallback design ensures the application remains functional even without an API key. It serves as both a useful daily tool and a reference implementation for building LLM-powered data aggregation applications.
