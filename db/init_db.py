# ================================================
# File:         db/init_db.py
# Description:  Creates initial database schema and tables
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 31 July 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

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
