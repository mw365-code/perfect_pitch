#!/usr/bin/env zsh
set -euo pipefail

ROOT_DIR="${1:-.}"
MAX_LINES="${2:-300}"

find "$ROOT_DIR" -type f \
  ! -path "*/.git/*" \
  ! -path "*/.venv/*" \
  ! -path "*/.idea/*" \
  ! -path "*/__pycache__/*" \
  -name "*.py" \
  -print0 \
  | xargs -0 wc -l \
  | awk -v max="$MAX_LINES" '$2 != "total" && $1 > max {print $1, $2; found=1} END{exit found?1:0}'
