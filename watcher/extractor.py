import re
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

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

# Best-effort reward guess: a number next to a known in-game resource
# name on the same line as the code (e.g. "LA26ALLY - 500 Gold").
REWARD_RE = re.compile(
    r"\b[x×]?\s*(\d[\d,]*)\s*[x×]?\s*"
    r"(gold|gems?|diamonds?|coins?|cash|chips?|xp|exp|energy|stamina|"
    r"tickets?|keys?|crystals?|tokens?|crowns?|food|wood|stone|iron|"
    r"metal|speedups?|resources?)\b",
    re.I,
)

# Best-effort expiry guess: a date near an "expires"/"valid until" style
# keyword on the same line as the code.
_MONTHS = (
    r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|"
    r"nov(?:ember)?|dec(?:ember)?"
)
_DATE_TOKEN = (
    r"(\d{4}-\d{1,2}-\d{1,2}"
    r"|\d{1,2}/\d{1,2}/\d{2,4}"
    r"|(?:" + _MONTHS + r")\.?\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s*\d{4})?"
    r"|\d{1,2}\s+(?:" + _MONTHS + r")\.?(?:,?\s*\d{4})?)"
)
EXPIRY_HINT_RE = re.compile(
    r"\b(?:expires?|expiration|valid\s+(?:until|through|till)|ends?)\b[:\s-]*" + _DATE_TOKEN,
    re.I,
)


def _parse_expiry(raw, today):
    cleaned = raw.strip().rstrip(".,")
    has_year = bool(re.search(r"\d{4}", cleaned))
    try:
        parsed = date_parser.parse(cleaned, fuzzy=False, default=datetime(today.year, 1, 1))
    except (ValueError, OverflowError):
        return None

    result = parsed.date()
    if not has_year and (today - result).days > 180:
        # A no-year date ("expires Jan 5") that's already >6 months in the
        # past almost certainly refers to next year, not this one.
        result = result.replace(year=result.year + 1)
    return result


def extract_candidates(html: str, today=None) -> list[dict]:
    if today is None:
        today = datetime.now(timezone.utc).date()

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    lines = soup.get_text("\n", strip=True).split("\n")
    found = {}
    for i, raw_line in enumerate(lines):
        upper_line = raw_line.upper()
        for code in CODE_RE.findall(upper_line):
            if code in found:
                continue
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

            # Reward/expiry text sometimes sits on the same line as the
            # code, sometimes on the line right after it (a table row
            # like "CODE | 100 Diamonds" flattens to two text lines) —
            # check both.
            context = raw_line
            if i + 1 < len(lines):
                context += "\n" + lines[i + 1]

            reward = None
            rm = REWARD_RE.search(context)
            if rm:
                reward = f"{rm.group(1)} {rm.group(2)}".strip()

            expires_at = None
            expired = None
            em = EXPIRY_HINT_RE.search(context)
            if em:
                parsed = _parse_expiry(em.group(1), today)
                if parsed:
                    expires_at = parsed.isoformat()
                    expired = parsed < today

            found[code] = {
                "code": code,
                "reward": reward,
                "expires_at": expires_at,
                "expired": expired,
            }

    return list(found.values())


def extract_codes(html: str) -> set[str]:
    return {c["code"] for c in extract_candidates(html)}
