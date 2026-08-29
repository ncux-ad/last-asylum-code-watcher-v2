import re
from bs4 import BeautifulSoup

# Conservative pattern: Last Asylum codes are normally compact uppercase/alphanumeric.
CODE_RE = re.compile(r"(?<![A-Za-z0-9])([A-Z][A-Z0-9]{5,15})(?![A-Za-z0-9])")

# Sites like lota.games recycle generic "lucky number" filler codes
# (LOVE666, VIP888, LAPJAP777...) across many unrelated games — these
# aren't Last Asylum specific, they're bait for the listing page.
GENERIC_LUCKY_SUFFIX_RE = re.compile(r"(\d)\1\1$")

# Pages like lota.games's game catalog embed UUIDs (e.g. game IDs);
# fragments of those look like codes but are pure hex digits/letters
# (0-9, A-F). Real codes seen so far always contain a non-hex letter
# (LA20WBZ9, LADCEX1223...), so an all-hex match is an ID, not a code.
HEX_ONLY_RE = re.compile(r"^[0-9A-F]+$")

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
        if code.isalpha():
            # Real codes always mix letters and digits (e.g. LA26ALLY,
            # LA25W8CM); a pure-letters match is prose, not a code.
            continue
        if GENERIC_LUCKY_SUFFIX_RE.search(code):
            continue
        if HEX_ONLY_RE.match(code):
            continue
        found.add(code)

    return found
