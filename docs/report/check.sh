#!/usr/bin/env bash
# Kiểm tra báo cáo: build sạch, số trang, chỗ còn trống, con số gõ tay.
# Dùng: bash check.sh [--draft]
#   --draft  cho phép "[chờ kết quả]" và không kiểm số trang (bản nháp).
# Thoát 0 khi hợp lệ, 1 kèm danh sách lỗi.
set -u
cd "$(dirname "$0")"
draft=0
[[ ${1:-} == --draft ]] && draft=1

# 1. Build. latexmk dừng ở lỗi đầu tiên (macro chưa định nghĩa) và coi trích dẫn,
#    tham chiếu chưa định nghĩa là lỗi ($warnings_as_errors trong .latexmkrc).
if ! latexmk -silent main.tex >build.out 2>&1; then
  echo "build lỗi:"
  grep -E '^(!|.*:[0-9]+:)|Warning|undefined' main.log build.out 2>/dev/null | head -20
  exit 1
fi

errors=()
# Mọi cảnh báo còn lại trong log cũng là lỗi.
warn=$(grep -E 'Warning' main.log || true)
if [[ -n $warn ]]; then
  errors+=("build có cảnh báo: $(head -3 <<<"$warn" | tr '\n' ' ')")
fi
if grep -q 'Warning--' main.blg 2>/dev/null; then
  errors+=("bibtex có cảnh báo: $(grep 'Warning--' main.blg | head -3 | tr '\n' ' ')")
fi

# 2. Trang vật lý của nhãn đầu mục 1 và cuối mục 8 (zref ghi \abspage vào main.aux).
abspage() { sed -nE "s/.*zref@newlabel\{$1\}.*\\\\abspage\{([0-9]+)\}.*/\1/p" main.aux | head -1; }
first=$(abspage sec:first)
last=$(abspage sec:last)
if [[ -z $first || -z $last ]]; then
  echo "không tìm thấy nhãn sec:first hoặc sec:last trong main.aux"
  exit 1
fi
pages=$((last - first + 1))
if ((!draft)) && ((pages < 15 || pages > 20)); then
  errors+=("mục 1–8 dài $pages trang, cần 15–20 trang")
fi

# 3. Chỗ còn trống trong toàn bộ PDF.
alltext=$(pdftotext main.pdf - | tr -s ' \n' '  ')
if grep -qF 'TODO' <<<"$alltext"; then
  errors+=("còn TODO")
fi
if ((!draft)) && grep -qF '[chờ kết quả]' <<<"$alltext"; then
  errors+=("còn [chờ kết quả]: $(grep -oF '[chờ kết quả]' <<<"$alltext" | wc -l) chỗ")
fi

# 4. Mọi con số giữa hai nhãn phải đến từ máy (numbers.json, bảng và hình sinh ra) hoặc nằm trong
#    check-allow.txt (năm, phiên bản, số mục...).
pdftotext -f "$first" -l "$last" main.pdf body.txt
stray=$(python3 - body.txt <<'PY'
import glob, json, re, subprocess, sys

TOKEN = re.compile(r"\d+(?:[.,]\d+)*")

def tokens(s):
    return set(TOKEN.findall(s))

allowed = set()
for value in json.load(open("generated/numbers.json")).values():
    allowed |= tokens(str(value))
for path in glob.glob("generated/tables/*.tex"):
    allowed |= tokens(open(path, encoding="utf-8").read())
for path in glob.glob("generated/figures/*.pdf"):
    allowed |= tokens(subprocess.run(["pdftotext", path, "-"], capture_output=True, text=True).stdout)
for line in open("check-allow.txt", encoding="utf-8"):
    line = line.split("#", 1)[0].strip()
    m = re.fullmatch(r"(\d+)\.\.(\d+)", line)
    if m:
        allowed |= {str(i) for i in range(int(m[1]), int(m[2]) + 1)}
    elif line:
        allowed.add(line)
# Số mục, bảng, hình lấy từ mục lục và file phụ của LaTeX.
for ext in ("toc", "lot", "lof"):
    try:
        allowed |= set(re.findall(r"\\numberline \{([\d.]+)\}", open(f"main.{ext}", encoding="utf-8").read()))
    except FileNotFoundError:
        pass

text = open(sys.argv[1], encoding="utf-8").read()
text = re.sub(r"(?m)^\s*\d+\s*$", " ", text)                    # số trang ở chân trang
text = re.sub(r"\d{4}-\d{2}-\d{2}", " ", text)                  # ngày ISO
text = re.sub(r"\b(?=[0-9a-f]*[a-f])(?=[0-9a-f]*\d)[0-9a-f]{7,40}\b", " ", text)  # mã commit
text = re.sub(r"\[\d+(?:[,–-]\s*\d+)*\]", " ", text)            # số trích dẫn
text = re.sub(r"\b(?:RQ|H|Q|F|t|p)\d+\b", " ", text)            # mã RQ, giả thuyết, truy vấn, đề
text = re.sub(r"(?:Bảng|Hình|mục|Mục|phụ lục|Phụ lục)\s+\d+(?:\.\d+)*", " ", text)
bad = sorted({t for t in tokens(text) if t not in allowed})
print(" ".join(bad))
PY
)
if [[ -n $stray ]]; then
  errors+=("con số không có nguồn máy: $stray")
fi

if ((${#errors[@]})); then
  printf '%s\n' "${errors[@]}"
  echo "mục 1–8: $pages trang"
  exit 1
fi
echo "OK: mục 1–8 dài $pages trang$( ((draft)) && echo ' (nháp)')"
