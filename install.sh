#!/bin/bash

# File: install.sh — Setup script for reelvo.ai
set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔧 Starting Reelvo.ai system setup...${NC}"

# ─────────────────────────────────────────────
# FFmpeg Installation Check
# ─────────────────────────────────────────────
if command -v ffmpeg &>/dev/null; then
    echo -e "${GREEN}✅ FFmpeg is already installed.${NC}"
else
    echo -e "📦 Installing FFmpeg..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update -qq
        sudo apt-get install -y ffmpeg
    else
        echo -e "${RED}❌ Unsupported OS for automatic FFmpeg installation. Please install it manually.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ FFmpeg installed successfully.${NC}"
fi

# ─────────────────────────────────────────────
# Optional: Python Environment Setup
# ─────────────────────────────────────────────
# echo -e "🐍 Setting up Python virtual environment..."
# python3 -m venv venv
# source venv/bin/activate
# pip install --upgrade pip
# pip install -r requirements.txt
# echo -e "${GREEN}✅ Python dependencies installed.${NC}"

echo -e "${GREEN}🎉 System setup complete! You're ready to go.${NC}"
