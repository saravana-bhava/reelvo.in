#!/bin/bash

# start.sh — Boot script for Reelvo.ai
set -euo pipefail

echo "🚀 Starting Reelvo.ai application..."

# Optional FFmpeg install (for local dev or non-containerized use)
if ! command -v ffmpeg &> /dev/null; then
    echo "🔧 FFmpeg not found. Installing..."
    sudo apt-get update -qq && sudo apt-get install -y ffmpeg
else
    echo "🎬 FFmpeg already installed."
fi

# Determine mode: development vs production
MODE=${ENV:-production}
PORT=${PORT:-5000}

if [[ "$MODE" == "development" ]]; then
    echo "👟 Running in development mode with Flask on port $PORT..."
    exec python3 app.py
else
    echo "🧱 Running in production mode with Gunicorn on port $PORT..."
    exec gunicorn app:app --bind 0.0.0.0:$PORT
fi
