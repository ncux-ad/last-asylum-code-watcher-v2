from dotenv import load_dotenv
load_dotenv()

from html import escape

from .config import (
    SOURCES, SEARCH_QUERIES, STATE_PATH,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_MESSAGE_THREAD_ID,
)
from .state import State
from .sources import scan_source
from .search import scan_search
from .notifier import send_telegram

STATUS_LABELS = {
    "confirmed": "подтверждён",
    "probable": "вероятно рабочий",
    "candidate": "не подтверждён",
}

def status_label(item):
    """Manual redemption checks (tools/verify_codes.py) are stronger
    evidence than the source-count heuristic, so they take priority
    over item['status'] when present."""
    manual = item.get("manual_verification")
    if manual and manual.get("result") == "ok":
        return "проверен вручную, рабочий"
    if manual and manual.get("result") == "expired":
        return "истёк"
    return STATUS_LABELS.get(item["status"], item["status"])

def format_post(code, item):
    text = (
        f"Код: <code>{escape(code)}</code>\n"
        f"Статус: {escape(status_label(item))}\n"
    )
    if item.get("reward"):
        text += f"Награда: {escape(item['reward'])}\n"
    return text

def notify_new_candidates(state):
    for code, item in state.data["codes"].items():
        if item["notified"]:
            continue
        if item["confidence"] < 0.60:
            continue

        text = format_post(code, item)

        try:
            send_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, text, TELEGRAM_MESSAGE_THREAD_ID)
        finally:
            item["notified"] = True

def main():
    state = State(STATE_PATH)

    for name, url in SOURCES:
        try:
            source, candidates = scan_source(name, url)
            for c in candidates:
                state.observe(c["code"], source, url, reward=c.get("reward"),
                              expires_at=c.get("expires_at"), expired=c.get("expired"))
            state.mark_missing(source, [c["code"] for c in candidates])
            print(f"[OK] {name}: {len(candidates)} codes")
        except Exception as e:
            print(f"[WARN] {name}: {e}")

    for query in SEARCH_QUERIES:
        try:
            for c in scan_search(query):
                state.observe(c["code"], "google-news", None, "discovery", reward=c.get("reward"),
                              expires_at=c.get("expires_at"), expired=c.get("expired"))
        except Exception as e:
            print(f"[WARN] search {query}: {e}")

    notify_new_candidates(state)
    state.save()
    print(f"Done. Known codes: {len(state.data['codes'])}")
