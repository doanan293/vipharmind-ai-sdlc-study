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
- **RQ5.** Lợi ích của làm theo đặc tả thay đổi thế nào khi dùng mô hình mạnh hơn (Claude Opus 5.5 so
  với Claude Sonnet 5.5, cùng trong Claude Code)?
- **RQ6.** Khoảng cách giữa hai cách làm thay đổi thế nào theo kích thước nhiệm vụ, từ một commit nhỏ
  tới cỡ một tính năng (nhiều commit, 750–1.500 dòng)? Đây là trục chính của câu chuyện nghiên cứu:
  làm theo đặc tả có một chi phí cố định (thiết kế, kế hoạch), chỉ có thể đáng khi nhiệm vụ đủ lớn.

RQ1, RQ2 do phần hồi cứu trả lời. RQ3 đến RQ6 do phần thực nghiệm trả lời.

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
- Không so sánh công cụ với công cụ. Ba công cụ dùng mô hình khác hãng, khác hạng nhau; phép so sánh
  luôn là hai cách làm trong cùng một công cụ. Ngoại lệ duy nhất là Sonnet với Opus trong Claude Code
  (RQ5): cùng công cụ, cùng hãng, chỉ khác mô hình, nên là phép so sánh sạch.
- Không viết lại lịch sử repo ViPharmind (không rebase, không force-push các commit đến mốc ở mục 5).
  Commit mới sau mốc được phép (ngày 2026-11-15: gộp `camera-ready` vào `v2.0.0` và chuẩn hóa spec,
  plan dưới `docs/superpowers/`); chúng không ảnh hưởng nghiên cứu vì mọi phân tích dùng mã commit cố định.

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
- Đợt 1 chạy hai mô hình, Claude Sonnet 5.5 và Claude Opus 5.5, để trả lời RQ5. Mọi mô hình ở mọi đợt
  dùng mức effort hoặc mức suy luận medium.
- Nhánh theo đặc tả tái hiện quy trình An thực sự dùng khi làm ViPharmind (spec, plan, làm theo plan),
  với cách chia việc tự nhiên, không ép số bước.
- Chạy bằng gói thuê bao sẵn có của An, không dùng khóa API trả theo lượng dùng.
- Hai thành viên thuyết trình gán nhãn nguyên nhân thất bại độc lập.

## 7. Thiết kế

### 7.1 Phần hồi cứu (RQ1, RQ2)

**Vai trò:** bối cảnh cho thực nghiệm, chiếm khoảng 3–4 trang trong báo cáo. Dữ liệu chỉ cho thống
kê mô tả (mục giới hạn bên dưới), nên không dàn trải thêm; sức chính dồn vào thực nghiệm (RQ3 đến RQ5).
Phần này cũng cho thấy An đã làm ViPharmind theo quy trình spec, plan nào, là quy trình mà nhánh theo
đặc tả của thực nghiệm tái hiện.

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

**Thực tế (2026-11-15).** An duyệt gộp `data/tasks/REVIEW.md`: chấp nhận nguyên văn mọi đề xuất tiêu chí 3 và
mọi nháp đề bài của AI, không sửa từng mục; ba mục có test hành vi chỉ thuộc loại `integration`
(#12, #20, #30) bị loại theo khuyến nghị của trợ lý. Một tác tử duyệt độc lập đã đối chiếu mẫu vài đề bài
với commit gốc. Báo cáo và khai báo sử dụng AI phải ghi đúng như vậy, và nêu ở phần hạn chế rằng đề bài
do AI soạn, tác giả không sửa.

**Chốt trước khi chạy.** Danh sách nhiệm vụ, đề bài, giả thuyết, chỉ số và kế hoạch phân tích được
commit và gắn thẻ git `prereg-v1` trước lượt chạy chính đầu tiên. Lượt chạy trên 2 nhiệm vụ thử được
phép trước thẻ này. Mọi thay đổi sau thẻ phải ghi lại trong báo cáo kèm lý do.

### 7.2b Tầng tính năng (RQ6, H5)

**Lý do.** Đề một commit có trung vị 120 dòng, trong khi một plan của ViPharmind gồm khoảng 11 phần
việc (khoảng 11 commit). Đề nhỏ có thể làm lợi ích của làm theo đặc tả không lộ ra (quyết định của An,
2026-11-15).

**Cách chọn.** Khảo sát khả thi ngày 2026-11-15 (`data/tasks/feature-feasibility/`): gom nguyên plan không
dùng được vì commit của các plan đan xen (dải dài tới 286 commit). Cắt phần lõi của từng plan backend
thành 16 đoạn commit liền nhau (4–12 commit) và chạy bộ test thật ở đầu và cuối mỗi đoạn. Chọn 3 đoạn
mà test ẩn chỉ cần đề bài nêu ít tên (6–25) và collect được độc lập:

| Mã | base | end | commit | Dòng src |
| --- | --- | --- | --- | --- |
| F08 web-api | `45271fddc023` | `cc0f06a67bfa` | 6 | 764 |
| F14 invitations | `c2935909a101` | `11079ab21c7f` | 4 | 1.464 |
| F15 collections | `11079ab21c7f` | `ef23fe8cb403` | 5 | 1.367 |

Trong đợt chọn đầu, F09 và F04 bị loại vì đề bài phải nêu 30–35 tên, gần như là một bản thiết kế viết
sẵn. Từ `prereg-v1`, mọi đoạn (kể cả F04, F07, F09) được xét lại theo cùng ngưỡng tối đa 35 tên. F08 chứa commit của nhiệm vụ nhỏ t03 và nhiệm vụ thử p02; báo cáo ghi chú, phân tích hai tầng
tách riêng.

**Khác với tầng nhỏ.** Mã nền là commit `base`; test ẩn là mọi `test_*.py` thêm hoặc sửa trong đoạn;
khi chấm khôi phục mọi file `backend/tests` đổi trong đoạn và `pyproject.toml`/`uv.lock` từ `end`, rồi
chạy toàn bộ test không mang nhãn `integration`. Đề bài có thêm mục "giao diện bắt buộc" sinh từ
`coupling.json` và `fakes_contract.json`, được Fable 5.2 duyệt độc lập (`data/tasks/FEATURE_REVIEW_fable.md`)
rồi An duyệt. Chạy trên cả 4 nhóm với 3 lần lặp như tầng nhỏ. Giới hạn thời gian đặt theo quy tắc:
tầng nhỏ 3600 s, tầng vừa gấp 2 (7200 s), tầng lớn gấp 3 (10800 s) (`docs/prereg/prereg-v1.md` mục 4).

**Ba tầng kích thước (quyết định của An 2026-11-15, trước thẻ `prereg-v1`).** Phân tích lấy mẫu lại theo
nhiệm vụ, nên số nhiệm vụ quan trọng hơn số lần lặp. Vì vậy giữ 3 lần lặp và tăng số nhiệm vụ:

- **Nhỏ:** 15 nhiệm vụ, mỗi nhiệm vụ 1 commit, 43–311 dòng `backend/src`.
- **Vừa:** tối đa 5 nhiệm vụ `m01`–`m05`, mỗi nhiệm vụ 2–3 commit liền nhau, 300–700 dòng, tối đa 20
  tên trong đề, lấp khoảng trống giữa hai tầng kia.
- **Lớn:** tối đa 5 đoạn trong 16 đoạn của `ranges.json` qua cùng tiêu chí: từ 750 dòng trở lên, tối đa
  35 tên trong đề (F08, F14, F15 và các đoạn khác như F04, F07, F09 nếu qua).

Tiêu chí chọn tầng vừa và hai đoạn lớn thêm giống hệt 3 đoạn đầu (commit liền nhau của một plan, chỉ
backend, test ẩn trượt ở base và đạt ở end, bản vá gốc chấm đạt không hồi quy, đề nêu được mọi tên test
cần), cộng giới hạn số dòng và số tên ở trên. Mọi ứng viên qua tiêu chí đều được nhận; tầng nào có hơn
5 ứng viên thì giữ theo thứ tự cố định (không chứa commit của t01–t15 trước, rồi số tên tăng dần, rồi mã
commit `end`). Mọi ứng viên và lý do loại được ghi ở `data/tasks/feature-feasibility/medium_candidates.json`;
việc chọn không dựa trên bất kỳ lượt chạy AI nào, và không lượt AI nào chạy trên một ứng viên trước thẻ
`prereg-v1.1`. Ràng buộc đầy đủ ở đầu `docs/prereg/prereg-v1.md`. Đề bài qua cùng quy trình: soạn, đối chiếu tên với test ẩn, Fable 5.2 duyệt
độc lập, An duyệt.

**Vì sao mở rộng (quyết định của An, 2026-11-15, sau chạy thử, trước thẻ `prereg-v1`).** Chạy thử cho
thấy Claude gần đạt trần trên đề nhỏ ở cả hai cách làm (11/12 và 12/12), nên khác biệt chỉ có thể lộ
ra ở nhiệm vụ lớn. Chỉ có 3 đoạn commit đủ sạch nên không thêm được đề; tăng lần lặp và số nhóm để
ước lượng ở tầng này đủ chặt. Quyết định này dựa trên hiện tượng chạm trần, không dựa trên hiệu số
giữa hai cách làm ở chạy thử (2 đề, chênh 1 lượt, không có ý nghĩa).

**Giới hạn của bộ chấm ở tầng này.** Test mang nhãn `integration` (cần Postgres thật) không nằm trong
bộ chấm, nên repository Postgres, migration và CLI quản trị của F14, F15 (khoảng một phần ba F15)
không được chấm. Giới hạn này như nhau cho hai cách làm.

### 7.3 Hai cách làm

| | Theo đặc tả | Vibe coding |
| --- | --- | --- |
| Đầu vào | Đề bài | Đề bài |
| Quy trình yêu cầu | Viết tài liệu thiết kế (spec), rồi kế hoạch (plan) chia thành các phần việc, rồi cài đặt theo kế hoạch và tự viết test | "Cài đặt việc này" |
| Người can thiệp | Không | Không |

Khác biệt duy nhất giữa hai cách là lời dặn về quy trình, lưu thành hai file mẫu trong repo. Cùng mô
hình, cùng quyền dùng công cụ, cùng giới hạn lượt và thời gian.

Mỗi lượt là **một phiên duy nhất** cho cả hai cách. Ở cách theo đặc tả, AI viết tài liệu thiết kế và
kế hoạch thành file trong thư mục làm việc rồi cài đặt tiếp trong cùng phiên đó; giới hạn lượt và
thời gian tính cho cả phiên. Không chia thành ba lần gọi riêng, để hai cách chỉ khác nhau ở lời dặn.
Lượt theo đặc tả mà không để lại file thiết kế và kế hoạch được đánh dấu "không tuân thủ quy trình".
Phép thử chính vẫn tính các lượt này (phân tích theo phân bổ); bỏ chúng chỉ là phân tích độ nhạy
(`docs/prereg/prereg-v1.md` mục 2).

**Tái hiện quy trình thật.** Lời dặn của nhánh theo đặc tả mô tả đúng quy trình An dùng khi làm
ViPharmind: viết spec, viết plan, rồi làm theo plan. Plan chia việc theo kích thước tự nhiên, mỗi phần
là một đơn vị trọn vẹn như trong các plan cũ của ViPharmind; lời dặn không đặt số bước hay độ nhỏ của
bước. Lời dặn được viết dựa trên các file spec, plan trong lịch sử ViPharmind (phần hồi cứu) và không
chép nguyên văn skill nào.

**Gọi đúng tên.** Trong báo cáo, nhánh này được gọi là "quy trình đặc tả tự động": AI tự viết thiết kế
và kế hoạch rồi cài đặt, không có người duyệt. Báo cáo đặt nó cạnh các quy trình cùng họ đã công bố
(GitHub Spec Kit, `taghavi_2026`) và đối chiếu với cách người làm nghề thực hành phát triển theo đặc tả
(`agarwal_2026`, `hill_2026`) để nói rõ thí nghiệm đo phần nào của quy trình đó.

Lý do không có nhánh "đặc tả do người duyệt": đặc tả gốc trong lịch sử ViPharmind được viết cho những
phần việc lớn hơn một commit và chỉ có ở một số nhiệm vụ, nên không ghép đều được vào 15 nhiệm vụ.
Hệ quả phải nêu ở phần hạn chế: nhánh "theo đặc tả" ở đây là bản tự động, không có bước người duyệt
đặc tả như quy trình An dùng khi làm ViPharmind.

### 7.4 Bộ chạy

Mỗi lượt chạy:

1. Xuất mã ViPharmind tại commit cha vào một thư mục mới **không kèm lịch sử git**, để AI không đọc
   được các commit tương lai.
2. Xóa các file test ẩn khỏi thư mục đó.
3. Gọi trợ lý lập trình ở chế độ không tương tác với đề bài và lời dặn của cách làm. Mỗi công cụ chạy
   **agent mặc định với bộ công cụ mặc định**, kể cả công cụ web (quyết định của An sau chạy thử,
   ruling R11). Chỉ bỏ phần cài thêm của người dùng: thư mục cấu hình sạch, không plugin, không skill,
   không MCP, không bộ nhớ, không file hướng dẫn riêng. Vì repo ViPharmind công khai, bộ chạy ghi mọi
   đường dẫn tới repo gốc xuất hiện trong nhật ký (`upstream_urls`); phần phân tích chạy lại một lần
   bỏ các lượt có truy cập này, và báo cáo ghi việc mở mạng là một hạn chế.
4. Khi AI dừng hoặc chạm giới hạn, chép test ẩn vào lại và chấm.
5. Lưu kết quả thô: đề bài đã gửi, toàn bộ nhật ký lượt chạy, bản vá, kết quả từng test, số liệu chi
   phí.

**Chạy song song.** Các lượt chạy song song, mỗi lượt một thư mục làm việc và một thư mục cấu hình
riêng, không dùng chung trạng thái. Thời gian chạy đo theo từng lượt. Thứ tự các lượt được xáo trộn
ngẫu nhiên có hạt giống cố định, để hai cách làm không rơi vào hai khung giờ khác nhau của dịch vụ.

Quy mô: 15 nhiệm vụ × 2 cách làm × 3 lần lặp = **90 lượt mỗi mô hình**. Đợt 1 có hai mô hình nên
180 lượt; tổng cả ba đợt là **360 lượt**. Tầng vừa và tầng lớn (mục 7.2b), mỗi tầng tối đa 5 nhiệm
vụ × 2 cách làm × 3 lần lặp × 4 nhóm, thêm tối đa 240 lượt; tổng tối đa **600 lượt**.

| Đợt | Công cụ (bản lúc thiết kế) | Lệnh chạy tự động | Mô hình | Vai trò |
| --- | --- | --- | --- | --- |
| 1 | Claude Code 2.1.325 | `claude -p` | Claude Sonnet 5.5 (`claude-sonnet-5-5`), effort medium | Kết quả chính, RQ3 |
| 1 | Claude Code 2.1.325 | `claude -p` | Claude Opus 5.5 (`claude-opus-5-5`), effort medium | RQ3, RQ5 |
| 2 | Antigravity CLI 1.5.8 (1.5.9 lúc chạy thử) | `agy -p` | Gemini 3.8 Flash Medium (`gemini-3.8-flash-medium`) | Kiểm chứng, RQ4 |
| 3 | Codex CLI 0.162.1 | `codex exec` | `gpt-6-luna`, mức suy luận medium | Kiểm chứng, RQ4 |

Ba đợt dùng cùng nhiệm vụ, cùng đề bài, cùng lời dặn. Bốn nhóm chạy cùng lúc vì mỗi nhóm có hạn mức
riêng; hạn chót thu dữ liệu, cách xử lý nhóm chưa chạy đủ và thứ tự ưu tiên ở `docs/prereg/prereg-v1.md`
mục 10.

Lý do chọn mô hình:

- **Claude Sonnet 5.5 và Claude Opus 5.5** cho đợt chính, đều ở effort medium: một mô hình hạng giữa
  và một mô hình mạnh nhất của cùng hãng, chạy trong cùng công cụ. Nếu Opus đạt gần hết nhiệm vụ ở cả
  hai cách (hiệu ứng trần), đó là kết quả cho RQ5, không phải lỗi thiết kế. Nếu ở 2 nhiệm vụ thử mọi
  lượt của Sonnet đều hỏng ở cả hai cách, xem lại bộ nhiệm vụ trước thẻ `prereg-v1`.
- **Gemini 3.8 Flash Medium:** An chọn mức Medium trong các mô hình của Google mà tài khoản
  Antigravity có. Không dùng các mô hình Claude có trong Antigravity vì cùng họ với đợt 1.
- **`gpt-6-luna`:** mô hình duy nhất tài khoản Codex của An có.

**Gói thuê bao.** Mọi lượt chạy dùng tài khoản thuê bao đã đăng nhập. Hệ quả cho bộ chạy:

- Thư mục cấu hình sạch vẫn phải giữ thông tin đăng nhập của công cụ.
- Khi chạm hạn mức, bộ chạy tạm dừng và chạy lại đúng lượt đó sau; lượt bị ngắt vì hạn mức không tính
  là thất bại và không tính vào 3 lần lặp.
- Chi phí bằng tiền là số quy đổi: lượng token thật của mỗi lượt (tách đọc cache, ghi cache) nhân với
  một bảng giá API công khai chốt ngày 2026-11-15 (`docs/prereg/prereg-v1.md` mục 7), ghi rõ là quy đổi.

**Nhiều tài khoản và proxy.** Theo ruling R11 (sau chạy thử), lượt chính không chạy qua proxy: mọi
công cụ gọi thẳng CLI của nó, proxy chỉ là nơi lấy token đăng nhập của các tài khoản phụ. Phần dưới
ghi lại cấu hình lúc thiết kế; chỗ nào nói chạy qua proxy thì không còn áp dụng.

An có nhiều tài khoản để đổi khi hết hạn mức. Thông tin đăng nhập nằm
trong proxy `cli-proxy-api` (v8.0.28) của repo
`/home/andv/personal/HUST/principle-technique-program-analysis`, thư mục `infra/proxy/`, dùng chung
volume Docker `vipharmind_cli_proxy_auth`. Theo `infra/proxy/MODELS.md` ngày 2026-11-08: 4 tài khoản
Antigravity, 4 tài khoản Codex miễn phí, 1 tài khoản Claude; proxy chia lượt xoay vòng và tự đổi tài
khoản khi một tài khoản hết hạn mức. Proxy là cổng gọi mô hình kiểu API, không phải trợ lý lập trình,
nên mỗi công cụ dùng nó theo cách riêng:

- **Claude Code:** 1 tài khoản, chạy thẳng bằng đăng nhập sẵn có, không qua proxy (token Claude trong
  proxy không dùng được cho Claude Code).
- **Codex CLI:** chạy thẳng `codex exec`, xoay vòng các đăng nhập trực tiếp như Antigravity.
- **Antigravity CLI:** chạy thẳng `agy` vì mức Medium chỉ có ở đó. Xoay vòng các đăng nhập trực tiếp:
  tài khoản 1 là `~/.gemini`, các tài khoản khác lấy token đăng nhập trong proxy chuyển sang định dạng
  của `agy` (đã chạy thử từng tài khoản). Bộ chạy tự đổi sang tài khoản kế tiếp khi hết hạn mức.

Mọi tài khoản đều của An. An quyết định xoay vòng nhiều tài khoản là chấp nhận được (2026-11-15).

Ràng buộc khi dùng proxy và nhiều tài khoản:

- Không chép khóa, token hay file cấu hình của proxy vào repo này; chỉ ghi đường dẫn.
- Proxy có thể sửa yêu cầu gửi đi (ép mức suy luận, đổi mô hình phía sau một tên gọi). Dùng cấu hình
  không ép mức suy luận, và ghi mô hình thực tế được phục vụ cho từng lượt.
- Ghi lại tài khoản thứ mấy (số thứ tự, không ghi email) phục vụ từng lượt. Báo cáo nêu rõ thí nghiệm
  chạy trên nhiều tài khoản (không qua proxy, ruling R11).

Phải kiểm tra khi chạy 2 nhiệm vụ thử, trước thẻ `prereg-v1`: điều khoản của từng gói về chạy tự
động; hạn mức thực tế; mỗi công cụ có trả lượng token hay không. Công cụ nào không cho chạy tự động thì
loại khỏi thí nghiệm và ghi lý do. (Yêu cầu tắt truy cập web đã bỏ theo ruling R11: mạng mở là hạn chế
được chấp nhận, xem mục 7.4.)

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
quy hơn và có chỉ số bảo trì không kém hơn. H4, khoảng cách về tỉ lệ đạt giữa hai cách làm ở Sonnet
lớn hơn ở Opus, tức làm theo đặc tả giúp mô hình yếu hơn nhiều hơn. H5, hiệu số tỉ lệ đạt (đặc tả trừ
vibe) tăng theo kích thước nhiệm vụ: ở tầng lớn lớn hơn ở tầng nhỏ, và tăng theo số dòng của bản vá gốc.

**Phân tích.** Phép thử xác nhận duy nhất là H1 trên nhóm `claude-sonnet`, tầng nhỏ; H5 là phép thử
phụ quan trọng nhất; còn lại là phụ (chi tiết ở `docs/prereg/prereg-v1.md` mục 9). So sánh theo cặp trên
từng nhiệm vụ. Báo cáo hiệu số kèm khoảng tin cậy bootstrap lấy mẫu lại theo nhiệm vụ. Với 15 nhiệm vụ, báo cáo cỡ hiệu ứng và khoảng tin cậy, không dựa kết luận
vào ngưỡng p. Báo cáo cả độ dao động giữa 3 lần lặp của cùng một nhiệm vụ.

Với RQ5, phân tích đợt 1 như một thiết kế 2 × 2 (cách làm × mô hình): báo cáo bốn tỉ lệ đạt, hiệu số
giữa hai cách làm ở từng mô hình, và hiệu của hai hiệu số đó (tương tác) kèm khoảng tin cậy bootstrap
theo nhiệm vụ. So sánh thêm Sonnet theo đặc tả với Opus vibe coding về tỉ lệ đạt và chi phí quy đổi.

**H5, tương tác cách làm × kích thước.** Phép thử chính: hiệu của hai hiệu số (tầng lớn trừ tầng
nhỏ) của tỉ lệ đạt đặc tả trừ vibe, gộp các nhóm chạy đủ ở cả ba tầng, kèm khoảng tin cậy bootstrap
lấy mẫu lại theo nhiệm vụ trong từng tầng. Phân tích bổ trợ trên mọi nhiệm vụ của ba tầng: hồi quy
logistic hỗn hợp `pass ~ arm × log(src_lines) + cohort + (1 + arm | task)`, có phương án lùi khi không
hội tụ (`docs/prereg/prereg-v1.md` mục 9, điểm 4); báo cáo hệ số tương tác và hình
"hiệu số theo kích thước" (mỗi điểm là một nhiệm vụ, đường xu hướng kèm dải tin cậy). Tầng vừa và tầng lớn mỗi tầng
chỉ có tối đa 5 nhiệm vụ, nên báo cáo nêu rõ đây là bằng chứng sơ bộ; mọi hướng kết quả (có, không, ngược
chiều) đều được báo cáo như nhau.

**Hiệu quả chi phí (bổ sung, quyết định của An 2026-11-15).** Với từng nhóm và từng tầng, báo cáo số
lượt đạt trên mỗi đô quy đổi (tổng lượt đạt chia tổng chi phí quy đổi) của hai cách làm, và chi phí
quy đổi trung bình cho một lượt đạt, kèm khoảng tin cậy bootstrap theo nhiệm vụ.

**Ca nghiên cứu định tính (bổ sung, quyết định của An 2026-11-15).** Quy tắc chọn chốt trước: trong tầng
lớn, với nhóm `claude-sonnet`, lấy nhiệm vụ có trị tuyệt đối hiệu số tỉ lệ đạt giữa hai cách
làm lớn nhất (hòa thì lấy nhiệm vụ có bản vá gốc lớn hơn); trong nhiệm vụ đó, lấy lượt có số lần lặp
nhỏ nhất của mỗi cách làm (ưu tiên một lượt đạt và một lượt không đạt nếu hai cách làm khác kết quả).
Đặt cạnh nhau: thiết kế và kế hoạch AI viết (cách làm theo đặc tả), chuỗi hành động chính, chỗ sai,
cách sửa, test ẩn trượt, chi phí. Nếu mọi nhiệm vụ tầng lớn có hiệu số bằng 0 thì lấy nhiệm vụ có bản
vá gốc lớn nhất. Trích nguyên văn nhật ký, đã xóa email. Phần này minh họa cơ chế, không dùng để kết luận.

**Theo kích thước nhiệm vụ.** Chia 15 nhiệm vụ theo số dòng thay đổi của bản vá gốc (nhỏ, vừa, lớn,
ngưỡng chốt trước thẻ `prereg-v1`) và báo cáo hiệu số giữa hai cách làm ở từng nhóm. Đây là phân tích
khám phá vì mỗi nhóm chỉ có khoảng 5 nhiệm vụ, không dùng để kết luận.

### 7.6 Phân tích lỗi và kiểm tra bằng người

- **Gán nhãn nguyên nhân thất bại.** Hai thành viên thuyết trình gán nhãn độc lập cho mọi lượt hợp lệ
  không đạt của hai nhóm Claude ở cả ba tầng, theo một bảng nhãn có định nghĩa và ví dụ. Họ nhận kết quả
  test và bản vá đã bỏ file thiết kế, kế hoạch, dưới mã ngẫu nhiên. Việc làm mù chỉ là một phần, vì bản
  vá vẫn có thể để lộ cách làm; người gán ghi "lộ cách làm" khi nhận ra. Báo cáo hệ số kappa của Cohen.
  Chỗ lệch nhau do An phân xử và ghi lại.
- **Bảng nhãn:** hiểu sai yêu cầu; làm thiếu; sai giao diện đã nêu trong đề bài; làm hỏng chức năng cũ;
  lỗi logic; không hoàn thành trong giới hạn; lỗi môi trường; cộng hai nhãn từ gán thử: đề bài thiếu
  hoặc mơ hồ; dùng sai kiểu hoặc API có sẵn của dự án. Bảng khóa tại thẻ `prereg-v1`
  (`docs/prereg/labeling-guide.md`).
- **Đạt test nhưng sai.** An đọc một mẫu ngẫu nhiên 20 lượt đạt, đối chiếu với bản vá gốc, ghi lại
  trường hợp mã đạt test nhưng sai hoặc thiếu hành vi.

### 7.7 Hạn chế phải nêu trong báo cáo

- Một dự án, một ngôn ngữ (Python), 15 nhiệm vụ một commit cộng tối đa 10 nhiệm vụ nhiều commit; các
  tầng có nhiệm vụ chung commit hoặc chung test ẩn.
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
docs/proposal/                 đề cương 1–2 trang
code/retrospective/            mã phân tích hồi cứu và kết quả
data/tasks/                    15 nhiệm vụ và 2 nhiệm vụ thử: commit, đề bài, danh sách test ẩn
code/prompts/                  hai file lời dặn của hai cách làm
code/harness/                  bộ chạy và bộ chấm
data/results/raw/              kết quả thô từng lượt
data/results/analysis/         bảng, hình, mã phân tích
labeling/                 bảng nhãn, phiếu gán nhãn của hai người, kết quả phân xử
docs/report/              báo cáo 15–20 trang
docs/presentation/        bài thuyết trình 15 phút (template-vi.pptx)
docs/team/                     bản kê đóng góp, mẫu đánh giá chéo, khai báo sử dụng AI, tài liệu chuẩn bị hỏi đáp
```

Sản phẩm theo yêu cầu của thầy:

| Yêu cầu | Ở đâu |
| --- | --- |
| Đề cương 1–2 trang | `docs/proposal/`, rút từ mục 1, 3, 5, 7 |
| Báo cáo viết 15–20 trang | `docs/report/` |
| Thuyết trình 15 phút, hỏi đáp 5 phút | `docs/presentation/`, `docs/team/` |
| Kho mã, dữ liệu, nội dung yêu cầu đã dùng, kết quả thô | repo này; đề bài ở `data/tasks/` và `code/prompts/`, kết quả thô ở `data/results/raw/` |
| Bản kê đóng góp cá nhân và khai báo sử dụng AI | `docs/team/` |

Tổng quan tài liệu trong báo cáo: tìm có quy trình, ghi lại từ khóa, nguồn, tiêu chí chọn, số bài tìm
được, sàng lọc, giữ lại; khoảng 15–25 nguồn, ưu tiên hội nghị và tạp chí có bình duyệt, 2023–2026.
Nhật ký tìm kiếm ở `docs/report/literature-log.md`. Ba nhóm:
bộ đo cho trợ lý lập trình và hạn chế của chúng; nghiên cứu về năng suất khi dùng AI; phát triển
theo đặc tả với AI. Mọi trích dẫn phải được mở và kiểm tra, không trích theo trí nhớ.

Khai báo sử dụng AI nêu đầy đủ: AI được dùng để làm ViPharmind, để dựng bộ chạy, để viết báo cáo và
slide, và là đối tượng được đo.

Thứ tự làm, mỗi bước là một kế hoạch riêng:

1. Đề cương.
2. Bộ nhiệm vụ và bộ chạy, chạy thử 2 nhiệm vụ, gắn thẻ `prereg-v1`. Làm sớm vì đây là rủi ro khả
   thi lớn nhất (hạn mức, tắt truy cập web, số token).
3. Chạy chính bốn nhóm cùng lúc, tầng nhỏ trước, rồi tầng vừa và tầng lớn sau thẻ `prereg-v1.1`;
   phân tích sau thẻ `prereg-v1-analysis`. Kết quả đầu tiên dùng cho báo cáo tiến độ.
4. Gán nhãn và kiểm tra bằng người.
5. Phân tích hồi cứu, bản gọn.
6. (Gộp vào bước 3: Antigravity và Codex chạy cùng lúc với Claude Code.)
7. Báo cáo, slide, tài liệu hỏi đáp.

Việc không phụ thuộc nhau thì chạy song song: tổng quan tài liệu và phân tích hồi cứu chạy cùng lúc
với bước 2–3; bốn nhóm chạy cùng lúc với nhau.

**Báo cáo tiến độ** (mốc thứ ba của thầy): nộp sau khi có kết quả chạy thử hoặc đợt 1, kèm số liệu
đầu tiên, để góp ý của thầy còn kịp vào thiết kế.

## 9. Phần để người thực hiện tự quyết

- Ngôn ngữ và thư viện của bộ chạy, bộ phân tích (mặc định: Python với `uv`, giống ViPharmind).
- Định dạng file nhiệm vụ và file kết quả thô.
- Cách xuất mã không kèm lịch sử và cách cô lập từng lượt chạy.
- Giới hạn thời gian cho mỗi lượt: đã chốt theo quy tắc ở `docs/prereg/prereg-v1.md` mục 4.
- Công cụ soạn báo cáo và slide (mặc định: LaTeX cho báo cáo, ppt-master cho slide như bài SoICT).
- Cách lọc khóa API và dữ liệu riêng khỏi nhật ký phiên.
- Số bản ghi và cách chọn mẫu khi trích nhật ký phiên làm minh họa.
