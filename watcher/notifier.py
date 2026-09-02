import requests

def send_telegram(token, chat_id, text, message_thread_id=None):
    if not token or not chat_id:
        return False

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if message_thread_id:
        payload["message_thread_id"] = message_thread_id

    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json=payload,
        timeout=15,
    )
    r.raise_for_status()
    return True
