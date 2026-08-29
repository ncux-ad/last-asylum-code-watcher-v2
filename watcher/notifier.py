import requests

def send_telegram(token, chat_id, text):
    if not token or not chat_id:
        return False

    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        },
        timeout=15,
    )
    r.raise_for_status()
    return True
