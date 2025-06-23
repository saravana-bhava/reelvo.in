#!/bin/bash

# Ensure fallback folder exists
mkdir -p fallback

# Font path (you can modify if needed)
FONT_PATH="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# List of [niche]=[background_color]
declare -A niches=(
  [motivation]="black"
  [inspiration]="darkblue"
  [sad]="gray"
  [love]="purple"
  [finance]="darkgreen"
)

# Generate fallback videos
for niche in "${!niches[@]}"; do
  color="${niches[$niche]}"
  echo "🎬 Generating: $niche (bg: $color)..."

  ffmpeg -f lavfi -i color=c=$color:s=1080x1920:d=10 \
    -vf "drawtext=fontfile=$FONT_PATH:text='${niche^^}':fontcolor=white:fontsize=80:x=(w-text_w)/2:y=(h-text_h)/2" \
    -c:v libx264 -preset veryfast -crf 28 -y "fallback/${niche}.mp4"
done

echo "✅ All fallback videos generated in /fallback/"
