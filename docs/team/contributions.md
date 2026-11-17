# Bản kê đóng góp cá nhân

Học phần: Chuyên đề nghiên cứu 1 (IT5421). Giảng viên: TS. Nguyễn Thanh Hùng.
Đề tài: *Phát triển theo đặc tả so với vibe coding: nghiên cứu tình huống và thực nghiệm đối chứng trên
một dự án phần mềm AI cho ngành dược Việt Nam.*

| Thành viên | MSHV | Vai trò |
| --- | --- | --- |
| Doãn Văn An | 20252778M | Nhóm trưởng, điều phối và giao việc; thực hiện phần lớn nghiên cứu: thiết kế, dựng bộ nhiệm vụ, bộ chạy, chạy thí nghiệm, phân tích, viết báo cáo, làm slide (có trợ lý AI hỗ trợ, xem `docs/team/ai-use.md`) |
| Lê Xuân Lợi | 20252781M | Phần bối cảnh và phương pháp: kiểm tra trích dẫn; gán nhãn mù nguyên nhân thất bại, kiểm tra lượt đạt, chấm tay E2; trả lời câu hỏi |
| Trần Ngọc Bảo | 20251227M | Phần kết quả: tính lại độc lập số liệu chính; gán nhãn mù nguyên nhân thất bại, kiểm tra lượt đạt, chấm tay E2; trả lời câu hỏi |

Bản kê ghi đúng việc đã làm, không chia đều cho đẹp. Phần lớn khối lượng nghiên cứu do An làm. Đóng góp
của Lợi và Bảo tập trung ở các bước đo bằng người (gán nhãn, chấm tay), kiểm tra độc lập và hỏi đáp. Gán nhãn là một bước đo của nghiên cứu: nó
cho số liệu kappa trong báo cáo, và nó chỉ có giá trị vì hai người gán không phải là người chạy thí nghiệm.

Chỗ ghi **[CHỜ KẾT QUẢ]** được điền sau khi chạy chính, gán nhãn và tập dượt xong. Chỗ ghi **[An điền]**
là số liệu An cung cấp.

## 1. Đóng góp theo sản phẩm

Ký hiệu: **C** = làm chính; **H** = hỗ trợ, góp ý; **–** = không tham gia.

| Sản phẩm, công việc | An | Lợi | Bảo | Ghi chú |
| --- | --- | --- | --- | --- |
| Chọn đề tài, đăng ký nhóm | C | H | H | Lợi, Bảo đồng ý đề tài [An xác nhận mức H] |
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
| Báo cáo viết (`docs/report/`) | C | H | H | Lợi, Bảo đọc bản nháp và góp ý [CHỜ KẾT QUẢ: ghi có hay không] |
| Slide và speaker notes (`docs/presentation/`) | C | H | H | Lợi, Bảo góp ý lời nói phần mình [CHỜ KẾT QUẢ] |
| Tập dượt thuyết trình | H | C | C | |
| Thuyết trình trên lớp | – | C | C | An không nói trong 15 phút, có mặt để hỗ trợ hỏi đáp [An xác nhận] |
| Trả lời câu hỏi | H | C | C | Theo phân công trong `qa-prep.md` |
| Tài liệu nhóm (`docs/team/`) | C | H | H | Phiếu đánh giá chéo do từng người tự điền |

## 2. Chi tiết từng người

### Doãn Văn An

- Thiết kế nghiên cứu: câu hỏi RQ1–RQ6, giả thuyết H1–H5, hai cách làm, ba tầng kích thước, bốn nhóm chạy.
- Tổng quan tài liệu: quy trình tìm có ghi lại (47 → 31 → 18 nguồn mới, cộng 6 nguồn cũ; 24 nguồn trong
  `references.bib`).
- Phân tích hồi cứu ViPharmind: bản đồ vòng đời, dấu vết spec/plan, mức sửa lại, kiểm tra tay 20 commit.
- Bộ nhiệm vụ: phễu sàng lọc 110 → 64 → 47 → 47 → 43; lấy mẫu phân tầng 15 nhiệm vụ nhỏ; quy tắc chọn
  tầng vừa (93 cửa sổ → 21 hợp lệ → 5); tầng lớn f08, f14, f15. Duyệt đề bài (duyệt gộp, xem
  `ai-use.md` mục 3).
- Bộ chạy, bộ chấm, chạy thử 2 nhiệm vụ, các quyết định sau chạy thử (ruling R11: không proxy, agent mặc
  định, mạng mở).
- Đăng ký trước và mọi thay đổi sau thẻ (mục 11 của `prereg-v1.md`).
- Vận hành lượt chạy chính: [CHỜ KẾT QUẢ: số lượt hợp lệ, số lượt lỗi, ngày kết thúc].
- Gói phân tích, báo cáo, slide, tài liệu nhóm.
- Phân xử nhãn lệch; dựng gói và soát lại kiểm tra "đạt test nhưng sai".
- Thời gian ước tính: [An điền] giờ.

### Lê Xuân Lợi

- Gán nhãn độc lập 30 lượt không đạt của hai nhóm Claude, theo `docs/prereg/labeling-guide.md`,
  không trao đổi với Bảo cho tới khi có kappa.
- Kiểm tra "đạt test nhưng sai": đối chiếu mù 10 lượt đạt (5 đặc tả, 5 vibe) với bản vá gốc; 10/10 đúng thật.
- Thuyết trình khoảng 7 phút: vấn đề và câu hỏi nghiên cứu, ViPharmind, tổng quan ngắn, phương pháp
  (bộ đề, hai cách làm, chống rò rỉ), kết quả hồi cứu.
- Chuẩn bị và trả lời các nhóm câu hỏi được giao trong `qa-prep.md`.
- Số buổi tập dượt: [CHỜ KẾT QUẢ]. Góp ý cho slide hoặc báo cáo: [CHỜ KẾT QUẢ: ghi cụ thể nếu có].
- Thời gian ước tính: [Lợi điền] giờ.

### Trần Ngọc Bảo

- Gán nhãn độc lập 30 lượt không đạt của hai nhóm Claude, cùng tập lượt và cùng quy tắc như
  Lợi.
- Kiểm tra "đạt test nhưng sai": đối chiếu mù 10 lượt đạt (5 đặc tả, 5 vibe) với bản vá gốc; 10/10 đúng thật.
- Thuyết trình khoảng 7 phút: kết quả thí nghiệm, Sonnet so với Opus, ba công cụ, đề nhỏ và đề lớn, phân
  loại lỗi, hạn chế, kết luận.
- Chuẩn bị và trả lời các nhóm câu hỏi được giao trong `qa-prep.md`.
- Số buổi tập dượt: [CHỜ KẾT QUẢ]. Góp ý cho slide hoặc báo cáo: [CHỜ KẾT QUẢ: ghi cụ thể nếu có].
- Thời gian ước tính: [Bảo điền] giờ.

## 3. Số liệu gán nhãn (điền sau khi gán)

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
| Doãn Văn An | | |
| Lê Xuân Lợi | | |
| Trần Ngọc Bảo | | |
