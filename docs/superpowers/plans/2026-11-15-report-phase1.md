# Báo cáo, giai đoạn 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Báo cáo LaTeX có khung đầy đủ, số liệu sinh tự động, mục 1–5 viết xong; tài liệu gán nhãn; báo cáo tiến độ dựng được khi có kết quả chạy thử.

**Architecture:** `docs/report/` là một dự án LaTeX (XeLaTeX, `latexmk`) cùng kiểu `docs/proposal/`. Gói Python `report_data` trong `docs/report/scripts/` đọc kết quả hồi cứu, phễu sàng lọc, nhật ký tài liệu và (khi có) kết quả chạy thử, rồi sinh `generated/numbers.tex`, `generated/numbers.json`, `generated/tables/*.tex`, `generated/figures/*.pdf`. Văn bản chỉ gọi macro số liệu.

**Tech Stack:** XeLaTeX, latexmk, BibTeX, Python 3.12 + uv, matplotlib, pytest, bash, `pdfinfo`, `pdftotext`.

**Spec:** `docs/superpowers/specs/2026-11-15-report-and-presentation-design.md` (mục 5.1, 5.3, 5.4, 5.5). Nội dung khoa học: `docs/superpowers/specs/2026-11-15-spec-vs-vibe-study-design.md`.

## Global Constraints

- Làm trong worktree `/home/andv/personal/vipharmind-ai-sdlc-study-report`, nhánh `report` tách từ `harness` (đã commit), đã gộp nhánh `retrospective` để có `data/retrospective/`.
- Tiếng Việt khoa học, câu ngắn, không thổi phồng; "vibe coding", "coding agent", tên công cụ, tên mô hình giữ tiếng Anh; số thập phân dấu phẩy.
- Times New Roman 12pt, A4, lề 2,5 cm, giãn dòng 1,2; trang bìa: tên đề tài, "Chuyên đề nghiên cứu 1 (IT5421)", "Giảng viên: TS. Nguyễn Thanh Hùng", ba thành viên kèm mã (Doãn Văn An 20252778M, Lê Xuân Lợi 20252781M, Trần Ngọc Bảo 20251227M), tháng 11/2026; không logo.
- Mọi con số trong văn bản là macro từ `generated/numbers.tex`; không gõ số kết quả bằng tay (số đếm cố định trong câu chữ như "ba nhóm" được phép).
- Chỉ trích nguồn có trong `docs/report/references.bib` (đã kiểm tra); thêm nguồn mới phải theo quy trình trong `literature-log.md`.
- Chỗ chờ kết quả dùng `\pending{...}` (hiện "[chờ kết quả]"); `check.sh --draft` cho phép, `check.sh` báo lỗi.
- 15–20 trang tính từ mục 1 đến hết mục 8; bìa, tóm tắt, mục lục, tài liệu tham khảo, phụ lục không tính.
- Khai báo đúng cách làm thật: đề bài do AI soạn và An duyệt gộp; kiểm tra quy tắc nối có gợi ý AI; AI tham gia viết báo cáo.
- Commit không có dòng ghi công AI.

## Review Focus

- Macro gọi trong `.tex` mà `numbers.tex` không định nghĩa → build phải lỗi (không im lặng in rỗng). Test ở Task 1.
- Thiếu file nguồn (chưa có kết quả chạy thử) → script vẫn sinh đủ macro, macro thiếu nhận `\pending{}`. Test ở Task 2.
- Số trong văn bản lệch file kết quả → `check.sh` đối chiếu mọi số trong PDF với `numbers.json`. Test ở Task 1.
- Dấu phẩy thập phân và phần trăm định dạng sai (88.7 thay vì 88,7) → hàm định dạng có test. Task 2.
- Trích dẫn không có trong `references.bib` → build lỗi (warnings as errors). Task 1.

---

### Task 1: Khung báo cáo và `check.sh`

**Files:** Create `docs/report/{main.tex,.latexmkrc,README.md,check.sh}`, `docs/report/sections/{00-frontmatter,01-introduction,02-related-work,03-questions,04-method,05-retrospective,06-results,07-discussion,08-conclusion,appendix}.tex`, `docs/report/generated/numbers.tex` (tạm, một macro mẫu).

- [ ] Viết `check.sh` trước, chạy trên khung rỗng để thấy nó báo lỗi đúng chỗ. `check.sh [--draft]` kiểm: build `latexmk` không lỗi, không warning; số trang giữa nhãn `\label{sec:first}` và `\label{sec:last}` (đọc từ file `.aux` hoặc bằng `\zref`/ghi trang vào file phụ) nằm trong 15–20 khi không `--draft`; không còn `TODO`; không còn "[chờ kết quả]" khi không `--draft`; mọi số dạng `\d+[,.]?\d*` trong PDF giữa hai nhãn có trong `generated/numbers.json` hoặc trong danh sách cho phép `check-allow.txt` (năm, số mục, số RQ…).
- [ ] Khung LaTeX: preamble theo Global Constraints, macro `\pending`, `\input{generated/numbers}`, mỗi mục `\input`; mục chưa viết chứa `\pending{...}`. Macro chưa định nghĩa phải gây lỗi build (đúng hành vi mặc định của LaTeX).
- [ ] Chạy `bash check.sh --draft` → exit 0; `bash check.sh` → exit 1 với thông báo "[chờ kết quả]" và số trang.
- [ ] Commit `docs(report): scaffold the report with a page and number check`.

### Task 2: Gói `report_data`

**Files:** Create `docs/report/scripts/{pyproject.toml,src/report_data/{__init__,fmt,sources,build,cli}.py,tests/...}`.

**Interfaces:**
- `fmt.number(x: float, decimals: int = 1) -> str` (dấu phẩy thập phân, dấu chấm phân cách nghìn: `13412 → "13.412"`, `88.66 → "88,7"`); `fmt.percent(part: int, total: int, decimals: int = 1) -> str`.
- `sources.load(root: Path) -> dict[str, Any]` đọc: `data/retrospective/{summary.md không đọc; lifecycle_by_stage.csv, rework_summary.csv, sessions.csv, spec_trace.csv, link-check.csv, commits.csv}`, `data/tasks/screening.json`, `data/tasks/t*/task.toml`, `data/tasks/p*/task.toml`, `docs/report/data/literature.toml` (Task 2 tạo, chép số từ `literature-log.md`: 15 truy vấn, 47 tìm thấy, 31 sàng lọc, 18 giữ, 24 tổng, số nguồn mỗi nhóm), `data/results/raw/` nếu có; thiếu nguồn nào thì khóa tương ứng là `None`.
- `build.write(data, out: Path) -> None` sinh `numbers.tex` (`\newcommand{\Num<Tên>}{<giá trị>}`; giá trị `None` → `\pending{<Tên>}`), `numbers.json` (cùng tên khóa, giá trị đã định dạng), bảng `tables/{lifecycle,rework,funnel,tasks,literature}.tex`, hình `figures/{lifecycle_by_week,rework_by_group}.pdf`.
- CLI `report-data build --root <repo> --out docs/report/generated`.

- [ ] Test trước với dữ liệu mẫu nhỏ trong `tests/fixtures/`: `test_number_uses_decimal_comma`, `test_percent_rounding`, `test_missing_source_gives_pending`, `test_numbers_tex_and_json_have_same_keys`, `test_funnel_matches_screening` (110 → 64 → 47 → 47 → 43 trên dữ liệu thật đọc từ repo khi có), `test_link_accuracy` (15/20).
- [ ] Cài đặt; `uv run report-data build --root ../../.. --out ../generated`; `latexmk` trong `docs/report` vẫn build.
- [ ] Commit `feat(report): generate numbers, tables and figures from result files`.

### Task 3: Mục 1–3 (giới thiệu, tổng quan tài liệu, câu hỏi nghiên cứu)

**Files:** Modify `docs/report/sections/{01-introduction,02-related-work,03-questions}.tex`.

- [ ] Mục 1 (khoảng 1,5 trang): bối cảnh coding agent; khoảng trống (không bài nào giữ nguyên đề bài, công cụ, mô hình và chỉ đổi lời dặn rồi chấm bằng test ẩn); giới thiệu ViPharmind trong hai câu trước khi dùng tên; đóng góp; bố cục báo cáo.
- [ ] Mục 2 (khoảng 3 trang): quy trình tìm có hệ thống (bảng `tables/literature.tex`); ba nhóm nguồn; đối chiếu riêng Hill ESEM 2026, FeatBench, Mock & Russo, Agarwal 2026; chỉ trích nguồn trong `references.bib` và chỉ nói điều ghi trong cột phát hiện của `literature-log.md`.
- [ ] Mục 3 (khoảng 0,5 trang): RQ1–RQ6 và H1–H4 nguyên văn ý từ bản thiết kế nghiên cứu; RQ6 ghi là khám phá.
- [ ] `bash check.sh --draft` → exit 0. Commit `docs(report): write the introduction, related work and research questions`.

### Task 4: Mục 4–5 (phương pháp, kết quả hồi cứu)

**Files:** Modify `docs/report/sections/{04-method,05-retrospective}.tex`, `appendix.tex`.

- [ ] Mục 4 (khoảng 4 trang): dữ liệu hồi cứu; phễu sàng lọc (`tables/funnel.tex`) và lấy mẫu phân tầng; cách duyệt đề (AI soạn, An duyệt gộp, ba mục yếu bị loại, tác tử đối chiếu mẫu); tầng tính năng (mục 7.2b); hai cách làm (lời dặn đầy đủ ở phụ lục); bộ chạy, bộ chấm (test ẩn, hồi quy, khôi phục test cũ, `pytest_config_touched`); chống rò rỉ (cây mã không có spec, plan cũ và file hướng dẫn; cấu hình sạch; thư mục ngẫu nhiên; không chạy song song hai lượt của cùng đề; bảng đối chiếu điều kiện ba công cụ lấy từ `docs/pilot-report.md` khi có, chưa có thì `\pending`); chỉ số; thống kê; chốt trước khi chạy.
- [ ] Mục 5 (khoảng 2 trang): bản đồ vòng đời (bảng và hình), giải thích vì sao khâu kiểm thử chiếm tỉ lệ lớn; 88,7% tính năng có plan và độ chính xác quy tắc 15/20 kèm cách kiểm (gợi ý AI, An đồng ý cả 20); mức sửa lại hai nhóm và câu "quan sát, không phải nhân quả"; nhật ký phiên không đầy đủ, số lần ngắt là số đo thay thế.
- [ ] Phụ lục: hai lời dặn nguyên văn (`\input` từ `code/prompts/*.md` qua `verbatim`), danh sách 15 + 2 + 3 đề (`tables/tasks.tex`).
- [ ] `bash check.sh --draft` → exit 0. Commit `docs(report): write the method and the retrospective results`.

### Task 5: Hướng dẫn và phiếu gán nhãn

**Files:** Create `docs/team/labeling/guide.md`, `docs/team/labeling/README.md`.

- [ ] `guide.md` tiếng Việt cho Lợi và Bảo: mục đích; họ nhận gì (log test, bản vá đã bỏ `docs/design.md` và `docs/plan.md`); bảng 7 nhãn khởi đầu (bản thiết kế nghiên cứu mục 7.6) mỗi nhãn một định nghĩa và một ví dụ dựng từ một đề thật trong `data/tasks/`; quy tắc khi một lượt có nhiều nguyên nhân (chọn nguyên nhân làm test hỏng đầu tiên); không trao đổi với nhau khi gán; cách nộp. `README.md`: phiếu `sheet.csv` sẽ được sinh sau chạy chính, cột `unit_id, label, note`.
- [ ] Commit `docs(team): add the failure-labeling guide`.

### Task 6: Báo cáo tiến độ (khi có kết quả chạy thử)

**Files:** Create `docs/report/progress.tex`.

- [ ] Chỉ làm khi `docs/pilot-report.md` và `data/results/raw/` của lượt chạy thử đã được commit trên nhánh `harness` (gộp vào nhánh `report`). PDF 3–4 trang: đề tài, việc đã làm (mục 1–5 rút gọn bằng cách `\input` lại các đoạn chính), kết quả chạy thử (bảng đạt/tổng theo nhóm và cách làm, kèm câu "chạy thử, chưa kết luận"), kế hoạch còn lại, câu hỏi xin góp ý thầy.
- [ ] Build sạch; commit `docs(report): add the progress report`.
