#!/bin/bash

# install.sh — Setup script for reelvo.ai
set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🔧 Starting Reelvo.ai system setup..."

# Check if FFmpeg is installed
if command -v ffmpeg &>/dev/null; then
    echo -e "${GREEN}✅ FFmpeg is already installed.${NC}"
else
    echo "📦 Installing FFmpeg..."
    sudo apt-get update -qq
    sudo apt-get install -y ffmpeg
    echo -e "${GREEN}✅ FFmpeg installed successfully.${NC}"
fi

# Optional Python setup (uncomment as needed)
# echo "🐍 Setting up Python virtual environment..."
# python3 -m venv venv
# source venv/bin/activate
# pip install --upgrade pip
# pip install -r requirements.txt
# echo -e "${GREEN}✅ Python dependencies installed.${NC}"

echo -e "${GREEN}✅ System setup complete! You're ready to go.${NC}"
