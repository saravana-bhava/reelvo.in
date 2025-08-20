# ================================================
# File:         seeders/seed_users.py
# Description:  Seed initial test users
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 20 August 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

import os
import sys

# Add project root to sys.path so 'models' can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import db, User
from werkzeug.security import generate_password_hash
from app import create_app

def create_admin(email, password):
    existing_user = User.query.filter_by(email=email).first()
    if not existing_user:
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            plan="Business",
            is_admin=True,
            email_verified=True
        )
        db.session.add(user)
        db.session.commit()
        print(f"✅ Admin user seeded: {email}")
    else:
        print(f"⚠️ Admin user already exists: {email}")

def run():
    app = create_app()
    with app.app_context():
        create_admin("developer@sazm.in", "D3v3l0p3r1!")
        create_admin("shivamkumr132@gmail.com", "ramjiramji1A@")

if __name__ == "__main__":
    run()
