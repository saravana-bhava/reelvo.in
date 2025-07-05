#!/bin/bash

# File: start.sh — Boot script for Reelvo.ai
set -euo pipefail

echo "🚀 Starting Reelvo.ai application..."

# ─────────────────────────────────────────────
# Ensure FFmpeg is installed (useful in dev/local)
# ─────────────────────────────────────────────
if ! command -v ffmpeg &> /dev/null; then
    echo "🔧 FFmpeg not found. Installing..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update -qq && sudo apt-get install -y ffmpeg
        echo "✅ FFmpeg installed."
    else
        echo "❌ FFmpeg installation not supported on this OS."
        exit 1
    fi
else
    echo "🎬 FFmpeg already installed."
fi

# ─────────────────────────────────────────────
# Determine environment mode
# ─────────────────────────────────────────────
MODE=${FLASK_ENV:-production}
PORT=${PORT:-5000}

if [[ "$MODE" == "development" ]]; then
    echo "👟 Running in development mode on port $PORT with Flask..."
    exec python3 main.py
else
    echo "🧱 Running in production mode on port $PORT with Gunicorn..."
    exec gunicorn main:flask_app --bind 0.0.0.0:$PORT
fi
