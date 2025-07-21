# File: models/token.py

from models.db import db
from models.base import TimestampMixin

class UserToken(db.Model, TimestampMixin):
    __tablename__ = 'user_tokens'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String, nullable=False)
    access_token = db.Column(db.String, nullable=False)
    refresh_token = db.Column(db.String)
    expires_at = db.Column(db.DateTime)
    platform = db.Column(db.String, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('email', 'platform', name='uq_email_platform'),
    )

    def __repr__(self):
        return f"<UserToken(email='{self.email}', platform='{self.platform}')>"
