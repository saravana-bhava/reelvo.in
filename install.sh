#!/bin/bash

# Exit on error
set -e

# Update package list and install FFmpeg
apt-get update && apt-get install -y ffmpeg
