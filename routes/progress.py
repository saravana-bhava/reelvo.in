# File: routes/progress.py

from flask import Blueprint, jsonify
from utils.progress_tracker import progress_status

progress_bp = Blueprint("progress", __name__)

@progress_bp.route("/progress/<task_id>", methods=["GET"])
def get_progress(task_id):
    """
    Returns the current progress of a task.
    Called periodically from the frontend while generating a reel.
    """
    status = progress_status.get(task_id)

    if status:
        return jsonify({
            "status": status.get("status", "unknown"),
            "message": status.get("message", ""),
            "percent": status.get("percent", 0),
        })

    return jsonify({
        "status": "not_found",
        "message": "No progress available for this task."
    }), 404
