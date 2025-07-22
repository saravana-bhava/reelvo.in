# File: routes/reels.py

import os
import uuid
import traceback
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from utils.reel_job import process_reel_job
from utils.auth_decorator import login_required
from utils.auth_utils import get_user_id, get_user_email
from models import db, Reel, Theme, User
from dotenv import load_dotenv

load_dotenv()

reels_bp = Blueprint("reels", __name__)
ALLOWED_EXTENSIONS = {"mp4", "mov", "avi", "mkv"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@reels_bp.route("/reels", methods=["GET", "POST"])
@login_required
def create_reel():
    user_id = get_user_id()
    error = None
    success = None

    if request.method == "POST":
        topic = request.form.get("topic", "").strip()
        voice = request.form.get("tts_voice", "")
        theme = request.form.get("theme", "")
        uploaded_file = request.files.get("video")

        if not topic:
            error = "Please enter a topic."
        elif uploaded_file and not allowed_file(uploaded_file.filename):
            error = "Invalid file type. Only mp4, mov, avi, mkv are allowed."
        else:
            try:
                uploaded_path = None
                if uploaded_file and uploaded_file.filename:
                    filename = secure_filename(uploaded_file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    upload_folder = os.path.join("input", "clips")
                    os.makedirs(upload_folder, exist_ok=True)
                    uploaded_path = os.path.join(upload_folder, unique_filename)
                    uploaded_file.save(uploaded_path)

                job_id = uuid.uuid4().hex
                process_reel_job(
                    task_id=job_id,
                    topic=topic,
                    voice=voice,
                    theme=theme,
                    user_id=user_id,
                    uploaded_path=uploaded_path
                )

                return redirect(url_for("reels.reel_status", job_id=job_id))

            except Exception as e:
                error = f"An error occurred: {str(e)}"
                traceback.print_exc()

    themes = db.session.query(Theme.name).distinct().order_by(Theme.name.asc()).all()
    theme_names = [t.name for t in themes]

    return render_template(
        "create_reel.html",
        error=error,
        success=success,
        themes=theme_names,
        form=request.form
    )


@reels_bp.route("/reels/status/<job_id>")
@login_required
def reel_status(job_id):
    return render_template("reel_status.html", job_id=job_id)


@reels_bp.route("/reels/delete/<filename>", methods=["POST"])
@login_required
def delete_reel(filename):
    user_id = get_user_id()
    reel = db.session.query(Reel).filter_by(user_id=user_id, filename=filename).first()
    if reel:
        db.session.delete(reel)
        db.session.commit()

    output_path = os.path.join("output", "reels", filename)
    if os.path.exists(output_path):
        os.remove(output_path)

    return redirect(url_for("reels.create_reel"))


@reels_bp.route('/reels/list')
@login_required
def list_reels():
    user_email = get_user_email()
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return redirect(url_for('auth.login'))

    reels = Reel.query.filter_by(user_id=user.id).order_by(Reel.created_at.desc()).all()

    return render_template(
        'reels.html',
        user=user.email,
        videos=[r.video_path for r in reels],
        vid_date_map={r.video_path: r.created_at.strftime('%Y-%m-%d %H:%M') for r in reels},
        scripts={r.video_path: r.script for r in reels}
    )


@reels_bp.route('/reels/<user_email>/<path:filename>')
@login_required
def serve_video(user_email, filename):
    video_dir = os.path.join('static', 'reels', user_email)
    return send_from_directory(video_dir, filename)


@reels_bp.route("/reels/progress/<job_id>")
@login_required
def reel_progress(job_id):
    from utils.progress_tracker import get_progress
    return jsonify(get_progress(job_id))
