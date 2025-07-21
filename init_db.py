# File: init_db.py

from app import create_app  # your Flask app factory
from models.db import db

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully.")
