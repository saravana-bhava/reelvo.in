#!/bin/bash

# start.sh — Boot script for Reelvo.ai
set -euo pipefail

echo "🚀 Starting Reelvo.ai application..."

# Optional FFmpeg install for local/dev environments
if ! command -v ffmpeg &> /dev/null; then
    echo "🔧 FFmpeg not found. Installing..."
    sudo apt-get update -qq && sudo apt-get install -y ffmpeg
else
    echo "🎬 FFmpeg already installed."
fi

# Use environment variable to toggle dev/prod
MODE=${ENV:-production}

if [[ "$MODE" == "development" ]]; then
    echo "👟 Running in development mode with Flask..."
    exec python3 app.py
else
    echo "🧱 Running in production mode with Gunicorn on port ${PORT:-5000}"
    exec gunicorn app:app --bind 0.0.0.0:${PORT:-5000}
fi
