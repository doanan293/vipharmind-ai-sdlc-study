# Hướng dẫn gán nhãn nguyên nhân thất bại

Bản khóa theo `prereg-v1` (chép từ `team/labeling/guide.md` của nhánh `report`, thêm hai nhãn mà chạy
thử đề xuất ở `docs/pilot-report.md` mục 7). Sau thẻ `prereg-v1`, không thêm hay đổi nhãn; mọi sửa
đổi đi qua mục 11 của bản đăng ký trước (`prereg/prereg-v1.md`).

Dành cho Lê Xuân Lợi và Trần Ngọc Bảo. Người soạn: Doãn Văn An (có trợ lý AI giúp soạn nháp).

## 1. Mục đích

Trong thí nghiệm, mỗi lượt chạy giao cho một coding agent một nhiệm vụ lấy từ commit thật của
ViPharmind. Một lượt **đạt** khi mọi test ẩn đạt và không test cũ nào hỏng. Với các lượt hợp lệ không
đạt của hai nhóm Claude (Claude Sonnet 5.5 và Claude Opus 5.5) ở cả ba tầng, cần biết vì sao chúng hỏng. Hai bạn gán nhãn độc
lập với nhau. Nhóm đo mức đồng thuận bằng hệ số kappa của Cohen; chỗ hai bạn chọn khác nhau do An phân
xử và ghi lại. Kết quả vào mục 6 của báo cáo (bản thiết kế nghiên cứu mục 7.6).

## 2. Các bạn nhận gì

Mỗi lượt có một mã ngẫu nhiên (`unit_id`), không chứa nhóm, cách làm hay số lần lặp, và một thư mục gồm:

- `prompt.md`: đề bài tiếng Anh mà agent nhận (chỉ phần đề bài, không có lời dặn về quy trình).
- `patch.diff`: bản vá agent làm so với mã nền. Các file `docs/design.md` và `docs/plan.md` đã bị bỏ,
  để giảm khả năng các bạn biết lượt đó thuộc cách làm nào (theo đặc tả hay vibe coding). Việc che này
  chỉ là một phần: bản vá vẫn có thể để lộ cách làm, ví dụ qua số test agent viết.
- `test-log.txt`: kết quả chạy toàn bộ test sau khi chép test ẩn vào: test nào hỏng, thông báo lỗi.

Đừng cố đoán lượt thuộc cách làm nào. Nếu một lượt để lộ cách làm (ví dụ bản vá nhắc tới "plan"),
cứ gán nhãn bình thường và ghi "lộ cách làm" vào cột `note`.

## 3. Bảng nhãn

Bảng được khóa tại thẻ `prereg-v1`: bảng khởi đầu 7 nhãn, cộng hai nhãn `de_bai_thieu` và `sai_api_co_san`
do gán thử trên các lượt chạy thử đề xuất. Từ lúc khóa, không thêm hay đổi nhãn.

Các ví dụ dưới đây được **dựng** từ đề bài thật trong `tasks/` để minh họa, chưa phải lượt chạy thật.

| Nhãn (ghi vào phiếu) | Định nghĩa | Ví dụ dựng từ một đề thật |
| --- | --- | --- |
| `hieu_sai` (hiểu sai yêu cầu) | Agent làm một việc khác với việc đề bài yêu cầu: hiểu sai mục đích hay hành vi chính, dù mã có thể chạy đúng theo cách nó hiểu. | `t05` (guardrail): đề bài nói lỗi khi gọi LLM thì cho câu hỏi qua ("fail open"). Agent lại chặn câu hỏi khi LLM lỗi. Test về lỗi LLM hỏng. |
| `lam_thieu` (làm thiếu) | Agent làm đúng hướng nhưng bỏ sót một phần đề bài yêu cầu: một hàm, một trường hợp, một lệnh. Phần đã làm thì đúng. | `t03` (OpenAPI): agent sửa `operationId` và lược đồ lỗi nhưng không thêm lệnh `pharma-agent export-openapi`. Test của CLI hỏng, test OpenAPI đạt. |
| `sai_giao_dien` (sai giao diện đã nêu trong đề bài) | Hành vi có thể đúng nhưng tên, vị trí hay chữ ký khác với điều đề bài đã nêu rõ: sai tên module, tên lớp, tên tham số, đường dẫn API. Test thường hỏng ở bước import hoặc gọi hàm. | `t14` (DeepInfra reranker): đề bài yêu cầu lớp `DeepInfraReranker` trong module `pharma_agent.infrastructure.retrieval.deepinfra_reranker`. Agent đặt lớp vào module khác, test báo `ModuleNotFoundError`. |
| `hong_chuc_nang_cu` (làm hỏng chức năng cũ) | Test ẩn có thể đạt, nhưng ít nhất một test cũ (test đã có từ trước) hỏng vì agent sửa mã cũ. | `t12` (skill catalog): agent sửa bộ phân tích SKILL.md có sẵn để đọc được file mới, làm hỏng test cũ của bộ phân tích. |
| `loi_logic` (lỗi logic) | Agent hiểu đúng việc, đặt đúng giao diện, nhưng cài đặt sai ở chi tiết: điều kiện biên, thứ tự, công thức, xử lý ngoại lệ. | `t08` (text helpers): `make_snippet` cắt chuỗi nhưng không tính độ dài của dấu `…`, nên kết quả dài hơn `max_chars` một ký tự. |
| `khong_hoan_thanh` (không hoàn thành trong giới hạn) | Lượt bị dừng vì chạm giới hạn thời gian trước khi agent làm xong; bản vá còn dở (file chưa tạo, hàm chưa viết). | `t01` (OrganizationService): bản vá chỉ có `errors.py` và một nửa `service.py`, nhiều phương thức chưa có. Lượt bị dừng vì hết giờ có ghi sẵn `het_gio` ở cột `note`. |
| `de_bai_thieu` (đề bài thiếu hoặc mơ hồ) | Đề bài không nêu một điều mà test ẩn cần, hoặc nêu theo cách hiểu được theo hai nghĩa, và agent chọn một cách hợp lý khác với test. Lỗi thuộc về nhiệm vụ, không thuộc về agent. | `p01` (chạy thử): đề bài định nghĩa `path` là "the tuple of enclosing headings", có thể hiểu là gồm hoặc không gồm tiêu đề của chính mục đó. Agent hiểu theo nghĩa không gồm; test mong nghĩa gồm. |
| `sai_api_co_san` (dùng sai kiểu hoặc API có sẵn của dự án) | Mã đúng ý đề bài nhưng nối sai với mã đã có trong dự án: đưa sai kiểu dữ liệu, gọi sai hàm, sai lớp có sẵn. Đề bài không nêu điều này; agent phải tự đọc mã nền. | `p01` (chạy thử): agent đưa thẳng `Collection` vào trường `BundleManifest.collection`, trong khi dự án đã có kiểu `BundleCollection` cho trường đó; test báo `ValidationError`. |
| `loi_moi_truong` (lỗi môi trường) | Lượt hỏng vì lý do ngoài mã của agent: thiếu thư viện, test không chạy được vì cấu hình, lỗi của bộ chấm, hết thời gian khi chạy test. Agent không làm gì sai. | Log báo lỗi khi cài gói phụ thuộc trước khi chạy test, không có test nào được chạy. |

Cách phân biệt các cặp hay nhầm:

- `hieu_sai` với `loi_logic`: nếu đọc mã thấy agent nhắm đúng hành vi mà đề bài mô tả nhưng viết sai chi
  tiết, chọn `loi_logic`. Nếu agent nhắm một hành vi khác, chọn `hieu_sai`.
- `lam_thieu` với `khong_hoan_thanh`: nếu cột `note` có sẵn `het_gio` (lượt bị dừng vì hết giờ), chọn
  `khong_hoan_thanh`. Nếu agent
  tự dừng và nói đã xong nhưng thiếu một phần, chọn `lam_thieu`.
- `sai_giao_dien` chỉ dùng khi đề bài **đã nêu rõ** tên hay chữ ký đó. Nếu đề bài không nêu, đó không
  phải lỗi giao diện.
- `de_bai_thieu` với `hieu_sai`: nếu đọc lại đề bài thấy cách agent hiểu là một cách đọc hợp lý của
  chính câu chữ trong đề, hoặc đề không nhắc tới điều test kiểm, chọn `de_bai_thieu`. Nếu đề đã nói rõ
  mà agent làm khác, chọn `hieu_sai`.
- `sai_api_co_san` với `sai_giao_dien`: nếu tên hay kiểu bị sai đã được đề bài nêu, chọn `sai_giao_dien`.
  Nếu đề bài không nêu và tên hay kiểu đó có sẵn trong mã nền, chọn `sai_api_co_san`.
- `sai_api_co_san` với `loi_logic`: nếu chỗ sai là cách nối với mã có sẵn (kiểu, hàm, lớp của dự án),
  chọn `sai_api_co_san`. Nếu chỗ sai nằm trong phần mã agent tự viết, chọn `loi_logic`.

## 4. Một lượt có nhiều nguyên nhân

Chỉ chọn **một** nhãn cho mỗi lượt: nguyên nhân làm hỏng test hỏng **đầu tiên** trong `test-log.txt`.
Nếu nhiều test hỏng cùng một lý do, đó là nhãn của lượt. Ghi các nguyên nhân khác (nếu thấy) vào cột
`note`, ngắn gọn.

## 5. Quy tắc làm việc

- Gán nhãn **một mình**. Không trao đổi với người kia về lượt nào, kể cả sau khi đã nộp, cho tới khi An
  công bố kết quả kappa.
- Không mở kho mã ViPharmind để xem lời giải gốc. Chỉ dùng đề bài, bản vá và log test.
- Không chắc thì vẫn chọn nhãn hợp nhất, và ghi lý do vào `note`.

## 6. Cách nộp

Điền cột `label` và `note` trong file phiếu của mình (`sheet-<tên>.csv`, xem `README.md`). Không sửa cột
`unit_id`. Gửi file lại cho An. An gộp hai phiếu, tính kappa và phân xử.
