"""
Email Module — Send beautifully formatted news digests via Gmail SMTP.
Tracks daily sends to avoid duplicates on auto-send.
"""

import json
import os
import smtplib
from datetime import date, datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

EMAIL_LOG_FILE = os.path.join(os.path.dirname(__file__), "email_log.json")


# ── Daily send tracking ──────────────────────────────────────────────────────

def _load_email_log() -> dict:
    if not os.path.exists(EMAIL_LOG_FILE):
        return {}
    try:
        with open(EMAIL_LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_email_log(log: dict) -> None:
    try:
        with open(EMAIL_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARNING] Failed to save email log: {e}")


def was_digest_sent_today() -> bool:
    log = _load_email_log()
    return log.get("last_sent_date", "") == date.today().isoformat()


def get_last_send_info() -> dict | None:
    """Return last send info or None if never sent."""
    log = _load_email_log()
    if not log.get("last_sent_date"):
        return None
    return {
        "date": log.get("last_sent_date", ""),
        "time": log.get("last_sent_time", ""),
        "recipient": log.get("last_recipient", ""),
        "article_count": log.get("last_article_count", 0),
    }


def _mark_sent_today(recipient: str, article_count: int) -> None:
    log = _load_email_log()
    log["last_sent_date"] = date.today().isoformat()
    log["last_sent_time"] = datetime.now(timezone.utc).isoformat()
    log["last_recipient"] = recipient
    log["last_article_count"] = article_count
    history = log.get("history", [])
    history.insert(0, {
        "date": date.today().isoformat(),
        "time": datetime.now(timezone.utc).isoformat(),
        "recipient": recipient,
        "article_count": article_count,
    })
    log["history"] = history[:30]
    _save_email_log(log)


# ── HTML email builder ───────────────────────────────────────────────────────

def _build_html_email(
    articles: list[dict],
    trending_topics: list[str],
) -> str:
    today_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    article_count = min(len(articles), 15)

    article_rows = ""
    for a in articles[:15]:
        pub = ""
        if a.get("published"):
            try:
                pub = a["published"].strftime("%b %d, %H:%M UTC")
            except Exception:
                pass
        desc = a.get("description", "")
        snippet = (desc[:180] + "...") if len(desc) > 180 else desc

        article_rows += f"""
        <tr>
          <td style="padding:16px 20px;border-bottom:1px solid #eef0f3;">
            <div style="font-size:11px;font-weight:700;text-transform:uppercase;
                        letter-spacing:.5px;color:#6c63ff;margin-bottom:4px;">
              {a['source']}{'&nbsp;&middot;&nbsp;' + pub if pub else ''}
            </div>
            <a href="{a['url']}" target="_blank"
               style="font-size:15px;font-weight:600;color:#1a1a2e;
                      text-decoration:none;line-height:1.4;">
              {a['title']}
            </a>
            <div style="font-size:13px;color:#666;margin-top:6px;line-height:1.5;">
              {snippet}
            </div>
            <div style="margin-top:8px;">
              <span style="display:inline-block;padding:2px 10px;border-radius:12px;
                           font-size:11px;font-weight:600;background:#f0eeff;color:#6c63ff;">
                {a.get('category', 'Tech')}
              </span>
            </div>
          </td>
        </tr>"""

    trending_html = ""
    if trending_topics:
        pills = "".join(
            f'<span style="display:inline-block;padding:6px 14px;border-radius:20px;'
            f'font-size:12px;font-weight:600;background:#f0eeff;color:#6c63ff;'
            f'margin:3px 4px;">{t}</span>'
            for t in trending_topics
        )
        trending_html = f"""
        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;">
          <tr>
            <td style="padding:20px;background:#fafafe;border-radius:12px;">
              <div style="font-size:13px;font-weight:700;text-transform:uppercase;
                          letter-spacing:1px;color:#888;margin-bottom:10px;">
                🔥 Trending Now
              </div>
              <div>{pills}</div>
            </td>
          </tr>
        </table>"""

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f4f5f7;
             font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,
             Helvetica,Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0"
       style="background:#f4f5f7;padding:20px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0"
           style="max-width:600px;width:100%;">

      <!-- Header -->
      <tr><td style="background:linear-gradient(135deg,#1a1a2e 0%,#302b63 50%,
                     #24243e 100%);padding:32px 30px;
                     border-radius:16px 16px 0 0;">
        <div style="font-size:26px;font-weight:800;color:#fff;">
          📡 Tech News Digest</div>
        <div style="font-size:14px;color:#c0bfff;margin-top:6px;">
          {today_str} &middot; {article_count} articles from top sources</div>
      </td></tr>

      <!-- Body -->
      <tr><td style="background:#fff;padding:28px 24px;">
        {trending_html}
        <div style="font-size:13px;font-weight:700;text-transform:uppercase;
                    letter-spacing:1px;color:#888;margin-bottom:12px;">
          📰 Top Stories</div>
        <table width="100%" cellpadding="0" cellspacing="0"
               style="border:1px solid #eef0f3;border-radius:12px;overflow:hidden;">
          {article_rows}
        </table>
      </td></tr>

      <!-- Footer -->
      <tr><td style="background:#fafafe;padding:20px 24px;
                     border-radius:0 0 16px 16px;text-align:center;">
        <div style="font-size:12px;color:#999;line-height:1.6;">
          Sent by <strong>Tech News Aggregator &amp; Summarizer</strong><br>
          Powered by AI &middot; TechCrunch, The Verge, Ars Technica,
          Wired, Hacker News &amp; more</div>
      </td></tr>

    </table>
  </td></tr>
</table>
</body></html>"""


# ── Send email ───────────────────────────────────────────────────────────────

def send_news_digest(
    smtp_email: str,
    smtp_password: str,
    recipient: str,
    articles: list[dict],
    trending_topics: list[str] | None = None,
) -> tuple[bool, str]:
    """Send a news digest email via Gmail SMTP.
    Returns (success, message).
    """
    if not articles:
        return False, "No articles to include in the digest."

    html = _build_html_email(articles, trending_topics or [])
    today_str = datetime.now(timezone.utc).strftime("%b %d, %Y")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📡 Tech News Digest — {today_str}"
    msg["From"] = smtp_email
    msg["To"] = recipient

    plain_lines = [f"Tech News Digest — {today_str}\n"]
    for i, a in enumerate(articles[:15], 1):
        plain_lines.append(f"{i}. [{a['source']}] {a['title']}\n   {a['url']}\n")
    msg.attach(MIMEText("\n".join(plain_lines), "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.send_message(msg)
        _mark_sent_today(recipient, len(articles))
        return True, f"Digest sent to **{recipient}** with {len(articles)} articles!"
    except smtplib.SMTPAuthenticationError:
        return (
            False,
            "Authentication failed — check your Gmail address and "
            "[App Password](https://myaccount.google.com/apppasswords).",
        )
    except Exception as e:
        return False, f"Failed to send email: {e}"
