from dotenv import load_dotenv
load_dotenv()

from .config import SOURCES, SEARCH_QUERIES, STATE_PATH, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from .state import State
from .sources import scan_source
from .search import scan_search
from .notifier import send_telegram

def notify_new_candidates(state):
    for code, item in state.data["codes"].items():
        if item["notified"]:
            continue
        if item["confidence"] < 0.60:
            continue

        sources = sorted(item["sources"])
        text = (
            "🆕 Last Asylum: Plague\n\n"
            f"Код: {code}\n"
            f"Статус: {item['status']}\n"
            f"Confidence: {item['confidence']:.0%}\n"
        )
        if item.get("reward"):
            text += f"Награда: {item['reward']}\n"
        if item.get("expires_at"):
            flag = " (уже истёк)" if item.get("expired") else ""
            text += f"Истекает: {item['expires_at']}{flag}\n"
        text += f"Источники: {len(sources)}\n\n" + "\n".join(f"• {s}" for s in sources)

        try:
            send_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, text)
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
