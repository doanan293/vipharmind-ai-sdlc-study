# Thiết kế nghiên cứu: phát triển theo đặc tả so với vibe coding

Ngày: 2026-11-15. Đề bài của môn: `2026-11-15-course-brief.md` cùng thư mục.

## 1. Đề tài

**Tiêu đề đăng ký:** Phát triển theo đặc tả so với vibe coding: nghiên cứu tình huống và thực nghiệm
đối chứng trên một dự án phần mềm AI cho ngành dược Việt Nam.

**Mã đề tài của thầy:** B3 là chính, mở rộng sang B4 (cách mô tả yêu cầu), B1 (hai đợt kiểm chứng bằng
công cụ khác) và F2 (tự xây bộ nhiệm vụ đánh giá).

**Môn học:** Chuyên đề nghiên cứu 1, chủ đề chung "AI trong công nghệ phần mềm".

## 2. Ý định và lý do

ViPharmind là một sản phẩm phần mềm thật, đã triển khai, được phát triển với trợ lý lập trình AI ở
mọi khâu: nghiên cứu, dữ liệu, mã, kiểm thử, triển khai. Đề tài dùng nó làm dự án thực nghiệm để trả
lời câu hỏi của môn học: AI giúp làm phần mềm như thế nào và tốt đến đâu.

Thứ được đo là **quá trình phát triển có AI tham gia**, không phải chất lượng của sản phẩm. Chất
lượng trả lời của hệ thống (nội dung bài báo SoICT 2026) chỉ xuất hiện vài dòng làm bối cảnh.

Mục tiêu điểm: A+. Thiết kế nhắm vào từng dòng tiêu chí chấm, nhất là phương pháp (20%) và kết quả,
phân tích phản biện (25%): có đối chứng, số liệu thật, lặp lại được, không thổi phồng.

## 3. Câu hỏi nghiên cứu

- **RQ1.** AI đã tham gia từng khâu của vòng đời ViPharmind ở mức nào, và để lại dấu vết gì trong
  kho mã?
- **RQ2.** Mã do AI viết phải sửa lại ở đâu và bao nhiêu?
- **RQ3.** Trên cùng một nhiệm vụ, làm theo đặc tả (viết thiết kế và kế hoạch trước) có cho kết quả
  tốt hơn giao việc trực tiếp (vibe coding) không, và tốn thêm bao nhiêu chi phí?
- **RQ4.** Kết luận của RQ3 có giữ nguyên khi đổi sang trợ lý lập trình và mô hình của hãng khác
  không?

RQ1, RQ2 do phần hồi cứu trả lời. RQ3, RQ4 do phần thực nghiệm trả lời.

## 4. Mục tiêu, ngoài phạm vi, điều phải tránh

**Mục tiêu**

- Một báo cáo 15–20 trang, một bài thuyết trình 15 phút, một kho mã chạy lại được, đủ bộ sản phẩm
  thầy yêu cầu.
- Kết quả RQ3 có đối chứng, tiêu chí đạt khách quan, mỗi nhiệm vụ chạy lặp.
- Hai thành viên thuyết trình trả lời được câu hỏi của thầy.

**Ngoài phạm vi**

- Không đánh giá lại chất lượng trả lời của ViPharmind.
- Không làm thí nghiệm trên frontend và `pharma-lab`; thực nghiệm chỉ dùng `backend/`.
- Không có nhánh thứ ba "đặc tả do người duyệt". Lý do ở mục 7.3.
- Không so sánh công cụ với công cụ hay mô hình với mô hình. Mỗi công cụ dùng một mô hình cố định,
  ba mô hình khác hạng nhau; phép so sánh luôn là hai cách làm trong cùng một công cụ.
- Không sửa gì trong repo ViPharmind.

**Điều phải tránh** (bài hỏng dù chạy được)

- Chọn hoặc đổi nhiệm vụ, chỉ số sau khi đã thấy kết quả.
- Giấu kết quả bất lợi, hoặc viết kết luận mạnh hơn số liệu cho phép.
- Ghi sai đóng góp của từng thành viên.
- Để lộ khóa API hay dữ liệu riêng trong nhật ký phiên khi công khai repo.
- Báo cáo trượt sang kể về sản phẩm thay vì về quá trình phát triển.

## 5. Ràng buộc

- **Nhóm 3 người.** An làm toàn bộ nghiên cứu, thí nghiệm, báo cáo, slide. Hai thành viên còn lại
  thuyết trình, trả lời câu hỏi và gán nhãn nguyên nhân thất bại (mục 7.6). Bản kê đóng góp ghi đúng
  như vậy.
- **Hạn nộp:** chưa có, slide của thầy để trống số tuần. Thiết kế không phụ thuộc mốc thời gian.
- **Repo ViPharmind** (`git@github.com:doanan293/ViPharmind.git`, công khai) là đối tượng nghiên cứu,
  chỉ đọc. Repo này trỏ tới nó bằng mã commit, không chép mã sang. Hai mốc cố định: `main` tại
  `3baae61d764f6d83f7205d0d4d97ee52dd8e0dbe` và `camera-ready` tại
  `61d10db85f0f4d9cb871e8fff89ce06e2c49b930` (đều 2026-11-10). Hai nhánh đã tách nhau: `camera-ready`
  có 21 commit riêng (bài báo, bài thuyết trình), `main` có 1 commit riêng.
- **Repo nghiên cứu** để riêng tư cho đến khi nhật ký phiên đã được lọc.
- **Commit:** không thêm dòng ghi công Claude hay AI vào commit, theo yêu cầu của An.
- **Ngôn ngữ:** báo cáo, slide, đề cương viết tiếng Việt.

## 6. Các cách tiếp cận đã cân nhắc

| Cách | Nội dung | Được | Mất |
| --- | --- | --- | --- |
| 1. Chỉ hồi cứu | Phân tích commit, spec, plan, nhật ký phiên theo từng khâu | Đúng ý "end to end", dữ liệu sẵn | Không có đối chứng, khó lặp lại |
| **2. Hồi cứu cộng một thực nghiệm đối chứng** | Hồi cứu gọn hơn, thêm thí nghiệm hai cách làm trên nhiệm vụ lấy từ commit thật | Giữ độ rộng, có đối chứng, tiêu chí khách quan | Tốn công dựng bộ nhiệm vụ và chi phí chạy |
| 3. Bộ đo so sánh công cụ | Dựng bộ nhiệm vụ rồi so 3–4 trợ lý lập trình | Thí nghiệm sạch nhất | Bỏ gần hết phần vòng đời |

An chọn **cách 2** theo khuyến nghị: giữ được ý định làm trọn vòng đời mà vẫn có đối chứng và số
liệu thật cho hai tiêu chí nặng điểm nhất.

Hai quyết định đi kèm, An đã đồng ý:

- Chạy ba công cụ theo ba đợt. Claude Code là kết quả chính; Antigravity và Codex chạy sau trên cùng
  bộ nhiệm vụ để trả lời RQ4.
- Chạy bằng gói thuê bao sẵn có của An, không dùng khóa API trả theo lượng dùng.
- Hai thành viên thuyết trình gán nhãn nguyên nhân thất bại độc lập.

## 7. Thiết kế

### 7.1 Phần hồi cứu (RQ1, RQ2)

**Vai trò:** bối cảnh cho thực nghiệm, chiếm khoảng 3–4 trang trong báo cáo. Dữ liệu chỉ cho thống
kê mô tả (mục giới hạn bên dưới), nên không dàn trải thêm; sức chính dồn vào thực nghiệm (RQ3, RQ4).

**Tập commit phân tích:** hợp của hai mốc `main` và `camera-ready` ở mục 5, mỗi commit tính một lần.
Lấy hợp vì khâu nghiên cứu và viết bài nằm trên `camera-ready`, còn sản phẩm nằm trên `main`. Các
nhánh khác (`dev`, `v2.0.0`) không tính.

Nguồn dữ liệu, số đo ngày 2026-11-15:

| Nguồn | Hiện có | Ghi chú |
| --- | --- | --- |
| Lịch sử git | 505 commit, 2026-07-23 đến 2026-11-10 | 221 feat, 115 docs, 50 fix, 47 refactor, 34 chore, 20 test |
| Tài liệu thiết kế và kế hoạch | 43 file spec, plan từng được thêm vào trong tập commit này, nằm ở `docs/`, `backend/docs/`, `frontend/docs/`, `seed-pipeline/docs/` dưới `superpowers/` | Phần lớn đã bị xóa khỏi cây hiện tại, phải lấy từ lịch sử |
| Nhật ký phiên Claude Code | 13 phiên (34 file `.jsonl` nếu tính cả nhật ký tác tử con) trong `~/.claude/projects/-home-andv-personal-vipharmind*` | **Không đầy đủ:** An xóa lịch sử chat giữa các phiên |
| Nhật ký Codex | `~/.codex/history.jsonl` có 2 dòng | Coi như không dùng được |

Việc phân tích:

- **Bản đồ vòng đời.** Gán mỗi commit vào một khâu (nghiên cứu và đánh giá, dữ liệu, mã backend, mã
  frontend, kiểm thử, triển khai, tài liệu) theo đường dẫn file và loại commit. Báo cáo số commit, số
  dòng thay đổi theo khâu và theo thời gian.
- **Dấu vết quy trình theo đặc tả.** Với mỗi file spec, plan: ngày tạo, các commit cài đặt theo sau.
  Đo tỉ lệ commit `feat` có spec hoặc plan đi trước.
- **Quy tắc nối commit với plan.** Một commit `feat` được coi là "có plan đi trước" khi nó chạm ít
  nhất một file mã có đường dẫn được nêu trong một file plan đã được thêm vào trước commit đó không
  quá 14 ngày. An kiểm tra tay một mẫu ngẫu nhiên 20 commit; báo cáo tỉ lệ quy tắc gán đúng.
- **Mức phải sửa lại (RQ2).** Với mỗi commit `feat`, đếm commit `fix` hoặc `refactor` chạm cùng file
  trong 14 ngày sau. So sánh nhóm `feat` có spec đi trước với nhóm không có.
- **Nhật ký phiên.** Dùng làm minh họa định tính và thống kê mô tả (số lượt, công cụ được gọi, số
  lần người sửa hướng) trên phần còn giữ được. Không suy rộng ra toàn dự án.

Giới hạn phải nêu trong báo cáo: commit không mang dấu ghi công AI (0 commit có `Co-Authored-By`),
nên "AI tham gia mọi khâu" dựa trên lời khai của tác giả và phần nhật ký còn lại, không đo được tỉ lệ
chính xác. So sánh `feat` có spec với không có spec là quan sát, không phải nhân quả; phần nhân quả
do thực nghiệm đảm nhận.

### 7.2 Bộ nhiệm vụ của thực nghiệm

Nguồn: commit `feat` trên `main` (mốc ở mục 5) chạm cả `backend/src` và `backend/tests`. Hiện có 110
commit như vậy. Tại mốc này bộ test backend chạy không cần Docker trong khoảng 1 phút (612 test đạt,
114 test `integration` bị bỏ qua).

Một nhiệm vụ gồm: commit gốc, commit cha (mã nền), đề bài, danh sách test ẩn.

**Test ẩn** là các file test mà commit gốc thêm mới hoặc sửa, lấy nguyên file ở phiên bản của commit
gốc. File test thêm mới không có trong thư mục AI làm việc. File test bị sửa thì AI thấy bản cũ của
commit cha; khi chấm, bản của commit gốc ghi đè lên. **Test cũ** là mọi test không mang nhãn
`integration` còn lại. Test `integration` không dùng ở bất kỳ bước nào.

Tiêu chí sàng lọc, áp dụng theo thứ tự, ghi lại số commit bị loại ở mỗi bước:

1. Commit không sửa file dùng chung của bộ test (`conftest.py`, `fakes.py`, `harness.py`,
   `memory_repository.py` và các file hỗ trợ khác không phải `test_*.py`). Hiện 39 trong 110 commit
   có sửa và bị loại. Lý do: khôi phục các file này lúc chấm sẽ ghi đè phần AI tự sửa và buộc điểm
   vào chi tiết nội bộ.
2. Tại commit cha, có ít nhất một test ẩn hỏng; tại commit gốc, mọi test ẩn đạt (hỏng-thành-đạt), và
   toàn bộ test cũ đạt ở cả hai commit. Test ẩn chạy được không cần Docker.
3. Test ẩn kiểm tra hành vi qua một giao diện nêu được trong đề bài (đường dẫn API, chữ ký hàm, lớp
   công khai), không phụ thuộc tên hàm nội bộ mà đề bài không nói tới.
4. Phần thay đổi ở `backend/src` từ 30 đến 400 dòng, để nhiệm vụ không quá vặt và không quá lớn.
5. Commit không chỉ là đổi tên hay di chuyển file.

Từ các commit qua sàng lọc, chọn **15 nhiệm vụ** bằng lấy mẫu ngẫu nhiên có hạt giống cố định, phân
tầng theo lớp mã (`api`, `application`, `domain`, `infrastructure`). Thêm **2 nhiệm vụ thử** ngoài
15 nhiệm vụ này để chạy thử bộ chạy.

**Đề bài.** Mỗi nhiệm vụ có một đề bài tiếng Anh 5–10 câu, viết từ thông điệp commit và hành vi mà
test ẩn kiểm tra: việc cần làm, giao diện phải giữ (đường dẫn, chữ ký), không nêu cách cài đặt. Hai
cách làm nhận **cùng một đề bài**.

**Ai viết.** AI soạn nháp đề bài và đề xuất đánh giá tiêu chí 3 cho từng commit; An đọc, sửa và duyệt
từng nhiệm vụ trước thẻ `prereg-v1`. Khai báo sử dụng AI ghi rõ việc này.

**Chốt trước khi chạy.** Danh sách nhiệm vụ, đề bài, giả thuyết, chỉ số và kế hoạch phân tích được
commit và gắn thẻ git `prereg-v1` trước lượt chạy chính đầu tiên. Lượt chạy trên 2 nhiệm vụ thử được
phép trước thẻ này. Mọi thay đổi sau thẻ phải ghi lại trong báo cáo kèm lý do.

### 7.3 Hai cách làm

| | Theo đặc tả | Vibe coding |
| --- | --- | --- |
| Đầu vào | Đề bài | Đề bài |
| Quy trình yêu cầu | Viết tài liệu thiết kế, rồi kế hoạch từng bước, rồi cài đặt theo kế hoạch và tự viết test | "Cài đặt việc này" |
| Người can thiệp | Không | Không |

Khác biệt duy nhất giữa hai cách là lời dặn về quy trình, lưu thành hai file mẫu trong repo. Cùng mô
hình, cùng quyền dùng công cụ, cùng giới hạn lượt và thời gian.

Mỗi lượt là **một phiên duy nhất** cho cả hai cách. Ở cách theo đặc tả, AI viết tài liệu thiết kế và
kế hoạch thành file trong thư mục làm việc rồi cài đặt tiếp trong cùng phiên đó; giới hạn lượt và
thời gian tính cho cả phiên. Không chia thành ba lần gọi riêng, để hai cách chỉ khác nhau ở lời dặn.
Lượt theo đặc tả mà không để lại file thiết kế và kế hoạch được đánh dấu "không tuân thủ quy trình",
vẫn chấm và báo cáo riêng.

**Gọi đúng tên.** Trong báo cáo, nhánh này được gọi là "quy trình đặc tả tự động": AI tự viết thiết kế
và kế hoạch rồi cài đặt, không có người duyệt. Lời dặn bám theo các bước của một quy trình đã công bố
(GitHub Spec Kit: đặc tả, kế hoạch, danh sách việc, cài đặt; `taghavi_2026`) và ghi rõ nguồn trong
file mẫu. Báo cáo đối chiếu với cách người làm nghề thực hành phát triển theo đặc tả (`agarwal_2026`)
để nói rõ thí nghiệm đo phần nào của quy trình đó.

Lý do không có nhánh "đặc tả do người duyệt": đặc tả gốc trong lịch sử ViPharmind được viết cho những
phần việc lớn hơn một commit và chỉ có ở một số nhiệm vụ, nên không ghép đều được vào 15 nhiệm vụ.
Hệ quả phải nêu ở phần hạn chế: nhánh "theo đặc tả" ở đây là bản tự động, không có bước người duyệt
đặc tả như quy trình An dùng khi làm ViPharmind.

### 7.4 Bộ chạy

Mỗi lượt chạy:

1. Xuất mã ViPharmind tại commit cha vào một thư mục mới **không kèm lịch sử git**, để AI không đọc
   được các commit tương lai.
2. Xóa các file test ẩn khỏi thư mục đó.
3. Gọi trợ lý lập trình ở chế độ không tương tác với đề bài và lời dặn của cách làm. Tắt công cụ truy
   cập web, vì repo ViPharmind công khai. Dùng thư mục cấu hình sạch: không plugin, không skill,
   không bộ nhớ, không file hướng dẫn riêng.
4. Khi AI dừng hoặc chạm giới hạn, chép test ẩn vào lại và chấm.
5. Lưu kết quả thô: đề bài đã gửi, toàn bộ nhật ký lượt chạy, bản vá, kết quả từng test, số liệu chi
   phí.

**Chạy song song.** Các lượt chạy song song, mỗi lượt một thư mục làm việc và một thư mục cấu hình
riêng, không dùng chung trạng thái. Thời gian chạy đo theo từng lượt. Thứ tự các lượt được xáo trộn
ngẫu nhiên có hạt giống cố định, để hai cách làm không rơi vào hai khung giờ khác nhau của dịch vụ.

Quy mô: 15 nhiệm vụ × 2 cách làm × 3 lần lặp = **90 lượt mỗi công cụ**, 270 lượt cho ba công cụ.

| Đợt | Công cụ (bản lúc thiết kế) | Lệnh chạy tự động | Mô hình | Vai trò |
| --- | --- | --- | --- | --- |
| 1 | Claude Code 2.1.325 | `claude -p` | Claude Sonnet 5.5 (`claude-sonnet-5-5`) | Kết quả chính, RQ3 |
| 2 | Antigravity CLI 1.5.8 | `agy -p` | Gemini 3.8 Flash Medium (`gemini-3.8-flash-medium`) | Kiểm chứng, RQ4 |
| 3 | Codex CLI 0.162.1 | `codex exec` | `gpt-6-luna`, mức suy luận medium | Kiểm chứng, RQ4 |

Ba đợt dùng cùng nhiệm vụ, cùng đề bài, cùng lời dặn. Đợt 2 và 3 chỉ bắt đầu sau khi đợt 1 xong và
đã phân tích; nếu thiếu thời gian, bỏ đợt 3 trước, rồi đợt 2, và ghi rõ trong báo cáo.

Lý do chọn mô hình:

- **Claude Sonnet 5.5** cho đợt chính: hạng giữa, để tránh hiệu ứng trần (mô hình mạnh nhất có thể
  đạt gần hết nhiệm vụ ở cả hai cách, không còn chênh lệch để đo) và vừa hạn mức gói thuê bao cho 90
  lượt. Nếu ở 2 nhiệm vụ thử mọi lượt đều đạt hoặc đều hỏng ở cả hai cách, xem lại lựa chọn này trước
  thẻ `prereg-v1`.
- **Gemini 3.8 Flash Medium:** An chọn mức Medium trong các mô hình của Google mà tài khoản
  Antigravity có. Không dùng các mô hình Claude có trong Antigravity vì cùng họ với đợt 1.
- **`gpt-6-luna`:** mô hình duy nhất tài khoản Codex của An có.

**Gói thuê bao.** Mọi lượt chạy dùng tài khoản thuê bao đã đăng nhập. Hệ quả cho bộ chạy:

- Thư mục cấu hình sạch vẫn phải giữ thông tin đăng nhập của công cụ.
- Khi chạm hạn mức, bộ chạy tạm dừng và chạy lại đúng lượt đó sau; lượt bị ngắt vì hạn mức không tính
  là thất bại và không tính vào 3 lần lặp.
- Chi phí bằng tiền là số quy đổi: lượng token thật của mỗi lượt nhân với bảng giá API công khai tại
  ngày chạy, ghi rõ là quy đổi.

**Nhiều tài khoản và proxy.** An có nhiều tài khoản để đổi khi hết hạn mức. Thông tin đăng nhập nằm
trong proxy `cli-proxy-api` (v8.0.28) của repo
`/home/andv/personal/HUST/principle-technique-program-analysis`, thư mục `infra/proxy/`, dùng chung
volume Docker `vipharmind_cli_proxy_auth`. Theo `infra/proxy/MODELS.md` ngày 2026-11-08: 4 tài khoản
Antigravity, 4 tài khoản Codex miễn phí, 1 tài khoản Claude; proxy chia lượt xoay vòng và tự đổi tài
khoản khi một tài khoản hết hạn mức. Proxy là cổng gọi mô hình kiểu API, không phải trợ lý lập trình,
nên mỗi công cụ dùng nó theo cách riêng:

- **Claude Code:** chỉ có 1 tài khoản, chạy thẳng bằng đăng nhập sẵn có, không qua proxy.
- **Codex CLI:** trỏ nhà cung cấp mô hình của Codex tới proxy để xoay vòng 4 tài khoản.
- **Antigravity CLI:** ưu tiên chạy thẳng `agy` vì mức Medium chỉ có ở đó (proxy chỉ có
  `gemini-3.8-flash-high`). Khi hết hạn mức thì đổi tài khoản đăng nhập của `agy`; cách đổi tự động
  do người thực hiện xác định khi chạy thử.

Ràng buộc khi dùng proxy và nhiều tài khoản:

- Không chép khóa, token hay file cấu hình của proxy vào repo này; chỉ ghi đường dẫn.
- Proxy có thể sửa yêu cầu gửi đi (ép mức suy luận, đổi mô hình phía sau một tên gọi). Dùng cấu hình
  không ép mức suy luận, và ghi mô hình thực tế được phục vụ cho từng lượt.
- Ghi lại tài khoản thứ mấy (số thứ tự, không ghi email) phục vụ từng lượt. Báo cáo nêu rõ thí nghiệm
  chạy trên nhiều tài khoản và qua proxy.
- Kiểm tra điều khoản của từng dịch vụ về việc xoay nhiều tài khoản trước khi chạy đợt 2 và 3.

Phải kiểm tra khi chạy 2 nhiệm vụ thử, trước thẻ `prereg-v1`: điều khoản của từng gói về chạy tự
động; hạn mức thực tế; cách tắt truy cập web ở `agy` và `codex`; mỗi công cụ có trả lượng token hay
không. Công cụ nào không tắt được truy cập web hoặc không cho chạy tự động thì loại khỏi thí nghiệm
và ghi lý do.

Ghi lại phiên bản công cụ và mã mô hình chính xác của từng lượt. Tra mốc dữ liệu huấn luyện của cả ba
mô hình; chỉ viết nhận định "mô hình chưa từng thấy mã này" cho mô hình có mốc trước 2026-07-23.

### 7.5 Chỉ số

| Chỉ số | Cách đo |
| --- | --- |
| **Đạt nhiệm vụ** (chính) | Mọi test ẩn đạt và không test cũ nào hỏng |
| Tỉ lệ test ẩn đạt | Số test ẩn đạt trên tổng |
| Hồi quy | Số test cũ bị hỏng |
| Chất lượng tĩnh | Số lỗi `ruff check`, số lỗi `pyrefly check`, test kiến trúc `tests/architecture` |
| Khả năng bảo trì | Độ phức tạp chu trình và chỉ số bảo trì (`radon cc`, `radon mi`) trên các file mã bị thay đổi, so với bản gốc |
| Test do AI viết | Số test thêm mới, độ phủ dòng trên phần mã thay đổi |
| Kích thước | Số dòng thêm, bớt so với bản vá gốc |
| Chi phí | Token vào, ra; chi phí quy đổi; thời gian chạy; số lượt |

**Giả thuyết ghi trước:** H1, làm theo đặc tả có tỉ lệ đạt nhiệm vụ cao hơn vibe coding. H2, làm
theo đặc tả tốn nhiều token và thời gian hơn. H3, làm theo đặc tả ít lỗi chất lượng tĩnh, ít hồi
quy hơn và có chỉ số bảo trì không kém hơn.

**Phân tích.** So sánh theo cặp trên từng nhiệm vụ. Báo cáo hiệu số kèm khoảng tin cậy bootstrap lấy
mẫu lại theo nhiệm vụ. Với 15 nhiệm vụ, báo cáo cỡ hiệu ứng và khoảng tin cậy, không dựa kết luận
vào ngưỡng p. Báo cáo cả độ dao động giữa 3 lần lặp của cùng một nhiệm vụ.

### 7.6 Phân tích lỗi và kiểm tra bằng người

- **Gán nhãn nguyên nhân thất bại.** Hai thành viên thuyết trình gán nhãn độc lập cho mọi lượt của đợt 1 không
  đạt, theo một bảng nhãn có định nghĩa và ví dụ. Họ nhận kết quả test và bản vá đã bỏ file thiết kế,
  kế hoạch, để không biết lượt đó thuộc cách làm nào. Báo cáo hệ số kappa của Cohen. Chỗ lệch nhau do
  An phân xử và ghi lại.
- **Bảng nhãn khởi đầu:** hiểu sai yêu cầu; làm thiếu; sai giao diện đã nêu trong đề bài; làm hỏng
  chức năng cũ; lỗi logic; không hoàn thành trong giới hạn; lỗi môi trường. Bảng được chỉnh sau khi
  gán thử trên các lượt của 2 nhiệm vụ thử, rồi khóa.
- **Đạt test nhưng sai.** An đọc một mẫu ngẫu nhiên 20 lượt đạt, đối chiếu với bản vá gốc, ghi lại
  trường hợp mã đạt test nhưng sai hoặc thiếu hành vi.

### 7.7 Hạn chế phải nêu trong báo cáo

- Một dự án, một ngôn ngữ (Python), 15 nhiệm vụ.
- Ba mô hình khác hạng nhau, nên không so sánh được công cụ với công cụ.
- Test ẩn được viết cho bản cài đặt gốc, và bản gốc được làm theo đặc tả, nên có thể thiên vị nhánh
  theo đặc tả.
- Nhánh theo đặc tả không có người duyệt.
- Đề bài do chính nhóm viết sau khi đã biết lời giải.
- Nhật ký phiên không đầy đủ; phần hồi cứu không đo được chính xác tỉ lệ mã do AI viết.
- Tác giả nghiên cứu cũng là tác giả dự án.

## 8. Sản phẩm và bố cục repo

```
docs/superpowers/specs/   đề bài của môn, bản thiết kế này
docs/superpowers/plans/   kế hoạch thực hiện
proposal/                 đề cương 1–2 trang
retrospective/            mã phân tích hồi cứu và kết quả
tasks/                    15 nhiệm vụ và 2 nhiệm vụ thử: commit, đề bài, danh sách test ẩn
prompts/                  hai file lời dặn của hai cách làm
harness/                  bộ chạy và bộ chấm
results/raw/              kết quả thô từng lượt
results/analysis/         bảng, hình, mã phân tích
labeling/                 bảng nhãn, phiếu gán nhãn của hai người, kết quả phân xử
report/                   báo cáo 15–20 trang
slides/                   bài thuyết trình 15 phút
team/                     bản kê đóng góp, mẫu đánh giá chéo, khai báo sử dụng AI, tài liệu chuẩn bị hỏi đáp
```

Sản phẩm theo yêu cầu của thầy:

| Yêu cầu | Ở đâu |
| --- | --- |
| Đề cương 1–2 trang | `proposal/`, rút từ mục 1, 3, 5, 7 |
| Báo cáo viết 15–20 trang | `report/` |
| Thuyết trình 15 phút, hỏi đáp 5 phút | `slides/`, `team/` |
| Kho mã, dữ liệu, nội dung yêu cầu đã dùng, kết quả thô | repo này; đề bài ở `tasks/` và `prompts/`, kết quả thô ở `results/raw/` |
| Bản kê đóng góp cá nhân và khai báo sử dụng AI | `team/` |

Tổng quan tài liệu trong báo cáo: tìm có quy trình, ghi lại từ khóa, nguồn, tiêu chí chọn, số bài tìm
được, sàng lọc, giữ lại; khoảng 15–25 nguồn, ưu tiên hội nghị và tạp chí có bình duyệt, 2023–2026.
Nhật ký tìm kiếm ở `report/literature-log.md`. Ba nhóm:
bộ đo cho trợ lý lập trình và hạn chế của chúng; nghiên cứu về năng suất khi dùng AI; phát triển
theo đặc tả với AI. Mọi trích dẫn phải được mở và kiểm tra, không trích theo trí nhớ.

Khai báo sử dụng AI nêu đầy đủ: AI được dùng để làm ViPharmind, để dựng bộ chạy, để viết báo cáo và
slide, và là đối tượng được đo.

Thứ tự làm, mỗi bước là một kế hoạch riêng:

1. Đề cương.
2. Bộ nhiệm vụ và bộ chạy, chạy thử 2 nhiệm vụ, gắn thẻ `prereg-v1`. Làm sớm vì đây là rủi ro khả
   thi lớn nhất (hạn mức, tắt truy cập web, số token).
3. Đợt 1 (Claude Code) và phân tích. Kết quả đầu tiên dùng cho báo cáo tiến độ.
4. Gán nhãn và kiểm tra bằng người.
5. Phân tích hồi cứu, bản gọn.
6. Đợt 2 (Antigravity) và đợt 3 (Codex).
7. Báo cáo, slide, tài liệu hỏi đáp.

Việc không phụ thuộc nhau thì chạy song song: tổng quan tài liệu và phân tích hồi cứu chạy cùng lúc
với bước 2–3; đợt 2 và đợt 3 chạy cùng lúc với nhau.

**Báo cáo tiến độ** (mốc thứ ba của thầy): nộp sau khi có kết quả chạy thử hoặc đợt 1, kèm số liệu
đầu tiên, để góp ý của thầy còn kịp vào thiết kế.

## 9. Phần để người thực hiện tự quyết

- Ngôn ngữ và thư viện của bộ chạy, bộ phân tích (mặc định: Python với `uv`, giống ViPharmind).
- Định dạng file nhiệm vụ và file kết quả thô.
- Cách xuất mã không kèm lịch sử và cách cô lập từng lượt chạy.
- Giới hạn lượt và thời gian cho mỗi lượt, chốt sau khi chạy 2 nhiệm vụ thử và ghi vào `prereg-v1`.
- Công cụ soạn báo cáo và slide (mặc định: LaTeX cho báo cáo, ppt-master cho slide như bài SoICT).
- Cách lọc khóa API và dữ liệu riêng khỏi nhật ký phiên.
- Số bản ghi và cách chọn mẫu khi trích nhật ký phiên làm minh họa.
