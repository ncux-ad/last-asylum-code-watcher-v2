import requests
from .extractor import extract_codes

HEADERS = {
    "User-Agent": "LastAsylumCodeRadar/2.0 (+public-page-monitor)"
}

def fetch(url, timeout=20):
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.text

def scan_source(name, url):
    html = fetch(url)
    return name, extract_codes(html)
