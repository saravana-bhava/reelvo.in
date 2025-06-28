# AI Instagram Reels Automation Platform (MVP)

A streamlined AI-powered platform that helps creators generate Instagram Reels automatically.  
Users select a niche, AI generates a script, TTS generates audio, FFmpeg builds the video, and the result is uploaded to Google Drive and optionally posted to Instagram.

------------------------------

FEATURES

- Simple login interface (no signup required)
- Niche selection (Motivation, Sad, Inspiration, Success, Life)
- AI script generation (OpenAI with fallback)
- Text-to-Speech via ElevenLabs / Google TTS / gTTS
- Video generation using FFmpeg or VEED fallback
- Subtitle overlay (SRT from TTS)
- Videos saved to /output/<username>/
- Uploads to Google Drive (optional)
- Auto-post to Instagram Reels (via Graph API)
- Scheduler-ready (cron/BullMQ)
- Subpath-ready via DispatcherMiddleware (/reelvo.ai)

------------------------------

TECH STACK

Backend: Python + Flask  
Video Engine: FFmpeg + Pexels/Pixabay clips  
TTS: ElevenLabs / Google Cloud TTS / gTTS  
AI Script: OpenAI GPT  
Storage: Local + Google Drive  
Frontend: HTML + Bootstrap dashboard  
Deployment: Render / Railway / Docker

------------------------------

FOLDER STRUCTURE

.
├── app.py                 # Flask app mounted at /reelvo.ai
├── install.sh             # FFmpeg installer
├── start.sh               # Launch with Gunicorn or Flask
├── requirements.txt       # All dependencies
├── render.yaml            # Render deployment config
├── templates/             # Login and dashboard HTML
├── utils/                 # Script/TTS/Subtitle generators
├── output/                # Output videos (organized by user)
├── fallback/              # Default fallback video assets
└── secure/                # OAuth credentials, if any

------------------------------

LOCAL DEVELOPMENT

git clone https://github.com/your-org/reelvo-ai.git  
cd reelvo-ai  
python3 -m venv venv && source venv/bin/activate  
pip install -r requirements.txt  
sudo apt-get install -y ffmpeg  
ENV=development ./start.sh  

Then visit: http://localhost:5000/reelvo.ai

------------------------------

MANUAL TESTING

python utils/fallback_ffmpeg.py  
python run_all.py demo  
python run_pipeline.py motivation demo

------------------------------

DEPLOYMENT ON RENDER

1. Push repo to GitHub
2. Connect to https://render.com
3. Render auto-detects render.yaml
4. Add secrets via the Render dashboard
5. Deploy

------------------------------

ENVIRONMENT VARIABLES (.env)

FLASK_SECRET_KEY=your_flask_key  
USE_OPENAI=false  
USE_ELEVENLABS=true  
USE_GOOGLE_CLOUD_TTS=false  
OPENAI_API_KEY=sk-...  
ELEVENLABS_API_KEY=...  
ELEVENLABS_VOICE_ID=9BWtsMINqrJLrRacOk9x  
GOOGLE_CLOUD_TTS_VOICE=en-US-Wavenet-D  
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json  
FB_APP_ID=...  
FB_APP_SECRET=...  
FB_PAGE_ACCESS_TOKEN=...  
INSTAGRAM_BUSINESS_ID=...  
DEFAULT_USERNAME=demo  
SLEEP_BETWEEN_RUNS=2

------------------------------

AUTHOR

Saravana Bhava  
https://sazm.in  
mail@sazm.in

------------------------------

LICENSE

This project is under private development for internal MVP/demo use only.  
To request access or licensing, please contact the author directly.
