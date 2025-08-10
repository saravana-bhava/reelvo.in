# ================================================
# File:         models/auto_post_plan.py
# Description:  Model for auto post plan
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 31 July 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

from datetime import datetime, timedelta
from models import db

class AutoPostPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    auto_post_time = db.Column(db.Time, nullable=False)
    language = db.Column(db.String(50), default="en")
    subtitles_enabled = db.Column(db.Boolean, default=True)
    watermark_enabled = db.Column(db.Boolean, default=True)
    voice_artist = db.Column(db.String(100), default="Google UK English Male")
    status = db.Column(db.String(20), default="Active")  # Active / Paused / Completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def end_date(self):
        return self.start_date + timedelta(days=self.duration_days - 1)

    def days_remaining(self):
        today = datetime.utcnow().date()
        remaining = (self.end_date() - today).days
        return max(remaining, 0)
