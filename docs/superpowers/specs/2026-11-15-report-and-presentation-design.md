# Thiết kế báo cáo, bài thuyết trình và tài liệu nhóm

Ngày: 2026-11-15. Đề bài của môn: `2026-11-15-course-brief.md`. Nghiên cứu được báo cáo:
`2026-11-15-spec-vs-vibe-study-design.md` (gọi tắt "bản thiết kế nghiên cứu").

## 1. Ý định

Nộp đủ bộ sản phẩm thầy yêu cầu cho đề tài "Phát triển theo đặc tả so với vibe coding: nghiên cứu tình
huống và thực nghiệm đối chứng trên một dự án phần mềm AI cho ngành dược Việt Nam", nhắm điểm A+. Bố cục
bám từng dòng tiêu chí chấm: hiểu vấn đề và tổng quan (20%), phương pháp (20%), kết quả và phân tích
phản biện (25%), báo cáo viết (10%), thuyết trình và hỏi đáp (15%), làm việc nhóm (10%).

Môn: Chuyên đề nghiên cứu 1, mã học phần IT5421. Giảng viên: TS. Nguyễn Thanh Hùng. Trang bìa chỉ có chữ
(chưa có logo trường); slide giữ một slide ghi nguồn Slidesgo cho tới khi An xác nhận có Premium.

Nhóm:

- **Doãn Văn An (20252778M)**, nhóm trưởng: điều phối và giao việc; thiết kế nghiên cứu, xây bộ đề, dựng
  bộ chạy và bộ chấm, chạy thực nghiệm, phân tích thống kê, viết báo cáo, làm slide.
- **Lê Xuân Lợi (20252781M)**, phần tổng quan và phương pháp: kiểm tra 24 nguồn tham khảo, kiểm tra quy
  tắc nối plan, gán nhãn nguyên nhân thất bại và chấm tay đối chiếu máy chấm; thuyết trình vấn đề,
  phương pháp, kết quả hồi cứu.
- **Trần Ngọc Bảo (20251227M)**, phần kết quả: tính lại độc lập số liệu chính, kiểm tra quy tắc nối
  plan, gán nhãn nguyên nhân thất bại và chấm tay đối chiếu máy chấm; thuyết trình kết quả thí nghiệm,
  hạn chế, kết luận.

## 2. Mục tiêu, ngoài phạm vi, điều phải tránh

**Mục tiêu**

- Báo cáo tiếng Việt 15–20 trang (không tính phụ lục), PDF build sạch từ LaTeX.
- Bài thuyết trình tiếng Việt 15 phút cho hai người nói, cộng 5 phút hỏi đáp, file PPTX và PDF dự phòng.
- Tài liệu nhóm: bản kê đóng góp, mẫu đánh giá chéo, khai báo sử dụng AI, tài liệu chuẩn bị hỏi đáp,
  hướng dẫn và phiếu gán nhãn.
- Mọi con số trong báo cáo và slide lấy từ file kết quả bằng máy, không gõ tay.

**Ngoài phạm vi**

- Không viết lại nội dung bài báo SoICT; chất lượng trả lời của ViPharmind tối đa một đoạn bối cảnh.
- Không làm báo cáo tiếng Anh, không làm poster.

**Điều phải tránh**

- Con số trong văn bản lệch file kết quả; kết luận mạnh hơn số liệu (nhất là tầng tính năng, chỉ 3 đề).
- Che giấu cách làm thật: đề bài do AI soạn và được duyệt gộp; kiểm tra quy tắc nối có gợi ý của AI;
  AI tham gia viết báo cáo và slide. Tất cả phải nằm trong báo cáo và khai báo sử dụng AI.
- Slide khác báo cáo về số liệu, tên mô hình, thuật ngữ.

## 3. Ràng buộc

- Báo cáo viết bằng LaTeX (An chọn, khoa không có mẫu bắt buộc), build bằng `latexmk` + XeLaTeX, phông
  Times New Roman 12pt, A4, giống kiểu đề cương `proposal/`.
- Slide làm trên template `docs/presentation/template-vi.pptx` (Slidesgo "Introduction to Coding
  Workshop", 16:9). Bản miễn phí bắt buộc giữ slide ghi nguồn Slidesgo; giữ một slide ghi nguồn ở cuối
  phần dự phòng trừ khi An xác nhận có tài khoản Premium.
- Nguồn tham khảo: chỉ dùng mục đã kiểm tra trong `docs/report/references.bib` (24 nguồn) cộng nguồn mới
  được kiểm tra theo cùng quy trình (`docs/report/literature-log.md`).
- Kết quả thí nghiệm chính chưa có: phần phụ thuộc kết quả viết sau khi chạy xong và sau thẻ
  `prereg-v1`.
- Commit không có dòng ghi công AI (quy ước của An cho các repo này).

## 4. Các cách đã cân nhắc

| Phần | Cách | Được | Mất | Chọn |
| --- | --- | --- | --- | --- |
| Số liệu trong báo cáo | **A. Sinh tự động**: script đọc `results/`, `retrospective/out/`, sinh bảng `.tex`, hình `.pdf` và file macro số liệu; văn bản chỉ gọi macro | Không lệch số; chạy lại phân tích là báo cáo tự cập nhật; kiểm tra được bằng máy | Thêm một phần việc dựng script | **A** (An đồng ý) |
| | B. Gõ tay | Nhanh lúc đầu | Dễ lệch số, đúng chỗ thầy chấm nặng | |
| Slide | **ppt-master trên `template-vi.pptx`** | Đúng template An chọn; giống quy trình bài SoICT; ra PPTX sửa tay được | Phải dọn 51 slide mẫu | **ppt-master** (An đồng ý) |
| | Beamer | Chung công cụ với báo cáo | Bỏ template của An | |

## 5. Thiết kế

### 5.1 Báo cáo (`docs/report/`)

**Bố cục**, khoảng 18 trang:

| # | Mục | Tiêu chí chấm | Trang | Viết khi nào |
| --- | --- | --- | --- | --- |
| 0 | Trang bìa (tên đề tài, môn, giảng viên, ba thành viên và mã), tóm tắt 200 từ, mục lục | Báo cáo viết | 1–2 | ngay, tóm tắt viết cuối |
| 1 | Giới thiệu: bối cảnh coding agent, khoảng trống, giới thiệu ViPharmind, đóng góp | Hiểu vấn đề | 1,5 | ngay |
| 2 | Tổng quan tài liệu: quy trình tìm có hệ thống (truy vấn, số bài qua từng bước), ba nhóm nguồn, khoảng trống mà đề tài lấp (đối chiếu Hill ESEM 2026, FeatBench, Mock & Russo) | Tổng quan | 3 | ngay |
| 3 | Câu hỏi nghiên cứu RQ1–RQ6 và giả thuyết H1–H4 | Hiểu vấn đề | 0,5 | ngay |
| 4 | Phương pháp: dữ liệu hồi cứu; xây bộ đề (phễu sàng lọc 110 → 43, tiêu chí, lấy mẫu phân tầng, duyệt đề); tầng tính năng; hai cách làm; bộ chạy và bộ chấm; chống rò rỉ và bảng đối chiếu điều kiện ba công cụ; chỉ số; thống kê; chốt trước khi chạy | Phương pháp | 4 | ngay (cập nhật sau chạy thử) |
| 5 | Kết quả hồi cứu (RQ1, RQ2): bản đồ vòng đời, 88,7% tính năng có plan, độ chính xác quy tắc nối 15/20, mức sửa lại, nhật ký phiên | Kết quả | 2 | ngay |
| 6 | Kết quả thí nghiệm (RQ3–RQ6): bảng chính, hiệu số và khoảng tin cậy, 2 × 2 Sonnet–Opus, ba công cụ, theo kích thước và tầng tính năng, chi phí, phân loại lỗi và kappa | Kết quả | 4 | sau chạy chính |
| 7 | Thảo luận và hạn chế: trả lời từng RQ, đối chiếu tài liệu, mối đe dọa đến tính hợp lệ (nội, ngoại, cấu trúc, kết luận) | Phân tích phản biện | 2 | sau chạy chính |
| 8 | Kết luận và hướng tiếp | | 0,5 | cuối |
| PL | Phụ lục: hai lời dặn nguyên văn, danh sách 15 + 3 đề, bảng đối chiếu điều kiện, khai báo sử dụng AI, bản kê đóng góp | | ngoài 20 trang | dần dần |

**Cấu trúc thư mục**

```
docs/report/
  main.tex, .latexmkrc, README.md, check.sh
  sections/*.tex          một file mỗi mục
  generated/              do script sinh, có commit: numbers.tex (macro \num...), tables/*.tex, figures/*.pdf
  scripts/                sinh generated/ từ results/ và retrospective/out/
  references.bib, literature-log.md (đã có)
```

**Số liệu sinh tự động.** Một gói Python nhỏ (`docs/report/scripts`, chạy bằng `uv`) đọc kết quả thô và
kết quả hồi cứu, sinh `generated/numbers.tex` gồm macro có tên rõ nghĩa (ví dụ
`\newcommand{\NumFeatWithPlanPct}{88,7}`), các bảng `booktabs` và hình `pdf` (matplotlib). Văn bản chỉ
dùng macro, không gõ số. `check.sh` của báo cáo kiểm: số trang 15–20 (không tính phụ lục), build không
warning, không còn `TODO`, mọi macro được định nghĩa, mọi `\cite` có trong `references.bib`.

**Văn phong.** Tiếng Việt khoa học, câu ngắn, không thổi phồng; thuật ngữ "vibe coding", "coding agent",
tên công cụ và mô hình giữ tiếng Anh. Số thập phân dùng dấu phẩy.

### 5.2 Bài thuyết trình (`docs/presentation/`)

- Công cụ: ppt-master, template `template-vi.pptx`. Khoảng 14 slide nội dung, 1 slide cảm ơn, 4–6 slide
  dự phòng cho hỏi đáp, slide ghi nguồn Slidesgo ở cuối.
- Lời nói tiếng Việt trong speaker notes của từng slide; thời lượng từng slide ghi trong
  `docs/presentation/rehearsal.md`.
- Chia người nói:
  - **Lê Xuân Lợi (khoảng 7 phút):** vấn đề và câu hỏi nghiên cứu, ViPharmind, tổng quan ngắn, phương
    pháp (bộ đề, hai cách làm, chống rò rỉ), kết quả hồi cứu.
  - **Trần Ngọc Bảo (khoảng 7 phút):** kết quả thí nghiệm, Sonnet–Opus, ba công cụ, đề nhỏ và đề lớn,
    phân loại lỗi, hạn chế, kết luận.
- Quy tắc cao nhất: mọi con số, tên mô hình và tuyên bố trên slide khớp báo cáo; số lấy từ cùng
  `generated/numbers.tex` hoặc file JSON tương đương do cùng script sinh.

### 5.3 Tài liệu nhóm (`team/`)

| File | Nội dung |
| --- | --- |
| `contributions.md` | Bản kê đóng góp đúng thực tế, theo từng sản phẩm và từng người |
| `peer-review.md` | Mẫu đánh giá chéo, ba người chấm lẫn nhau theo tiêu chí của thầy |
| `ai-use.md` | Khai báo sử dụng AI đầy đủ: làm ViPharmind, dựng bộ chạy và bộ chấm, soạn đề bài (duyệt gộp), gợi ý kiểm tra quy tắc nối, viết báo cáo và slide, AI là đối tượng được đo |
| `qa-prep.md` | Khoảng 25 câu thầy dễ hỏi, mỗi câu có câu trả lời 2–4 câu và con số dẫn chứng; chia theo phần của từng người nói |
| `labeling/guide.md`, `labeling/sheet.csv` | Hướng dẫn gán nhãn nguyên nhân thất bại kèm ví dụ cho từng nhãn, phiếu gán nhãn cho hai người, cách tính kappa (bản thiết kế nghiên cứu mục 7.6) |

### 5.4 Thứ tự làm

1. Khung báo cáo, script số liệu, `check.sh`; viết mục 1–5 (không cần kết quả chính).
2. Báo cáo tiến độ cho thầy (mốc thứ ba) từ mục 1–5 và kết quả chạy thử.
3. Tài liệu gán nhãn và buổi tập gán nhãn trên lượt chạy thử.
4. Sau chạy chính: mục 6–8, tóm tắt, phụ lục.
5. Slide và speaker notes; tài liệu hỏi đáp; tập dượt theo `rehearsal.md`.
6. Bản kê đóng góp, đánh giá chéo, khai báo AI ở dạng cuối.

## 5.5 Quyết định chi tiết (sau lượt đọc kiểm tra của người làm)

Đánh dấu "(lựa chọn của trợ lý)" là quyết định do trợ lý đưa ra, An kiểm lại khi đọc.

- **Nguồn số liệu thí nghiệm** (lựa chọn của trợ lý): định dạng kết quả thô của bộ chạy
  (`results/raw/<cohort>/<task>/<arm>-r<rep>/` với `grade.json`, `meta.json`) được coi là cố định từ
  thẻ `prereg-v1`. Script báo cáo được dựng và kiểm thử ngay bằng kết quả chạy thử làm dữ liệu mẫu.
- **Nơi tính thống kê** (lựa chọn của trợ lý): khoảng tin cậy bootstrap, hiệu số, kappa tính trong một
  gói phân tích riêng `analysis/` (đúng chỗ `results/analysis/` của bản thiết kế nghiên cứu, có kế
  hoạch riêng). Gói đó xuất `results/analysis/summary.json`. Script báo cáo chỉ đọc file này và kết quả
  hồi cứu rồi định dạng; không tự tính thống kê.
- **Số liệu cho slide** (lựa chọn của trợ lý): script báo cáo sinh cùng lúc `generated/numbers.tex` và
  `generated/numbers.json` từ một nguồn. Bước dựng slide chèn số từ `numbers.json`; một script kiểm
  tra đọc chữ trong PPTX và báo mọi con số trên slide không có trong `numbers.json`.
- **Chỗ chờ kết quả** (lựa chọn của trợ lý): macro `\pending{...}` hiện "[chờ kết quả]". `check.sh
  --draft` cho phép macro này; `check.sh` (bản nộp) báo lỗi nếu còn. Báo cáo tiến độ là một PDF ngắn
  (`docs/report/progress.tex`) dựng từ chính các mục 1–5 và kết quả chạy thử.
- **Nguồn sự thật đã có:** quy trình tìm tài liệu và số bài qua từng bước ở
  `docs/report/literature-log.md` (47 → 31 → 18 nguồn mới, cộng 6 nguồn cũ); phễu sàng lọc
  110 → 43 ở `tasks/SCREENING.md`; số liệu ViPharmind và hồi cứu ở `retrospective/out/summary.md` (nhánh
  `retrospective`, sẽ gộp vào `main`).
- **Tài liệu nhóm** nằm ở `team/` gốc repo, như bản thiết kế nghiên cứu mục 8. Đóng góp của Lợi và Bảo
  ghi theo việc thật: số lượt đã gán nhãn, số buổi tập dượt; An cung cấp số liệu này khi xong. Phiếu
  đánh giá chéo do từng thành viên tự điền, trợ lý chỉ soạn mẫu.
- **Đếm trang** (lựa chọn của trợ lý): 15–20 trang tính từ mục 1 đến hết mục 8; trang bìa, tóm tắt,
  mục lục, tài liệu tham khảo và phụ lục không tính. `check.sh` đếm theo nhãn đầu mục 1 và cuối mục 8.

## 6. Phần để người thực hiện tự quyết

- Tên macro, tên file trong `generated/`, kiểu hình (giữ đơn giản, đọc được khi in đen trắng).
- Cách gói script số liệu (một CLI `report-data build` là đủ).
- Chọn layout cụ thể trong template cho từng slide.
- Mẫu trang bìa: tự thiết kế đơn giản, chỉ có chữ; thêm logo nếu An gửi sau.
