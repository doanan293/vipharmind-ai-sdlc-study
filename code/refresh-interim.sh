#!/usr/bin/env bash
# Làm mới mọi số liệu thăm dò (E2 đề sơ sài, E1 Haiku) trong báo cáo và slide bằng một lệnh.
#
#   bash code/refresh-interim.sh            # chạy sdlc-e2; chạy sdlc-e1 nếu Haiku đã đủ 138 lượt
#   SKIP_E1=1 bash code/refresh-interim.sh  # không chạy sdlc-e1 (dùng data/results/analysis/e1 đã có)
#
# Các bước: (1) sdlc-e2 -> data/results/analysis/e2-interim; (2) sdlc-e1 nếu đủ lượt -> data/results/analysis/e1;
# (3) report-data build; (4) build main.pdf và kiểm (check.sh --draft); (5) build slide, chạy check_numbers.py.
# Dữ liệu chạy thô nằm ở .worktrees/run*/results/raw (không commit). Không commit gì; xem `git status` rồi
# commit bằng tay.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
R="${RUNS_ROOT:-$here/.worktrees}"
SKILL_DIR="${SKILL_DIR:-$here/.agents/skills/ppt-master}"
DETAILED=("$R/run/results/raw/main"
          "$R/run2/results/raw/main-tiers"
          "$R/run3/results/raw/haiku")
BRIEF="$R/run3/results/raw/brief"
HAIKU_UNITS=138

step() { printf '\n== %s\n' "$*"; }

step "1/5 sdlc-e2 -> data/results/analysis/e2-interim"
(cd "$here/code/analysis" && uv run sdlc-e2 --detailed "${DETAILED[@]}" --brief "$BRIEF" \
   --out "$here/data/results/analysis/e2-interim")

haiku=$(find "${DETAILED[2]}" -name grade.json | wc -l)
if [ -z "${SKIP_E1:-}" ] && [ "$haiku" -ge "$HAIKU_UNITS" ]; then
  step "2/5 sdlc-e1 (Haiku $haiku/$HAIKU_UNITS lượt) -> data/results/analysis/e1"
  (cd "$here/code/analysis" && uv run sdlc-e1 --results "${DETAILED[@]}" --seed 20261115 \
     --repo "$R/vipharmind" --model-bootstrap 999 --jobs 4)
else
  step "2/5 bỏ qua sdlc-e1 (Haiku $haiku/$HAIKU_UNITS lượt${SKIP_E1:+, SKIP_E1})"
fi
# mức khớp của mẫu chấm tay (draw_human_check.py kappa ghi vào data/results/analysis/e2)
if [ -f "$here/data/results/analysis/e2/human-check-agreement.json" ]; then
  cp "$here/data/results/analysis/e2/human-check-agreement.json" "$here/data/results/analysis/e2-interim/"
fi

step "3/5 report-data build"
(cd "$here/docs/report/scripts" && uv run report-data build --root ../../.. --out ../generated)
# hai hình hồi cứu sinh lại khác byte nhưng không khác nội dung
git -C "$here" checkout -q -- docs/report/generated/figures/lifecycle_by_week.pdf \
  docs/report/generated/figures/rework_by_group.pdf

step "4/5 main.pdf và check.sh --draft"
(cd "$here/docs/report" && bash check.sh --draft)

step "5/5 slide và check_numbers.py"
SKILL_DIR="$SKILL_DIR" bash "$here/docs/presentation/build.sh"

python3 - "$here/docs/report/generated/numbers.json" <<'PY'
import json, sys
n = json.load(open(sys.argv[1]))
print(f"\nE2: {n.get('ETwoLabel')} · phạm vi: {n.get('ETwoScope')} · đã chấm "
      f"{n.get('ETwoBriefJudged')}/{n.get('ETwoBriefExpected')}")
print(f"E2 gộp: {n.get('ETwoPooledAllPp')} [{n.get('ETwoPooledAllLowPp')}; {n.get('ETwoPooledAllHighPp')}] đpt"
      f" · đọc: {n.get('ETwoReading')}")
print(f"E1: {'có' if n.get('EOneSmallSpecPct') else 'chưa có'}")
PY
