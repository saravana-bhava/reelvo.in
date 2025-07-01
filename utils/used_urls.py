# File: utils/used_urls.py

"""
Tracks used video clip URLs per generation session to avoid duplicates.
Used in Pexels/Pixabay clip fetchers.
"""

import os
import json
from typing import Set

USED_URLS_FILE = "used_urls.json"


def load_used_urls() -> Set[str]:
    if os.path.exists(USED_URLS_FILE):
        with open(USED_URLS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_used_urls(urls: Set[str]) -> None:
    with open(USED_URLS_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(urls), f, indent=2)


def add_url(url: str) -> None:
    urls = load_used_urls()
    urls.add(url)
    save_used_urls(urls)
