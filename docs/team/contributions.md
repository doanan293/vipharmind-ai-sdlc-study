# Bản kê đóng góp cá nhân

Học phần: Chuyên đề nghiên cứu 1 (IT5421). Giảng viên: TS. Nguyễn Thanh Hùng.
Đề tài: *Phát triển theo đặc tả so với vibe coding: nghiên cứu tình huống và thực nghiệm đối chứng trên
một dự án phần mềm AI cho ngành dược Việt Nam.*

| Thành viên | MSHV | Vai trò |
| --- | --- | --- |
| Doãn Văn An | 20252778M | Nhóm trưởng, điều phối và giao việc; thực hiện phần lớn nghiên cứu: thiết kế chính, dựng bộ nhiệm vụ, bộ chạy, chạy thí nghiệm, phân tích, viết báo cáo, làm slide (có trợ lý AI hỗ trợ, xem `docs/team/ai-use.md`) |
| Lê Xuân Lợi | 20252781M | **Phần bối cảnh và phương pháp:** kiểm tra trích dẫn; phản biện báo cáo mục 1–5, slide 1–13. Cùng Bảo: hỗ trợ chọn đề tài, góp ý thiết kế; đo lường bằng người (gán nhãn nguyên nhân thất bại, kiểm tra lượt đạt, chấm tay kiểm tra đối chứng người – máy trên đề sơ sài) |
| Trần Ngọc Bảo | 20251227M | **Phần kết quả:** kiểm tra độc lập số liệu chính; phản biện báo cáo mục 6–8, slide 14–30. Cùng Lợi: hỗ trợ chọn đề tài, góp ý thiết kế; đo lường bằng người (gán nhãn nguyên nhân thất bại, kiểm tra lượt đạt, chấm tay kiểm tra đối chứng người – máy trên đề sơ sài) |

Bản kê ghi đúng việc đã làm, không chia đều cho đẹp. Phần lớn khối lượng nghiên cứu do An làm. Đóng góp
của Lợi và Bảo tập trung ở các bước đo bằng người (gán nhãn, chấm tay, kiểm tra), kiểm tra độc lập
và phản biện. Gán nhãn là một bước đo của nghiên cứu: nó
cho số liệu kappa trong báo cáo, và nó chỉ có giá trị vì hai người gán không phải là người chạy thí nghiệm.

## 1. Đóng góp theo sản phẩm

Ký hiệu: **C** = làm chính; **H** = hỗ trợ, góp ý; **–** = không tham gia.

| Sản phẩm, công việc | An | Lợi | Bảo | Ghi chú |
| --- | --- | --- | --- | --- |
| Chọn đề tài, đăng ký nhóm | C | H | H | Lợi, Bảo cùng bàn và chọn đề tài |
| Thiết kế nghiên cứu (câu hỏi, giả thuyết, hai cách làm, tầng kích thước) | C | H | H | An thiết kế chính; Lợi, Bảo góp ý thiết kế |
| Đề cương 1–2 trang (`docs/proposal/`) | C | – | – | |
| Tổng quan tài liệu (tìm, mở, kiểm tra 24 nguồn; `docs/report/literature-log.md`) | C | – | – | AI hỗ trợ tìm kiếm; An kiểm tra |
| Phân tích hồi cứu ViPharmind (RQ1, RQ2; 505 commit, 43 file spec/plan) | C | – | – | Gồm kiểm tra tay 20 commit cho quy tắc nối |
| Sàng lọc và dựng bộ nhiệm vụ (110 → 43 commit; 15 + 5 + 3 nhiệm vụ) | C | – | – | Đề bài do AI soạn, An duyệt (xem `ai-use.md`) |
| Bộ chạy và bộ chấm (`code/harness/`) | C | – | – | Mã do AI viết theo kế hoạch An duyệt |
| Chạy thử, ruling R11, đăng ký trước (`prereg-v1`, `prereg-v1.1`, `prereg-v1-analysis`) | C | – | – | |
| Chạy chính (552 lượt dự kiến, 4 nhóm) | C | – | – | |
| Gói phân tích (`code/analysis/`) | C | – | – | Mã do AI viết; Fable 5.2 duyệt độc lập |
| Gán nhãn nguyên nhân thất bại (mù) | – | C | C | Hai người làm độc lập; An không gán, chỉ phân xử chỗ lệch |
| Phân xử nhãn lệch | C | – | – | An biết cách làm của từng lượt, nên nhãn sau phân xử không mù |
| Kiểm tra "đạt test nhưng sai" (20 lượt) | H | C | C | Lợi, Bảo mỗi người 10 lượt, mù cách làm; An giao việc và soát lại. Kết quả: 20/20 đúng thật |
| Chấm tay mẫu kiểm tra đối chứng người – máy (24 lượt đề sơ sài) | H | C | C | Hai người chấm độc lập, che cách làm, để đo mức khớp với người chấm máy; mẫu rút bằng mã theo hạt giống cố định; An giao việc. Xong 17/11: kappa Lợi–Bảo 0,93; người–máy 0,88 và 0,90. |
| Kiểm tra trích dẫn (24 nguồn) | H | C | – | Lợi đã tự mở lại 24 bài báo và đường link; đối chiếu tên tác giả, năm và các con số đưa vào báo cáo, xác nhận không có số liệu nào bị sai hay nói quá (xong 17/11, file `kiem-trich-dan.csv`) |
| Kiểm tra độc lập số liệu chính (tính lại bằng bảng tính) | H | – | C | Bảo tự kéo PivotTable trên Excel từ dữ liệu gốc `runs.csv` (không đụng vào code của nhóm); 18 ô tỉ lệ đạt khớp báo cáo; trung vị token tầng nhỏ (báo cáo không có bảng trung vị) cho thấy đặc tả tốn hơn vibe ở cả ba nhóm (×1,65–2,59), cùng chiều H2 (xong 17/11, file `kiem-so-lieu.csv`) |
| Báo cáo viết (`docs/report/`) | C | H | H | Lợi phản biện mục 1–5, Bảo mục 6–8; các góp ý về cách dùng từ, ví dụ thực tế và cách đọc số liệu đã được sửa theo trao đổi ở `phan-viec.md` mục 4 |
| Slide và speaker notes (`docs/presentation/`) | C | H | H | Lợi góp ý slide 1–13, Bảo slide 14–30; cả ba cùng rà soát nội dung slide (`phan-viec.md` mục 4) |
| Thuyết trình trên lớp | – | – | – | Chưa phân công người nói; cả ba thành viên cùng nắm toàn bộ nội dung để sẵn sàng trình bày |
| Chuẩn bị hỏi đáp | C | H | H | An soạn `qa-prep.md`; Lợi ôn nhóm A–F, J, M; Bảo ôn nhóm G–L, N |
| Điều phối, phân việc (`docs/team/phan-viec.md`) | C | – | – | |
| Tài liệu nhóm (`docs/team/`) | C | H | H | Phiếu đánh giá chéo do từng người tự điền |

## 2. Chi tiết từng người

### Doãn Văn An

- Thiết kế nghiên cứu: câu hỏi RQ1–RQ6, giả thuyết H1–H5, hai cách làm, ba tầng kích thước, bốn nhóm chạy
  (Lợi, Bảo góp ý).
- Tổng quan tài liệu: quy trình tìm có ghi lại (47 → 31 → 18 nguồn mới, cộng 6 nguồn cũ; 24 nguồn trong
  `references.bib`).
- Phân tích hồi cứu ViPharmind: bản đồ vòng đời, dấu vết spec/plan, mức sửa lại, kiểm tra tay 20 commit.
- Bộ nhiệm vụ: phễu sàng lọc 110 → 64 → 47 → 47 → 43; lấy mẫu phân tầng 15 nhiệm vụ nhỏ; quy tắc chọn
  tầng vừa (93 cửa sổ → 21 hợp lệ → 5); tầng lớn f08, f14, f15. Duyệt đề bài (duyệt gộp, xem
  `ai-use.md` mục 3).
- Bộ chạy, bộ chấm, chạy thử 2 nhiệm vụ, các quyết định sau chạy thử (ruling R11: không proxy, agent mặc
  định, mạng mở).
- Đăng ký trước và mọi thay đổi sau thẻ (mục 11 của `prereg-v1.md`).
- Vận hành lượt chạy chính (2026-11-15 đến 2026-11-16): 414 lượt hợp lệ của ba nhóm (138 mỗi nhóm); 0 lượt
  hết giờ, thoát lỗi hay bị loại vì lỗi bộ chạy. `agy-gemini` bị bỏ ở 73/138 lượt vì cả bốn tài khoản hết hạn
  mức (báo cáo mục 4.2). Thí nghiệm thăm dò: E1 (Haiku) 138/138 lượt hợp lệ; E2 kết thúc thu thập tối
  2026-11-16 (lượt đề sơ sài cuối bắt đầu 22:46, mốc báo cáo dùng; chạy và chấm xong 23:18), ba nhóm Claude
  đủ 414 lượt đề sơ sài, Codex dừng ở 78/90 lượt tầng nhỏ vì hết hạn mức (mục 4.6).
- Gói phân tích, báo cáo, slide, tài liệu nhóm.
- Phân xử nhãn lệch; dựng gói và soát lại kiểm tra "đạt test nhưng sai".
- Điều phối nhóm và duyệt cuối báo cáo, slide (`phan-viec.md` mục 1).

### Lê Xuân Lợi

- Hỗ trợ chọn đề tài và góp ý thiết kế nghiên cứu.
- Gán nhãn độc lập 30 lượt không đạt của hai nhóm Claude, theo `docs/prereg/labeling-guide.md`,
  không trao đổi với Bảo cho tới khi có kappa.
- Kiểm tra "đạt test nhưng sai": đối chiếu mù 10 lượt đạt (5 đặc tả, 5 vibe) với bản vá gốc; 10/10 đúng thật.
- Kiểm tra trích dẫn: đã tự mở từng link của cả 24 tài liệu; đối chiếu tên bài, tác giả, năm và từng con số trích dẫn trong bài (số nhiệm vụ, tỉ lệ giải quyết, mức chênh lệch năng suất). Toàn bộ 24 nguồn đều vào được và số liệu trích dẫn đúng với bài gốc (xong 17/11, xem `kiem-trich-dan.csv`).
- Ôn hỏi đáp nhóm A–F, J, M trong `qa-prep.md`.
- Chấm tay mẫu kiểm tra đối chứng người – máy (24 lượt đề sơ sài), độc lập với Bảo: xong 17/11, 282 mục; khớp với Bảo kappa 0,93, với người chấm máy kappa 0,88.
- Góp ý cho slide và báo cáo: đã đọc kỹ phần bối cảnh, phương pháp (mục 1–5) và rà soát slide 1–13; góp ý thống nhất cách gọi bản vá, giải thích thêm về lỗi phần mềm dược (xem `phan-viec.md` mục 4).

### Trần Ngọc Bảo

- Hỗ trợ chọn đề tài và góp ý thiết kế nghiên cứu.
- Gán nhãn độc lập 30 lượt không đạt của hai nhóm Claude, cùng tập lượt và cùng quy tắc như
  Lợi.
- Kiểm tra "đạt test nhưng sai": đối chiếu mù 10 lượt đạt (5 đặc tả, 5 vibe) với bản vá gốc; 10/10 đúng thật.
- Kiểm tra độc lập số liệu chính: tự lập bảng Pivot trên Excel từ dữ liệu thô `runs.csv` mà không chạy code phân tích có sẵn của nhóm. Số lượt đạt ở cả 18 ô (3 mô hình × 3 cỡ nhiệm vụ × 2 cách làm) khớp bảng ở mục 6 báo cáo; trung vị token tầng nhỏ (báo cáo không có bảng trung vị) cho thấy đặc tả tốn hơn vibe ở cả ba nhóm (×1,65–2,59), cùng chiều H2 (xong 17/11, xem `kiem-so-lieu.csv`).
- Ôn hỏi đáp nhóm G–L, N trong `qa-prep.md`.
- Chấm tay mẫu kiểm tra đối chứng người – máy (24 lượt đề sơ sài), độc lập với Lợi: xong 17/11, 282 mục; khớp với Lợi kappa 0,93, với người chấm máy kappa 0,90.
- Góp ý cho slide và báo cáo: đã đọc phản biện mục 6–8 và rà soát phần slide kết quả (14–30); góp ý giữ cách diễn giải cẩn trọng khi khoảng tin cậy chứa 0, lưu ý riêng về nhóm Codex tầng lớn (xem `phan-viec.md` mục 4).

## 3. Số liệu gán nhãn (vòng 2)

| Mục | Giá trị |
| --- | --- |
| Số lượt cần gán (lượt hợp lệ không đạt của `claude-sonnet` và `claude-opus`, ba tầng) | 30 (17 đặc tả, 13 vibe) |
| Số lượt Lợi đã gán | 30 (vòng 2) |
| Số lượt Bảo đã gán | 30 (vòng 2) |
| Kappa của Cohen | 0,95 (đồng ý 29/30) |
| Số lượt lệch nhãn, An phân xử | 1 (t07, phân xử là `de_bai_thieu`) |
| Tỉ lệ lượt ghi "lộ cách làm" | 2/30 (Bảo ghi ở 2 lượt f15 vì docstring nhắc "spec"; Lợi không ghi) |

Vòng 1 bị loại theo đề nghị của Lợi và Bảo vì điền chưa kỹ; vòng 2 gán lại cả 30 lượt với mã mới, kèm mã
nguồn test ẩn và thứ tự quyết định cố định (ghi ở mục 11 của `prereg-v1.md`).

## 4. Đề xuất về điểm cá nhân

Tiêu chí của thầy cho phép điều chỉnh điểm cá nhân. Nhóm không tự đề xuất hệ số; bản kê này và phiếu đánh
giá chéo (`docs/team/peer-review.md`) là căn cứ để thầy quyết định. [Nhóm thống nhất trước buổi nộp nếu muốn
ghi thêm đề xuất.]

## 5. Xác nhận

Ba thành viên đã đọc bản kê này và xác nhận nó đúng với việc đã làm.

| Thành viên | Ngày | Xác nhận |
| --- | --- | --- |
| Doãn Văn An | 17/11/2026 | Đã xác nhận |
| Lê Xuân Lợi | 17/11/2026 | Đã xác nhận |
| Trần Ngọc Bảo | 17/11/2026 | Đã xác nhận |
