# File: db/init_db.py

import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully.")
