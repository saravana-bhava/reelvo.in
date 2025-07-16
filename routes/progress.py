# File: routes/progress.py

from flask import Blueprint, jsonify, current_app
from utils.progress_tracker import progress_status

progress_bp = Blueprint("progress", __name__)

@progress_bp.route("/progress/<task_id>", methods=["GET"])
def get_progress(task_id):
    """
    API Endpoint to check progress of a given task_id.
    Typically called from the frontend while a reel is being generated.
    """
    status = progress_status.get(task_id)

    if status:
        current_app.logger.debug(f"[Progress] task_id={task_id} → {status}")
        return jsonify({
            "status": status.get("status", "unknown"),
            "message": status.get("message", ""),
            "percent": status.get("percent", 0),
            "download_url": status.get("download_url", "")
        })

    current_app.logger.warning(f"[Progress] No status found for task_id={task_id}")
    return jsonify({
        "status": "not_found",
        "message": "No progress available for this task."
    }), 404
