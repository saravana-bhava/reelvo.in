#!/usr/bin/env bash

# File: install.sh — Setup script for reelvo.ai
set -euo pipefail

# ─────────────────────────────────────────────
# Color Codes
# ─────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔧 Starting Reelvo.ai system setup...${NC}"

# ─────────────────────────────────────────────
# FFmpeg Installation Check
# ─────────────────────────────────────────────
if command -v ffmpeg &>/dev/null; then
    echo -e "${GREEN}✅ FFmpeg is already installed.${NC}"
else
    echo -e "${YELLOW}📦 FFmpeg not found. Installing...${NC}"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update -qq
        sudo apt-get install -y ffmpeg
    else
        echo -e "${RED}❌ Unsupported OS for automatic FFmpeg installation. Please install FFmpeg manually.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ FFmpeg installed successfully.${NC}"
fi

# ─────────────────────────────────────────────
# Optional: Python Virtual Environment Setup
# ─────────────────────────────────────────────
# echo -e "${YELLOW}🐍 Setting up Python virtual environment...${NC}"
# if ! command -v python3 &>/dev/null; then
#     echo -e "${RED}❌ Python3 is not installed. Please install it first.${NC}"
#     exit 1
# fi
# python3 -m venv venv
# source venv/bin/activate
# pip install --upgrade pip
# if [[ -f "requirements.txt" ]]; then
#     pip install -r requirements.txt
#     echo -e "${GREEN}✅ Python dependencies installed.${NC}"
# else
#     echo -e "${RED}❌ requirements.txt not found.${NC}"
# fi

echo -e "${GREEN}🎉 System setup complete! You're ready to go.${NC}"
