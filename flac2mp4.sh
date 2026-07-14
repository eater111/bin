#!/usr/bin/env bash

set -euo pipefail

find . -type f -iname "*.flac" -print0 | while IFS= read -r -d '' flac; do

    dir="$(dirname "$flac")"
    filename="$(basename "$flac")"
    base="${filename%.*}"

    output="$dir/$base.mp4"

    if [[ -f "$output" ]]; then
        echo "Skipping (exists): $output"
        continue
    fi

    echo "Processing: $flac"

    tmp_cover="$(mktemp --suffix=.jpg)"
    cover=""

    # Extract embedded artwork if present
    if ffmpeg -nostdin -loglevel error -y \
        -i "$flac" \
        -an \
        -c:v mjpeg \
        "$tmp_cover" 2>/dev/null; then

        if [[ -s "$tmp_cover" ]]; then
            cover="$tmp_cover"
        fi
    fi

    # Fallback covers
    if [[ -z "$cover" ]]; then
        for candidate in \
            "$dir/cover.jpg" \
            "$dir/Cover.jpg" \
            "$dir/folder.jpg" \
            "$dir/Folder.jpg" \
            "$dir/cover.png" \
            "$dir/folder.png"
        do
            if [[ -f "$candidate" ]]; then
                cover="$candidate"
                break
            fi
        done
    fi

    if [[ -z "$cover" ]]; then
        echo "No artwork found: $flac"
        rm -f "$tmp_cover"
        continue
    fi

    ffmpeg -nostdin -hide_banner -loglevel warning -y \
        -loop 1 -i "$cover" \
        -i "$flac" \
        -map 0:v:0 \
        -map 1:a:0 \
        -vf "scale=1920:1080:force_original_aspect_ratio=decrease,\
pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black" \
        -c:v libx264 \
        -preset medium \
        -tune stillimage \
        -pix_fmt yuv420p \
        -c:a aac \
        -b:a 320k \
        -metadata title="$(ffprobe -v quiet -show_entries format_tags=TITLE -of default=nw=1:nk=1 "$flac")" \
        -metadata artist="$(ffprobe -v quiet -show_entries format_tags=ARTIST -of default=nw=1:nk=1 "$flac")" \
        -metadata album="$(ffprobe -v quiet -show_entries format_tags=ALBUM -of default=nw=1:nk=1 "$flac")" \
        -shortest \
        -movflags +faststart \
        "$output"

    rm -f "$tmp_cover"

    echo "Created: $output"
done

echo "Done."
