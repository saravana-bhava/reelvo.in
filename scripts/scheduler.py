from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from reelvoapp import db
from models.auto_post_plan import AutoPostPlan

def auto_post_reels():
    now = datetime.utcnow()
    plans = AutoPostPlan.query.filter_by(status="Active").all()

    for plan in plans:
        if plan.days_remaining() > 0 and plan.auto_post_time.hour == now.hour and plan.auto_post_time.minute == now.minute:
            print(f"Auto-posting reel for user {plan.user_id} on topic {plan.topic}")
            # TODO: Call your reel posting logic here

def start_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=auto_post_reels, trigger="interval", minutes=1)
    scheduler.start()
    print("Auto-Posting Scheduler started!")
