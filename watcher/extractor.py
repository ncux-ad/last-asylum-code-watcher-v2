import re
from bs4 import BeautifulSoup

# Conservative pattern: Last Asylum codes are normally compact uppercase/alphanumeric.
CODE_RE = re.compile(r"(?<![A-Za-z0-9])([A-Z][A-Z0-9]{5,15})(?![A-Za-z0-9])")

STOPWORDS = {
    "LASTASYLUM", "PLAGUE", "ANDROID", "GOOGLEPLAY", "APPSTORE",
    "POCKETGAMER", "GIFT", "CODES", "CODE", "ACTIVE", "EXPIRED",
    "REDEEM", "REWARDS", "SETTINGS", "CONFIRM", "DISCORD",
    "FACEBOOK", "YOUTUBE", "INSTAGRAM", "TELEGRAM", "DOWNLOAD",
}

def extract_codes(html: str) -> set[str]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    text = soup.get_text(" ", strip=True).upper()
    found = set()

    for code in CODE_RE.findall(text):
        if code in STOPWORDS:
            continue
        if code.isalpha() and len(code) < 7:
            continue
        found.add(code)

    return found
