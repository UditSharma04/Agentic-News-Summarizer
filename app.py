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
from emailer import send_news_digest, was_digest_sent_today, get_last_send_info

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


# ── Email Digest (sidebar section + auto-send) ───────────────────────────────
_smtp_ready = bool(SMTP_EMAIL and SMTP_PASSWORD)

with st.sidebar:
    st.markdown("---")
    st.markdown('<p class="filter-hd">📧 Email Digest</p>', unsafe_allow_html=True)

    if not _smtp_ready:
        st.caption("Add `SMTP_EMAIL` & `SMTP_PASSWORD` to `.env` to enable email digests.")
    else:
        _recipient = st.text_input(
            "Recipient email",
            value=DIGEST_RECIPIENT,
            placeholder="you@example.com",
            key="digest_email_input",
        )

        last_info = get_last_send_info()
        if was_digest_sent_today() and last_info:
            try:
                _ts = datetime.fromisoformat(last_info["time"])
                _lbl = _ts.strftime("%H:%M UTC")
            except Exception:
                _lbl = "earlier"
            st.success(f"✅ Sent today at {_lbl} to {last_info['recipient']}", icon="📧")

        if st.button("📧 Send News Digest", use_container_width=True, key="btn_send_digest"):
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
                else:
                    st.error(_msg)

        if DIGEST_RECIPIENT:
            st.caption(f"Auto-sends to **{DIGEST_RECIPIENT}** on first load each day.")

# Auto-send on first load of the day
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
tab_briefing, tab_articles, tab_analytics, tab_chat, tab_arch = st.tabs([
    "🧠 AI Briefing", "📰 All Articles", "📊 Analytics", "💬 Ask AI", "🏗️ How It Works"
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
    st.markdown("### Analytics Dashboard")
    st.caption("Visual breakdown of today's tech news landscape.")

    if not articles:
        st.warning("No articles to analyze.")
    else:
        # Dark theme for Altair
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

        # 1. Articles per source
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

        # 2. Category distribution
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

        # 3. Publish timeline
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

        # 4. Sentiment breakdown
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


# ━━ Tab 5: How It Works ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_arch:
    st.markdown("### Application Architecture")
    st.caption("End-to-end data flow from news sources to AI-powered summaries.")

    st.markdown("""<svg viewBox="0 0 800 520" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:800px;margin:1rem auto;display:block">
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
        ("Ask AI Chat",
         "A <strong>conversational interface</strong> lets users ask questions about today's news. "
         "All fetched articles are injected as context into the system prompt. "
         "Chat history is maintained throughout the session."),
        ("Analytics Dashboard",
         "Four <strong>Altair charts</strong> visualize the news landscape: articles per source, "
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
        '<li><code>feedparser</code> &mdash; RSS/Atom parsing</li>'
        '<li><code>requests</code> &mdash; HTTP &amp; API calls</li>'
        '<li><code>BeautifulSoup</code> &mdash; HTML cleaning</li>'
        '<li><code>ThreadPoolExecutor</code> &mdash; Concurrent fetching</li></ul></div>'
        '<div><h3 style="font-size:1rem">AI / LLM</h3><ul>'
        '<li><code>OpenAI GPT-4o-mini</code> &mdash; Summarization</li>'
        '<li>Sentiment analysis &mdash; Batch classification</li>'
        '<li>Chat &mdash; Article-context-aware Q&amp;A</li>'
        '<li>JSON extraction &mdash; Topics &amp; sentiment</li></ul></div>'
        '<div><h3 style="font-size:1rem">Infrastructure</h3><ul>'
        '<li><code>python-dotenv</code> &mdash; Config management</li>'
        '<li><code>@st.cache_data</code> &mdash; 10-min TTL cache</li>'
        '<li>Local JSON &mdash; Briefing history persistence</li>'
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
