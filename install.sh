#!/bin/bash

# install.sh — Setup for reelvo.ai
set -euo pipefail

echo "🔧 Installing system dependencies..."

# Colors
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Check if ffmpeg is already installed
if command -v ffmpeg &>/dev/null; then
    echo -e "${GREEN}✅ FFmpeg is already installed.${NC}"
else
    echo "📦 Installing FFmpeg..."
    sudo apt-get update -qq
    sudo apt-get install -y ffmpeg
    echo -e "${GREEN}✅ FFmpeg installed successfully.${NC}"
fi

# Optional future steps:
# echo "📦 Installing Python dependencies..."
# pip install -r requirements.txt

echo -e "${GREEN}✅ System setup complete.${NC}"
