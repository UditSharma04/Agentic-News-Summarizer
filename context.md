# Project Context: Tech News Aggregator & Summarizer

> This document provides full context for anyone who needs to understand, document, or extend this project.

---

## 1. Problem Statement

Keeping up with the fast-moving tech news landscape is overwhelming. Engineers, product managers, and tech leaders must monitor multiple news outlets daily (TechCrunch, The Verge, Hacker News, Wired, Ars Technica, etc.) to stay informed. There is no single tool that:

- Aggregates tech news from multiple trusted sources into one place.
- Removes duplicate stories that appear across outlets.
- Provides AI-generated executive briefings summarizing the day's top stories, trends, and market signals.
- Offers sentiment analysis across headlines to gauge the tone of the news cycle.
- Allows conversational Q&A about the day's news using a large language model.

**The manual process is time-consuming, fragmented, and lacks intelligent analysis.**

---

## 2. Goal / Objective

Build an **agentic AI-powered web application** that:

1. Automatically fetches tech news from 8 curated sources concurrently.
2. Deduplicates articles across sources using title-similarity matching.
3. Classifies headline sentiment (positive / negative / neutral) using OpenAI GPT.
4. Extracts trending topics from the current news cycle.
5. Generates on-demand per-article summaries and executive daily briefings.
6. Provides a conversational AI chat interface grounded in the day's articles.
7. Displays interactive analytics (charts for source distribution, sentiment, category, timeline).
8. Persists briefing history for later review.
9. Works gracefully without an API key via keyword-based fallbacks.

---

## 3. Tech Stack

### 3.1 Languages & Frameworks

| Layer            | Technology                                                                 |
|------------------|---------------------------------------------------------------------------|
| Language         | Python 3.10+ (tested with Python 3.13)                                    |
| Web Framework    | Streamlit (reactive, widget-based Python web UI)                           |
| Styling          | Custom CSS injected into Streamlit (dark glassmorphism theme)              |
| Charts           | Altair (declarative statistical visualization) + Pandas (data wrangling)   |

### 3.2 AI / LLM

| Component           | Detail                                                        |
|----------------------|---------------------------------------------------------------|
| Provider             | OpenAI                                                        |
| Default Model        | `gpt-4o-mini` (configurable to `gpt-4o` or `gpt-3.5-turbo`)  |
| Python SDK           | `openai >= 1.12.0`                                            |
| Uses                 | Summarization, sentiment analysis, trending topics, chat Q&A  |
| Fallback (no key)    | Keyword-based sentiment, extractive summaries, word-frequency topics |

### 3.3 Data Fetching & Parsing

| Library          | Purpose                                              |
|------------------|------------------------------------------------------|
| `feedparser`     | Parse RSS and Atom feeds from 7 news sources          |
| `requests`       | HTTP client for Hacker News API and full-body fetches  |
| `beautifulsoup4` | HTML stripping and content cleaning                    |
| `newspaper3k`    | Article body extraction (dependency)                   |
| `lxml`           | Fast XML/HTML parser backend                           |

### 3.4 Concurrency

- Python `concurrent.futures.ThreadPoolExecutor` for parallel fetching from all 8 sources simultaneously.

### 3.5 Configuration & Environment

- `python-dotenv` loads variables from `.env` file.
- All tunable settings (API key, model, timeouts, article limits) are environment variables.

### 3.6 Development Tools Used to Build This Project

| Tool               | Role                                                    |
|--------------------|---------------------------------------------------------|
| VS Code / Cursor   | Primary IDE                                             |
| GitHub Copilot     | AI pair-programming assistant used during development    |
| OpenAI API         | Powers all runtime AI features (summaries, chat, etc.)   |
| Git + GitHub       | Version control and remote repository                    |
| Terminal (zsh)     | Running Streamlit dev server, pip installs               |

---

## 4. Architecture & Workflow

### 4.1 High-Level Flow

```
User opens Streamlit app (localhost:8501)
        │
        ▼
┌───────────────────────────────────────────┐
│  1. FETCH  (news_fetcher.py)              │
│     - ThreadPoolExecutor spawns workers   │
│     - 7 RSS sources → feedparser.parse()  │
│     - 1 Hacker News → Firebase REST API   │
│     - Each article: extract title, URL,   │
│       description, content, publish date  │
│     - Clean HTML with BeautifulSoup       │
│     - Normalize dates to UTC              │
│     - Estimate reading time (200 wpm)     │
└───────────────┬───────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────┐
│  2. DEDUPLICATE  (news_fetcher.py)        │
│     - Normalize titles (lowercase, strip  │
│       punctuation)                        │
│     - Compare word overlap between titles │
│     - If overlap > 70% → mark duplicate   │
│     - Keep first occurrence only          │
└───────────────┬───────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────┐
│  3. ANALYZE  (summarizer.py)              │
│     - Batch all headlines → single GPT    │
│       call for sentiment classification   │
│     - Extract 8-10 trending topics via    │
│       GPT from current headlines          │
│     - Cache results (10-min TTL via       │
│       @st.cache_data)                     │
└───────────────┬───────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────┐
│  4. DISPLAY  (app.py)                     │
│     - 5 tabs: AI Briefing, All Articles,  │
│       Analytics, Ask AI, How It Works     │
│     - Sidebar: source/category filters,   │
│       keyword alerts, search              │
│     - 2-column card grid with sentiment   │
│       color indicators, favicons, badges  │
│     - Stats bar: article count, sources,  │
│       avg sentiment, alert count, time    │
└───────────────┬───────────────────────────┘
                │
        (User interaction)
                │
        ┌───────┴────────┬──────────────┬──────────────┐
        ▼                ▼              ▼              ▼
  ┌──────────┐   ┌────────────┐  ┌──────────┐  ┌──────────┐
  │ Summarize│   │  Executive │  │   Chat   │  │Analytics │
  │ Article  │   │  Briefing  │  │  Q & A   │  │  Charts  │
  │(per card)│   │ (all news) │  │(ask AI)  │  │ (Altair) │
  └────┬─────┘   └─────┬──────┘  └────┬─────┘  └──────────┘
       │               │              │
       ▼               ▼              ▼
   OpenAI GPT      OpenAI GPT     OpenAI GPT
   (structured     (executive     (system prompt
    prompt)         prompt)        includes all
                       │           articles as
                       ▼           context)
                 Save to JSON
                 (history.py)
```

### 4.2 Step-by-Step Workflow

1. **App Startup**: `streamlit run app.py` boots the Streamlit server. `app.py` imports `config.py`, `news_fetcher.py`, `summarizer.py`, and `history.py`.

2. **Config Loading**: `config.py` reads `.env` via `python-dotenv` and exposes settings as module-level constants (`OPENAI_API_KEY`, `OPENAI_MODEL`, `MAX_ARTICLES_PER_SOURCE`, etc.). It also defines the `NEWS_SOURCES` list (8 dicts, each with name, type, URL, category, domain).

3. **News Fetching**: On page load, `fetch_all_news()` in `news_fetcher.py` is called (cached for 10 minutes). It:
   - Creates a `ThreadPoolExecutor` and submits one task per source.
   - RSS sources are fetched with `feedparser.parse(url)`.
   - Hacker News uses the Firebase REST API (`/topstories.json` then `/item/{id}.json` for each story).
   - Each raw entry is normalized into a dict: `{title, url, description, content, source, category, domain, published, reading_time}`.
   - HTML is stripped with `BeautifulSoup(text, "html.parser").get_text()`.
   - Dates are parsed and normalized to UTC.
   - Reading time is estimated at 200 words per minute.

4. **Deduplication**: `_deduplicate(articles)` normalizes titles to lowercase, strips punctuation, computes word-set overlap between every pair, and removes articles with >70% overlap (keeping the first seen).

5. **Sentiment Analysis**: `analyze_sentiment(articles)` sends all headlines in a single batch to GPT with a prompt asking for `positive`, `negative`, or `neutral` per headline. Results are parsed and attached to each article. Fallback: keyword matching against positive/negative word lists.

6. **Trending Topics**: `extract_trending_topics(articles)` sends headlines to GPT asking for 8-10 trending topic tags. Fallback: word frequency analysis (most common non-stopword nouns).

7. **UI Rendering** (`app.py`):
   - Custom CSS is injected for the dark glassmorphism theme.
   - A hero section with animated gradient is displayed.
   - Sidebar allows filtering by source, category, and keyword alerts.
   - Stats bar shows article count, source count, average sentiment score, alert count, and current UTC time.
   - Trending topic pills are displayed below the stats bar.
   - Articles are rendered in a 2-column card grid with source favicons (Google Favicons API), category tags, reading time, sentiment-colored left border, and optional alert badges.

8. **On-Demand Summarization**: When a user clicks "Summarize" on an article card:
   - If the article content is < 200 characters, `fetch_article_body(url)` retrieves the full page.
   - The content is sent to GPT with a structured prompt requesting: summary, "why it matters", and key players.
   - Result is cached in `st.session_state` keyed by article index.

9. **Executive Briefing**: When the user clicks "Generate Briefing":
   - All article headlines + descriptions are concatenated into a digest.
   - Sent to GPT with an executive briefing prompt asking for: Top Stories, Trends & Themes, Market Signals, Quick Bites.
   - The briefing is displayed and auto-saved to `briefing_history.json` via `history.save_briefing()`.

10. **AI Chat**: The "Ask AI" tab provides a conversational interface:
    - All fetched articles are injected into the system prompt as context.
    - User messages and AI responses are stored in `st.session_state.chat_history` (last 20 exchanges).
    - Each user message triggers a GPT call with the full conversation history.

11. **Analytics**: Four Altair charts are generated using Pandas DataFrames:
    - Articles by source (horizontal bar chart)
    - Category distribution (donut chart)
    - Publish timeline by hour (bar chart)
    - Sentiment breakdown by source (stacked bar chart)

12. **Briefing History**: `history.py` manages persistence:
    - `save_briefing(text, count)` appends `{timestamp, briefing, article_count}` to `briefing_history.json`.
    - `load_history()` reads and returns the last 20 entries.

---

## 5. External APIs & Integrations

| API / Service                  | Endpoint / URL                                          | Auth         | Purpose                                   |
|-------------------------------|---------------------------------------------------------|--------------|-------------------------------------------|
| OpenAI Chat Completions       | `https://api.openai.com/v1/chat/completions`            | API Key      | Summaries, sentiment, topics, chat         |
| Hacker News Firebase API      | `https://hacker-news.firebaseio.com/v0/topstories.json` | None         | Fetch top story IDs                        |
| Hacker News Item API          | `https://hacker-news.firebaseio.com/v0/item/{id}.json`  | None         | Fetch individual story details             |
| TechCrunch RSS                | `https://techcrunch.com/feed/`                          | None         | RSS feed                                   |
| The Verge RSS                 | `https://www.theverge.com/rss/index.xml`                | None         | Atom feed                                  |
| Ars Technica RSS              | `https://feeds.arstechnica.com/arstechnica/index`       | None         | RSS feed                                   |
| Wired RSS                     | `https://www.wired.com/feed/rss`                        | None         | RSS feed                                   |
| MIT Technology Review RSS     | `https://www.technologyreview.com/feed/`                | None         | RSS feed                                   |
| VentureBeat RSS               | `https://venturebeat.com/feed/`                         | None         | RSS feed                                   |
| The Register Atom             | `https://www.theregister.com/headlines.atom`            | None         | Atom feed                                  |
| Google Favicons               | `https://www.google.com/s2/favicons?sz=32&domain=...`   | None         | Source logos in article cards               |

---

## 6. Algorithms

### 6.1 Deduplication Algorithm

```
For each pair of articles (A, B):
    1. Normalize titles: lowercase, strip punctuation
    2. Tokenize into word sets: words_A, words_B
    3. Compute overlap = |words_A ∩ words_B| / min(|words_A|, |words_B|)
    4. If overlap > 0.70 → mark B as duplicate, keep A
```

### 6.2 Fallback Sentiment (No API Key)

```
positive_words = {"launch", "grow", "breakthrough", "profit", "innovation", ...}
negative_words = {"crash", "breach", "layoff", "hack", "decline", ...}

For each headline:
    1. Tokenize to lowercase words
    2. Count matches in positive_words and negative_words
    3. If positive_count > negative_count → "positive"
       If negative_count > positive_count → "negative"
       Else → "neutral"
```

### 6.3 Reading Time Estimation

```
reading_time_minutes = ceil(word_count / 200)
```

### 6.4 Caching Strategy

- `@st.cache_data(ttl=600)` (10 minutes) on: `fetch_all_news()`, `analyze_sentiment()`, `extract_trending_topics()`
- Per-article summaries cached in `st.session_state[f"sum_{article_index}"]`

---

## 7. Project File Structure

```
Manish_agentic/
├── app.py                  # Main Streamlit app (743 lines) — UI, tabs, CSS, rendering
├── news_fetcher.py         # News fetching module (222 lines) — RSS, HN API, dedup
├── summarizer.py           # AI module (292 lines) — summaries, sentiment, chat, topics
├── history.py              # History persistence (42 lines) — save/load briefings
├── config.py               # Configuration (79 lines) — env vars, source definitions
├── requirements.txt        # Python dependencies (9 packages)
├── .env.example            # Environment variable template
├── .env                    # Actual environment variables (gitignored)
├── .gitignore              # Git ignore rules
├── briefing_history.json   # Persisted briefing history (gitignored)
└── README.md               # Project documentation
```

---

## 8. Dependencies (requirements.txt)

```
feedparser>=6.0.0
openai>=1.12.0
requests>=2.31.0
streamlit>=1.31.0
python-dotenv>=1.0.0
beautifulsoup4>=4.12.0
newspaper3k>=0.2.8
lxml>=5.1.0
lxml_html_clean>=0.1.0
```

---

## 9. How to Run

```bash
# 1. Clone
git clone https://github.com/UditSharma04/Agentic-News-Summarizer

# move the current directory to the cloned folder in your terminal
cd Agentic-News-Summarizer.  

# 2. Virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 5. Run
streamlit run app.py
# Opens at http://localhost:8501
```

---

## 10. Key Design Decisions

1. **Streamlit over Flask/Django**: Chosen for rapid prototyping — no frontend code needed, widgets are Python functions, hot reload built in.
2. **ThreadPoolExecutor over asyncio**: Simpler threading model sufficient for I/O-bound RSS/API fetches; no need for async complexity.
3. **gpt-4o-mini as default**: Balances cost and quality — cheap enough for batch sentiment/topic calls, smart enough for good summaries.
4. **Fallback mode**: Ensures the app is fully functional without an API key, making it easy to demo and test.
5. **Local JSON for history**: No database overhead — briefing history is append-only and capped at 20 entries.
6. **10-minute cache TTL**: Prevents hammering news sources on every Streamlit rerun while keeping content reasonably fresh.
7. **70% dedup threshold**: Tuned to catch cross-source duplicates without accidentally merging related-but-different stories.
