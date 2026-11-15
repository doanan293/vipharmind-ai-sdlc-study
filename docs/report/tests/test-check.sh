#!/usr/bin/env bash
# Kiểm thử check.sh: chép báo cáo sang thư mục tạm, gài một lỗi, xem check.sh có bắt được không.
# Chạy: bash docs/report/tests/test-check.sh (mỗi ca build lại báo cáo, mất vài chục giây).
set -u
here=$(cd "$(dirname "$0")/.." && pwd)
fails=0

fresh() {
  local dir
  dir=$(mktemp -d)
  # Chỉ chép mã nguồn; bỏ file trung gian và PDF để mỗi ca build từ đầu.
  (cd "$here" && tar --exclude='./tests' --exclude='./scripts/.venv' --exclude='*.aux' \
    --exclude='*.log' --exclude='*.fls' --exclude='*.fdb_latexmk' --exclude='*.xdv' \
    --exclude='*.bbl' --exclude='*.blg' --exclude='*.toc' --exclude='main.pdf' -cf - .) |
    (cd "$dir" && tar -xf -)
  echo "$dir"
}

# expect <tên ca> <mã thoát mong đợi> <chuỗi phải có trong output, rỗng = bỏ qua> <thư mục> [đối số check.sh]
expect() {
  local name=$1 want=$2 needle=$3 dir=$4
  shift 4
  local out code
  out=$(bash "$dir/check.sh" "$@" 2>&1)
  code=$?
  if [[ $code != "$want" ]]; then
    echo "FAIL $name: exit $code, mong đợi $want"
    echo "$out" | tail -5
    fails=$((fails + 1))
  elif [[ -n $needle ]] && ! grep -qF -- "$needle" <<<"$out"; then
    echo "FAIL $name: output thiếu '$needle'"
    echo "$out" | tail -5
    fails=$((fails + 1))
  else
    echo "ok   $name"
  fi
  rm -rf "$dir"
}

# Gài một dòng vào đầu mục 1.
inject() {
  local dir=$1 line=$2
  printf '%s\n' "$line" >>"$dir/sections/01-introduction.tex"
}

expect draft_passes 0 "OK" "$(fresh)" --draft
expect final_rejects_pending 1 "[chờ kết quả]" "$(fresh)"
expect final_reports_page_count 1 "trang" "$(fresh)"

d=$(fresh); inject "$d" '\NumDoesNotExist'
expect undefined_macro_fails_build 1 "build" "$d" --draft

d=$(fresh); inject "$d" 'Xem \cite{khong_co_2099}.'
expect unknown_citation_fails_build 1 "build" "$d" --draft

d=$(fresh); inject "$d" 'Một con số gõ tay 98765 không có trong numbers.json.'
expect hand_typed_number_rejected 1 "98765" "$d" --draft

d=$(fresh); inject "$d" 'Một con số thập phân gõ tay 42,7 phần trăm.'
expect hand_typed_decimal_rejected 1 "42,7" "$d" --draft

d=$(fresh); inject "$d" 'TODO viết tiếp.'
expect todo_rejected 1 "TODO" "$d" --draft

if ((fails)); then
  echo "$fails ca hỏng"
  exit 1
fi
echo "mọi ca đạt"
