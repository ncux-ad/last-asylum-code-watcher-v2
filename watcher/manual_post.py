"""Operator-run tool: post one already-known code to Telegram, bypassing
the auto-notify confidence threshold. Meant for codes that were manually
verified (tools/verify_codes.py) but don't have enough independent sources
to clear notify_new_candidates()'s 0.60 confidence bar on their own.

Usage: python -m watcher.manual_post <CODE>
"""
import sys

from dotenv import load_dotenv
load_dotenv()

from .config import STATE_PATH, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_MESSAGE_THREAD_ID
from .state import State
from .notifier import send_telegram
from .app import format_post

def main():
    if len(sys.argv) != 2:
        print("Usage: python -m watcher.manual_post <CODE>")
        raise SystemExit(1)

    code = sys.argv[1].strip()
    state = State(STATE_PATH)
    item = state.data["codes"].get(code)
    if item is None:
        print(f"[ERROR] Code {code} not found in state")
        raise SystemExit(1)

    text = format_post(code, item)
    send_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, text, TELEGRAM_MESSAGE_THREAD_ID)
    item["notified"] = True
    state.save()
    print(f"[OK] Posted {code}")

if __name__ == "__main__":
    main()
