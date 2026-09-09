"""Operator-run tool: record a code you already checked by hand in-game -
no browser automation, no candidate list to wait for. Unlike
tools/verify_codes.py, this works for a code state.json has never seen
before (e.g. one someone just told you), not only for existing
candidates.

Creates the code (source "manual" by default) if it isn't already in
state.json, applies the verification result the same way
tools/verify_codes.py does, and - for a working ("ok") code - posts it
to Telegram in the same run, same as watcher/manual_post.py, unless
--no-notify is passed.

Usage:
    python -m watcher.add_code <CODE> --reward "200 алмазов"
    python -m watcher.add_code <CODE> --result expired
    python -m watcher.add_code <CODE> --result invalid --no-notify
"""
import argparse

from dotenv import load_dotenv
load_dotenv()

from .app import format_post
from .config import STATE_PATH, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_MESSAGE_THREAD_ID
from .notifier import send_telegram
from .state import State, utcnow

RESULT_CHOICES = ("ok", "invalid", "used", "expired", "not_found")


def add_code(state, code, result, reward=None, source="manual", url=None, verified_at=None):
    """Ensure `code` exists in `state`, then merge in a manual verification
    result exactly like tools/verify_codes.py's apply_to_public_state()."""
    if result != "not_found" and code not in state.data["codes"] and code not in state.data["not_found"]:
        state.observe(code, source, url=url, status="reported")
    state.apply_manual_verification(code, result, reward, verified_at or utcnow())


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("code")
    parser.add_argument("--result", choices=RESULT_CHOICES, default="ok")
    parser.add_argument("--reward", default=None, help="Награда, как в игре (для --result ok)")
    parser.add_argument("--source", default="manual")
    parser.add_argument("--no-notify", action="store_true", help="Не постить в Telegram, даже если result=ok")
    args = parser.parse_args()

    code = args.code.strip()
    state = State(STATE_PATH)
    add_code(state, code, args.result, args.reward, args.source)
    state.save()

    item = state.data["codes"].get(code)
    if item is None:
        print(f"[OK] {code}: not_found — удалён/заблокирован в публичном state")
        return

    print(f"[OK] {code}: status={item['status']} confidence={item['confidence']} "
          f"manual_verification={item['manual_verification']}")

    if args.result == "ok" and not args.no_notify and not item.get("notified"):
        text = format_post(code, item)
        if send_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, text, TELEGRAM_MESSAGE_THREAD_ID):
            item["notified"] = True
            state.save()
            print(f"[OK] Posted {code} to Telegram")
        else:
            print("[SKIP] TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID не заданы — не отправлено")


if __name__ == "__main__":
    main()
