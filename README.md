# 🎬 Reelvo

> **AI-Powered Content Automation Platform**

Generate, schedule, and publish short-form video content using AI-assisted workflows, automated media processing, and integrated publishing pipelines.

---

## Overview

Reelvo is an end-to-end content automation platform designed to streamline the creation and publishing of short-form social media content.

It combines AI-generated scripts, automated voiceovers, royalty-free media sourcing, subtitle generation, scheduling, and publishing into a unified workflow that significantly reduces manual effort while maintaining content quality.

Originally developed as a production MVP, Reelvo demonstrates practical software engineering across AI integration, workflow automation, media processing, and scalable backend architecture.

---

## Key Capabilities

### 🤖 AI Content Generation

- GPT-powered script generation
- Prompt-based content workflows
- Configurable AI providers

### 🎙 Voice Generation

- Google Cloud Text-to-Speech
- gTTS fallback support
- Multiple voice options

### 🎥 Automated Video Production

- FFmpeg rendering pipeline
- Subtitle generation
- Stock media integration
- Royalty-free video sourcing
- Automated composition

### 📅 Publishing Workflow

- Content scheduling
- Batch processing
- Automatic publishing
- Instagram Graph API integration

### ☁ Storage & Automation

- Google Drive integration
- Local asset management
- Scheduled background jobs
- Automated processing pipelines

---

# Architecture

Reelvo follows a modular architecture separating content generation, media processing, scheduling, publishing, and storage into independent components.

```
                AI Providers
                     │
                     ▼
             Script Generation
                     │
                     ▼
             Voice Generation
                     │
                     ▼
             Media Processing
                     │
                     ▼
           Video Composition (FFmpeg)
                     │
                     ▼
            Publishing Scheduler
                     │
                     ▼
         Instagram Graph API / Storage
```

---

# Technology Stack

| Layer | Technology |
|--------|------------|
| Backend | Python, Flask |
| AI | OpenAI GPT |
| Voice | Google Cloud TTS, gTTS |
| Video | FFmpeg |
| Media | Pexels, Pixabay |
| Frontend | HTML, Tailwind CSS |
| Database | SQLite |
| Authentication | Instagram Graph API |
| Deployment | Docker, Railway, Render |

---

# Features

- AI-powered script generation
- Automated voiceovers
- Subtitle generation
- Royalty-free stock video sourcing
- Video rendering with FFmpeg
- Instagram publishing
- Scheduling & automation
- Google Drive integration
- Modular CLI tools
- Batch processing support

---

# Project Structure

```
app.py
routes/
models/
scripts/
templates/
static/
utils/
assets/
db/
```

---

# Local Development

```bash
git clone https://github.com/saravana-bhava/reelvo.in.git

cd reelvo.in

python -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

python app.py
```

---

# Configuration

Environment variables are managed using:

```
.env
```

A template is provided:

```
.env.template
```

---

# Deployment

The platform supports deployment to:

- Railway
- Render
- Docker
- Linux VPS

---

# Current Status

**Production MVP**

The repository represents a working production prototype demonstrating AI-assisted content automation, workflow orchestration, media processing, and social publishing pipelines.

---

# Engineering Highlights

- Modular backend architecture
- AI workflow orchestration
- Automated media processing
- Scalable scheduled jobs
- Production-ready publishing pipeline
- Clean separation of services
- Extensible automation framework

---

# Related Projects

## 🚀 SazM

Senior Software Engineering & Architecture Consulting

https://sazm.in

---

## 📚 Project Portfolio

100+ production software systems delivered across multiple industries.

https://sazm.in/projects

---

## ✍ Engineering Insights

Articles on software architecture, platform modernization, AI engineering, and technical leadership.

https://sazm.in/articles

---

# Author

**Saravana Bhava**

Senior Software Engineer • Software Architect • Technical Lead

🌐 https://sazm.in

💼 https://linkedin.com/in/saravana-bhava

📧 sabajobs@gmail.com

---

# License

Private portfolio project.

Source code is published for portfolio and demonstration purposes.

For commercial licensing or collaboration, please contact the author.

---

> *Engineering automation that scales content production through reliable software architecture and AI-assisted workflows.*
