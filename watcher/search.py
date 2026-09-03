import urllib.parse
import requests
from bs4 import BeautifulSoup
from .extractor import extract_candidates

HEADERS = {
    "User-Agent": "LastAsylumCodeRadarBot/2.1 (+https://github.com/ncux-ad/last-asylum-code-watcher-v2; low-frequency hobby code tracker, runs every few hours)"
}

def google_news_rss(query):
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({
        "q": query,
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en",
    })
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "xml")
    return [x.find("link").text for x in soup.find_all("item") if x.find("link")]

def scan_search(query):
    merged = {}
    for url in google_news_rss(query)[:15]:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if not r.ok:
                continue
            for candidate in extract_candidates(r.text):
                existing = merged.get(candidate["code"])
                if existing is None:
                    merged[candidate["code"]] = candidate
                    continue
                if not existing.get("reward") and candidate.get("reward"):
                    existing["reward"] = candidate["reward"]
                if not existing.get("expires_at") and candidate.get("expires_at"):
                    existing["expires_at"] = candidate["expires_at"]
                    existing["expired"] = candidate["expired"]
        except requests.RequestException:
            pass
    return list(merged.values())
