# Bản bổ sung `prereg-v1.2`: Haiku và điều kiện đề sơ sài (thăm dò)

Ngày: 2026-11-16. Văn bản này bổ sung `prereg/prereg-v1.md` và `prereg/prereg-v1.1.md`. Nó thêm hai thí
nghiệm **thăm dò**. Mọi điều hai văn bản trước không nói khác ở đây thì giữ nguyên; văn bản này không đổi
giả thuyết H1–H5, chỉ số, kế hoạch phân tích hay quy tắc loại của thí nghiệm chính.

An quyết định ngày: **2026-11-16** (yêu cầu thêm đề sơ sài và Haiku, chọn quy mô đầy đủ cho cả hai).

## Vị trí của văn bản này: viết sau khi đã thấy kết quả chính

- Văn bản này được viết **sau khi** An và trợ lý AI đã xem số liệu mô tả của thí nghiệm chính (sáng
  2026-11-16): tỉ lệ đạt theo nhóm, tầng và cách làm của claude-sonnet, claude-opus, codex-luna và phần
  agy-gemini đã xong; trung vị số test tự viết, độ phủ, hồi quy, vi phạm kiến trúc, thời gian và token.
  Mục 11 của `prereg-v1` ghi lại việc mở kết quả này.
- Lý do thêm, nêu đúng như đã xảy ra: (1) đề bài của thí nghiệm chính nêu đủ tên, chữ ký và quy tắc, nên
  nhánh vibe nhận một yêu cầu chi tiết hơn nhiều so với vibe coding thật, nơi đề thường chỉ một hai câu;
  (2) kết quả chính gợi ý quy trình giúp agent yếu hơn nhiều hơn (Codex), nên cần thêm một agent yếu hơn
  trong cùng họ Claude.
- Vì cả hai lý do đều đến từ việc đã xem kết quả, **mọi phân tích trong văn bản này là thăm dò**. Báo cáo
  phải gọi chúng là thăm dò, không dùng chúng để xác nhận hay bác bỏ H1–H5, và nêu rằng chúng được thêm sau
  khi thấy kết quả chính.
- Các quy tắc dưới đây (đề sơ sài, danh sách hành vi, cách chấm, lệnh chạy, phân tích) được chốt bằng thẻ
  `prereg-v1.2` **trước lượt AI đầu tiên** của hai thí nghiệm này.

## Thí nghiệm E1: Haiku theo thiết kế gốc

- Nhóm mới `claude-haiku`: Claude Code, mô hình `claude-haiku-5-5`, effort medium, tài khoản 1 (cùng CLI,
  cùng tài khoản với hai nhóm Claude kia; `harness/cohorts.toml`).
- Đúng thiết kế chính: 23 nhiệm vụ (t01–t15, m01–m05, f08, f14, f15), hai cách làm, 3 lần lặp, đề
  `prompt.md`, giới hạn thời gian theo tầng (3600 / 7200 / 10800 s), hạt giống 20261115. 138 lượt.
- Phân tích bằng đúng mã đã khóa ở thẻ `prereg-v1-analysis`, nhưng là phân tích riêng (thêm Haiku như một
  nhóm), không gộp vào kết quả xác nhận. Báo cáo so sánh Haiku với Sonnet và Opus một cách mô tả.

## Thí nghiệm E2: đề sơ sài (thiết kế 2 × 2)

### Đề sơ sài

Mỗi nhiệm vụ có thêm `tasks/<id>/brief.md`. Quy tắc viết (chốt trước khi viết, kiểm bằng máy khi lưu):

- một hoặc hai câu, **không quá 30 từ**, viết như người dùng nhờ agent;
- nêu mục tiêu của thay đổi, rút từ câu đầu của `prompt.md`; được nêu khái niệm sản phẩm và dịch vụ hay
  thư viện bên ngoài đã có trong câu đó (ví dụ Gmail API, Langfuse, DeepInfra, fastapi-users);
- **không** có đường dẫn module, tên lớp hay hàm, chữ ký, tên trường, tên lỗi, hằng số hay giá trị số
  mặc định; không có ký tự `` ` ``; không có chuỗi dạng `a_b` hay `f()`.

Đề sơ sài được viết một lần, trước mọi lượt E2, và không sửa sau đó. Độ dài và tiền tố mã băm SHA-256:

| Nhiệm vụ | Số từ | sha256 (16 ký tự đầu) |
|---|---|---|
| t01 | 24 | d8d1cb56349faa18 |
| t02 | 26 | 02e4af02869ddecf |
| t03 | 21 | 082070b5bade4d8d |
| t04 | 17 | 3d41f222aa8b25f1 |
| t05 | 18 | 871a946a45346342 |
| t06 | 21 | ce1252603b13d6ae |
| t07 | 18 | 579c2f7f2b068ff1 |
| t08 | 17 | 01b9b0355a946632 |
| t09 | 17 | 7a36e05c2f1640ea |
| t10 | 16 | 0c6e4aa749eb3961 |
| t11 | 16 | f62f85b974829392 |
| t12 | 20 | 647ff66c6f740d5b |
| t13 | 17 | fc6aed15551cab07 |
| t14 | 6 | e6a443f43300f48b |
| t15 | 13 | 8c8d4f280f72a570 |
| m01 | 24 | b349f1ca2ba78dfb |
| m02 | 26 | 9571edefd48d7961 |
| m03 | 21 | 6fef81f21cffe7b3 |
| m04 | 24 | de9ef245b219fd03 |
| m05 | 22 | 65bf6703c1565c1e |
| f08 | 24 | 7c23fe1c7ef92cbf |
| f14 | 24 | f8e929fc078f673e |
| f15 | 21 | d4dd909fb33c2296 |

### Các điều kiện

- Hai cách làm giữ nguyên khối hướng dẫn (`prompts/spec.md`, `prompts/vibe.md`); chỉ phần đề đổi từ
  `prompt.md` sang `brief.md` (cờ `--prompt-file brief.md`, ghi vào `meta.json` trường `prompt_file`).
- Nhóm: `claude-sonnet`, `claude-opus`, `claude-haiku`, `codex-luna`. agy-gemini không chạy E2 vì hết
  hạn mức. 23 nhiệm vụ × 2 cách làm × 3 lần lặp × 4 nhóm = **552 lượt**.
- Kết hợp với thí nghiệm chính (đề chi tiết) thành thiết kế 2 × 2: mức chi tiết của đề × cách làm.

### Chỉ số của E2

1. **Tỉ lệ đạt bài kiểm tra ẩn**: vẫn được tính và báo cáo, nhưng **không** được đọc là độ đúng, vì bài
   kiểm tra ẩn gọi đúng tên mà đề sơ sài không nêu. Dự kiến gần 0.
2. **Chỉ số tự động** (đọc được cho cả hai mức chi tiết, như thí nghiệm chính): hồi quy trên bộ test sẵn có,
   lỗi ruff và pyrefly, kiến trúc, số test AI tự viết, độ phủ dòng thay đổi, số dòng, thời gian, token.
3. **Điểm danh sách hành vi** (chỉ số chính của E2): tỉ lệ mục hành vi được đáp ứng, xem dưới.

### Danh sách hành vi và cách chấm

- **Danh sách**: mỗi nhiệm vụ một tệp `tasks/<id>/checklist.md`, rút **chỉ từ các bài kiểm tra ẩn** của
  nhiệm vụ: mỗi hành vi mà bài kiểm tra khẳng định thành một mục, viết bằng lời, không đòi đúng tên (ví
  dụ "xóa tổ chức đòi nhập lại đúng tên tổ chức"). Danh sách được viết và chốt bằng một commit **trước khi
  chấm** lượt E2 nào, và không sửa sau khi đã thấy một kết quả chấm nào. Người viết không xem bản vá của
  lượt E2 nào khi viết.
- **Người chấm máy**: một agent cố định, `codex` với `gpt-6-luna`, effort medium, prompt chấm cố định
  (`prompts/judge.md`, chốt cùng danh sách), chạy trong thư mục sạch chứa cây mã cuối của lượt. Trước khi
  chấm, `docs/design.md` và `docs/plan.md` bị xóa và thư mục không mang tên nhóm, cách làm hay lần lặp.
  Người chấm được đọc và chạy mã; mỗi mục cho một nhãn `met`, `not_met` hoặc `unclear` cùng lý do ngắn.
  Điểm của lượt = số `met` / số mục; `unclear` tính là không đạt và được đếm riêng.
- **Che cách làm chưa trọn**: test do AI viết vẫn còn trong cây mã, nên người chấm có thể đoán được nhánh
  spec. Đây là hạn chế phải nêu.
- **Kiểm tra độ tin cậy của người chấm máy**:
  (a) Lợi và Bảo chấm tay, độc lập, một mẫu ngẫu nhiên 24 lượt E2 (phân tầng theo nhóm và cách làm, hạt
  giống 20261115), cũng bị che cách làm như người chấm máy; báo cáo tỉ lệ đồng ý theo mục và kappa của Cohen
  giữa người với người và giữa người với máy.
  (b) Người chấm máy chấm thêm một mẫu ngẫu nhiên 48 lượt **đề chi tiết** của thí nghiệm chính (phân tầng
  theo nhóm, cách làm và kết quả đạt hay không); báo cáo mức khớp giữa "đạt mọi mục" và "đạt bài kiểm tra
  ẩn". Đây là kiểm tra tính hợp lệ của danh sách.
- Nếu đủ hạn mức, người chấm máy chấm **mọi** lượt đề chi tiết của bốn nhóm E2 để so điểm danh sách giữa
  hai mức chi tiết; nếu không, so sánh giữa hai mức chi tiết chỉ dùng chỉ số tự động, và báo cáo nói rõ.

### Phân tích của E2 (thăm dò)

- So sánh chính: trong điều kiện đề sơ sài, chênh lệch điểm danh sách hành vi giữa spec và vibe, theo
  từng nhóm và gộp, với khoảng tin cậy bootstrap theo nhiệm vụ (như mục 9 của `prereg-v1`, hạt giống
  20261115, 9999 lần).
- So sánh 2 × 2: tương tác giữa mức chi tiết và cách làm trên các chỉ số tự động (hồi quy, test tự viết,
  độ phủ, token) và, nếu có điểm danh sách cho đề chi tiết, trên điểm danh sách. Đọc theo dấu và độ lớn,
  không kiểm định xác nhận.
- Không có ngưỡng ý nghĩa; báo cáo ước lượng và khoảng tin cậy, kèm câu "thăm dò, thêm sau khi thấy kết
  quả chính".

## Lệnh chạy

Chạy từ một cây làm việc riêng tại commit mang thẻ `prereg-v1.2` (`../vipharmind-ai-sdlc-study-run3`),
mỗi tầng một lệnh, cùng các thông số khác như thí nghiệm chính (`--reps 3 --jobs 8 --seed 20261115`).
Hai chuỗi lệnh chạy song song; trong mỗi chuỗi, các tầng chạy lần lượt nhỏ → vừa → lớn.

E1 (đầu ra `results/raw/haiku`, thư mục làm việc `/tmp/sdlc-runs-haiku`):

```
harness/.venv/bin/sdlc-harness run --repo /home/andv/personal/vipharmind \
  --cohorts claude-haiku --tasks <tầng> --reps 3 --jobs 8 --seed 20261115 \
  --timeout-s <3600|7200|10800> --out results/raw/haiku --work-root /tmp/sdlc-runs-haiku
```

E2 (đầu ra `results/raw/brief`, thư mục làm việc `/tmp/sdlc-runs-brief`):

```
harness/.venv/bin/sdlc-harness run --repo /home/andv/personal/vipharmind \
  --cohorts claude-sonnet,claude-opus,claude-haiku,codex-luna --tasks <tầng> \
  --prompt-file brief.md --reps 3 --jobs 8 --seed 20261115 \
  --timeout-s <3600|7200|10800> --out results/raw/brief --work-root /tmp/sdlc-runs-brief
```

`<tầng>` là `t01,…,t15`, `m01,…,m05` hoặc `f08,f14,f15`, ghi rõ từng mã. Mọi quy tắc kết cục ở mục 4
của `prereg-v1` áp dụng nguyên. Hạn chót như agy-gemini: **2026-11-29**; lượt chưa xong lúc đó được báo
cáo là thiếu, phân tích chạy trên phần đã có và ghi rõ.

## Hạn chế phải nêu

- Thêm sau khi thấy kết quả chính; thăm dò.
- Đề sơ sài do trợ lý AI viết theo quy tắc; một người dùng thật có thể viết khác.
- Người chấm máy là một mô hình cũng có trong các nhóm (Codex), có thể thiên vị bài của chính nó; báo cáo
  điểm theo nhóm và mức khớp với người chấm.
- Cách làm chỉ được che một phần với người chấm.
- Claude chỉ có một tài khoản: ba nhóm Claude của E1 và E2 chia nhau hạn mức, nên thời gian chạy có thể
  kéo dài và tốc độ phản hồi có thể khác thí nghiệm chính.

## Chốt danh sách hành vi và người chấm (2026-11-16, trước khi chấm lượt nào)

- `tasks/<id>/checklist.md` của 23 nhiệm vụ (306 mục) do một agent riêng viết chỉ từ các bài kiểm tra mà commit
  của nhiệm vụ thêm hoặc sửa; agent đó không mở thư mục kết quả nào. Ghi chú từng nhiệm vụ: `tasks/CHECKLIST_NOTES.md`.
- **Điểm phụ `score_core`** (thêm trước khi chấm): một agent riêng khác gắn ` [exact]` cho mục mà muốn đạt phải có
  một giá trị chữ cụ thể không xác định được từ `brief.md` cộng cây mã khởi đầu mà agent thấy (sau khi bỏ các thư mục
  `superpowers` và tệp cấu hình agent) hay từ hợp đồng của dịch vụ bên ngoài được nêu tên. 45/306 mục được gắn, ở 15
  nhiệm vụ (`tasks/CHECKLIST_EXACT.md`). Điểm chính `score` vẫn tính trên mọi mục; `score_core` bỏ các mục `[exact]`
  và là phân tích độ nhạy. Người chấm không thấy thẻ `[exact]`.
- Prompt chấm: `prompts/judge.md`. Mã chấm: `sdlc-harness judge` (`harness/src/sdlc_harness/judge.py`); kết quả
  mỗi lượt ở `judge.json` cạnh `grade.json`. Mỗi lượt được thử tối đa 4 lần (xoay tài khoản khi hết hạn mức, đăng
  nhập lỗi hoặc câu trả lời không đúng dạng); lượt vẫn hỏng sau đó được báo cáo là thiếu điểm.
- Thẻ `prereg-v1.2-judge` chốt các tệp trên trước lượt chấm đầu tiên.
