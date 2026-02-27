"""
Tech News Aggregator & Summarizer — Streamlit App v3
Features: AI briefings, sentiment analysis, analytics dashboard,
chat, keyword alerts, sort, trending topics, briefing history.
"""

import re
import altair as alt
import pandas as pd
import streamlit as st
from datetime import datetime, timezone

from config import NEWS_SOURCES, OPENAI_API_KEY, SMTP_EMAIL, SMTP_PASSWORD, DIGEST_RECIPIENT
from news_fetcher import fetch_all_news, fetch_article_body
from summarizer import (
    summarize_article, summarize_all, extract_trending_topics,
    analyze_sentiment, chat_about_news,
)
from history import save_briefing, load_history
from emailer import send_news_digest, was_digest_sent_today, get_last_send_info, get_send_history
from health_check import run_all_checks

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

.stat-card{
    background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);
    border-radius:14px;padding:1.1rem 1rem;text-align:center;transition:border-color .2s;
}
.stat-card:hover{border-color:rgba(108,99,255,.3)}
.stat-icon{font-size:1.4rem;margin-bottom:.25rem}
.stat-num{font-size:1.7rem;font-weight:800;color:#6c63ff}
.stat-num.green{color:#5bda7d}
.stat-label{font-size:.78rem;color:#888e99;margin-top:.15rem}

.trending-bar{display:flex;flex-wrap:wrap;gap:.5rem;padding:.5rem 0}
.trending-pill{
    display:inline-block;padding:.35rem .85rem;border-radius:20px;
    font-size:.82rem;font-weight:600;
    background:rgba(108,99,255,.1);border:1px solid rgba(108,99,255,.25);
    color:#c5bfff!important;transition:all .15s;cursor:default;
}
.trending-pill:hover{background:rgba(108,99,255,.2);border-color:#6c63ff}

div[data-testid="stTextInput"] input{
    background:rgba(255,255,255,.04)!important;
    border:1px solid rgba(255,255,255,.1)!important;
    color:#e0e0e5!important;border-radius:10px!important;
}

.card{
    background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);
    border-radius:14px;padding:1.2rem 1.5rem;margin-bottom:.65rem;transition:all .2s;
}
.card:hover{
    border-color:rgba(108,99,255,.35);box-shadow:0 8px 30px rgba(108,99,255,.1);
    transform:translateY(-2px);
}
.card.sentiment-positive{border-left:4px solid #5bda7d}
.card.sentiment-negative{border-left:4px solid #ff6b6b}
.card.sentiment-neutral{border-left:4px solid #555e6e}
.card.alert-match{border-color:rgba(255,183,77,.5);box-shadow:0 0 15px rgba(255,183,77,.12)}
.card-header{display:flex;align-items:center;gap:.6rem;margin-bottom:.5rem}
.card-favicon{width:18px;height:18px;border-radius:3px;opacity:.85}
.card-source{font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.6px;color:#a89bff}
.card-meta-right{margin-left:auto;font-size:.72rem;color:#666e7a;display:flex;align-items:center;gap:.5rem}
.card-title{font-size:1.12rem;font-weight:700;line-height:1.38;margin-bottom:.35rem}
.card-title a{color:#ededf2!important;text-decoration:none;transition:color .15s}
.card-title a:hover{color:#a89bff!important}
.card-desc{font-size:.9rem;color:#9ea3ad;line-height:1.6;margin-bottom:.5rem}
.card-footer{display:flex;align-items:center;gap:.75rem;font-size:.76rem;color:#666e7a;flex-wrap:wrap}
.card-tag{padding:.2rem .55rem;border-radius:12px;font-size:.7rem;font-weight:600;background:rgba(108,99,255,.08);color:#a89bff}
.reading-time{display:flex;align-items:center;gap:.25rem}
.alert-badge{
    padding:.2rem .55rem;border-radius:12px;font-size:.68rem;font-weight:700;
    background:rgba(255,183,77,.15);color:#ffb74d;border:1px solid rgba(255,183,77,.3);
}
.sentiment-dot{
    width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:.15rem;
}
.sentiment-dot.pos{background:#5bda7d}
.sentiment-dot.neg{background:#ff6b6b}
.sentiment-dot.neu{background:#555e6e}

.summary-box{
    background:rgba(108,99,255,.06);border-left:4px solid #6c63ff;
    border-radius:8px;padding:1.1rem 1.3rem;margin-top:.5rem;
    font-size:.9rem;line-height:1.75;color:#d8d9de!important;
}
.summary-box strong{color:#a89bff!important}
.briefing-box{
    background:rgba(108,99,255,.05);border:1px solid rgba(108,99,255,.18);
    border-radius:14px;padding:1.8rem 2.2rem;line-height:1.8;font-size:.94rem;color:#d8d9de!important;
}
.briefing-box strong{color:#a89bff!important}

.history-entry{
    background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);
    border-radius:10px;padding:1rem 1.3rem;margin-bottom:.5rem;
    font-size:.88rem;line-height:1.7;color:#b8bcc6!important;
}
.history-entry strong{color:#a89bff!important}
.history-meta{font-size:.75rem;color:#666e7a;margin-bottom:.4rem}

.arch-card{
    background:rgba(255,255,255,.025);border:1px solid rgba(255,255,255,.06);
    border-radius:14px;padding:1.6rem 2rem;margin-bottom:1rem;
}
.arch-card h3{color:#a89bff!important;margin:0 0 .6rem 0;font-size:1.1rem}
.arch-card p,.arch-card li{color:#b8bcc6!important;font-size:.9rem;line-height:1.7}
.arch-card code{background:rgba(108,99,255,.1);color:#c5bfff;padding:.12rem .4rem;border-radius:4px;font-size:.82rem}

.step{
    display:flex;gap:1rem;align-items:flex-start;
    background:rgba(255,255,255,.025);border:1px solid rgba(255,255,255,.06);
    border-radius:12px;padding:1.2rem 1.4rem;margin-bottom:.65rem;
}
.step-n{
    background:linear-gradient(135deg,#6c63ff,#5a52d5);color:#fff;
    font-weight:800;font-size:.95rem;min-width:34px;height:34px;
    border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;
}
.step-body h4{color:#e0dff5!important;margin:0 0 .25rem;font-size:.98rem}
.step-body p{color:#a8adb7!important;margin:0;font-size:.88rem;line-height:1.65}
.step-body code{background:rgba(108,99,255,.1);color:#c5bfff;padding:.1rem .4rem;border-radius:4px;font-size:.8rem}

.filter-hd{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:1.2px;color:#888e99;margin:.6rem 0 .3rem}
section[data-testid="stSidebar"] .stCheckbox{padding-bottom:0}
.api-pill{display:inline-flex;align-items:center;gap:.35rem;padding:.35rem .75rem;border-radius:20px;font-size:.78rem;font-weight:600}
.api-pill.ok{background:rgba(40,167,69,.1);color:#5bda7d;border:1px solid rgba(40,167,69,.22)}
.api-pill.no{background:rgba(255,193,7,.08);color:#ffc940;border:1px solid rgba(255,193,7,.18)}

.chat-article-link{
    display:flex;align-items:center;gap:.6rem;
    background:rgba(108,99,255,.06);border:1px solid rgba(108,99,255,.22);
    border-radius:10px;padding:.75rem 1rem;margin:.4rem 0;transition:all .2s;
}
.chat-article-link:hover{border-color:#6c63ff;background:rgba(108,99,255,.14);transform:translateX(4px)}
.chat-article-link a{
    color:#a89bff!important;text-decoration:none;font-weight:600;font-size:.92rem;flex:1;
}
.chat-article-link a:hover{color:#c5bfff!important;text-decoration:underline}
.chat-article-source{
    font-size:.7rem;color:#888e99;text-transform:uppercase;font-weight:700;letter-spacing:.5px;
}
.chat-brief{
    background:rgba(91,218,125,.06);border:1px solid rgba(91,218,125,.18);
    border-radius:10px;padding:.8rem 1.1rem;margin:.5rem 0;
    font-size:.9rem;line-height:1.6;color:#c8ffe0!important;font-style:italic;
}
.chat-external-box{
    background:rgba(255,183,77,.05);border-left:4px solid #ffb74d;
    border-radius:8px;padding:1.1rem 1.3rem;margin:.5rem 0;
    font-size:.9rem;line-height:1.75;color:#d8d9de!important;
}
.chat-external-box strong{color:#ffb74d!important}

.health-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:.7rem;margin:.8rem 0}
.health-card{
    background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);
    border-radius:12px;padding:1rem 1.2rem;transition:all .2s;position:relative;overflow:hidden;
}
.health-card::before{
    content:'';position:absolute;top:0;left:0;width:4px;height:100%;border-radius:4px 0 0 4px;
}
.health-card.ok::before{background:#5bda7d}
.health-card.err::before{background:#ff6b6b}
.health-card.noconf::before{background:#555e6e}
.health-card:hover{border-color:rgba(108,99,255,.3)}
.health-name{font-size:.95rem;font-weight:700;color:#ededf2;display:flex;align-items:center}
.health-type{font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:#888e99;margin-top:2px}
.health-status{display:flex;align-items:center;gap:.4rem;margin-top:.45rem;font-size:.82rem;font-weight:600}
.health-status.ok{color:#5bda7d}
.health-status.err{color:#ff6b6b}
.health-status.noconf{color:#888e99}
.health-msg{font-size:.78rem;color:#9ea3ad;margin-top:.3rem;line-height:1.4}
.health-latency{
    position:absolute;top:.85rem;right:1rem;font-size:.72rem;font-weight:700;
    color:#888e99;background:rgba(255,255,255,.04);padding:.2rem .5rem;border-radius:8px;
}
.health-summary{
    display:flex;gap:1.5rem;align-items:center;padding:.8rem 1.2rem;
    background:rgba(255,255,255,.025);border:1px solid rgba(255,255,255,.06);
    border-radius:12px;margin-bottom:1rem;flex-wrap:wrap;
}
.health-summary-item{font-size:.9rem;font-weight:700;display:flex;align-items:center;gap:.4rem}
.health-summary-item .dot{width:10px;height:10px;border-radius:50%;display:inline-block}
.health-summary-item .dot.g{background:#5bda7d}
.health-summary-item .dot.r{background:#ff6b6b}
.health-summary-item .dot.y{background:#888e99}
</style>""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
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
_smtp_ready = bool(SMTP_EMAIL and SMTP_PASSWORD)

with st.sidebar:
    st.markdown("## 📡 Controls")

    with st.expander("🌐 Sources", expanded=False):
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

    with st.expander("📂 Categories", expanded=False):
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
    st.markdown('<p class="filter-hd">Keyword Alerts</p>', unsafe_allow_html=True)
    st.caption("Comma-separated. Matching articles get highlighted.")
    alert_input = st.text_input(
        "Watchlist keywords",
        placeholder="AI, Apple, cybersecurity...",
        key="alert_kw_input",
        label_visibility="collapsed",
    )
    alert_keywords = [k.strip().lower() for k in alert_input.split(",") if k.strip()]

    st.markdown("---")
    if OPENAI_API_KEY:
        st.markdown('<span class="api-pill ok">OpenAI Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="api-pill no">No API Key</span>', unsafe_allow_html=True)
        st.caption("Add `OPENAI_API_KEY` to `.env`")
    if _smtp_ready:
        st.markdown('<span class="api-pill ok">📧 Email Ready</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="api-pill no">📧 Email Not Set</span>', unsafe_allow_html=True)
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


# ── Sentiment (cached) ───────────────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def _cached_sentiment(titles_joined: str) -> dict[str, str]:
    titles = titles_joined.split(" ||| ")
    return analyze_sentiment([{"title": t} for t in titles])

sentiment_map: dict[str, str] = {}
if articles:
    _sent_key = " ||| ".join(a["title"] for a in articles[:50])
    sentiment_map = _cached_sentiment(_sent_key)


# ── Alert matching helper ─────────────────────────────────────────────────────
def _is_alert(article: dict) -> bool:
    if not alert_keywords:
        return False
    text = (article["title"] + " " + article.get("description", "")).lower()
    return any(kw in text for kw in alert_keywords)

alert_count = sum(1 for a in articles if _is_alert(a))

# Show alert feedback in sidebar
if alert_keywords and articles:
    with st.sidebar:
        if alert_count > 0:
            st.success(f"🔔 {alert_count} article{'s' if alert_count != 1 else ''} match your keywords!", icon="🔔")
            matched = [a for a in articles if _is_alert(a)]
            for m in matched[:5]:
                st.caption(f"• {m['title'][:80]}")
            if alert_count > 5:
                st.caption(f"  ...and {alert_count - 5} more")
        else:
            st.info(f"No articles match: {', '.join(alert_keywords)}", icon="🔍")


# ── Stats ─────────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
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
    pos_count = sum(1 for s in sentiment_map.values() if s == "positive")
    pct = round(pos_count / max(len(sentiment_map), 1) * 100)
    st.markdown(
        '<div class="stat-card"><div class="stat-icon">😊</div>'
        f'<div class="stat-num green">{pct}%</div>'
        '<div class="stat-label">Positive</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(
        '<div class="stat-card"><div class="stat-icon">🔔</div>'
        f'<div class="stat-num">{alert_count}</div>'
        '<div class="stat-label">Alerts</div></div>', unsafe_allow_html=True)
with c5:
    st.markdown(
        '<div class="stat-card"><div class="stat-icon">🕐</div>'
        f'<div class="stat-num">{datetime.now(timezone.utc).strftime("%H:%M")}</div>'
        '<div class="stat-label">UTC Now</div></div>', unsafe_allow_html=True)


# ── Trending Topics ───────────────────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def _cached_topics(titles_joined: str) -> list[str]:
    titles = titles_joined.split(" ||| ")
    return extract_trending_topics([{"title": t} for t in titles])

topics: list[str] = []
if articles:
    _topics_key = " ||| ".join(a["title"] for a in articles[:30])
    topics = _cached_topics(_topics_key)
    if topics:
        pills = "".join(f'<span class="trending-pill">{t}</span>' for t in topics)
        st.markdown(
            f'<div style="margin:.8rem 0 .4rem"><span style="font-size:.78rem;font-weight:700;'
            f'color:#888e99;text-transform:uppercase;letter-spacing:1px">'
            f'Trending Now</span></div><div class="trending-bar">{pills}</div>',
            unsafe_allow_html=True)

st.markdown("")


# ── Auto-send email digest on first load of the day ──────────────────────────
if (
    _smtp_ready
    and DIGEST_RECIPIENT
    and articles
    and not was_digest_sent_today()
    and "auto_digest_attempted" not in st.session_state
):
    st.session_state.auto_digest_attempted = True
    _ok, _msg = send_news_digest(
        SMTP_EMAIL, SMTP_PASSWORD, DIGEST_RECIPIENT, articles, topics,
    )
    if _ok:
        st.toast(f"📧 Daily digest auto-sent to {DIGEST_RECIPIENT}!", icon="✅")


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_briefing, tab_articles, tab_analytics, tab_chat, tab_email, tab_arch = st.tabs([
    "🧠 AI Briefing", "📰 All Articles", "📊 Analytics", "💬 Ask AI", "📧 Email Digest", "🏗️ How It Works",
])


# ━━ Tab 1: Briefing ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_briefing:
    st.markdown("### Daily Tech Briefing")
    st.caption("AI-generated executive summary with top stories, trends, and market signals.")

    if st.button("Generate Briefing", type="primary", use_container_width=True):
        with st.spinner("Analyzing headlines and generating briefing..."):
            briefing = summarize_all(articles)
        st.markdown(f'<div class="briefing-box">{_md(briefing)}</div>', unsafe_allow_html=True)
        # Save to history
        save_briefing(briefing, len(articles))
    else:
        st.info("Click **Generate Briefing** to get an AI-powered overview of all fetched headlines.", icon="💡")

    # Past briefings
    st.markdown("")
    st.markdown("### Past Briefings")
    hist = load_history()
    if not hist:
        st.caption("No past briefings yet. Generate one above to get started.")
    else:
        for i, entry in enumerate(hist[:10]):
            ts = entry.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts)
                label = dt.strftime("%b %d, %Y at %H:%M UTC")
            except Exception:
                label = ts
            ac = entry.get("article_count", "?")
            with st.expander(f"{label}  ({ac} articles)", expanded=False):
                st.markdown(
                    f'<div class="history-entry">{_md(entry.get("briefing", ""))}</div>',
                    unsafe_allow_html=True)


# ━━ Tab 2: Articles ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_articles:
    if not articles:
        st.warning("No articles found. Try selecting more sources or categories.")
    else:
        # Alert banner
        if alert_count > 0:
            st.warning(
                f"🔔 **{alert_count} article{'s' if alert_count != 1 else ''}** match your watchlist "
                f"keywords: **{', '.join(alert_keywords)}** — look for the orange ALERT badges below.",
                icon="🔔",
            )

        # Controls row
        ctrl_left, ctrl_right = st.columns([3, 1])
        with ctrl_left:
            query = st.text_input("🔍 Search articles", placeholder="Filter by title or description...", key="search_q")
        with ctrl_right:
            sort_option = st.selectbox(
                "Sort by",
                ["Newest First", "Oldest First", "Shortest Read", "Longest Read", "Source A-Z"],
                key="sort_opt",
            )

        filtered = articles
        if query:
            q = query.lower()
            filtered = [a for a in articles if q in a["title"].lower() or q in a.get("description", "").lower()]

        # Sort
        if sort_option == "Oldest First":
            filtered.sort(key=lambda a: a.get("published") or datetime.min.replace(tzinfo=timezone.utc))
        elif sort_option == "Shortest Read":
            filtered.sort(key=lambda a: a.get("reading_time", 1))
        elif sort_option == "Longest Read":
            filtered.sort(key=lambda a: a.get("reading_time", 1), reverse=True)
        elif sort_option == "Source A-Z":
            filtered.sort(key=lambda a: a.get("source", ""))
        # Newest First is the default order

        st.caption(f"Showing {len(filtered)} of {len(articles)} articles")

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

                # Sentiment
                sent = sentiment_map.get(article["title"], "neutral")
                sent_cls = f"sentiment-{sent}"
                dot_cls = {"positive": "pos", "negative": "neg", "neutral": "neu"}[sent]

                # Alert
                is_alerted = _is_alert(article)
                alert_cls = " alert-match" if is_alerted else ""

                alert_badge = ""
                if is_alerted:
                    alert_badge = '<span class="alert-badge">ALERT</span>'

                st.markdown(
                    f'<div class="card {sent_cls}{alert_cls}">'
                    f'<div class="card-header">'
                    f'<img class="card-favicon" src="{fav}" alt="">'
                    f'<span class="card-source"><span class="sentiment-dot {dot_cls}"></span>{article["source"]}</span>'
                    f'<span class="card-meta-right">{alert_badge}{pub}</span>'
                    f'</div>'
                    f'<div class="card-title"><a href="{article["url"]}" target="_blank">{article["title"]}</a></div>'
                    f'<div class="card-desc">{article.get("description", "")[:220]}</div>'
                    f'<div class="card-footer">'
                    f'<span class="card-tag">{article["category"]}</span>'
                    f'<span class="reading-time">&#128337; {rt} min read</span>'
                    f'</div></div>',
                    unsafe_allow_html=True)

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


# ━━ Tab 3: Analytics ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_analytics:
    st.markdown("### Analytics & Service Health")
    st.caption("Monitor service health and explore visual analytics of today's news.")

    # ── Service Health Dashboard (top) ────────────────────────────────────────
    _health_icons = {
        "TechCrunch": _favicon("techcrunch.com"),
        "The Verge": _favicon("theverge.com"),
        "Ars Technica": _favicon("arstechnica.com"),
        "Wired": _favicon("wired.com"),
        "Hacker News": _favicon("news.ycombinator.com"),
        "MIT Technology Review": _favicon("technologyreview.com"),
        "VentureBeat": _favicon("venturebeat.com"),
        "The Register": _favicon("theregister.com"),
        "OpenAI": _favicon("openai.com"),
        "Gmail SMTP": _favicon("gmail.com"),
    }

    st.markdown("#### 🩺 Service Health")
    if st.button("🔍 Check App Health", type="primary", key="btn_health"):
        with st.spinner("Pinging all services..."):
            health_results = run_all_checks()
        st.session_state.health_results = health_results

    if "health_results" in st.session_state:
        results = st.session_state.health_results
        healthy = sum(1 for r in results if r["status"] == "healthy")
        errors = sum(1 for r in results if r["status"] == "error")
        not_conf = sum(1 for r in results if r["status"] == "not_configured")
        active_results = [r for r in results if r["latency_ms"] > 0]
        avg_latency = round(
            sum(r["latency_ms"] for r in active_results)
            / max(len(active_results), 1)
        )

        st.markdown(
            f'<div class="health-summary">'
            f'<span class="health-summary-item"><span class="dot g"></span> {healthy} Healthy</span>'
            f'<span class="health-summary-item"><span class="dot r"></span> {errors} Error{"s" if errors != 1 else ""}</span>'
            f'<span class="health-summary-item"><span class="dot y"></span> {not_conf} Not Configured</span>'
            f'<span class="health-summary-item" style="margin-left:auto;color:#888e99;font-weight:400">'
            f'Avg latency: <strong>{avg_latency}ms</strong></span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        cards_html = '<div class="health-grid">'
        for r in results:
            status = r["status"]
            if status == "healthy":
                cls, status_icon, label = "ok", "✅", "Healthy"
            elif status == "error":
                cls, status_icon, label = "err", "❌", "Error"
            else:
                cls, status_icon, label = "noconf", "⚪", "Not Configured"

            latency_html = ""
            if r["latency_ms"] > 0:
                latency_html = f'<span class="health-latency">{r["latency_ms"]}ms</span>'

            icon_url = _health_icons.get(r["name"], "")
            icon_img = (
                f'<img src="{icon_url}" style="width:22px;height:22px;border-radius:4px;'
                f'vertical-align:middle;margin-right:6px" alt="">'
                if icon_url else ""
            )

            cards_html += (
                f'<div class="health-card {cls}">'
                f'{latency_html}'
                f'<div class="health-name">{icon_img}{r["name"]}</div>'
                f'<div class="health-type">{r["type"]}</div>'
                f'<div class="health-status {cls}">{status_icon} {label}</div>'
                f'<div class="health-msg">{r["message"]}</div>'
                f'</div>'
            )
        cards_html += '</div>'
        st.markdown(cards_html, unsafe_allow_html=True)
    else:
        st.info("Click **Check App Health** to ping all services and see their status.", icon="💡")

    # ── Charts ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📊 News Analytics")

    if not articles:
        st.warning("No articles to analyze.")
    else:
        dark_config = {
            "config": {
                "background": "transparent",
                "axis": {
                    "labelColor": "#888e99", "titleColor": "#888e99",
                    "gridColor": "rgba(255,255,255,0.05)", "domainColor": "#444",
                },
                "legend": {"labelColor": "#b0b5c0", "titleColor": "#888e99"},
                "title": {"color": "#dcdde1"},
                "view": {"stroke": "transparent"},
            }
        }
        alt.themes.register("dark_custom", lambda: dark_config)
        alt.themes.enable("dark_custom")

        chart_left, chart_right = st.columns(2)

        with chart_left:
            st.markdown("##### Articles by Source")
            src_df = pd.DataFrame([{"Source": a["source"]} for a in articles])
            src_counts = src_df["Source"].value_counts().reset_index()
            src_counts.columns = ["Source", "Count"]
            c = alt.Chart(src_counts).mark_bar(cornerRadiusEnd=6, color="#6c63ff").encode(
                x=alt.X("Count:Q", title="Articles"),
                y=alt.Y("Source:N", sort="-x", title=""),
            ).properties(height=250)
            st.altair_chart(c, use_container_width=True)

        with chart_right:
            st.markdown("##### Category Distribution")
            cat_df = pd.DataFrame([{"Category": a["category"]} for a in articles])
            cat_counts = cat_df["Category"].value_counts().reset_index()
            cat_counts.columns = ["Category", "Count"]
            c2 = alt.Chart(cat_counts).mark_arc(innerRadius=50, cornerRadius=4).encode(
                theta=alt.Theta("Count:Q"),
                color=alt.Color("Category:N", scale=alt.Scale(scheme="purples")),
                tooltip=["Category", "Count"],
            ).properties(height=250)
            st.altair_chart(c2, use_container_width=True)

        chart_left2, chart_right2 = st.columns(2)

        with chart_left2:
            st.markdown("##### Publish Timeline (by hour)")
            time_data = []
            for a in articles:
                if a.get("published"):
                    time_data.append({"Hour": a["published"].hour, "Source": a["source"]})
            if time_data:
                time_df = pd.DataFrame(time_data)
                c3 = alt.Chart(time_df).mark_bar(cornerRadiusEnd=4, color="#a89bff").encode(
                    x=alt.X("Hour:O", title="Hour (UTC)"),
                    y=alt.Y("count():Q", title="Articles"),
                ).properties(height=250)
                st.altair_chart(c3, use_container_width=True)
            else:
                st.caption("No timestamp data available.")

        with chart_right2:
            st.markdown("##### Sentiment Breakdown")
            if sentiment_map:
                sent_data = []
                for a in articles:
                    s = sentiment_map.get(a["title"], "neutral")
                    sent_data.append({"Source": a["source"], "Sentiment": s.capitalize()})
                sent_df = pd.DataFrame(sent_data)
                color_scale = alt.Scale(
                    domain=["Positive", "Negative", "Neutral"],
                    range=["#5bda7d", "#ff6b6b", "#555e6e"],
                )
                c4 = alt.Chart(sent_df).mark_bar(cornerRadiusEnd=4).encode(
                    x=alt.X("count():Q", title="Articles"),
                    y=alt.Y("Source:N", sort="-x", title=""),
                    color=alt.Color("Sentiment:N", scale=color_scale),
                    tooltip=["Source", "Sentiment", "count()"],
                ).properties(height=250)
                st.altair_chart(c4, use_container_width=True)
            else:
                st.caption("No sentiment data available.")


# ━━ Tab 4: Ask AI ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_chat:
    st.markdown("### Ask AI About Today's News")
    st.caption("Chat with an AI that has read all of today's fetched articles.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    def _render_chat_response(result: dict, msg_idx: int):
        """Render a structured chat response with article links and summary buttons."""
        if result.get("found") and result.get("matched_articles"):
            st.markdown("✅ **Yes, there's news about this in today's articles!**")
            if result.get("brief"):
                st.markdown(
                    f'<div class="chat-brief">{result["brief"]}</div>',
                    unsafe_allow_html=True,
                )
            for art_idx, art in enumerate(result["matched_articles"]):
                st.markdown(
                    f'<div class="chat-article-link">'
                    f'<span>📰</span>'
                    f'<a href="{art["url"]}" target="_blank">{art["title"]}</a>'
                    f'<span class="chat-article-source">{art["source"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                summary_key = f"chat_sum_{msg_idx}_{art_idx}"
                if summary_key not in st.session_state:
                    if st.button("📝 Get Summary", key=f"btn_cs_{msg_idx}_{art_idx}"):
                        with st.spinner("Generating summary..."):
                            art_copy = dict(art)
                            if len(art_copy.get("content", "")) < 200:
                                body = fetch_article_body(art_copy["url"])
                                if body:
                                    art_copy["content"] = body
                            summary = summarize_article(art_copy)
                            st.session_state[summary_key] = summary
                        st.markdown(
                            f'<div class="summary-box">{_md(summary)}</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown(
                        f'<div class="summary-box">{_md(st.session_state[summary_key])}</div>',
                        unsafe_allow_html=True,
                    )
            if result.get("response"):
                st.markdown("")
                st.markdown(result["response"])
        else:
            web_results = result.get("web_results", [])
            if web_results:
                st.markdown(
                    "🌐 **Not in today's articles, but here's what I found "
                    "from the web (last 48 hours):**"
                )
                st.markdown(
                    f'<div class="chat-external-box">'
                    f'{_md(result.get("response", "No information available."))}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.markdown("**📎 Sources:**")
                for wr in web_results:
                    src_label = wr.get("source", "")
                    src_html = (
                        f'<span class="chat-article-source">{src_label}</span>'
                        if src_label else ""
                    )
                    st.markdown(
                        f'<div class="chat-article-link">'
                        f'<span>🔗</span>'
                        f'<a href="{wr["url"]}" target="_blank">{wr["title"]}</a>'
                        f'{src_html}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    f'<div class="chat-external-box">'
                    f'<strong>🔍 No recent news found about this topic in the '
                    f'last 48 hours.</strong><br><br>'
                    f'{_md(result.get("response", "No information available."))}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # Display chat history
    for idx, msg in enumerate(st.session_state.chat_history):
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant" and "result" in msg:
                _render_chat_response(msg["result"], idx)
            else:
                st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask about today's tech news..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                history_for_ai = [
                    {"role": h["role"], "content": h["content"]}
                    for h in st.session_state.chat_history[:-1]
                ]
                result = chat_about_news(articles, prompt, history_for_ai)
            _render_chat_response(result, len(st.session_state.chat_history))

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": result["response"],
            "result": result,
        })


# ━━ Tab 5: Email Digest ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_email:
    st.markdown("### 📧 Email News Digest")
    st.caption("Send a beautifully formatted email digest of today's top tech news.")

    if not _smtp_ready:
        st.warning(
            "**Email not configured.** Add these to your `.env` file to get started:\n\n"
            "```\n"
            "SMTP_EMAIL=your.gmail@gmail.com\n"
            "SMTP_PASSWORD=your-app-password\n"
            "```\n\n"
            "Use a [Gmail App Password](https://myaccount.google.com/apppasswords), "
            "not your regular password.",
            icon="🔒",
        )
    else:
        # ── Send section ─────────────────────────────────────────────────────
        send_col, preview_col = st.columns([1, 1])

        with send_col:
            st.markdown("#### Send Digest")
            _recipient = st.text_input(
                "Recipient email",
                value=DIGEST_RECIPIENT,
                placeholder="you@example.com",
                key="digest_email_input",
            )

            if was_digest_sent_today():
                last_info = get_last_send_info()
                if last_info:
                    try:
                        _ts = datetime.fromisoformat(last_info["time"])
                        _lbl = _ts.strftime("%H:%M UTC")
                    except Exception:
                        _lbl = "earlier"
                    st.success(
                        f"Today's digest sent at **{_lbl}** to **{last_info['recipient']}** "
                        f"({last_info['article_count']} articles)",
                        icon="✅",
                    )

            if st.button(
                "📧 Send News Digest Now",
                type="primary",
                use_container_width=True,
                key="btn_send_digest",
            ):
                if not _recipient or not _recipient.strip():
                    st.error("Enter a recipient email address.")
                elif not articles:
                    st.warning("No articles fetched yet.")
                else:
                    with st.spinner("Sending digest..."):
                        _ok, _msg = send_news_digest(
                            SMTP_EMAIL, SMTP_PASSWORD,
                            _recipient.strip(), articles, topics,
                        )
                    if _ok:
                        st.success(_msg, icon="✅")
                        st.balloons()
                    else:
                        st.error(_msg)

            st.markdown("")
            st.markdown("#### Settings")
            st.markdown(
                f"**SMTP Account:** `{SMTP_EMAIL}`\n\n"
                f"**Auto-send:** {'✅ Enabled' if DIGEST_RECIPIENT else '❌ Disabled'}"
            )
            if DIGEST_RECIPIENT:
                st.caption(
                    f"Auto-sends to **{DIGEST_RECIPIENT}** on first app load each day. "
                    f"Set `DIGEST_RECIPIENT` in `.env` to change or remove."
                )
            else:
                st.caption(
                    "Set `DIGEST_RECIPIENT` in `.env` to auto-send a digest "
                    "every time the app is loaded fresh each day."
                )

        with preview_col:
            st.markdown("#### Email Preview")
            if not articles:
                st.info("No articles fetched yet. Preview will appear once articles load.")
            else:
                preview_count = min(len(articles), 15)
                st.caption(f"Digest will include **{preview_count}** articles and trending topics.")
                st.markdown(
                    '<div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);'
                    'border-radius:12px;padding:1rem 1.2rem;max-height:400px;overflow-y:auto;">',
                    unsafe_allow_html=True,
                )
                if topics:
                    pills = " ".join(
                        f'`{t}`' for t in topics
                    )
                    st.markdown(f"**🔥 Trending:** {pills}")
                    st.markdown("")
                for i, a in enumerate(articles[:8], 1):
                    pub = ""
                    if a.get("published"):
                        pub = a["published"].strftime("%b %d, %H:%M")
                    st.markdown(
                        f"**{i}. {a['title']}**\n\n"
                        f"<small style='color:#888'>{a['source']}"
                        f"{'&nbsp;·&nbsp;' + pub if pub else ''}"
                        f"&nbsp;·&nbsp;{a.get('category', '')}</small>",
                        unsafe_allow_html=True,
                    )
                if len(articles) > 8:
                    st.caption(f"... and {preview_count - 8} more articles")
                st.markdown('</div>', unsafe_allow_html=True)

        # ── Send history ─────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### Send History")
        email_history = get_send_history()
        if not email_history:
            st.caption("No digests sent yet. Send one above to get started!")
        else:
            hist_data = []
            for entry in email_history[:15]:
                try:
                    dt = datetime.fromisoformat(entry["time"])
                    date_str = dt.strftime("%b %d, %Y")
                    time_str = dt.strftime("%H:%M UTC")
                except Exception:
                    date_str = entry.get("date", "?")
                    time_str = "?"
                hist_data.append({
                    "Date": date_str,
                    "Time": time_str,
                    "Recipient": entry.get("recipient", "?"),
                    "Articles": entry.get("article_count", "?"),
                })
            st.dataframe(
                hist_data,
                use_container_width=True,
                hide_index=True,
            )


# ━━ Tab 6: How It Works ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_arch:
    st.markdown("### Application Architecture")
    st.caption("End-to-end data flow — from news sources through AI processing to email delivery and health monitoring.")

    st.markdown("""<svg viewBox="0 0 800 640" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:800px;margin:1rem auto;display:block">
  <defs>
    <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#302b63"/>
      <stop offset="100%" style="stop-color:#24243e"/>
    </linearGradient>
    <filter id="shadow"><feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.15" flood-color="#6c63ff"/></filter>
  </defs>
  <style>
    .box{fill:url(#g1);stroke:rgba(108,99,255,0.35);stroke-width:1.5;rx:10}
    .box-api{fill:rgba(253,126,20,0.08);stroke:#fd7e14;stroke-width:1.5;rx:10}
    .box-out{fill:rgba(40,167,69,0.08);stroke:#28a745;stroke-width:1.5;rx:10}
    .box-core{fill:url(#g1);stroke:#6c63ff;stroke-width:2;rx:12;filter:url(#shadow)}
    .box-email{fill:rgba(255,183,77,0.08);stroke:#ffb74d;stroke-width:1.5;rx:10}
    .box-health{fill:rgba(77,208,225,0.08);stroke:#4dd0e1;stroke-width:1.5;rx:10}
    .label{fill:#dddaf5;font-size:12px;font-weight:700;font-family:sans-serif;text-anchor:middle}
    .sublabel{fill:#888e99;font-size:9px;font-family:sans-serif;text-anchor:middle}
    .arrow{stroke:#6c63ff;stroke-width:2;marker-end:url(#ah)}
    .arrow-o{stroke:#ffb74d;stroke-width:1.5;stroke-dasharray:5,3;marker-end:url(#aho)}
  </style>
  <marker id="ah" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
    <path d="M0,0 L8,3 L0,6" fill="#6c63ff"/>
  </marker>
  <marker id="aho" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
    <path d="M0,0 L8,3 L0,6" fill="#ffb74d"/>
  </marker>

  <!-- Row 1: Sources -->
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
  <text class="label" x="710" y="28">+3 More</text>
  <text class="sublabel" x="710" y="42">MIT, VB,</text>
  <text class="sublabel" x="710" y="53">Register</text>

  <!-- Arrows: Sources → Fetcher -->
  <line class="arrow" x1="75" y1="60" x2="400" y2="115"/>
  <line class="arrow" x1="200" y1="60" x2="400" y2="115"/>
  <line class="arrow" x1="325" y1="60" x2="400" y2="115"/>
  <line class="arrow" x1="450" y1="60" x2="400" y2="115"/>
  <line class="arrow" x1="575" y1="60" x2="400" y2="115"/>
  <line class="arrow" x1="710" y1="60" x2="400" y2="115"/>

  <!-- Row 2: Fetcher -->
  <rect class="box-core" x="260" y="115" width="280" height="55"/>
  <text class="label" x="400" y="140" style="font-size:14px">News Fetcher</text>
  <text class="sublabel" x="400" y="158">news_fetcher.py &middot; feedparser + requests</text>
  <line class="arrow" x1="400" y1="170" x2="400" y2="200"/>

  <!-- Row 3: Parse -->
  <rect class="box-core" x="260" y="200" width="280" height="55"/>
  <text class="label" x="400" y="225" style="font-size:14px">Parse &amp; Clean</text>
  <text class="sublabel" x="400" y="243">BeautifulSoup &middot; HTML strip &middot; Normalize</text>
  <line class="arrow" x1="400" y1="255" x2="400" y2="285"/>

  <!-- Row 4: Dedup -->
  <rect class="box-core" x="260" y="285" width="280" height="55"/>
  <text class="label" x="400" y="310" style="font-size:14px">Categorize &amp; Deduplicate</text>
  <text class="sublabel" x="400" y="328">Category mapping &middot; Title similarity check</text>

  <!-- Arrows: Dedup → 4 outputs -->
  <line class="arrow" x1="330" y1="340" x2="105" y2="390"/>
  <line class="arrow" x1="370" y1="340" x2="295" y2="390"/>
  <line class="arrow" x1="430" y1="340" x2="490" y2="390"/>
  <line class="arrow" x1="470" y1="340" x2="670" y2="390"/>

  <!-- Row 5: Four output boxes -->
  <rect class="box-out" x="20" y="390" width="170" height="55"/>
  <text class="label" x="105" y="413" style="fill:#5bda7d;font-size:12px">Display Articles</text>
  <text class="sublabel" x="105" y="430">UI &middot; Cards &middot; Search &middot; Sort</text>

  <rect class="box-core" x="210" y="390" width="170" height="55"/>
  <text class="label" x="295" y="413" style="font-size:12px">AI Engine</text>
  <text class="sublabel" x="295" y="430">Chat &middot; Summary &middot; Briefing</text>

  <rect class="box-email" x="400" y="390" width="180" height="55"/>
  <text class="label" x="490" y="413" style="fill:#ffb74d;font-size:12px">Email Digest</text>
  <text class="sublabel" x="490" y="430">Gmail SMTP &middot; HTML &middot; Auto-send</text>

  <rect class="box-health" x="600" y="390" width="170" height="55"/>
  <text class="label" x="685" y="413" style="fill:#4dd0e1;font-size:12px">Health Monitor</text>
  <text class="sublabel" x="685" y="430">Concurrent pings &middot; Latency</text>

  <!-- Google News fallback (dashed arrow into AI Engine) -->
  <rect class="box-api" x="5" y="475" width="185" height="42"/>
  <text class="label" x="97" y="494" style="fill:#ffa54c;font-size:11px">Google News RSS</text>
  <text class="sublabel" x="97" y="508">Web search fallback &middot; 48h</text>
  <line class="arrow-o" x1="190" y1="490" x2="260" y2="445"/>

  <!-- Arrows: outputs → final -->
  <line class="arrow" x1="105" y1="445" x2="340" y2="560"/>
  <line class="arrow" x1="295" y1="445" x2="370" y2="560"/>
  <line class="arrow" x1="490" y1="445" x2="430" y2="560"/>
  <line class="arrow" x1="685" y1="445" x2="460" y2="560"/>

  <!-- Health Monitor side arrows (checking sources) -->
  <line class="arrow-o" x1="685" y1="390" x2="685" y2="70" style="stroke:#4dd0e1;stroke-dasharray:4,4;stroke-width:1;opacity:.4;marker-end:none"/>
  <text class="sublabel" x="730" y="230" style="fill:#4dd0e1;font-size:8px;writing-mode:tb">health checks</text>

  <!-- Final output -->
  <rect class="box-out" x="250" y="555" width="300" height="45" style="filter:url(#shadow)"/>
  <text class="label" x="400" y="575" style="fill:#5bda7d;font-size:13px">Full-Stack AI News Platform</text>
  <text class="sublabel" x="400" y="590">Articles + Summaries + Email + Monitoring</text>
</svg>""", unsafe_allow_html=True)

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
        ("Sentiment Analysis",
         "All headlines are sent to <strong>GPT</strong> in a single batch call. Each article is "
         "classified as <strong>positive, negative,</strong> or <strong>neutral</strong>. Results "
         "color-code card borders and feed the Analytics dashboard."),
        ("Display, Search &amp; Sort",
         "Articles render in a <strong>two-column card grid</strong> with source favicons, "
         "category tags, reading time, and sentiment indicators. Search filters in real time. "
         "Sort by date, reading time, or source name."),
        ("Keyword Alerts",
         "Users define <strong>watchlist keywords</strong> in the sidebar. Articles matching any "
         "keyword get an amber <strong>ALERT</strong> badge and highlighted border. "
         "The stats bar shows a live alert count."),
        ("AI Summary &amp; Briefing",
         "<strong>Per-article summaries</strong> include key facts, why it matters, and key players. "
         "<strong>Executive briefings</strong> include Top Stories, Trends, Market Signals, and Quick Bites. "
         "Briefings are <strong>auto-saved</strong> to local JSON for history."),
        ("Smart AI Chat",
         "The chat uses <strong>structured JSON responses</strong> from GPT to determine if the "
         "user's question matches any fetched article. <strong>If found:</strong> shows a brief, "
         "highlighted clickable links to matching articles, and a <strong>Get Summary</strong> button "
         "for each. <strong>If not found:</strong> automatically searches <strong>Google News RSS</strong> "
         "for real articles from the last 48 hours, then summarizes those results &mdash; no hallucination."),
        ("Email Digest",
         "A <strong>Gmail SMTP</strong> integration sends beautifully formatted HTML email digests "
         "with trending topics and top stories. Supports <strong>manual send</strong> from the Email tab "
         "and <strong>auto-send on first daily load</strong> when <code>DIGEST_RECIPIENT</code> is configured. "
         "Send history is tracked in a local JSON log. Uses <code>smtplib</code> with TLS encryption."),
        ("Service Health Monitor",
         "A <strong>concurrent health checker</strong> pings all external services in parallel: "
         "8 RSS/Atom feeds, Hacker News API, OpenAI API, and Gmail SMTP. Each check reports "
         "<strong>status, latency,</strong> and a descriptive message. Results display as a card grid "
         "with <strong>brand favicons</strong> and color-coded health indicators."),
        ("Analytics Dashboard",
         "The <strong>health dashboard</strong> sits at the top for quick service monitoring. "
         "Below, four <strong>Altair charts</strong> visualize the news landscape: articles per source, "
         "category distribution (donut), publish timeline by hour, and sentiment breakdown per source."),
    ]
    for i, (title, desc) in enumerate(steps, 1):
        st.markdown(
            f'<div class="step"><div class="step-n">{i}</div>'
            f'<div class="step-body"><h4>{title}</h4><p>{desc}</p></div></div>',
            unsafe_allow_html=True)

    st.markdown("")
    st.markdown("### Tech Stack")
    st.markdown(
        '<div class="arch-card">'
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:1.2rem">'
        '<div><h3 style="font-size:1rem">Frontend</h3><ul>'
        '<li><code>Streamlit</code> &mdash; Reactive web UI</li>'
        '<li>Custom CSS &mdash; Dark glassmorphism theme</li>'
        '<li><code>Altair</code> &mdash; Interactive charts</li>'
        '<li>SVG &mdash; Architecture diagram</li></ul></div>'
        '<div><h3 style="font-size:1rem">Data Layer</h3><ul>'
        '<li><code>feedparser</code> &mdash; RSS/Atom + Google News</li>'
        '<li><code>requests</code> &mdash; HTTP &amp; API calls</li>'
        '<li><code>BeautifulSoup</code> &mdash; HTML cleaning</li>'
        '<li><code>ThreadPoolExecutor</code> &mdash; Concurrent fetching</li></ul></div>'
        '<div><h3 style="font-size:1rem">AI / LLM</h3><ul>'
        '<li><code>OpenAI GPT-4o-mini</code> &mdash; Summarization</li>'
        '<li>Sentiment analysis &mdash; Batch classification</li>'
        '<li>Smart Chat &mdash; JSON structured responses</li>'
        '<li>Web fallback &mdash; Google News RSS + AI summary</li></ul></div>'
        '<div><h3 style="font-size:1rem">Email</h3><ul>'
        '<li><code>smtplib</code> &mdash; Gmail SMTP with TLS</li>'
        '<li><code>email.mime</code> &mdash; HTML email builder</li>'
        '<li>Auto-send &mdash; Daily digest on first load</li>'
        '<li>Send history &mdash; JSON log tracking</li></ul></div>'
        '<div><h3 style="font-size:1rem">Monitoring</h3><ul>'
        '<li>Health checks &mdash; All services concurrently</li>'
        '<li>Latency tracking &mdash; Per-service ms timing</li>'
        '<li>Brand favicons &mdash; Google Favicon API</li>'
        '<li>Status grid &mdash; Healthy / Error / Not Configured</li></ul></div>'
        '<div><h3 style="font-size:1rem">Infrastructure</h3><ul>'
        '<li><code>python-dotenv</code> &mdash; Config management</li>'
        '<li><code>@st.cache_data</code> &mdash; 10-min TTL cache</li>'
        '<li>Local JSON &mdash; Briefing + email history</li>'
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
