# 🎬 Reelvo – AI Instagram Reels Automation Platform (MVP)

**Reelvo** is an end-to-end automation platform that **generates, schedules, and auto-posts Instagram Reels** using GPT-based script generation, TTS voiceovers, and royalty-free stock footage. Ideal for creators, agencies, and AI content workflows.

---

## 🚀 Features

- 🧠 **AI-Powered Script Generation** (OpenAI/GPT)
- 🗣️ **Voiceovers** using Google Cloud TTS or gTTS
- 🎞️ **Stock Video** from Pexels, Pixabay, with fallbacks
- 🎬 **FFmpeg Subtitled Video Generation**
- 📁 **Local User-Specific Output** (`/output/<email>/`)
- ☁️ **Optional Upload to Google Drive**
- 📲 **Auto-post to Instagram** via Graph API
- 🕒 **Daily CRON Scheduler**
- 🔄 **Modular Architecture** (batchable CLI scripts)

---

## 🛠 Tech Stack

| Layer       | Technology                              |
|-------------|------------------------------------------|
| Backend     | Python, Flask                            |
| AI          | OpenAI GPT (via OpenRouter)              |
| TTS         | Google Cloud TTS / gTTS                  |
| Video       | FFmpeg, Pexels, Pixabay, Freesound       |
| Storage     | Local filesystem + Google Drive          |
| Auth        | Instagram Graph API                      |
| Frontend    | HTML, TailwindCSS, Bootstrap elements    |
| Deployment  | Render / Railway / Docker-Compatible     |

---

## 📁 Project Structure

\`\`\`
.
├── app.py                      # Flask entry point
├── assets/                    # Default clips, fonts, logos, music
├── db/                        # SQLite DB and init scripts
├── models/                    # SQLAlchemy models
├── routes/                    # Flask route modules
├── scripts/                   # Scheduled jobs, CLI pipelines
├── secure/                    # OAuth and service credentials
├── seeders/                   # Seeder scripts for themes/users/plans
├── static/                    # CSS, images, favicon
├── templates/                 # HTML templates (Jinja)
├── utils/                     # All helper functions
├── token.json                 # Instagram auth token cache
├── requirements.txt           # Python dependencies
├── package.json               # JS/Tailwind dependencies
├── tailwind.config.js         # Tailwind config
├── render.yaml                # Render.com deployment config
├── postcss.config.js          # PostCSS (Tailwind build)
└── README.md
\`\`\`

---

## ⚙️ Local Development

\`\`\`bash
git clone https://github.com/your-org/reelvo.git
cd reelvo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
sudo apt-get install -y ffmpeg
python app.py
\`\`\`

Visit: [http://localhost:5000/reelvo.in](http://localhost:5000/reelvo.in)

---

## 🧪 CLI Scripts

\`\`\`bash
python scripts/post_scheduled_reels.py
\`\`\`

---

## 🔐 Environment Variables (`.env.example`)

See `.env.example` for all configuration variables.
Use it to create your local `.env` file for deployment or development.

---

## 👨‍💻 Author

**Saravana Bhava**  
🌐 [https://sazm.in](https://sazm.in)  
📧 [mail@sazm.in](mailto:mail@sazm.in)

---

## 📄 License

**Private MVP – Not Open Source**  
For demo, licensing, or deployment access, please contact the author.