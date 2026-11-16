#!/usr/bin/env bash
# Build the presentation from template-vi.pptx with ppt-master (Edit Native PPTX route).
# Usage: SKILL_DIR=<path to .claude/skills/ppt-master> docs/presentation/build.sh
# Output: docs/presentation/vipharmind-slides.pptx and .pdf; the workspace deck/ is not committed.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
skill="${SKILL_DIR:-$here/../../.claude/skills/ppt-master}"
[ -d "$skill" ] || { echo "set SKILL_DIR to the ppt-master skill directory" >&2; exit 1; }
cd "$here"
if [ ! -d deck/authoring-svg-flat ]; then
  python3 "$skill/scripts/pptx_to_svg.py" template-vi.pptx -o deck --inheritance-mode both --roundtrip >/dev/null
fi
python3 build_deck.py
python3 "$skill/scripts/svg_authoring_view.py" deck/authoring-svg-flat --refresh-summary >/dev/null
python3 "$skill/scripts/svg_quality_checker.py" deck --roundtrip --json > deck/validation/quality.log
grep -A3 "Total files" deck/validation/quality.log
out=$(python3 "$skill/scripts/svg_to_pptx.py" deck --roundtrip --primary-language vi-VN 2>&1 | tee deck/validation/export.log | grep -oE '[^ ]*exports/[^ ]*\.pptx' | tail -1)
grep -E 'Round-trip export summary' deck/validation/export.log || true
cp "$out" vipharmind-slides.pptx
python3 "$skill/scripts/pptx_delivery_check.py" vipharmind-slides.pptx > deck/validation/delivery.json || true
(cd deck/validation && timeout 300 soffice --headless --convert-to pdf "$here/vipharmind-slides.pptx" >/dev/null 2>&1) && mv deck/validation/vipharmind-slides.pdf vipharmind-slides.pdf
python3 check_numbers.py vipharmind-slides.pptx
