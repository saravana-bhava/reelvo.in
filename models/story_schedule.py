# ================================================
# File:         models/story_schedule.py
# Description:  Model storing scheduled story jobs
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 20 August 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

from models import db
from models.base import TimestampMixin

class StorySchedule(db.Model, TimestampMixin):
    __tablename__ = 'story_schedules'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=False)

    scheduled_for = db.Column(db.DateTime, nullable=True)
    timezone = db.Column(db.String(50), default='Asia/Kolkata', nullable=False)

    retry_count = db.Column(db.Integer, default=0, nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # Values: pending/processing/posted/failed
    error_log = db.Column(db.Text)

    __table_args__ = (
        db.CheckConstraint("status IN ('pending', 'processing', 'posted', 'failed')"),
        db.Index('idx_story_schedule_time', 'scheduled_for'),
        db.Index('idx_story_schedule_status', 'status'),
        db.Index('idx_story_schedule_user', 'user_id'),
    )

    def __repr__(self):
        return f"<StorySchedule(id={self.id}, status='{self.status}')>"
