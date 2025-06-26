# run_pipeline.py

import sys
from create_video import create_video_for_category

def run_pipeline(category: str, username: str = "demo"):
    print(f"\n⚙️ Starting pipeline for: {category.upper()} | User: {username}")
    try:
        result = create_video_for_category(category, username)
        if result:
            print(f"[✅] Reel generated → {result}")
        else:
            print(f"[❌] Video generation failed for {category}")
    except Exception as e:
        print(f"[❌] Pipeline failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) not in [2, 3]:
        print("Usage: python run_pipeline.py <category> [username]")
        print("Example: python run_pipeline.py motivation demo")
    else:
        category = sys.argv[1].lower()
        username = sys.argv[2] if len(sys.argv) == 3 else "demo"
        run_pipeline(category, username)
