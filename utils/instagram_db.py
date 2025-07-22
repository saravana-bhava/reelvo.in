# File: utils/instagram_db.py

from datetime import datetime, timedelta
from models import db
from models.user import User
from models.token import UserToken
from models.reel import Reel


def get_instagram_credentials(user_email):
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return None

    token = UserToken.query.filter_by(email=user_email, platform='instagram').first()
    if not token:
        return None

    return {
        "access_token": token.access_token,
        "expires_at": token.expires_at,
        "ig_user_id": token.ig_user_id
    }


def update_instagram_tokens(user_email, access_token, ig_user_id, refresh_token="", expires_in=5184000):
    user = User.query.filter_by(email=user_email).first()
    if not user:
        raise ValueError(f"User with email {user_email} not found")

    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    token = UserToken.query.filter_by(email=user_email, platform='instagram').first()

    if token:
        token.access_token = access_token
        token.refresh_token = refresh_token
        token.expires_at = expires_at
        token.ig_user_id = ig_user_id
    else:
        token = UserToken(
            email=user_email,
            platform='instagram',
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            ig_user_id=ig_user_id
        )
        db.session.add(token)

    db.session.commit()


def delete_instagram_token(user_email):
    token = UserToken.query.filter_by(email=user_email, platform='instagram').first()
    if token:
        db.session.delete(token)
        db.session.commit()


def log_post_to_db(user_email, video_path, caption, platform, permalink):
    user = User.query.filter_by(email=user_email).first()
    if not user:
        raise ValueError(f"User with email {user_email} not found")

    reel = Reel(
        user_id=user.id,
        video_path=video_path,
        caption=caption,
        platform=platform,
        status='posted',
        posted_at=datetime.utcnow(),
        script='',
        theme_name='',
        lang='en',
        error_log=f"Posted to IG: {permalink}"
    )

    db.session.add(reel)
    db.session.commit()
