#!/usr/bin/env bash
# Kiểm tra đề cương trước khi nộp: số trang, các con số và tên mô hình, chỗ còn trống.
# Chạy trong thư mục proposal/ sau khi build. Thoát 0 khi hợp lệ, 1 kèm danh sách lỗi.
set -u
cd "$(dirname "$0")"
pdf=de-cuong.pdf
if [[ ! -f $pdf ]]; then
  echo "$pdf không tồn tại"
  exit 1
fi

errors=()
pages=$(pdfinfo "$pdf" | awk '/^Pages:/ {print $2}')
if [[ $pages != 1 && $pages != 2 ]]; then
  errors+=("đề cương dài $pages trang, tối đa 2")
fi

# Gộp các dòng để cụm từ bị ngắt dòng vẫn tìm được.
text=$(pdftotext -layout "$pdf" - | tr -s ' \n' '  ')
for needle in "505" "15 nhiệm vụ" "360" "Claude Opus 5.5" "Claude Sonnet 5.5" "Gemini 3.8 Flash" "gpt-6-luna" \
  "vibe coding" "không so sánh công cụ với công cụ"; do
  if ! grep -qF -- "$needle" <<<"$text"; then
    errors+=("thiếu: $needle")
  fi
done
for banned in "TODO" "??"; do
  if grep -qF -- "$banned" <<<"$text"; then
    errors+=("còn chỗ trống: $banned")
  fi
done

if ((${#errors[@]})); then
  printf '%s\n' "${errors[@]}"
  exit 1
fi
echo "OK: $pages trang"
