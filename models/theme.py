# File: models/theme.py

from models import db

class Theme(db.Model):
    __tablename__ = 'themes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    lang = db.Column(db.String(10), nullable=False)
    content = db.Column(db.Text, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('name', 'lang', name='uq_theme_name_lang'),
        db.Index('idx_themes_name_lang', 'name', 'lang'),
    )

    def __repr__(self):
        return f"<Theme(id={self.id}, name='{self.name}', lang='{self.lang}')>"
