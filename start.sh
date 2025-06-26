#!/bin/bash

# Exit immediately if any command fails
set -e

echo "🚀 Starting Reelvo.ai application..."

# Optionally install FFmpeg if not already installed (useful for local/dev)
if ! command -v ffmpeg &> /dev/null; then
    echo "🔧 FFmpeg not found. Installing..."
    apt-get update -qq && apt-get install -y ffmpeg
else
    echo "🎬 FFmpeg already installed."
fi

# Run the Flask app directly for development
# Uncomment this if you're running locally
# echo "👟 Running in development mode"
# exec python3 app.py

# Run with Gunicorn in production
echo "🧱 Running with Gunicorn on port ${PORT:-5000}"
exec gunicorn app:app --bind 0.0.0.0:${PORT:-5000}
