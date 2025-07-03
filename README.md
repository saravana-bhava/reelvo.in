# 🎬 AI Instagram Reels Automation Platform (MVP)

A streamlined AI-powered platform that helps creators **automatically generate Instagram Reels**.  
Users choose a niche, AI writes a script, TTS converts it to voice, FFmpeg builds a vertical video, and the output is uploaded to Google Drive — optionally auto-posted to Instagram.

---

## 🚀 FEATURES

- 🔐 Simple login interface (no signup required)
- 🎯 Niche selection: *Motivation*, *Sad*, *Inspiration*, *Success*, *Life*
- 🧠 Script generation using OpenAI GPT (with fallback support)
- 🗣️ Text-to-Speech via **ElevenLabs**, **Google TTS**, or **gTTS**
- 🎞️ Video generation using **FFmpeg** (with optional VEED fallback)
- 🎬 Subtitles (auto-generated from TTS and overlaid via SRT)
- 💾 Videos saved to `/output/<user_name>/`
- ☁️ Upload to Google Drive (public sharable link)
- 📲 Auto-post to Instagram Reels (Graph API integration)
- ⏱️ Scheduler-ready (via cron or BullMQ-compatible)
- 🛣️ Subpath-ready: served under `/reelvo.ai` via `DispatcherMiddleware`

---

## 🛠 TECH STACK

**Backend:** Python + Flask  
**Video Engine:** FFmpeg + Pexels / Pixabay stock clips  
**TTS:** ElevenLabs / Google Cloud TTS / gTTS  
**AI Scripts:** OpenAI GPT  
**Storage:** Local + Google Drive  
**Frontend:** Plain HTML + CSS (Bootstrap-inspired)  
**Deployment:** Render / Railway / Docker-ready

---

## 📁 FOLDER STRUCTURE

```
.
├── app.py                 # Flask app, mounted at /reelvo.ai
├── install.sh             # FFmpeg installer script
├── start.sh               # Run with Flask/Gunicorn
├── requirements.txt       # Dependencies list
├── render.yaml            # Render deployment config
├── templates/             # HTML templates (login, dashboard)
├── utils/                 # All TTS, subtitle, script tools
├── output/                # Output videos per user
└── secure/                # OAuth credentials (.gitignored)
```

---

## ⚙️ LOCAL DEVELOPMENT

```bash
git clone https://github.com/your-org/reelvo-ai.git
cd reelvo-ai
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
sudo apt-get install -y ffmpeg
ENV=development ./start.sh
```

Then visit: [http://localhost:5000/reelvo.ai](http://localhost:5000/reelvo.ai)

---

## 🧪 MANUAL TESTING

```bash
python utils/fallback_ffmpeg.py          # Generate fallback reel
python run_pipeline.py motivation demo   # Run end-to-end for 'motivation' theme
python run_all.py demo                   # Regenerate all reels for demo user
```

---

## 🚢 DEPLOYMENT (RENDER.COM)

1. Push repo to GitHub
2. Connect to [https://render.com](https://render.com)
3. Render will detect `render.yaml` automatically
4. Add `.env` variables via dashboard
5. Click **Deploy**

---

## 🔐 ENVIRONMENT VARIABLES (`.env`)

```env
# Core
FLASK_SECRET_KEY=your_flask_secret_key
DEFAULT_USERNAME=demo

# OpenAI
USE_OPENAI=true
OPENAI_API_KEY=sk-...

# ElevenLabs TTS
USE_ELEVENLABS=true
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=9BWtsMINqrJLrRacOk9x

# Google Cloud TTS
USE_GOOGLE_CLOUD_TTS=false
GOOGLE_CLOUD_TTS_VOICE=en-US-Wavenet-D
GOOGLE_APPLICATION_CREDENTIALS=secure/credentials.json

# Instagram (Graph API)
FB_APP_ID=...
FB_APP_SECRET=...
FB_PAGE_ACCESS_TOKEN=...
INSTAGRAM_BUSINESS_ID=...

# Google Drive
GOOGLE_DRIVE_PARENT_FOLDER_ID=...
GOOGLE_APPLICATION_CREDENTIALS=secure/credentials.json

# Misc
SLEEP_BETWEEN_RUNS=2
```

---

## 👨‍💻 AUTHOR

**Saravana Bhava**  
🌐 [https://sazm.in](https://sazm.in)  
📬 mail@sazm.in

---

## 📄 LICENSE

This project is under **private internal development** for MVP/demo use only.  
For licensing or access, please contact the author directly.

---
