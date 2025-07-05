# File: utils/reel_history.py

"""
Handles reading and writing reel history for users.
Stores script text, caption, permalink, and timestamp per user and reel.
"""

import os
import json
from typing import Dict, List, Optional

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "..", "db")
HISTORY_FILE = os.path.join(DB_DIR, "reel_history.json")
os.makedirs(DB_DIR, exist_ok=True)


def load_reel_history() -> Dict[str, Dict[str, Dict[str, str]]]:
    """
    Load the entire reel history JSON from disk.

    Returns:
        Dict[str, Dict[str, Dict[str, str]]]: Mapping of user_email → {filename: {script, caption, permalink, timestamp}}
    """
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass  # Corrupt or empty file
    return {}


def save_reel_history(history: Dict[str, Dict[str, Dict[str, str]]]) -> None:
    """
    Save the reel history JSON to disk.

    Args:
        history: Updated history dictionary.
    """
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def add_reel_to_history(
    user_email: str,
    filename: str,
    script: str,
    caption: Optional[str] = None,
    permalink: Optional[str] = None,
    timestamp: Optional[str] = None
) -> None:
    """
    Add a new reel record to the user's history.

    Args:
        user_email: Unique username.
        filename: Reel video filename.
        script: Script text for the reel.
        caption: Instagram caption.
        permalink: Instagram permalink.
        timestamp: ISO timestamp string.
    """
    history = load_reel_history()
    user_email = user_email.strip()
    filename = filename.strip()

    if user_email not in history:
        history[user_email] = {}

    history[user_email][filename] = {
        "script": script.strip(),
        "caption": caption or "",
        "permalink": permalink or "",
        "timestamp": timestamp or ""
    }

    save_reel_history(history)


def list_user_reels(user_email: str) -> List[str]:
    """
    List all reel filenames created by a specific user.

    Args:
        user_email: The user whose reels to list.

    Returns:
        List[str]: List of filenames (e.g., "output_01.mp4")
    """
    history = load_reel_history()
    return list(history.get(user_email.strip(), {}).keys())


def get_user_script(user_email: str, filename: str) -> Optional[str]:
    """
    Retrieve the script text used for a specific reel.

    Args:
        user_email: The user who owns the reel.
        filename: The reel's filename.

    Returns:
        Optional[str]: The associated script, or None if not found.
    """
    history = load_reel_history()
    record = history.get(user_email.strip(), {}).get(filename.strip())
    if record:
        return record.get("script")
    return None


def get_user_reel_data(user_email: str, filename: str) -> Optional[Dict[str, str]]:
    """
    Retrieve full reel metadata for a specific reel.

    Args:
        user_email: The user who owns the reel.
        filename: The reel's filename.

    Returns:
        Optional[Dict[str, str]]: Dict with script, caption, permalink, timestamp.
    """
    history = load_reel_history()
    return history.get(user_email.strip(), {}).get(filename.strip())
