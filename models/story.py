# ================================================
# File:         models/story.py
# Description:  Story model storing manual story upload data
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 20 August 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

from models import db
from models.base import TimestampMixin

class Story(db.Model, TimestampMixin):
    __tablename__ = 'stories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 🔑 Relationship
    user = db.relationship("User", backref="stories", lazy="joined")

    caption = db.Column(db.Text)  # stories may or may not have text
    video_path = db.Column(db.Text, nullable=False)  # must be ≤15s video
    thumbnail_path = db.Column(db.Text)

    lang = db.Column(db.String(10), default='en', nullable=False)

    is_scheduled = db.Column(db.Boolean, default=False, nullable=False)
    scheduled_at = db.Column(db.DateTime)
    posted_at = db.Column(db.DateTime)

    platform = db.Column(db.String(20), default='instagram', nullable=False)
    status = db.Column(db.String(20), default='draft', nullable=False)
    # Values: draft / scheduled / posted / failed

    error_log = db.Column(db.Text)

    __table_args__ = (
        db.CheckConstraint("status IN ('draft', 'scheduled', 'posted', 'failed')"),
        db.Index('idx_stories_user', 'user_id'),
        db.Index('idx_stories_schedule', 'is_scheduled', 'scheduled_at'),
        db.Index('idx_stories_status', 'status'),
    )

    def __repr__(self):
        return f"<Story(id={self.id}, status='{self.status}')>"
