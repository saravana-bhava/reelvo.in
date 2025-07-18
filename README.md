# 🎬 AI Instagram Reels Automation Platform (MVP)

An AI-powered platform that **automatically generates and schedules Instagram Reels** using GPT scripts, TTS voices, and stock video footage — optionally auto-posted to Instagram and backed up on Google Drive.

---

## 🚀 FEATURES

- 🧠 **AI script generation** via GPT with fallbacks  
- 🗣️ **Voiceover** Google Cloud TTS / gTTS  
- 🎞️ **Stock footage** pulled from Pexels & Pixabay  
- 🎬 **Subtitled videos** created with FFmpeg  
- 📁 **Stored locally** per user in `/output/<email>/`  
- ☁️ **Uploaded to Google Drive**  
- 📲 **Auto-posts** to Instagram via Graph API  
- 🕒 **Scheduler** for daily auto-posting (via CRON)  
- 🔄 Modular scripts (for pipeline, post, schedule, batch)  

---

## 🛠 TECH STACK

| Layer     | Tech                                  |
|-----------|---------------------------------------|
| Backend   | Python + Flask                        |
| AI        | OpenAI GPT                            |
| TTS       | Google TTS / gTTS                     |
| Video     | FFmpeg + stock clips (Pexels/Pixabay) |
| Storage   | Local filesystem + Google Drive       |
| Auth      | Instagram Graph API + Tokens          |
| Frontend  | HTML + CSS (Bootstrap-inspired)       |
| Deploy    | Render / Railway / Docker-compatible  |

---

## 📁 PROJECT STRUCTURE

```
.
├── app.py
├── install.sh
├── start.sh
├── requirements.txt
├── render.yaml
├── templates/
├── routes/
├── utils/
├── scripts/
├── scripts/logs/
├── db/
├── secure/
└── output/
```

---

## ⚙️ LOCAL DEVELOPMENT

```bash
git clone https://github.com/your-org/reelvo.in.git
cd reelvo.in
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
sudo apt-get install -y ffmpeg
FLASK_ENV=development ./start.sh
```

Visit: [http://localhost:5000/reelvo.in](http://localhost:5000/reelvo.in)

---

## 🧪 TESTING SCRIPTS (MANUAL)

```bash
# Run full generation pipeline for one category
python scripts/run_generation_pipeline.py motivation developer@sazm.in

# Run all 5 categories for one user
python scripts/run_all_tasks.py developer@sazm.in

# Run auto-post and schedule check (use in CRON)
python scripts/run_category_pipeline.py

# Schedule all unscheduled reels
python scripts/schedule_reels.py developer@sazm.in

# Post reels due for today
python scripts/post_scheduled_reels.py developer@sazm.in
```

---

## 🔐 ENVIRONMENT CONFIG (`.env`)

```env
# File: .env

# ─────────────────────────────────────────────
# ENVIRONMENT
# ─────────────────────────────────────────────
DEFAULT_EMAIL=developer@sazm.in
DISABLE_CACHE=false
FLASK_ENV=production
FLASK_SECRET_KEY=your-production-secret-key
HOST=reelvo-ai.dev.sazm.in
LOG_LEVEL=INFO
PORT=5000
PROTOCOL=https
SLEEP_BETWEEN_RUNS=2

# ──────────────────────────────────────────────────
# SMTP EMAIL SETTINGS (for password reset)
# ──────────────────────────────────────────────────
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-smtp-email@example.com
SMTP_PASSWORD=your-smtp-password
SMTP_SENDER_NAME=Reelvo Support
SMTP_USE_TLS=true

# ──────────────────────────────────────────────────
# OPENAI SETTINGS
# ──────────────────────────────────────────────────
USE_OPENAI=false
PROVIDER=openrouter
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=deepseek/deepseek-chat-v3-0324:free

# ──────────────────────────────────────────────────
# GOOGLE CLOUD TTS SETTINGS
# ──────────────────────────────────────────────────
USE_GOOGLE_CLOUD_TTS=true
GOOGLE_APPLICATION_CREDENTIALS=/var/www/html/SazM/reelvo.in/secure/credentials.json
GOOGLE_CLOUD_TTS_VOICE=hi-IN-Wavenet-A

# ──────────────────────────────────────────────────
# GOOGLE DRIVE
# ──────────────────────────────────────────────────
UPLOAD_TO_DRIVE=true
GOOGLE_DRIVE_PARENT_FOLDER_ID=your-google-drive-folder-id

# ──────────────────────────────────────────────────
# INSTAGRAM GRAPH API SETTINGS
# ──────────────────────────────────────────────────
POST_TO_IG=true
FB_APP_ID=your-fb-app-id
FB_APP_SECRET=your-fb-app-secret

# ──────────────────────────────────────────────────
# PEXELS API SETTINGS
# ──────────────────────────────────────────────────
USE_PEXELS=true
PEXELS_API_KEY=your-pexels-api-key

# ──────────────────────────────────────────────────
# PIXABAY API SETTINGS
# ──────────────────────────────────────────────────
USE_PIXABAY=true
PIXABAY_API_KEY=your-pixabay-api-key

# ──────────────────────────────────────────────────
# FREESOUND API SETTINGS
# ──────────────────────────────────────────────────
FREESOUND_API_CLIENT=your-freesound-client-id
FREESOUND_API_KEY=your-freesound-api-key
```

---

## 📦 DEPLOYMENT (RENDER.COM)

1. Push repo to GitHub  
2. Create a new Web Service on [https://render.com](https://render.com)  
3. Add required `.env` variables in Render dashboard  
4. Render auto-detects `render.yaml`  
5. Click **Deploy**

---

## 👨‍💻 AUTHOR

**Saravana Bhava**  
🔗 [https://sazm.in](https://sazm.in)  
📧 mail@sazm.in

---

## 📄 LICENSE

Private MVP – Not open source.  
For demo access, licensing, or deployment rights, contact the author directly.


