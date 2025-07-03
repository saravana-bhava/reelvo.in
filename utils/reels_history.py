# File: utils/reel_history.py

"""
Handles reading and writing reel history for users.
Stores script text and video filenames per user.
"""

import os
import json
from typing import Dict, List

HISTORY_FILE = "reel_history.json"
os.makedirs(os.path.dirname(HISTORY_FILE) or ".", exist_ok=True)


def load_reel_history() -> Dict[str, Dict[str, str]]:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_reel_history(history: Dict[str, Dict[str, str]]) -> None:
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def add_reel_to_history(user_name: str, filename: str, script: str) -> None:
    history = load_reel_history()
    if user_name not in history:
        history[user_name] = {}
    history[user_name][filename] = script.strip()
    save_reel_history(history)


def list_user_reels(user_name: str) -> List[str]:
    history = load_reel_history()
    return list(history.get(user_name, {}).keys())


def get_user_script(user_name: str, filename: str) -> str:
    history = load_reel_history()
    return history.get(user_name, {}).get(filename, "")
