"""Operator-run tool to check candidate codes against the official
redemption site (https://gevents.globallap.com/gamecode/index.html?gameId=440).

Deliberately NOT part of the scheduled scraper and NOT automated end
to end: login (Google/Facebook OAuth or OTP), server/character
selection, and the actual redeem click are all done by a human in a
real, visible browser window. Scripting those would mean either
replaying a login flow unattended (a different, higher-risk trust
model than passively reading public pages, and against Google/
Facebook/the game's ToS) or blindly guessing selectors on an
authenticated screen this tool has never actually seen. Instead this
script just opens the page for convenience and walks the operator
through the list of unverified candidates, recording what they report
back.

Usage:
    pip install -r requirements-manual-verify.txt
    playwright install chromium
    python tools/verify_codes.py
"""
import json
from datetime import datetime, timezone
from pathlib import Path

REDEMPTION_URL = "https://gevents.globallap.com/gamecode/index.html?gameId=440"
STATE_PATH = Path("data/state.json")
VERIFICATIONS_PATH = Path("data/manual_verifications.json")
RESULT_CHOICES = ("ok", "invalid", "used", "expired", "skip")


def load_verifications():
    if not VERIFICATIONS_PATH.exists():
        return {}
    return json.loads(VERIFICATIONS_PATH.read_text(encoding="utf-8"))


def save_verification(code, result, reward):
    data = load_verifications()
    data[code] = {
        "result": result,
        "reward": reward,
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }
    VERIFICATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    VERIFICATIONS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return data


def load_candidates():
    if not STATE_PATH.exists():
        return []
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    already_verified = load_verifications()
    codes = [
        code
        for code, item in state.get("codes", {}).items()
        if code not in already_verified and item.get("status") in ("candidate", "probable", "confirmed")
    ]
    return sorted(codes)


def prompt_result(code, input_fn=input):
    print(f"\nКод: {code}")
    print("Введите его на странице в открытом браузере и нажмите Confirm.")
    while True:
        result = input_fn(f"Результат [{'/'.join(RESULT_CHOICES)}]: ").strip().lower()
        if result in RESULT_CHOICES:
            break
        print(f"Не понял, введите одно из: {', '.join(RESULT_CHOICES)}")
    reward = None
    if result == "ok":
        reward = input_fn("Награда (как показано на странице, можно пусто): ").strip() or None
    return result, reward


def main():
    from playwright.sync_api import sync_playwright  # optional dep, see requirements-manual-verify.txt

    codes = load_candidates()
    if not codes:
        print("Нет непроверенных кандидатов в data/state.json.")
        return

    print(f"К проверке: {len(codes)} код(ов).")
    print("Сейчас откроется браузер. Войдите (Facebook/Google/OTP),")
    print("выберите сервер и персонажа, затем вернитесь в терминал.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(REDEMPTION_URL)
        input("\nГотовы вводить коды? Нажмите Enter, когда вошли в аккаунт и выбрали сервер/персонажа...")

        for code in codes:
            result, reward = prompt_result(code)
            if result == "skip":
                continue
            save_verification(code, result, reward)
            print(f"Сохранено: {code} -> {result}" + (f" ({reward})" if reward else ""))

        browser.close()

    print(f"\nГотово. Результаты в {VERIFICATIONS_PATH}")


if __name__ == "__main__":
    main()
