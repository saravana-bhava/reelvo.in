# ================================================
# File:         utils/instagram_db.py
# Description:  Store Instagram tokens, user info in DB
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 20 August 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

from datetime import datetime, timedelta
from models import db
from models.user import User
from models.token import UserToken
from models.reel import Reel
from models.story import Story


def get_instagram_credentials(user_email):
    """
    Retrieve Instagram token data for a given user's email.
    """
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return None

    token = UserToken.query.filter_by(user_id=user.id, platform='instagram').first()
    if not token:
        return None

    return {
        "access_token": token.access_token,
        "expires_at": token.expires_at,
        "platform_user_id": token.platform_user_id
    }


def update_instagram_tokens(user_id, access_token, refresh_token="", expires_in=5184000, platform_user_id=None):
    """
    Update or insert Instagram tokens for a user.
    """
    user = User.query.get(user_id)
    if not user:
        raise ValueError(f"User with ID {user_id} not found")

    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    token = UserToken.query.filter_by(user_id=user_id, platform='instagram').first()

    if token:
        token.access_token = access_token
        token.refresh_token = refresh_token
        token.expires_at = expires_at
        if platform_user_id:
            token.platform_user_id = platform_user_id
    else:
        token = UserToken(
            user_id=user_id,
            platform='instagram',
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            platform_user_id=platform_user_id
        )
        db.session.add(token)

    db.session.commit()


def delete_instagram_token(user_id):
    """
    Delete stored Instagram token for a given user.
    """
    token = UserToken.query.filter_by(user_id=user_id, platform='instagram').first()
    if token:
        db.session.delete(token)
        db.session.commit()


def log_post_to_db(reel_id, permalink):
    """
    Mark a Reel as posted and log the Instagram permalink.
    """
    reel = Reel.query.get(reel_id)
    if not reel:
        raise ValueError(f"Reel with ID {reel_id} not found")

    reel.status = 'posted'
    reel.posted_at = datetime.utcnow()
    reel.error_log = f"Posted to IG: {permalink}"

    db.session.commit()


def log_story_to_db(story_id, permalink):
    """
    Mark a Story as posted and log the Instagram permalink.
    """
    story = Story.query.get(story_id)
    if not story:
        raise ValueError(f"Story with ID {story_id} not found")

    story.status = 'posted'
    story.posted_at = datetime.utcnow()
    story.error_log = f"Posted to IG: {permalink}"
    story.permalink = permalink   # 👈 optional if you store it

    db.session.commit()
