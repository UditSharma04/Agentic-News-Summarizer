"""
Tech News Aggregator & Summarizer — Streamlit App v2
Premium dark-theme UI with AI-powered briefings, trending topics,
search, reading time, favicons, and an interactive architecture page.
"""

import re
import streamlit as st
from datetime import datetime, timezone

from config import NEWS_SOURCES, OPENAI_API_KEY
from news_fetcher import fetch_all_news, fetch_article_body
from summarizer import summarize_article, summarize_all, extract_trending_topics

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Tech News Aggregator",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""<style>
.block-container{padding-top:1.5rem}

/* Hero */
.hero{
    background:linear-gradient(135deg,#0f0c29 0%,#302b63 50%,#24243e 100%);
    padding:2.4rem 2.8rem;border-radius:18px;margin-bottom:1.6rem;
    position:relative;overflow:hidden;
}
.hero::before{
    content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;
    background:radial-gradient(circle,rgba(108,99,255,.12) 0%,transparent 60%);
    animation:pulse 8s ease-in-out infinite;
}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.1)}}
.hero h1{margin:0;font-size:2.3rem;color:#fff!important;position:relative;z-index:1}
.hero p{margin:.4rem 0 0;font-size:1.05rem;color:#c0bfff!important;position:relative;z-index:1}

/* Stat cards */
.stat-card{
    background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);
    border-radius:14px;padding:1.1rem 1rem;text-align:center;
    transition:border-color .2s;
}
.stat-card:hover{border-color:rgba(108,99,255,.3)}
.stat-icon{font-size:1.4rem;margin-bottom:.25rem}
.stat-num{font-size:1.7rem;font-weight:800;color:#6c63ff}
.stat-label{font-size:.78rem;color:#888e99;margin-top:.15rem}

/* Trending pills */
.trending-bar{display:flex;flex-wrap:wrap;gap:.5rem;padding:.5rem 0}
.trending-pill{
    display:inline-block;padding:.35rem .85rem;border-radius:20px;
    font-size:.82rem;font-weight:600;
    background:rgba(108,99,255,.1);border:1px solid rgba(108,99,255,.25);
    color:#c5bfff!important;transition:all .15s;cursor:default;
}
.trending-pill:hover{background:rgba(108,99,255,.2);border-color:#6c63ff}

/* Search */
div[data-testid="stTextInput"] input{
    background:rgba(255,255,255,.04)!important;
    border:1px solid rgba(255,255,255,.1)!important;
    color:#e0e0e5!important;border-radius:10px!important;
}

/* Article card */
.card{
    background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);
    border-radius:14px;padding:1.2rem 1.5rem;margin-bottom:.65rem;
    transition:all .2s;
}
.card:hover{
    border-color:rgba(108,99,255,.35);
    box-shadow:0 8px 30px rgba(108,99,255,.1);
    transform:translateY(-2px);
}
.card-header{display:flex;align-items:center;gap:.6rem;margin-bottom:.5rem}
.card-favicon{width:18px;height:18px;border-radius:3px;opacity:.85}
.card-source{
    font-size:.75rem;font-weight:700;text-transform:uppercase;
    letter-spacing:.6px;color:#a89bff;
}
.card-meta-right{margin-left:auto;font-size:.72rem;color:#666e7a}
.card-title{font-size:1.12rem;font-weight:700;line-height:1.38;margin-bottom:.35rem}
.card-title a{color:#ededf2!important;text-decoration:none;transition:color .15s}
.card-title a:hover{color:#a89bff!important}
.card-desc{font-size:.9rem;color:#9ea3ad;line-height:1.6;margin-bottom:.5rem}
.card-footer{display:flex;align-items:center;gap:1rem;font-size:.76rem;color:#666e7a}
.card-tag{
    padding:.2rem .55rem;border-radius:12px;font-size:.7rem;font-weight:600;
    background:rgba(108,99,255,.08);color:#a89bff;
}
.reading-time{display:flex;align-items:center;gap:.25rem}

/* Summary & Briefing */
.summary-box{
    background:rgba(108,99,255,.06);border-left:4px solid #6c63ff;
    border-radius:8px;padding:1.1rem 1.3rem;margin-top:.5rem;
    font-size:.9rem;line-height:1.75;color:#d8d9de!important;
}
.summary-box strong{color:#a89bff!important}
.briefing-box{
    background:rgba(108,99,255,.05);
    border:1px solid rgba(108,99,255,.18);
    border-radius:14px;padding:1.8rem 2.2rem;
    line-height:1.8;font-size:.94rem;color:#d8d9de!important;
}
.briefing-box strong{color:#a89bff!important}

/* Architecture page */
.arch-card{
    background:rgba(255,255,255,.025);border:1px solid rgba(255,255,255,.06);
    border-radius:14px;padding:1.6rem 2rem;margin-bottom:1rem;
}
.arch-card h3{color:#a89bff!important;margin:0 0 .6rem 0;font-size:1.1rem}
.arch-card p,.arch-card li{color:#b8bcc6!important;font-size:.9rem;line-height:1.7}
.arch-card code{
    background:rgba(108,99,255,.1);color:#c5bfff;
    padding:.12rem .4rem;border-radius:4px;font-size:.82rem;
}

/* Flow diagram */
.flow-wrap{display:flex;flex-direction:column;align-items:center;gap:0;padding:.5rem 0}
.flow-row{display:flex;align-items:center;justify-content:center;gap:.6rem;flex-wrap:wrap}
.flow-box{
    background:rgba(108,99,255,.08);border:1px solid rgba(108,99,255,.25);
    border-radius:10px;padding:.6rem 1rem;text-align:center;
    min-width:105px;color:#dddaf5!important;font-size:.82rem;font-weight:600;
}
.flow-box.core{background:linear-gradient(135deg,#302b63,#24243e);border-color:#6c63ff}
.flow-box.out{border-color:#28a745;background:rgba(40,167,69,.08)}
.flow-box.api{border-color:#fd7e14;background:rgba(253,126,20,.06)}
.flow-sub{font-size:.68rem;color:#888e99;margin-top:.15rem;font-weight:400}
.flow-arrow{color:#6c63ff;font-size:1.3rem;padding:.2rem 0}

/* Step cards */
.step{
    display:flex;gap:1rem;align-items:flex-start;
    background:rgba(255,255,255,.025);border:1px solid rgba(255,255,255,.06);
    border-radius:12px;padding:1.2rem 1.4rem;margin-bottom:.65rem;
}
.step-n{
    background:linear-gradient(135deg,#6c63ff,#5a52d5);color:#fff;
    font-weight:800;font-size:.95rem;min-width:34px;height:34px;
    border-radius:50%;display:flex;align-items:center;justify-content:center;
    flex-shrink:0;
}
.step-body h4{color:#e0dff5!important;margin:0 0 .25rem;font-size:.98rem}
.step-body p{color:#a8adb7!important;margin:0;font-size:.88rem;line-height:1.65}
.step-body code{
    background:rgba(108,99,255,.1);color:#c5bfff;
    padding:.1rem .4rem;border-radius:4px;font-size:.8rem;
}

/* Sidebar */
.filter-hd{
    font-size:.7rem;font-weight:700;text-transform:uppercase;
    letter-spacing:1.2px;color:#888e99;margin:.6rem 0 .3rem;
}
section[data-testid="stSidebar"] .stCheckbox{padding-bottom:0}
.api-pill{
    display:inline-flex;align-items:center;gap:.35rem;
    padding:.35rem .75rem;border-radius:20px;font-size:.78rem;font-weight:600;
}
.api-pill.ok{background:rgba(40,167,69,.1);color:#5bda7d;border:1px solid rgba(40,167,69,.22)}
.api-pill.no{background:rgba(255,193,7,.08);color:#ffc940;border:1px solid rgba(255,193,7,.18)}
</style>""", unsafe_allow_html=True)


# ── Helper ────────────────────────────────────────────────────────────────────
def _md(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"###\s*(.+)", r"<strong style='font-size:1.08rem'>\1</strong>", text)
    text = text.replace("\n\n", "<br><br>").replace("\n", "<br>")
    return text


def _favicon(domain: str) -> str:
    return f"https://www.google.com/s2/favicons?sz=32&domain={domain}"


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="hero">'
    '<h1>📡 Tech News Aggregator &amp; Summarizer</h1>'
    '<p>AI-powered briefings from the top tech news sources &mdash; all in one place.</p>'
    '</div>',
    unsafe_allow_html=True,
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📡 Controls")

    st.markdown('<p class="filter-hd">Sources</p>', unsafe_allow_html=True)

    all_source_names = [s["name"] for s in NEWS_SOURCES]
    if "sel_sources" not in st.session_state:
        st.session_state.sel_sources = set(all_source_names)

    for s in NEWS_SOURCES:
        on = st.checkbox(s["name"], value=s["name"] in st.session_state.sel_sources, key=f"src_{s['name']}")
        if on:
            st.session_state.sel_sources.add(s["name"])
        else:
            st.session_state.sel_sources.discard(s["name"])
    selected_sources = list(st.session_state.sel_sources)

    st.markdown("---")
    st.markdown('<p class="filter-hd">Categories</p>', unsafe_allow_html=True)

    all_categories = sorted(set(s["category"] for s in NEWS_SOURCES))
    if "sel_categories" not in st.session_state:
        st.session_state.sel_categories = set(all_categories)

    for c in all_categories:
        on = st.checkbox(c, value=c in st.session_state.sel_categories, key=f"cat_{c}")
        if on:
            st.session_state.sel_categories.add(c)
        else:
            st.session_state.sel_categories.discard(c)
    selected_categories = list(st.session_state.sel_categories)

    st.markdown("---")
    if OPENAI_API_KEY:
        st.markdown('<span class="api-pill ok">OpenAI Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="api-pill no">No API Key</span>', unsafe_allow_html=True)
        st.caption("Add `OPENAI_API_KEY` to `.env`")
    st.markdown("")
    st.caption("Built with Streamlit + OpenAI")


# ── Fetch ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def _cached_fetch(keys: tuple) -> list[dict]:
    return fetch_all_news(selected_sources=list(keys))

def load_articles():
    if not selected_sources:
        return []
    with st.spinner("Fetching latest tech news..."):
        arts = _cached_fetch(tuple(sorted(selected_sources)))
    return [a for a in arts if a["category"] in selected_categories]

articles = load_articles()

# ── Stats ─────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        '<div class="stat-card"><div class="stat-icon">📰</div>'
        f'<div class="stat-num">{len(articles)}</div>'
        '<div class="stat-label">Articles</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(
        '<div class="stat-card"><div class="stat-icon">🌐</div>'
        f'<div class="stat-num">{len(set(a["source"] for a in articles))}</div>'
        '<div class="stat-label">Sources</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(
        '<div class="stat-card"><div class="stat-icon">🏷️</div>'
        f'<div class="stat-num">{len(set(a["category"] for a in articles))}</div>'
        '<div class="stat-label">Categories</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(
        '<div class="stat-card"><div class="stat-icon">🕐</div>'
        f'<div class="stat-num">{datetime.now(timezone.utc).strftime("%H:%M")}</div>'
        '<div class="stat-label">UTC Now</div></div>', unsafe_allow_html=True)

# ── Trending Topics ───────────────────────────────────────────────────────────
if articles:
    @st.cache_data(ttl=600, show_spinner=False)
    def _cached_topics(titles_joined: str) -> list[str]:
        # Reconstruct minimal article dicts from joined titles
        titles = titles_joined.split(" ||| ")
        return extract_trending_topics([{"title": t} for t in titles])

    titles_key = " ||| ".join(a["title"] for a in articles[:30])
    topics = _cached_topics(titles_key)

    if topics:
        pills = "".join(f'<span class="trending-pill">{t}</span>' for t in topics)
        st.markdown(
            f'<div style="margin:.8rem 0 .4rem"><span style="font-size:.78rem;font-weight:700;'
            f'color:#888e99;text-transform:uppercase;letter-spacing:1px">'
            f'Trending Now</span></div><div class="trending-bar">{pills}</div>',
            unsafe_allow_html=True,
        )

st.markdown("")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_briefing, tab_articles, tab_arch = st.tabs([
    "🧠 AI Briefing", "📰 All Articles", "🏗️ How It Works"
])


# ━━ Tab 1: Briefing ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_briefing:
    st.markdown("### Daily Tech Briefing")
    st.caption("AI-generated executive summary with top stories, trends, and market signals.")

    if st.button("Generate Briefing", type="primary", use_container_width=True):
        with st.spinner("Analyzing headlines and generating briefing..."):
            briefing = summarize_all(articles)
        st.markdown(f'<div class="briefing-box">{_md(briefing)}</div>', unsafe_allow_html=True)
    else:
        st.info("Click **Generate Briefing** to get an AI-powered overview of all fetched headlines.", icon="💡")


# ━━ Tab 2: Articles ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_articles:
    if not articles:
        st.warning("No articles found. Try selecting more sources or categories.")
    else:
        # Search bar
        query = st.text_input("🔍 Search articles", placeholder="Type to filter by title or description...")

        filtered = articles
        if query:
            q = query.lower()
            filtered = [
                a for a in articles
                if q in a["title"].lower() or q in a.get("description", "").lower()
            ]

        st.caption(f"Showing {len(filtered)} of {len(articles)} articles")

        # Two-column layout
        col_left, col_right = st.columns(2)
        for idx, article in enumerate(filtered):
            col = col_left if idx % 2 == 0 else col_right

            with col:
                pub = ""
                if article.get("published"):
                    pub = article["published"].strftime("%b %d, %H:%M")

                domain = article.get("domain", "")
                fav = _favicon(domain)
                rt = article.get("reading_time", 1)

                st.markdown(
                    f'<div class="card">'
                    f'<div class="card-header">'
                    f'<img class="card-favicon" src="{fav}" alt="">'
                    f'<span class="card-source">{article["source"]}</span>'
                    f'<span class="card-meta-right">{pub}</span>'
                    f'</div>'
                    f'<div class="card-title"><a href="{article["url"]}" target="_blank">{article["title"]}</a></div>'
                    f'<div class="card-desc">{article.get("description", "")[:220]}</div>'
                    f'<div class="card-footer">'
                    f'<span class="card-tag">{article["category"]}</span>'
                    f'<span class="reading-time">&#128337; {rt} min read</span>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

                with st.expander("🤖 AI Summary", expanded=False):
                    sk = f"sum_{idx}"
                    if sk not in st.session_state:
                        if st.button("Summarize", key=f"btn_{idx}"):
                            with st.spinner("Summarizing..."):
                                if len(article.get("content", "")) < 200:
                                    body = fetch_article_body(article["url"])
                                    if body:
                                        article["content"] = body
                                s = summarize_article(article)
                                st.session_state[sk] = s
                            st.markdown(f'<div class="summary-box">{_md(s)}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="summary-box">{_md(st.session_state[sk])}</div>', unsafe_allow_html=True)


# ━━ Tab 3: How It Works ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_arch:
    st.markdown("### Application Architecture")
    st.caption("End-to-end data flow from news sources to AI-powered summaries.")

    # ── SVG-based flow diagram ────────────────────────────────────────────────
    st.markdown("""<svg viewBox="0 0 800 520" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:800px;margin:1rem auto;display:block">
  <defs>
    <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#302b63"/>
      <stop offset="100%" style="stop-color:#24243e"/>
    </linearGradient>
    <linearGradient id="g2" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#6c63ff"/>
      <stop offset="100%" style="stop-color:#5a52d5"/>
    </linearGradient>
    <filter id="shadow"><feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.15" flood-color="#6c63ff"/></filter>
  </defs>

  <style>
    .box{fill:url(#g1);stroke:rgba(108,99,255,0.35);stroke-width:1.5;rx:10}
    .box-api{fill:rgba(253,126,20,0.08);stroke:#fd7e14;stroke-width:1.5;rx:10}
    .box-out{fill:rgba(40,167,69,0.08);stroke:#28a745;stroke-width:1.5;rx:10}
    .box-core{fill:url(#g1);stroke:#6c63ff;stroke-width:2;rx:12;filter:url(#shadow)}
    .label{fill:#dddaf5;font-size:12px;font-weight:700;font-family:sans-serif;text-anchor:middle}
    .sublabel{fill:#888e99;font-size:9px;font-family:sans-serif;text-anchor:middle}
    .arrow{stroke:#6c63ff;stroke-width:2;marker-end:url(#ah)}
  </style>

  <marker id="ah" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
    <path d="M0,0 L8,3 L0,6" fill="#6c63ff"/>
  </marker>

  <rect class="box" x="20" y="10" width="110" height="50"/>
  <text class="label" x="75" y="33">TechCrunch</text>
  <text class="sublabel" x="75" y="48">RSS Feed</text>

  <rect class="box" x="145" y="10" width="110" height="50"/>
  <text class="label" x="200" y="33">The Verge</text>
  <text class="sublabel" x="200" y="48">RSS Feed</text>

  <rect class="box" x="270" y="10" width="110" height="50"/>
  <text class="label" x="325" y="33">Ars Technica</text>
  <text class="sublabel" x="325" y="48">RSS Feed</text>

  <rect class="box" x="395" y="10" width="110" height="50"/>
  <text class="label" x="450" y="33">Wired</text>
  <text class="sublabel" x="450" y="48">RSS Feed</text>

  <rect class="box-api" x="520" y="10" width="110" height="50"/>
  <text class="label" x="575" y="33" style="fill:#ffa54c">Hacker News</text>
  <text class="sublabel" x="575" y="48">REST API</text>

  <rect class="box" x="645" y="10" width="130" height="50"/>
  <text class="label" x="710" y="28">MIT Tech</text>
  <text class="sublabel" x="710" y="42">Review</text>
  <text class="sublabel" x="710" y="53">RSS Feed</text>

  <line class="arrow" x1="75" y1="60" x2="400" y2="115"/>
  <line class="arrow" x1="200" y1="60" x2="400" y2="115"/>
  <line class="arrow" x1="325" y1="60" x2="400" y2="115"/>
  <line class="arrow" x1="450" y1="60" x2="400" y2="115"/>
  <line class="arrow" x1="575" y1="60" x2="400" y2="115"/>
  <line class="arrow" x1="710" y1="60" x2="400" y2="115"/>

  <rect class="box-core" x="260" y="115" width="280" height="55"/>
  <text class="label" x="400" y="140" style="font-size:14px">News Fetcher</text>
  <text class="sublabel" x="400" y="158">news_fetcher.py &middot; feedparser + requests</text>

  <line class="arrow" x1="400" y1="170" x2="400" y2="200"/>

  <rect class="box-core" x="260" y="200" width="280" height="55"/>
  <text class="label" x="400" y="225" style="font-size:14px">Parse &amp; Clean</text>
  <text class="sublabel" x="400" y="243">BeautifulSoup &middot; HTML strip &middot; Normalize</text>

  <line class="arrow" x1="400" y1="255" x2="400" y2="285"/>

  <rect class="box-core" x="260" y="285" width="280" height="55"/>
  <text class="label" x="400" y="310" style="font-size:14px">Categorize &amp; Deduplicate</text>
  <text class="sublabel" x="400" y="328">Category mapping &middot; Title similarity check</text>

  <line class="arrow" x1="340" y1="340" x2="220" y2="385"/>
  <line class="arrow" x1="460" y1="340" x2="580" y2="385"/>

  <rect class="box-out" x="120" y="385" width="200" height="55"/>
  <text class="label" x="220" y="408" style="fill:#5bda7d;font-size:13px">Display Articles</text>
  <text class="sublabel" x="220" y="428">Streamlit UI &middot; Cards &middot; Search</text>

  <rect class="box-core" x="480" y="385" width="200" height="55"/>
  <text class="label" x="580" y="408" style="font-size:13px">AI Summarizer</text>
  <text class="sublabel" x="580" y="428">OpenAI GPT &middot; Agentic prompts</text>

  <line class="arrow" x1="220" y1="440" x2="400" y2="480"/>
  <line class="arrow" x1="580" y1="440" x2="400" y2="480"/>

  <rect class="box-out" x="250" y="475" width="300" height="40" style="filter:url(#shadow)"/>
  <text class="label" x="400" y="500" style="fill:#5bda7d;font-size:13px">Articles + Summaries + Briefing</text>
</svg>""", unsafe_allow_html=True)

    # ── Steps ─────────────────────────────────────────────────────────────────
    st.markdown("")
    st.markdown("### Step-by-Step Breakdown")

    steps = [
        ("Fetch from Sources",
         "The app connects to <strong>8 tech news sources</strong> concurrently using "
         "<code>ThreadPoolExecutor</code>. RSS sources are parsed with <code>feedparser</code>. "
         "Hacker News uses its Firebase REST API. All fetching runs in parallel for speed."),
        ("Parse &amp; Clean",
         "Raw HTML is stripped with <code>BeautifulSoup</code>. The parser extracts "
         "<strong>title, URL, description, full content,</strong> and <strong>publish date</strong>. "
         "Dates are normalized to UTC. Reading time is estimated at 200 wpm."),
        ("Deduplicate &amp; Categorize",
         "Near-duplicate articles (same story from multiple sources) are removed using "
         "title similarity matching (70% word overlap threshold). "
         "Each article inherits its source's category for filtering."),
        ("Display &amp; Search",
         "Articles render in a <strong>two-column card grid</strong> with source favicons, "
         "category tags, and reading time. The search bar filters articles in real time. "
         "Results are cached for 10 minutes with <code>@st.cache_data</code>."),
        ("AI Summary (Per Article)",
         "Clicking <strong>Summarize</strong> sends the article's content to <strong>OpenAI GPT</strong>. "
         "The model returns a structured summary with <strong>key facts, why it matters,</strong> and "
         "<strong>key players</strong> involved."),
        ("AI Briefing (All Articles)",
         "<strong>Generate Briefing</strong> sends all headlines to GPT in a single prompt. "
         "The model produces an executive briefing with <strong>Top Stories, Trends &amp; Themes, "
         "Market Signals,</strong> and <strong>Quick Bites</strong>."),
        ("Trending Topics",
         "Headlines are analyzed by GPT to extract <strong>8-10 trending topic tags</strong> "
         "displayed as interactive pills above the articles. Falls back to word-frequency "
         "extraction when no API key is set."),
    ]
    for i, (title, desc) in enumerate(steps, 1):
        st.markdown(
            f'<div class="step"><div class="step-n">{i}</div>'
            f'<div class="step-body"><h4>{title}</h4><p>{desc}</p></div></div>',
            unsafe_allow_html=True)

    # ── Tech Stack ────────────────────────────────────────────────────────────
    st.markdown("")
    st.markdown("### Tech Stack")
    st.markdown(
        '<div class="arch-card">'
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:1.2rem">'
        '<div><h3 style="font-size:1rem">Frontend</h3><ul>'
        '<li><code>Streamlit</code> &mdash; Reactive web UI</li>'
        '<li>Custom CSS &mdash; Dark glassmorphism theme</li>'
        '<li>SVG &mdash; Architecture diagram</li></ul></div>'
        '<div><h3 style="font-size:1rem">Data Layer</h3><ul>'
        '<li><code>feedparser</code> &mdash; RSS/Atom parsing</li>'
        '<li><code>requests</code> &mdash; HTTP &amp; API calls</li>'
        '<li><code>BeautifulSoup</code> &mdash; HTML cleaning</li>'
        '<li><code>ThreadPoolExecutor</code> &mdash; Concurrent fetching</li></ul></div>'
        '<div><h3 style="font-size:1rem">AI / LLM</h3><ul>'
        '<li><code>OpenAI GPT-4o-mini</code> &mdash; Summarization</li>'
        '<li>Structured prompts &mdash; Briefings &amp; topics</li>'
        '<li>JSON extraction &mdash; Trending tags</li></ul></div>'
        '<div><h3 style="font-size:1rem">Infrastructure</h3><ul>'
        '<li><code>python-dotenv</code> &mdash; Config management</li>'
        '<li><code>@st.cache_data</code> &mdash; 10-min TTL cache</li>'
        '<li>Title deduplication &mdash; 70% overlap threshold</li></ul></div>'
        '</div></div>',
        unsafe_allow_html=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "📡 Tech News Aggregator &amp; Summarizer &mdash; "
    "TechCrunch, The Verge, Ars Technica, Wired, Hacker News, "
    "MIT Technology Review, VentureBeat, The Register"
)
