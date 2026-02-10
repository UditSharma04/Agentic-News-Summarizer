# 📡 Tech News Aggregator & Summarizer

An **agentic AI-powered tool** that fetches tech news from multiple top sources and generates intelligent summaries — all in a clean, modern web interface.

## Features

- **Multi-source aggregation** — Pulls latest articles from TechCrunch, The Verge, Ars Technica, Wired, Hacker News, and MIT Technology Review
- **AI-powered briefings** — Generates an executive-style daily briefing identifying top stories, trends, and themes
- **Per-article summaries** — Click to get a concise AI summary of any individual article
- **Smart filtering** — Filter by source, category, or both
- **Beautiful UI** — Modern, responsive Streamlit interface with article cards and stats
- **Fallback mode** — Works without an API key (shows raw descriptions instead of AI summaries)

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure your API key

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 3. Run the app

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## Architecture

```
├── app.py             # Streamlit web application (UI layer)
├── news_fetcher.py    # Fetches articles from RSS feeds & Hacker News API
├── summarizer.py      # OpenAI-powered summarization (agentic core)
├── config.py          # Source definitions & app configuration
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variable template
└── README.md          # This file
```

### How it works

1. **Fetch** — `news_fetcher.py` pulls articles from 6 sources using RSS (via `feedparser`) and the Hacker News Firebase API
2. **Parse** — Extracts titles, descriptions, dates, and cleans HTML content
3. **Summarize** — `summarizer.py` sends article context to OpenAI and receives concise, insightful summaries
4. **Brief** — The "AI Briefing" mode sends all headlines to the LLM to identify themes, top stories, and trends
5. **Display** — `app.py` renders everything in a polished Streamlit interface with cards, filters, and stats

## News Sources

| Source | Type | Category |
|---|---|---|
| TechCrunch | RSS | General Tech |
| The Verge | RSS | General Tech |
| Ars Technica | RSS | Deep Tech |
| Wired | RSS | Tech & Culture |
| Hacker News | API | Developer & Startups |
| MIT Technology Review | RSS | Research & Innovation |

## Configuration

All settings can be configured via environment variables (`.env` file):

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | Your OpenAI API key (required for AI features) |
| `OPENAI_MODEL` | `gpt-4o-mini` | Which OpenAI model to use |
| `MAX_ARTICLES_PER_SOURCE` | `5` | Articles to fetch per source |
| `SUMMARY_MAX_TOKENS` | `300` | Max tokens for article summaries |
| `FETCH_TIMEOUT` | `15` | HTTP timeout in seconds |

## License

MIT
