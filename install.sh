#!/bin/bash

# Exit immediately on error
set -e

echo "🔧 Installing system dependencies..."

# Update package list and install ffmpeg (with minimal output)
apt-get update -qq && apt-get install -y ffmpeg

echo "✅ FFmpeg installed successfully."
