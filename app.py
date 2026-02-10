"""
Tech News Aggregator & Summarizer — Streamlit App
An agentic tool that fetches tech news from multiple sources and
provides AI-powered summaries and briefings.
"""

import streamlit as st
from datetime import datetime, timezone

from config import NEWS_SOURCES, OPENAI_API_KEY
from news_fetcher import fetch_all_news, fetch_article_body
from summarizer import summarize_article, summarize_all

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Tech News Aggregator",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom Styles (dark-theme) ───────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Global ── */
    .block-container { padding-top: 2rem; }

    /* ── Hero ── */
    .hero {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        padding: 2.2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
    }
    .hero h1 { margin: 0; font-size: 2.2rem; color: #fff !important; }
    .hero p  { margin: 0.4rem 0 0; font-size: 1.05rem; color: #c0bfff !important; }

    /* ── Article card ── */
    .article-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 0.75rem;
        transition: box-shadow .2s, border-color .2s;
    }
    .article-card:hover {
        box-shadow: 0 4px 24px rgba(108,99,255,.15);
        border-color: rgba(108,99,255,.3);
    }
    .article-source {
        font-size: .78rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: .5px;
        color: #a89bff; margin-bottom: .4rem;
    }
    .article-title { font-size: 1.15rem; font-weight: 700; margin-bottom: .4rem; line-height: 1.35; }
    .article-title a { color: #f0f0f5 !important; text-decoration: none; }
    .article-title a:hover { color: #a89bff !important; }
    .article-meta { font-size: .8rem; color: #888e99; margin-bottom: .6rem; }
    .article-desc { font-size: .92rem; color: #b0b5c0; line-height: 1.55; }

    /* ── Summary / Briefing boxes ── */
    .summary-box {
        background: rgba(108,99,255,.07);
        border-left: 4px solid #6c63ff;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-top: .5rem;
        font-size: .92rem; line-height: 1.7;
        color: #dcdde1 !important;
    }
    .summary-box strong { color: #a89bff !important; }
    .briefing-box {
        background: rgba(108,99,255,.06);
        border: 1px solid rgba(108,99,255,.2);
        border-radius: 12px;
        padding: 1.5rem 2rem;
        line-height: 1.75; font-size: .95rem;
        color: #dcdde1 !important;
    }
    .briefing-box strong { color: #a89bff !important; }

    /* ── Stat cards ── */
    .stat-card {
        background: rgba(255,255,255,.04);
        border: 1px solid rgba(255,255,255,.08);
        border-radius: 12px; padding: 1rem; text-align: center;
    }
    .stat-num  { font-size: 1.8rem; font-weight: 800; color: #6c63ff; }
    .stat-label { font-size: .8rem; color: #888e99; margin-top: .2rem; }

    /* ── Sidebar ── */
    .filter-heading {
        font-size: .72rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 1.2px;
        color: #888e99; margin: .75rem 0 .4rem 0;
    }
    section[data-testid="stSidebar"] .stCheckbox { padding-bottom: 0; }
    .api-badge {
        display: inline-flex; align-items: center; gap: .4rem;
        padding: .4rem .8rem; border-radius: 20px;
        font-size: .8rem; font-weight: 600;
    }
    .api-badge.ok   { background: rgba(40,167,69,.12); color: #5bda7d; border: 1px solid rgba(40,167,69,.25); }
    .api-badge.miss { background: rgba(255,193,7,.1);  color: #ffc940; border: 1px solid rgba(255,193,7,.2); }

    /* ── Architecture page ── */
    .arch-section {
        background: rgba(255,255,255,.03);
        border: 1px solid rgba(255,255,255,.07);
        border-radius: 14px;
        padding: 1.75rem 2rem;
        margin-bottom: 1.25rem;
    }
    .arch-section h3 { color: #a89bff !important; margin-top: 0; font-size: 1.15rem; }
    .arch-section p,
    .arch-section li { color: #c0c4cc !important; font-size: .93rem; line-height: 1.7; }
    .arch-section code {
        background: rgba(108,99,255,.12);
        color: #c5bfff;
        padding: .15rem .45rem;
        border-radius: 4px;
        font-size: .85rem;
    }

    /* Flow diagram */
    .flow-container {
        display: flex; flex-direction: column;
        align-items: center; gap: 0;
        padding: 1rem 0;
    }
    .flow-row {
        display: flex; align-items: center;
        justify-content: center; gap: .75rem;
        flex-wrap: wrap;
    }
    .flow-node {
        background: rgba(108,99,255,.1);
        border: 1px solid rgba(108,99,255,.3);
        border-radius: 10px;
        padding: .65rem 1.1rem;
        text-align: center;
        min-width: 110px;
        color: #e0dff5 !important;
        font-size: .85rem; font-weight: 600;
    }
    .flow-node.accent {
        background: linear-gradient(135deg, #302b63, #24243e);
        border-color: #6c63ff;
    }
    .flow-node.green  { border-color: #28a745; background: rgba(40,167,69,.1); }
    .flow-node.orange { border-color: #fd7e14; background: rgba(253,126,20,.08); }
    .flow-node-label { font-size: .7rem; color: #888e99; margin-top: .2rem; }
    .flow-arrow {
        color: #6c63ff; font-size: 1.4rem;
        line-height: 1; padding: .25rem 0;
    }
    .flow-arrow-right { color: #6c63ff; font-size: 1.3rem; margin: 0 .15rem; }

    /* Step cards */
    .step-card {
        display: flex; gap: 1rem; align-items: flex-start;
        background: rgba(255,255,255,.03);
        border: 1px solid rgba(255,255,255,.07);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: .75rem;
    }
    .step-num {
        background: linear-gradient(135deg, #6c63ff, #5a52d5);
        color: white; font-weight: 800; font-size: 1rem;
        min-width: 36px; height: 36px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0;
    }
    .step-body h4 { color: #e0dff5 !important; margin: 0 0 .3rem 0; font-size: 1rem; }
    .step-body p  { color: #b0b5c0 !important; margin: 0; font-size: .9rem; line-height: 1.6; }
    .step-body code {
        background: rgba(108,99,255,.12); color: #c5bfff;
        padding: .1rem .4rem; border-radius: 4px; font-size: .82rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Hero Header ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero">
        <h1>📡 Tech News Aggregator & Summarizer</h1>
        <p>AI-powered briefings from the top tech news sources — all in one place.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📡 Controls")

    # ── Sources ───────────────────────────────────────────────────────────────
    st.markdown('<p class="filter-heading">Sources</p>', unsafe_allow_html=True)

    all_source_names = [s["name"] for s in NEWS_SOURCES]
    if "sel_sources" not in st.session_state:
        st.session_state.sel_sources = set(all_source_names)

    for source in NEWS_SOURCES:
        checked = st.checkbox(
            source["name"],
            value=source["name"] in st.session_state.sel_sources,
            key=f"src_{source['name']}",
        )
        if checked:
            st.session_state.sel_sources.add(source["name"])
        else:
            st.session_state.sel_sources.discard(source["name"])

    selected_sources = list(st.session_state.sel_sources)

    st.markdown("---")

    # ── Categories ────────────────────────────────────────────────────────────
    st.markdown('<p class="filter-heading">Categories</p>', unsafe_allow_html=True)

    all_categories = sorted(set(s["category"] for s in NEWS_SOURCES))
    if "sel_categories" not in st.session_state:
        st.session_state.sel_categories = set(all_categories)

    for cat in all_categories:
        checked = st.checkbox(
            cat,
            value=cat in st.session_state.sel_categories,
            key=f"cat_{cat}",
        )
        if checked:
            st.session_state.sel_categories.add(cat)
        else:
            st.session_state.sel_categories.discard(cat)

    selected_categories = list(st.session_state.sel_categories)

    st.markdown("---")

    # ── API status ────────────────────────────────────────────────────────────
    if OPENAI_API_KEY:
        st.markdown('<span class="api-badge ok">✅ OpenAI Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="api-badge miss">⚠️ No API Key</span>', unsafe_allow_html=True)
        st.caption("Add `OPENAI_API_KEY` to `.env` for AI summaries.")

    st.markdown("")
    st.caption("Built with Streamlit + OpenAI")


# ── Fetch Articles ────────────────────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def _cached_fetch(source_names: tuple) -> list[dict]:
    return fetch_all_news(selected_sources=list(source_names))


def load_articles():
    if not selected_sources:
        return []
    with st.spinner("Fetching latest tech news..."):
        arts = _cached_fetch(tuple(sorted(selected_sources)))
    return [a for a in arts if a["category"] in selected_categories]


articles = load_articles()

# ── Stats Row ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
sources_active = len(set(a["source"] for a in articles))
with c1:
    st.markdown(
        f'<div class="stat-card"><div class="stat-num">{len(articles)}</div>'
        f'<div class="stat-label">Articles Fetched</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(
        f'<div class="stat-card"><div class="stat-num">{sources_active}</div>'
        f'<div class="stat-label">Active Sources</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(
        f'<div class="stat-card"><div class="stat-num">{len(set(a["category"] for a in articles))}</div>'
        f'<div class="stat-label">Categories</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(
        f'<div class="stat-card"><div class="stat-num">{datetime.now(timezone.utc).strftime("%H:%M UTC")}</div>'
        f'<div class="stat-label">Last Refreshed</div></div>', unsafe_allow_html=True)

st.markdown("")


# ── Helper ────────────────────────────────────────────────────────────────────
def _md(text: str) -> str:
    """Convert minimal markdown to HTML for custom divs."""
    import re
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"### (.+)", r"<strong style='font-size:1.1rem'>\1</strong>", text)
    text = text.replace("\n\n", "<br><br>").replace("\n", "<br>")
    return text


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_briefing, tab_articles, tab_arch = st.tabs([
    "🧠 AI Briefing", "📰 All Articles", "🏗️ How It Works"
])


# ── Tab 1: AI Briefing ───────────────────────────────────────────────────────
with tab_briefing:
    st.markdown("### Daily Tech Briefing")
    st.caption("An AI-generated executive summary of today's top tech headlines.")

    if st.button("Generate Briefing", type="primary", use_container_width=True):
        with st.spinner("Analyzing headlines and generating briefing..."):
            briefing = summarize_all(articles)
        st.markdown(f'<div class="briefing-box">{_md(briefing)}</div>', unsafe_allow_html=True)
    else:
        st.info("Click **Generate Briefing** to get an AI-powered overview of all fetched headlines.", icon="💡")


# ── Tab 2: All Articles ──────────────────────────────────────────────────────
with tab_articles:
    if not articles:
        st.warning("No articles found. Try selecting more sources or categories.")
    else:
        for idx, article in enumerate(articles):
            pub_str = ""
            if article.get("published"):
                pub_str = article["published"].strftime("%b %d, %Y · %H:%M UTC")

            st.markdown(f"""
            <div class="article-card">
                <div class="article-source">{article['source']} · {article['category']}</div>
                <div class="article-title">
                    <a href="{article['url']}" target="_blank">{article['title']}</a>
                </div>
                <div class="article-meta">{pub_str}</div>
                <div class="article-desc">{article.get('description', '')[:300]}</div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("🤖 Get AI Summary", expanded=False):
                summary_key = f"summary_{idx}"
                if summary_key not in st.session_state:
                    if st.button("Summarize this article", key=f"btn_{idx}"):
                        with st.spinner("Summarizing..."):
                            if len(article.get("content", "")) < 200:
                                body = fetch_article_body(article["url"])
                                if body:
                                    article["content"] = body
                            summary = summarize_article(article)
                            st.session_state[summary_key] = summary
                        st.markdown(
                            f'<div class="summary-box">{_md(summary)}</div>',
                            unsafe_allow_html=True)
                else:
                    st.markdown(
                        f'<div class="summary-box">{_md(st.session_state[summary_key])}</div>',
                        unsafe_allow_html=True)


# ── Tab 3: How It Works ──────────────────────────────────────────────────────
with tab_arch:
    st.markdown("### Application Architecture")
    st.caption("A visual walkthrough of how the Tech News Aggregator works end-to-end.")

    # ── Flow Diagram ──────────────────────────────────────────────────────────
    _flow = (
        '<div class="arch-section" style="text-align:center">'
        '<h3>Data Flow</h3>'
        '<div class="flow-container">'
        '<div class="flow-row">'
        '<div class="flow-node">TechCrunch<div class="flow-node-label">RSS Feed</div></div>'
        '<div class="flow-node">The Verge<div class="flow-node-label">RSS Feed</div></div>'
        '<div class="flow-node">Ars Technica<div class="flow-node-label">RSS Feed</div></div>'
        '<div class="flow-node">Wired<div class="flow-node-label">RSS Feed</div></div>'
        '<div class="flow-node orange">Hacker News<div class="flow-node-label">REST API</div></div>'
        '<div class="flow-node">MIT Tech Review<div class="flow-node-label">RSS Feed</div></div>'
        '</div>'
        '<div class="flow-arrow">\u2B07</div>'
        '<div class="flow-row">'
        '<div class="flow-node accent" style="min-width:280px">'
        'News Fetcher<br><span class="flow-node-label">news_fetcher.py &middot; feedparser + requests</span>'
        '</div>'
        '</div>'
        '<div class="flow-arrow">\u2B07</div>'
        '<div class="flow-row">'
        '<div class="flow-node accent" style="min-width:280px">'
        'Parse &amp; Clean<br><span class="flow-node-label">Strip HTML &middot; Extract metadata &middot; Normalize dates</span>'
        '</div>'
        '</div>'
        '<div class="flow-arrow">\u2B07</div>'
        '<div class="flow-row">'
        '<div class="flow-node accent" style="min-width:280px">'
        'Categorize &amp; Sort<br><span class="flow-node-label">Assign category &middot; Sort by date (newest first)</span>'
        '</div>'
        '</div>'
        '<div class="flow-arrow">\u2B07</div>'
        '<div class="flow-row" style="gap:2rem">'
        '<div class="flow-node green" style="min-width:220px">'
        'Display Articles<br><span class="flow-node-label">Streamlit UI &middot; Cards &middot; Filters</span>'
        '</div>'
        '<div class="flow-node accent" style="min-width:220px">'
        'AI Summarizer<br><span class="flow-node-label">summarizer.py &middot; OpenAI GPT</span>'
        '</div>'
        '</div>'
        '<div class="flow-arrow">\u2B07</div>'
        '<div class="flow-row">'
        '<div class="flow-node green" style="min-width:320px">'
        'User sees articles + AI summaries + daily briefing'
        '</div>'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(_flow, unsafe_allow_html=True)

    # ── Step-by-step breakdown ────────────────────────────────────────────────
    st.markdown("")
    st.markdown("### Step-by-Step Breakdown")

    steps = [
        (
            "Fetch from Sources",
            "The app connects to <strong>6 tech news sources</strong> simultaneously. "
            "For RSS-based sources (TechCrunch, The Verge, Ars Technica, Wired, MIT Technology Review), "
            "it uses <code>feedparser</code> to parse their XML feeds. "
            "For Hacker News, it hits the <strong>Firebase REST API</strong> to pull top stories. "
            "All fetching happens in <code>news_fetcher.py</code>."
        ),
        (
            "Parse &amp; Clean Content",
            "Raw HTML from feed descriptions is stripped using <code>BeautifulSoup</code>. "
            "The parser extracts the <strong>title, URL, description, full content,</strong> and "
            "<strong>publish date</strong> from each entry. Dates are normalized to UTC. "
            "Content is truncated to 2,000 characters to keep summaries efficient."
        ),
        (
            "Categorize Articles",
            "Each source is pre-mapped to a category in <code>config.py</code>: "
            "<strong>General Tech, Deep Tech, Tech &amp; Culture, Developer &amp; Startups, "
            "Research &amp; Innovation</strong>. Articles inherit their source's category automatically. "
            "Users can filter by both source and category using the sidebar."
        ),
        (
            "Cache &amp; Display",
            "Fetched articles are <strong>cached for 10 minutes</strong> using Streamlit's "
            "<code>@st.cache_data</code> decorator, so switching filters doesn't re-fetch. "
            "Articles are rendered as styled cards sorted by date, with source labels, "
            "timestamps, and description previews."
        ),
        (
            "AI Summarization (Per Article)",
            "When you click <strong>Summarize</strong> on any article, the app sends "
            "its title, description, and content to <strong>OpenAI GPT</strong> via <code>summarizer.py</code>. "
            "If the RSS description is too short, it fetches the full article body from the URL first. "
            "The model returns a concise 2-3 sentence summary."
        ),
        (
            "AI Briefing (All Articles)",
            "The <strong>Generate Briefing</strong> button sends all headlines and descriptions "
            "to GPT in a single prompt. The model acts as a <strong>tech news analyst</strong> and "
            "produces a structured briefing with: <strong>Top Stories</strong> (3-4 most impactful), "
            "<strong>Trends &amp; Themes</strong> (patterns across stories), and "
            "<strong>Quick Bites</strong> (one-liners for the rest)."
        ),
    ]

    for i, (title, desc) in enumerate(steps, 1):
        st.markdown(
            f'<div class="step-card">'
            f'<div class="step-num">{i}</div>'
            f'<div class="step-body"><h4>{title}</h4><p>{desc}</p></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Tech Stack ────────────────────────────────────────────────────────────
    st.markdown("")
    st.markdown("### Tech Stack")

    _stack = (
        '<div class="arch-section">'
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem">'
        '<div><h3 style="font-size:1rem">Frontend</h3><ul>'
        '<li><code>Streamlit</code> &mdash; Web UI framework</li>'
        '<li>Custom CSS &mdash; Dark-theme cards &amp; layout</li>'
        '</ul></div>'
        '<div><h3 style="font-size:1rem">Data Fetching</h3><ul>'
        '<li><code>feedparser</code> &mdash; RSS/Atom feed parsing</li>'
        '<li><code>requests</code> &mdash; HTTP client for APIs</li>'
        '<li><code>BeautifulSoup</code> &mdash; HTML cleaning</li>'
        '</ul></div>'
        '<div><h3 style="font-size:1rem">AI / LLM</h3><ul>'
        '<li><code>OpenAI API</code> &mdash; GPT-4o-mini summarization</li>'
        '<li>Agentic prompting &mdash; Structured briefings</li>'
        '</ul></div>'
        '<div><h3 style="font-size:1rem">Configuration</h3><ul>'
        '<li><code>python-dotenv</code> &mdash; Environment management</li>'
        '<li><code>config.py</code> &mdash; Source definitions</li>'
        '</ul></div>'
        '</div></div>'
    )
    st.markdown(_stack, unsafe_allow_html=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "📡 Tech News Aggregator & Summarizer · "
    "Sources: TechCrunch, The Verge, Ars Technica, Wired, Hacker News, MIT Technology Review"
)
