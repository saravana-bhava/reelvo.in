# File: models/plan.py

from models import db
from models.base import TimestampMixin

class Plan(db.Model, TimestampMixin):
    __tablename__ = 'plans'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    weekly_ad_limit = db.Column(db.Integer, default=5, nullable=False)
    number_of_ads = db.Column(db.Integer, default=10, nullable=False)

    def __repr__(self):
        return f"<Plan(id={self.id}, name='{self.name}')>"
