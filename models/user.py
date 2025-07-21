# File: models/user.py

from models.db import db
from models.base import TimestampMixin

class User(db.Model, TimestampMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    plan = db.Column(db.String(50))
    is_admin = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
