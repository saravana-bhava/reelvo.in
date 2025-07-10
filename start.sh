#!/bin/bash

# File: start.sh — Boot script for Reelvo
set -euo pipefail

# ─────────────────────────────────────────────
# Color Codes
# ─────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 Starting Reelvo application...${NC}"

# ─────────────────────────────────────────────
# Ensure FFmpeg is installed
# ─────────────────────────────────────────────
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}🔧 FFmpeg not found. Installing...${NC}"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update -qq
        sudo apt-get install -y ffmpeg
        echo -e "${GREEN}✅ FFmpeg installed.${NC}"
    else
        echo -e "${RED}❌ FFmpeg installation not supported on this OS.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}🎬 FFmpeg already installed.${NC}"
fi

# ─────────────────────────────────────────────
# Determine environment mode
# ─────────────────────────────────────────────
MODE="${FLASK_ENV:-production}"
PORT="${PORT:-5000}"

if [[ "$MODE" == "development" ]]; then
    echo -e "${YELLOW}👟 Running in development mode on port ${PORT} with Flask...${NC}"
    exec python3 main.py
else
    echo -e "${GREEN}🧱 Running in production mode on port ${PORT} with Gunicorn...${NC}"
    if ! command -v gunicorn &> /dev/null; then
        echo -e "${RED}❌ Gunicorn not installed.${NC}"
        echo -e "${YELLOW}👉 Run: pip install gunicorn${NC}"
        exit 1
    fi
    exec gunicorn main:flask_app --bind "0.0.0.0:$PORT"
fi
