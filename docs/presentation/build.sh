#!/usr/bin/env bash
# Build the defense deck: vipharmind-slides.pptx (python-pptx, no template), its PDF, and the number check.
# Usage: bash docs/presentation/build.sh
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
cd "$here"
python3 make_deck.py
mkdir -p deck
(cd deck && timeout 300 soffice --headless --convert-to pdf "$here/vipharmind-slides.pptx" >/dev/null 2>&1)
mv deck/vipharmind-slides.pdf vipharmind-slides.pdf
python3 check_numbers.py vipharmind-slides.pptx --final
