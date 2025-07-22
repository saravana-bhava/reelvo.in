# File: models/progress.py

from models.db import db
from datetime import datetime


class ProgressTask(db.Model):
    __tablename__ = 'progress_tasks'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(128), unique=True, nullable=False)

    status = db.Column(db.Text, nullable=False, default="Starting...")
    percent = db.Column(db.Integer, nullable=False, default=0)

    start_time = db.Column(
        db.Float, nullable=False,
        default=lambda: datetime.utcnow().timestamp()
    )
    elapsed = db.Column(db.Integer, nullable=False, default=0)

    download_url = db.Column(db.Text, nullable=True, default="")

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False,
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return (
            f"<ProgressTask task_id={self.task_id} "
            f"percent={self.percent} status={self.status}>"
        )
