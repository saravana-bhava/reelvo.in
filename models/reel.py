# File: models/reel.py

from models.db import db
from models.base import TimestampMixin

class Reel(db.Model, TimestampMixin):
    __tablename__ = 'reels'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    title = db.Column(db.Text)
    script = db.Column(db.Text, nullable=False)
    caption = db.Column(db.Text, nullable=False)

    video_path = db.Column(db.Text, nullable=False)
    audio_path = db.Column(db.Text)
    thumbnail_path = db.Column(db.Text)

    theme_name = db.Column(db.String(100))
    lang = db.Column(db.String(10), default='en', nullable=False)

    is_scheduled = db.Column(db.Boolean, default=False, nullable=False)
    scheduled_at = db.Column(db.DateTime)
    posted_at = db.Column(db.DateTime)

    platform = db.Column(db.String(20), default='instagram', nullable=False)
    status = db.Column(db.String(20), default='draft', nullable=False)  # Values: draft/scheduled/posted/failed

    error_log = db.Column(db.Text)

    __table_args__ = (
        db.CheckConstraint("status IN ('draft', 'scheduled', 'posted', 'failed')"),
        db.Index('idx_reels_user', 'user_id'),
        db.Index('idx_reels_schedule', 'is_scheduled', 'scheduled_at'),
        db.Index('idx_reels_status', 'status'),
    )

    def __repr__(self):
        return f"<Reel(id={self.id}, status='{self.status}')>"
