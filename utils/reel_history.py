# File: utils/reel_history.py

"""
Handles reading and writing reel history for users.
Stores script text and video filenames per user.
"""

import os
import json
from typing import Dict, List, Optional

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "..", "db")
HISTORY_FILE = os.path.join(DB_DIR, "reel_history.json")
os.makedirs(DB_DIR, exist_ok=True)


def load_reel_history() -> Dict[str, Dict[str, str]]:
    """
    Load the entire reel history JSON from disk.

    Returns:
        Dict[str, Dict[str, str]]: Mapping of user_name → {filename: script}
    """
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass  # Corrupt or empty file
    return {}


def save_reel_history(history: Dict[str, Dict[str, str]]) -> None:
    """
    Save the reel history JSON to disk.

    Args:
        history: Updated history dictionary.
    """
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def add_reel_to_history(user_name: str, filename: str, script: str) -> None:
    """
    Add a new reel record to the user's history.

    Args:
        user_name: Unique username.
        filename: Reel video filename.
        script: Script text for the reel.
    """
    history = load_reel_history()
    user_name = user_name.strip()
    filename = filename.strip()

    if user_name not in history:
        history[user_name] = {}

    history[user_name][filename] = script.strip()
    save_reel_history(history)


def list_user_reels(user_name: str) -> List[str]:
    """
    List all reel filenames created by a specific user.

    Args:
        user_name: The user whose reels to list.

    Returns:
        List[str]: List of filenames (e.g., "output_01.mp4")
    """
    history = load_reel_history()
    return list(history.get(user_name.strip(), {}).keys())


def get_user_script(user_name: str, filename: str) -> Optional[str]:
    """
    Retrieve the script text used for a specific reel.

    Args:
        user_name: The user who owns the reel.
        filename: The reel's filename.

    Returns:
        Optional[str]: The associated script, or None if not found.
    """
    history = load_reel_history()
    return history.get(user_name.strip(), {}).get(filename.strip())
