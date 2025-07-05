# File: utils/used_urls.py

"""
Tracks used video clip URLs per generation session to avoid duplicates.
Used in Pexels/Pixabay clip fetchers.
"""

import os
import json
from typing import Set

# Use consistent absolute path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USED_URLS_FILE = os.path.join(BASE_DIR, "used_urls.json")


def load_used_urls() -> Set[str]:
    """
    Load used video URLs from JSON file.

    Returns:
        Set[str]: Set of previously used URLs.
    """
    if os.path.exists(USED_URLS_FILE):
        try:
            with open(USED_URLS_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except (json.JSONDecodeError, TypeError):
            # Fallback to empty if file is corrupted
            return set()
    return set()


def save_used_urls(urls: Set[str]) -> None:
    """
    Save updated set of used video URLs to JSON file.

    Args:
        urls (Set[str]): Updated set of used URLs.
    """
    with open(USED_URLS_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(urls), f, indent=2)


def add_url(url: str) -> None:
    """
    Add a new URL to the used list and persist it.

    Args:
        url (str): Newly used video URL.
    """
    urls = load_used_urls()
    urls.add(url)
    save_used_urls(urls)
