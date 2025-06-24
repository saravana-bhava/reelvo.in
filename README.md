# AI Instagram Reels Automation Platform (MVP)

A streamlined content automation tool for creators — users pick a niche → AI generates a script → a reel is auto-created → uploaded to Google Drive → and posted to Instagram.

## ✨ Features

- 🔐 Simple login interface (no signup required)
- 🎯 Niche selection (Motivation, Sad, Inspiration, Success, Life)
- 🧠 AI script generation via OpenAI API (with fallback)
- 🎬 Video creation using VEED API or FFmpeg fallback
- 📁 Output video saved to `/output` directory
- ☁️ Uploads to Google Drive (configurable)
- 📱 Auto-post to Instagram Reels (via Graph API)
- 🔁 Scheduler-ready (via cron or BullMQ)
- 🌐 Works under subpath (e.g. `/reelvo.ai`) via DispatcherMiddleware

## 🚀 Tech Stack

- **Backend**: Python + Flask
- **Frontend**: HTML + CSS (templated)
- **Video**: VEED.io API + FFmpeg fallback
- **AI**: OpenAI GPT
- **Storage**: Google Drive API
- **Deployable On**:
  - [x] Render (recommended)
  - [x] Railway

## 📁 Folder Structure

```
.
├── app.py                 # Main Flask app (mounted at /reelvo.ai)
├── install.sh             # Installs ffmpeg
├── start.sh               # Starts gunicorn + installs ffmpeg
├── requirements.txt       # Python dependencies
├── render.yaml            # Render deployment config
├── .vercel.json           # Vercel config (not recommended)
├── templates/             # HTML templates (login + dashboard)
├── utils/                 # Script and video generation tools
├── fallback/              # Pre-generated fallback videos
├── output/                # Generated videos go here
└── docs/                  # Project notes, NDA, briefs
```

## 🛠 Local Development

```bash
# Set up environment
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Install ffmpeg if needed
sudo apt-get install -y ffmpeg

# Run the app
python app.py
```

Then visit: [http://localhost:5000/reelvo.ai](http://localhost:5000/reelvo.ai)

## 🧪 Testing FFmpeg Fallback

You can manually run:

```bash
python utils/fallback_ffmpeg.py
```

Or trigger generation from the dashboard with a selected theme.

## ☁️ Deploying to Render

1. Push to GitHub
2. Connect your repo on [Render.com](https://render.com)
3. Use `render.yaml` (auto detected)

---

## 👤 Author

**Saravana Bhava**  
🌐 [https://sazm.in](https://sazm.in)

---

## 📄 License

This project is under private development for internal MVP/demo use. For licensing, contact the author.
