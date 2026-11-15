# Đề bài môn Chuyên đề nghiên cứu 1

Chủ đề chung của môn: AI trong công nghệ phần mềm. Nội dung dưới đây chép lại từ slide của thầy
(chụp ngày 2026-11-15). Các đề tài A–F là gợi ý, không bắt buộc chọn đúng một mã.

## Đề tài gợi ý

### Hướng A · Yêu cầu và thiết kế

| Mã | Đề tài | Việc cần làm và kết quả kỳ vọng |
| --- | --- | --- |
| A1 | Dùng AI phát hiện mơ hồ, thiếu sót, mâu thuẫn trong tài liệu đặc tả yêu cầu | So sánh kết quả của công cụ với đánh giá của người có chuyên môn trên một bộ tài liệu đặc tả công khai; đo tỉ lệ phát hiện đúng và bỏ sót |
| A2 | Sinh user story và tiêu chí chấp nhận từ tài liệu nghiệp vụ | Đánh giá chất lượng theo tiêu chí INVEST; so sánh giữa các công cụ và với bản do người viết |
| A3 | Sinh mô hình UML, ERD từ mô tả bằng ngôn ngữ tự nhiên | Sinh sơ đồ (PlantUML, Mermaid) cho 5–10 bài toán; đo độ đúng và đủ so với lời giải mẫu |
| A4 | AI hỗ trợ lựa chọn kiến trúc và ghi lại quyết định thiết kế | Thử trên 2–3 hệ thống mẫu; phân tích chất lượng lập luận đánh đổi, điểm mạnh và điểm mù của công cụ |
| A5 | Từ bản thiết kế giao diện đến mã nguồn | So sánh các công cụ chuyển bản thiết kế hoặc ảnh chụp màn hình thành mã giao diện; đo độ giống và chất lượng mã |

Phù hợp với học viên mạnh về phân tích thiết kế hệ thống. Khó khăn chung: nhóm phải tự xây lời giải
chuẩn để chấm.

### Hướng B · Sinh mã và trợ lý lập trình

| Mã | Đề tài | Việc cần làm và kết quả kỳ vọng |
| --- | --- | --- |
| B1 | So sánh các trợ lý lập trình trên cùng một bộ nhiệm vụ thực tế | Chọn 3–4 công cụ, 15–20 nhiệm vụ; đo tỉ lệ làm đúng, thời gian, số lần người phải can thiệp, chi phí |
| B2 | Giao việc cho coding agent: công cụ tự xử lý báo cáo lỗi đến đâu? | Dùng một công cụ có sẵn trên các issue thật của một dự án mã nguồn mở; thống kê tỉ lệ thành công, phân loại nguyên nhân thất bại |
| B3 | Phát triển theo đặc tả so với "vibe coding" | Xây cùng một ứng dụng nhỏ theo hai cách; so sánh chất lượng mã, độ phủ test, khả năng bảo trì |
| B4 | Ảnh hưởng của cách mô tả yêu cầu tới chất lượng mã AI sinh ra | So sánh mô tả sơ sài, mô tả chi tiết, có kèm tài liệu và quy ước dự án; đo tỉ lệ đạt test và số lần phải sửa |
| B5 | Sinh mã backend từ lược đồ cơ sở dữ liệu và đặc tả API | So sánh công cụ AI với công cụ sinh mã truyền thống (scaffolding, ORM); đo độ đúng, độ đầy đủ, công sức chỉnh sửa |

Yêu cầu chung: bộ nhiệm vụ cố định trước khi chạy, tiêu chí đạt khách quan (test tự động), mỗi nhiệm
vụ chạy lặp nhiều lần.

### Hướng C · Kiểm thử và chất lượng mã

| Mã | Đề tài | Việc cần làm và kết quả kỳ vọng |
| --- | --- | --- |
| C1 | Sinh unit test tự động bằng AI | So sánh với công cụ sinh test truyền thống (EvoSuite, Pynguin) trên dự án mã nguồn mở; đo coverage và mutation score |
| C2 | Sinh test API và test giao diện từ đặc tả | Sinh test từ đặc tả OpenAPI hoặc kịch bản người dùng (Playwright); đo tỉ lệ chạy được và số lỗi phát hiện |
| C3 | Review mã tự động bằng AI so với người review | Chạy công cụ trên các pull request đã có nhận xét của người; đo mức trùng khớp và tỉ lệ cảnh báo nhiễu |
| C4 | Phát hiện code smell và tái cấu trúc mã tự động | So sánh công cụ AI với SonarQube; dùng bộ test để kiểm tra việc tái cấu trúc có giữ nguyên hành vi |
| C5 | Sinh ca kiểm thử từ tài liệu yêu cầu | Sinh ca kiểm thử chức năng từ đặc tả; đo độ phủ yêu cầu, so sánh với bộ ca kiểm thử do kiểm thử viên viết |

Thuận lợi: chỉ số đo rõ ràng, công cụ đối chứng miễn phí. Công cụ mutation testing gợi ý: PIT (Java),
mutmut (Python).

### Hướng D · Gỡ lỗi, bảo trì và tiến hoá

| Mã | Đề tài | Việc cần làm và kết quả kỳ vọng |
| --- | --- | --- |
| D1 | Sửa lỗi tự động bằng AI | Chạy trên các bộ lỗi chuẩn (Defects4J, BugsInPy, QuixBugs); đo tỉ lệ vá đúng; phân tích các bản vá đạt test nhưng sai |
| D2 | Định vị lỗi từ log, thông báo lỗi và báo cáo lỗi | So sánh công cụ AI với kỹ thuật định vị lỗi truyền thống; đo tỉ lệ chỉ đúng vị trí trong 1 và 5 gợi ý đầu |
| D3 | Hiện đại hoá hệ thống cũ bằng AI | Chuyển đổi mã hoặc nâng cấp phiên bản (ví dụ Java 8 lên 21, Python 2 lên 3); đo tỉ lệ biên dịch được và đạt test |
| D4 | Sinh và duy trì tài liệu kỹ thuật, commit message | Đánh giá độ chính xác và đầy đủ bằng chỉ số tự động kết hợp đánh giá của người đọc |
| D5 | Hỗ trợ người mới tìm hiểu một dự án lớn | Xây bộ câu hỏi về một dự án thật; so sánh các công cụ hỏi đáp trên mã nguồn; đo độ đúng và thời gian làm quen |

Thuận lợi: nhiều bộ dữ liệu chuẩn có sẵn. D3 có giá trị thực tiễn với doanh nghiệp làm dịch vụ chuyển
đổi hệ thống.

### Hướng E · Triển khai, vận hành và bảo mật

| Mã | Đề tài | Việc cần làm và kết quả kỳ vọng |
| --- | --- | --- |
| E1 | Mức độ an toàn của mã do AI sinh | Sinh mã theo các kịch bản dễ phát sinh lỗ hổng (CWE); quét bằng CodeQL, Semgrep; so sánh giữa các công cụ |
| E2 | AI phát hiện và vá lỗ hổng so với công cụ phân tích tĩnh | Chạy trên bộ dữ liệu lỗ hổng công khai; đo tỉ lệ phát hiện đúng, bỏ sót và tỉ lệ vá đúng |
| E3 | AI trong CI/CD và hạ tầng dạng mã | Sinh Dockerfile, cấu hình pipeline, Terraform; để công cụ tự sửa build hỏng; đo tỉ lệ chạy được và lỗi cấu hình |
| E4 | Phân tích log và sự cố vận hành bằng trợ lý AI | Thử trên bộ log công khai (ví dụ Loghub); đo độ đúng khi xác định nguyên nhân, so với cách phân tích thủ công |
| E5 | Độ tin cậy của thư viện do AI gợi ý | Kiểm tra thư viện được gợi ý: có tồn tại, còn được bảo trì, có lỗ hổng đã biết, giấy phép phù hợp hay không |

Phù hợp với học viên có nền an toàn thông tin hoặc DevOps. Mọi thử nghiệm bảo mật chỉ thực hiện trên
hệ thống của chính nhóm.

### Hướng F · Con người, quy trình và đánh giá

| Mã | Đề tài | Việc cần làm và kết quả kỳ vọng |
| --- | --- | --- |
| F1 | AI có thật sự làm tăng năng suất lập trình viên? | Tổng quan có phê phán các nghiên cứu đã công bố; thiết kế và chạy một thí nghiệm nhỏ ngay trong lớp |
| F2 | Đánh giá công cụ AI lập trình thế nào cho đúng? | Phân tích hạn chế của các bộ đo phổ biến (SWE-bench); xây và thử một bộ nhiệm vụ đánh giá nhỏ của riêng nhóm |
| F3 | Thực trạng dùng AI tại doanh nghiệp phần mềm Việt Nam | Khảo sát và phỏng vấn; đối chiếu với Stack Overflow, DORA; nêu rào cản và thực trạng chính sách |
| F4 | Tác động của AI tới đào tạo và kỹ năng kỹ sư phần mềm | Tổng quan nghiên cứu; khảo sát sinh viên, giảng viên; đề xuất điều chỉnh cho chương trình đào tạo |
| F5 | Bản quyền, giấy phép và quy định sử dụng AI trong tổ chức phần mềm | Phân tích rủi ro pháp lý và dữ liệu; so sánh quy định của các tổ chức; soạn một bộ quy định mẫu |

Ít lập trình nhưng đòi hỏi thiết kế bảng hỏi, chọn mẫu, phân tích dữ liệu chặt chẽ. F3 và F4 có giá
trị vì đang thiếu dữ liệu của Việt Nam.

## Sản phẩm phải nộp và các mốc thời gian

Slide để trống số tuần của từng mốc.

| Mốc | Nội dung |
| --- | --- |
| Tuần __ | Đăng ký nhóm và đề tài |
| Tuần __ | Đề cương 1–2 trang: câu hỏi nghiên cứu, phương pháp, phân công |
| Tuần __ | Báo cáo tiến độ ngắn, nhận góp ý |
| Tuần __ | Nộp báo cáo cuối và thuyết trình |

Bộ sản phẩm cuối kỳ:

- Báo cáo viết, 15–20 trang
- Thuyết trình 15 phút, hỏi đáp 5 phút
- Kho mã, dữ liệu, nội dung yêu cầu đã dùng và kết quả thô
- Bản kê đóng góp cá nhân và khai báo sử dụng AI

Các mốc tuần, độ dài báo cáo và thời lượng thuyết trình là đề xuất, điều chỉnh theo lịch và quy định
học phần.

## Tiêu chí đánh giá

| Tiêu chí | Trọng số | Mức tốt nghĩa là |
| --- | --- | --- |
| Hiểu vấn đề và tổng quan tài liệu | 20% | Câu hỏi nghiên cứu rõ; tổng quan có hệ thống, nguồn tin cậy và cập nhật |
| Phương pháp, thiết kế thực nghiệm | 20% | Chỉ số đo phù hợp; có đối chứng; mô tả đủ để người khác lặp lại |
| Kết quả và phân tích phản biện | 25% | Số liệu thật; nêu hạn chế của nghiên cứu; không thổi phồng |
| Báo cáo viết | 10% | Cấu trúc khoa học, trích dẫn đúng, hình và bảng rõ ràng |
| Thuyết trình và trả lời câu hỏi | 15% | Đúng giờ, mạch lạc; mọi thành viên đều trả lời được |
| Làm việc nhóm, đóng góp cá nhân | 10% | Phân công rõ; có đánh giá chéo; điểm cá nhân có thể điều chỉnh |

Tổng 100%. Trọng số là đề xuất, điều chỉnh theo đề cương học phần.
