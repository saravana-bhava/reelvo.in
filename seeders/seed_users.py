# File: seeders/seed_users.py

import os
import sys

# Add project root to sys.path so 'models' can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import db, User
from werkzeug.security import generate_password_hash
from app import create_app

def run():
    app = create_app()
    with app.app_context():
        admin_email = "developer@sazm.in"
        existing_user = User.query.filter_by(email=admin_email).first()
        if not existing_user:
            user = User(
                email=admin_email,
                password_hash=generate_password_hash("D3v3l0p3r1!"),
                plan="Business",
                is_admin=True,
                email_verified=True
            )
            db.session.add(user)
            db.session.commit()
            print("✅ Admin user seeded.")
        else:
            print("⚠️ Admin user already exists.")

        admin_email = "shivamkumr132@gmail.com"
        existing_user = User.query.filter_by(email=admin_email).first()
        if not existing_user:
            user = User(
                email=admin_email,
                password_hash=generate_password_hash("ramjiramji1A@"),
                plan="Business",
                is_admin=True,
                email_verified=True
            )
            db.session.add(user)
            db.session.commit()
            print("✅ Admin user seeded.")
        else:
            print("⚠️ Admin user already exists.")

if __name__ == "__main__":
    run()
