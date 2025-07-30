# ================================================
# File:         seeders/seed_plans.py
# Description:  No description provided.
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 31 July 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

import os
import sys

# Add the project root to sys.path to enable imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import db, Plan
from app import create_app

def seed_plans():
    app = create_app()
    with app.app_context():
        if Plan.query.count() > 0:
            print("⚠️ Plans already seeded. Skipping.")
            return

        plans = [
            Plan(name="Free", price=0.0, weekly_ad_limit=3, number_of_ads=10),
            Plan(name="Starter", price=99.0, weekly_ad_limit=10, number_of_ads=100),
            Plan(name="Basic", price=199.0, weekly_ad_limit=20, number_of_ads=100),
            Plan(name="Pro", price=499.0, weekly_ad_limit=50, number_of_ads=100),
            Plan(name="Business", price=999.0, weekly_ad_limit=100, number_of_ads=100),
        ]

        db.session.bulk_save_objects(plans)
        db.session.commit()
        print("✅ Plans seeded successfully.")

if __name__ == "__main__":
    seed_plans()
