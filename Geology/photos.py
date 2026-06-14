"""
photos.py — fetch a representative photo + short description for each rock type
from the Wikipedia REST API (free, no key required).
"""

import urllib.parse
import requests
import streamlit as st

WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/"

# Map our parsed rock-type keys to the best Wikipedia article title.
WIKI_TITLES = {
    "limestone": "Limestone",
    "sandstone": "Sandstone",
    "shale": "Shale",
    "dolostone": "Dolomite (rock)",
    "dolomite": "Dolomite (rock)",
    "chert": "Chert",
    "conglomerate": "Conglomerate (geology)",
    "mudstone": "Mudstone",
    "siltstone": "Siltstone",
    "coal": "Coal",
    "sedimentary": "Sedimentary rock",
    "sedimentary rocks": "Sedimentary rock",
}

# Wikipedia asks API clients to send a descriptive User-Agent.
HEADERS = {"User-Agent": "ChattanoogaGeologyDashboard/1.0 (Streamlit educational project)"}


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def wiki_summary(title):
    """Return {'image': url|None, 'extract': str, 'url': page_url} for a title, or None."""
    try:
        url = WIKI_SUMMARY + urllib.parse.quote(title.replace(" ", "_"))
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        d = r.json()
        img = (d.get("thumbnail") or {}).get("source") or (d.get("originalimage") or {}).get("source")
        return {
            "image": img,
            "extract": d.get("extract", "") or "",
            "url": (d.get("content_urls", {}).get("desktop", {}) or {}).get("page", ""),
        }
    except Exception:
        return None


def rock_info(rock_key, fallback_label=""):
    """Photo + blurb for a rock-type key (e.g. 'limestone'). Falls back gracefully."""
    title = WIKI_TITLES.get(str(rock_key).lower())
    if not title:
        title = (fallback_label or str(rock_key)).split("(")[0].strip() or "Rock"
    info = wiki_summary(title)
    if info is None:
        info = {"image": None, "extract": "", "url": ""}
    info["title"] = title
    return info
