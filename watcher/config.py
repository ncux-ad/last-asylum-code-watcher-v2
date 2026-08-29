import os

SOURCES = [
    ("pocketgamer", "https://www.pocketgamer.com/last-asylum-plague/codes/"),
    ("app-time", "https://app-time.ru/games/last-asylum-plague/codes"),
    ("lastasylumplague", "https://lastasylumplague.com/guides/active-gift-codes-and-how-to-redeem-ios-android/"),
    ("lastasylum", "https://lastasylum.com/gift-codes"),
    ("last-asylum-fun", "https://www.last-asylum.fun/"),
    ("lota", "https://lota.games/en/game/019f735d-8adc-751f-8073-3930143815c9/giftcodes"),
]

SEARCH_QUERIES = [
    '"Last Asylum: Plague" "gift code"',
    '"Last Asylum Plague" "redeem code"',
    '"Last Asylum" "new code"',
    '"LA1OW9F7X"',
]

STATE_PATH = os.getenv("STATE_PATH", "data/state.json")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
