# Báo cáo nghiên cứu

- Build: `latexmk` trong thư mục này, ra `main.pdf` (XeLaTeX, phông Times New Roman).
- Số liệu: mọi con số trong văn bản là macro trong `generated/numbers.tex`. Sinh lại bằng
  `cd scripts && uv run report-data build --root ../../.. --out ../generated`. Không gõ số kết quả bằng tay.
- Kiểm tra: `bash check.sh --draft` cho bản nháp; `bash check.sh` cho bản nộp (mục 1–5 dài 15–20 trang,
  không còn "[chờ kết quả]"). Cả hai kiểm build không lỗi, không cảnh báo, không còn `TODO`, và mọi con số
  giữa đầu mục 1 và cuối mục 8 có trong `generated/` hoặc `check-allow.txt`.
- Kiểm thử của `check.sh`: `bash tests/test-check.sh`.
- Chỗ chờ kết quả viết `\pending{...}`, hiện "[chờ kết quả]".
- Nguồn trích dẫn: chỉ `references.bib`; thêm nguồn theo quy trình trong `literature-log.md`.
