import requests
from .extractor import extract_candidates

HEADERS = {
    "User-Agent": "LastAsylumCodeRadarBot/2.1 (+https://github.com/ncux-ad/last-asylum-code-watcher-v2; low-frequency hobby code tracker, runs every few hours)"
}

def fetch(url, timeout=20):
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.text

def scan_source(name, url):
    html = fetch(url)
    return name, extract_candidates(html)
