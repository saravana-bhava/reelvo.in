# File: instagram_token_refresher.py

import time
import logging
import requests
from db.conn import get_db_conn

logger = logging.getLogger("instagram_refresher")
logging.basicConfig(level=logging.INFO)

def refresh_instagram_tokens():
    """Refreshes Instagram long-lived tokens once every 24 hours for all users."""
    logger.info("🔄 Starting Instagram token refresher loop...")

    while True:
        try:
            conn = get_db_conn()
            cursor = conn.cursor()

            cursor.execute("SELECT user_email, access_token FROM instagram_tokens")
            users = cursor.fetchall()

            for row in users:
                user_email = row["user_email"]
                token = row["access_token"]

                if not token:
                    logger.warning(f"[⚠️] No token for user: {user_email}")
                    continue

                refresh_url = (
                    "https://graph.instagram.com/refresh_access_token"
                    f"?grant_type=ig_refresh_token&access_token={token}"
                )

                logger.info(f"[🔁] Refreshing token for {user_email}...")
                try:
                    response = requests.get(refresh_url, timeout=15)
                    response.raise_for_status()
                    data = response.json()

                    new_token = data.get("access_token", token)
                    expires_in = data.get("expires_in")

                    cursor.execute("""
                        UPDATE instagram_tokens
                        SET access_token = ?, expires_in = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_email = ?
                    """, (new_token, expires_in, user_email))
                    conn.commit()

                    logger.info(f"[✅] Token refreshed for {user_email} (expires in {expires_in}s)")
                except Exception as e:
                    logger.warning(f"[❌] Error refreshing token for {user_email}: {e}")

        except Exception as e:
            logger.error(f"[‼️] Database error: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

        logger.info("⏳ Sleeping for 24 hours...")
        time.sleep(24 * 3600)
