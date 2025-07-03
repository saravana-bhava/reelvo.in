# File: post_reel_real.py

import os
from dotenv import load_dotenv
from utils.insta_direct import post_to_instagram_direct

# Load environment variables from .env file
load_dotenv()

# Read values from .env
access_token = os.getenv("FB_PAGE_ACCESS_TOKEN")
ig_account_id = os.getenv("INSTAGRAM_BUSINESS_ID")

# Safety check
if not access_token or not ig_account_id:
    raise ValueError("FB_PAGE_ACCESS_TOKEN or IG_ACCOUNT_ID is missing in your .env file.")

# Reel info
video_path = "output/demo/videos/sell_moringa_protein_powder_en_video.mp4"
caption = "Unlock the power of nature with moringa protein powder—nature’s superfuel for your body and soul! Packed with pure plant energy, it boosts strength, sharpens focus, and fuels your day the clean, green way. No artificial junk—just pure, earth-grown goodness. Whether you're crushing workouts or chasing dreams, moringa gives you the edge. It's not just protein—it's a revolution. Rise stronger. Live brighter. Fuel with moringa today!"
username = "demo"
task_id = "reel-post-moringa"

# Trigger the post
result = post_to_instagram_direct(
    video_path=video_path,
    caption=caption,
    ig_account_id=ig_account_id,
    access_token=access_token,
    username=username,
    video_url=None,
    task_id=task_id
)

print("==== POST RESULT ====")
print(result)
