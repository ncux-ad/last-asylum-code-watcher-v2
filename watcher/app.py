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
            f"Источники: {len(sources)}\n\n"
            + "\n".join(f"• {s}" for s in sources)
        )

        try:
            send_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, text)
        finally:
            item["notified"] = True

def main():
    state = State(STATE_PATH)

    for name, url in SOURCES:
        try:
            source, codes = scan_source(name, url)
            for code in codes:
                state.observe(code, source, url)
            state.mark_missing(source, codes)
            print(f"[OK] {name}: {len(codes)} codes")
        except Exception as e:
            print(f"[WARN] {name}: {e}")

    for query in SEARCH_QUERIES:
        try:
            for code in scan_search(query):
                state.observe(code, "google-news", None, "discovery")
        except Exception as e:
            print(f"[WARN] search {query}: {e}")

    notify_new_candidates(state)
    state.save()
    print(f"Done. Known codes: {len(state.data['codes'])}")
