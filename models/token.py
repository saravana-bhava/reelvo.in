# File: models/token.py

from models import db
from models.base import TimestampMixin

class UserToken(db.Model, TimestampMixin):
    __tablename__ = 'user_tokens'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    access_token = db.Column(db.String, nullable=False)
    refresh_token = db.Column(db.String)
    expires_at = db.Column(db.DateTime)
    platform = db.Column(db.String, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'platform', name='uq_user_id_platform'),
    )

    def __repr__(self):
        return f"<UserToken(user_id={self.user_id}, platform='{self.platform}')>"
