# Tech News Aggregator & Summarizer

An **agentic AI-powered** application that fetches tech news from 8 top sources, generates intelligent summaries, performs sentiment analysis, and provides an interactive chat interface — all wrapped in a modern dark-themed web UI.

---

## Table of Contents

- [Features](#features)
- [Demo](#demo)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [News Sources](#news-sources)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **Multi-source aggregation** — Fetches articles concurrently from 8 tech news sources using RSS feeds and APIs
- **AI-powered executive briefings** — Generates daily briefings with top stories, trends, market signals, and quick bites
- **Per-article AI summaries** — On-demand summaries with key facts, impact analysis, and key players
- **Sentiment analysis** — Batch classifies all headlines as positive, negative, or neutral
- **Trending topics** — Extracts real-time topic tags from current headlines
- **Interactive AI chat** — Ask questions about today's news with full article context
- **Analytics dashboard** — Four interactive Altair charts: articles by source, category distribution, publish timeline, and sentiment breakdown
- **Keyword alerts** — Set watchlist keywords to highlight matching articles with alert badges
- **Smart filtering** — Filter by source, category, or search query; sort by date, reading time, or source
- **Briefing history** — Auto-saves past AI briefings to local JSON for later review
- **Deduplication** — Removes near-duplicate articles across sources (70% word overlap threshold)
- **Fallback mode** — Works without an API key using keyword-based sentiment and extractive summaries

---

## Demo

Once running, the app is accessible at `http://localhost:8501` and includes five tabs:

| Tab | Description |
|-----|-------------|
| **AI Briefing** | Generate and review AI-powered executive summaries |
| **All Articles** | Browse, search, sort, and summarize individual articles |
| **Analytics** | Visual charts of the news landscape |
| **Ask AI** | Chat interface for questions about today's news |
| **How It Works** | Interactive architecture diagram and step-by-step breakdown |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | [Streamlit](https://streamlit.io/) with custom CSS (dark glassmorphism theme) |
| **Charts** | [Altair](https://altair-viz.github.io/) (interactive visualizations) |
| **Data Fetching** | [feedparser](https://feedparser.readthedocs.io/) (RSS/Atom), [requests](https://requests.readthedocs.io/) (HTTP/API) |
| **HTML Parsing** | [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) |
| **AI/LLM** | [OpenAI GPT](https://platform.openai.com/) (gpt-4o-mini by default) |
| **Concurrency** | Python `ThreadPoolExecutor` for parallel source fetching |
| **Config** | [python-dotenv](https://github.com/theskumar/python-dotenv) for environment variable management |

---

## Prerequisites

- **Python 3.10+** (tested with Python 3.13)
- **pip** (Python package manager)
- **OpenAI API key** (optional — the app works without it but AI features will be disabled)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/UditSharma04/Manish_agentic.git
cd Manish_agentic
```

### 2. Create a virtual environment

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (Command Prompt):**

```bash
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**

```bash
python -m venv venv
venv\Scripts\Activate.ps1
```

You should see `(venv)` at the beginning of your terminal prompt, confirming the virtual environment is active.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

Open the `.env` file and add your OpenAI API key:

```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

> **Note:** The app runs without an API key, but AI summaries, briefings, sentiment analysis, trending topics, and chat will use basic fallback methods instead.

### 5. Run the application

```bash
streamlit run app.py
```

The app will open automatically in your browser at **http://localhost:8501**.

### 6. Deactivate the virtual environment (when done)

```bash
deactivate
```

---

## Configuration

All settings are configured via environment variables in the `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *(none)* | Your OpenAI API key ([get one here](https://platform.openai.com/api-keys)) |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model to use (`gpt-4o`, `gpt-4o-mini`, `gpt-3.5-turbo`) |
| `MAX_ARTICLES_PER_SOURCE` | `5` | Maximum articles to fetch per news source |
| `SUMMARY_MAX_TOKENS` | `300` | Maximum tokens for each article summary |
| `FETCH_TIMEOUT` | `15` | HTTP request timeout in seconds |

---

## Usage

### Generating an AI Briefing

1. Open the **AI Briefing** tab
2. Click **Generate Briefing**
3. The AI will analyze all fetched headlines and produce an executive summary with top stories, trends, and market signals
4. Past briefings are saved automatically and viewable in the "Past Briefings" section

### Browsing Articles

1. Use the **sidebar** to filter by source or category
2. Use the **search bar** to filter by keywords in titles/descriptions
3. Use the **sort dropdown** to order by date, reading time, or source
4. Click **Summarize** on any article card to get an AI-generated summary

### Setting Keyword Alerts

1. In the sidebar, enter comma-separated keywords (e.g., `AI, Apple, cybersecurity`)
2. Matching articles will be highlighted with an orange **ALERT** badge
3. The stats bar shows a live alert count

### Using AI Chat

1. Open the **Ask AI** tab
2. Type questions like "What are the biggest AI stories today?" or "Compare the Apple and Google news"
3. The AI has full context of all fetched articles

---

## Project Structure

```
Manish_agentic/
├── app.py                  # Streamlit web application (UI, tabs, styling)
├── news_fetcher.py         # Concurrent article fetching from RSS & Hacker News API
├── summarizer.py           # OpenAI-powered summarization, sentiment, chat, topics
├── history.py              # Briefing history persistence (local JSON)
├── config.py               # App configuration and news source definitions
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

### Module Responsibilities

| Module | Purpose |
|--------|---------|
| `app.py` | Streamlit UI with 5 tabs, custom CSS, article cards, charts, and chat interface |
| `news_fetcher.py` | Fetches articles from RSS feeds (feedparser) and Hacker News Firebase API; handles deduplication, date parsing, and reading time estimation |
| `summarizer.py` | OpenAI integration for article summaries, executive briefings, trending topics, sentiment analysis, and conversational Q&A; includes keyword-based fallbacks |
| `history.py` | Saves and loads AI briefing history to/from a local JSON file |
| `config.py` | Loads environment variables and defines the 8 news source configurations |

---

## How It Works

1. **Fetch** — `news_fetcher.py` connects to 8 sources concurrently using `ThreadPoolExecutor`. RSS sources are parsed with `feedparser`; Hacker News uses its Firebase REST API.

2. **Parse & Clean** — Raw HTML is stripped with BeautifulSoup. Titles, URLs, descriptions, content, and publish dates are extracted. Dates are normalized to UTC. Reading time is estimated at 200 wpm.

3. **Deduplicate** — Near-duplicate articles (same story from multiple sources) are removed using title similarity matching with a 70% word overlap threshold.

4. **Analyze** — Headlines are sent to GPT in batch calls for sentiment classification (positive/negative/neutral) and trending topic extraction.

5. **Display** — Articles render in a two-column card grid with source favicons, category tags, reading time, sentiment indicators, and alert badges.

6. **Summarize** — On-demand per-article summaries and executive briefings are generated via OpenAI with structured prompts. Briefings are auto-saved to local JSON.

7. **Chat** — A conversational interface injects all fetched articles as context into the system prompt, enabling users to ask questions about the day's news.

---

## News Sources

| Source | Type | Category |
|--------|------|----------|
| [TechCrunch](https://techcrunch.com) | RSS | General Tech |
| [The Verge](https://theverge.com) | RSS | General Tech |
| [Ars Technica](https://arstechnica.com) | RSS | Deep Tech |
| [Wired](https://wired.com) | RSS | Tech & Culture |
| [Hacker News](https://news.ycombinator.com) | API | Developer & Startups |
| [MIT Technology Review](https://technologyreview.com) | RSS | Research & Innovation |
| [VentureBeat](https://venturebeat.com) | RSS | AI & Enterprise |
| [The Register](https://theregister.com) | RSS | Infrastructure & Security |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m "Add your feature"`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the [MIT License](LICENSE).
