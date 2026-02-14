"""
Briefing History — Local JSON persistence for past AI briefings.
"""

import json
import os
from datetime import datetime, timezone

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "briefing_history.json")


def save_briefing(briefing_text: str, article_count: int) -> None:
    """Append a briefing to the local history file."""
    history = load_history()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "briefing": briefing_text,
        "article_count": article_count,
    }
    history.insert(0, entry)
    # Keep last 20 briefings
    history = history[:20]
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARNING] Failed to save briefing history: {e}")


def load_history() -> list[dict]:
    """Load past briefings from the local JSON file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []
