#!/bin/bash

# Exit immediately if any command fails
set -e

# Install ffmpeg (if not already installed)
apt-get update && apt-get install -y ffmpeg

# Run the Flask app directly (dev) OR use gunicorn in production
# python3 app.py  # For development
exec gunicorn app:app --bind 0.0.0.0:${PORT:-5000}
