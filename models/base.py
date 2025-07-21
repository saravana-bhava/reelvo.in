# File: models/base.py

from datetime import datetime
from models.db import db

class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to a model."""
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
