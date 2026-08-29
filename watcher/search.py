import urllib.parse
import requests
from bs4 import BeautifulSoup
from .extractor import extract_codes

HEADERS = {"User-Agent": "LastAsylumCodeRadar/2.0"}

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
    codes = set()
    for url in google_news_rss(query)[:15]:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.ok:
                codes |= extract_codes(r.text)
        except requests.RequestException:
            pass
    return codes
