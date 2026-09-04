"""Learning/research tool: opens the code-redemption site in a real,
visible browser (same URL as tools/verify_codes.py) and logs every
network request/response it makes to a local file — so you can see
what the JS front-end actually talks to under the hood (plain REST?
GraphQL? something else?) before deciding whether a lighter-weight
client (plain HTTP, no browser) could ever replace Playwright here.

Deliberately NOT automation: you drive the browser yourself — login
(OTP/bound email/OAuth), server/character selection, entering a code —
exactly like tools/verify_codes.py. This script only *watches*, it
never fills in a field or clicks anything. Nothing here is scheduled,
nothing feeds data/state.json, this is a one-off research session.

Sensitive-looking header/field names (containing "token", "auth",
"password", "otp", "secret", "session", "cookie" - case-insensitive)
are redacted before anything is written to disk. This is a best-effort
filter, not a guarantee: read the resulting log yourself before sharing
it with anyone, including pasting it into a chat.

Usage:
    pip install -r requirements-manual-verify.txt   # already has playwright
    playwright install chromium
    python tools/inspect_redemption_traffic.py

Log: data/redemption-traffic.jsonl (gitignored, overwritten each run).
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

REDEMPTION_URL = "https://gevents.globallap.com/gamecode/index.html?gameId=440"
OUT_PATH = Path("data/redemption-traffic.jsonl")

# Статика, которую не разбираем целиком — сам факт запроса всё равно
# попадёт в лог отдельной строкой, просто без тела ответа.
STATIC_EXTS = (".js", ".css", ".png", ".jpg", ".jpeg", ".svg", ".woff", ".woff2", ".ico", ".map", ".gif")

SENSITIVE_KEY_RE = re.compile(r"(token|auth|password|passwd|otp|secret|session|cookie)", re.IGNORECASE)

MAX_BODY_CHARS = 4000  # чтобы одна большая HTML/JSON-страница не разнесла лог


def redact(value):
    """Рекурсивно затирает значения полей, похожих по имени на секреты."""
    if isinstance(value, dict):
        return {
            k: ("[REDACTED]" if SENSITIVE_KEY_RE.search(k) else redact(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def redact_headers(headers):
    return {k: ("[REDACTED]" if SENSITIVE_KEY_RE.search(k) else v) for k, v in headers.items()}


def is_static(url):
    return url.split("?", 1)[0].lower().endswith(STATIC_EXTS)


def try_json(text):
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return None


def append_log(entry):
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main():
    from playwright.sync_api import sync_playwright  # optional dep, see requirements-manual-verify.txt

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if OUT_PATH.exists():
        OUT_PATH.unlink()  # свежий лог на каждый запуск, не копим старое

    def handle_request(request):
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": "request",
            "method": request.method,
            "url": request.url,
            "headers": redact_headers(request.headers),
        }
        if not is_static(request.url):
            body = request.post_data
            if body:
                parsed = try_json(body)
                if parsed is not None:
                    entry["body"] = redact(parsed)
                else:
                    entry["body"] = body[:MAX_BODY_CHARS]
        append_log(entry)

    def handle_response(response):
        if is_static(response.url):
            return
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": "response",
            "status": response.status,
            "url": response.url,
            "headers": redact_headers(response.headers),
        }
        ctype = response.headers.get("content-type", "")
        if "json" in ctype or "text" in ctype:
            try:
                text = response.text()
                parsed = try_json(text)
                entry["body"] = redact(parsed) if parsed is not None else text[:MAX_BODY_CHARS]
            except Exception as e:
                entry["body_error"] = str(e)
        append_log(entry)

    def wire_page(p):
        p.on("request", handle_request)
        p.on("response", handle_response)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        # OAuth-вход (Google/Facebook) иногда открывается в отдельном
        # окне — подписываемся и на новые страницы контекста тоже.
        context.on("page", wire_page)

        page = context.new_page()
        wire_page(page)
        page.goto(REDEMPTION_URL)

        print(f"Лог пишется в {OUT_PATH.resolve()}")
        print("Пройдите вход и введите код(ы) как обычно — скрипт только наблюдает,")
        print("ничего сам не нажимает и не заполняет.")
        input("\nНажмите Enter в этом терминале, когда закончите...\n")

        browser.close()

    n = sum(1 for _ in OUT_PATH.open(encoding="utf-8"))
    print(f"Готово: {n} записей в {OUT_PATH}.")
    print("Просмотрите файл сами перед тем, как кому-то показывать —")
    print("фильтр секретов best-effort, не гарантия.")


if __name__ == "__main__":
    main()
