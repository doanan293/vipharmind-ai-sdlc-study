# Đăng ký trước, phiên bản 1 (`prereg-v1`)

Ngày: 2026-11-15. Nghiên cứu: *Phát triển theo đặc tả so với vibe coding: nghiên cứu tình huống và thực
nghiệm đối chứng trên một dự án phần mềm AI cho ngành dược Việt Nam*. Bản thiết kế đầy đủ:
`docs/superpowers/specs/2026-11-15-spec-vs-vibe-study-design.md`. Văn bản này chốt những gì sẽ chạy và
cách phân tích **trước lượt chạy chính đầu tiên**. Mọi thay đổi sau thẻ `prereg-v1` được ghi ở mục 11,
kèm ngày và lý do. Chỗ văn bản này khác bản thiết kế thì văn bản này được áp dụng.

An duyệt văn bản này ngày: **2026-11-15** (cùng ngày An duyệt lại đề t05, t07, t13; hạn thu dữ liệu 2026-11-29 và ngưỡng −5 điểm MI được An xác nhận).

## Phạm vi và bản bổ sung `prereg-v1.1`

Phạm vi của bản này: **tầng nhỏ** (15 nhiệm vụ một commit) và toàn bộ giả thuyết, chỉ số, phân tích cho
cả ba tầng. Bản bổ sung `prereg-v1.1` chỉ được thêm: mã nhiệm vụ, commit `base` và `end`, số dòng
`backend/src`, số tên nêu trong đề, mã băm SHA-256 của từng đề bài tầng vừa và tầng lớn. Nó không được
đổi giả thuyết, chỉ số, kế hoạch phân tích, số lần lặp, giới hạn thời gian hay quy tắc loại.

Ràng buộc cho `prereg-v1.1`:

1. **Thời điểm.** Thẻ `prereg-v1.1` được gắn trước lượt chạy chính đầu tiên của bất kỳ tầng nào. Nếu
   không kịp, lượt chạy chính tầng nhỏ được phép bắt đầu trước, nhưng khi đó không ai mở `grade.json`
   hay tính tỉ lệ đạt của tầng nhỏ cho tới khi `prereg-v1.1` đã gắn thẻ; trong lúc chờ chỉ được xem số
   lượt theo trạng thái. Mục 11 ghi ngày gắn thẻ và ngày mở kết quả.
2. **Tập ứng viên.** Ứng viên tầng lớn là 16 đoạn trong `sub_ranges` của
   `tasks/feature-feasibility/ranges.json` tại thẻ `prereg-v1`. Ứng viên tầng vừa là mọi đoạn 2–3 commit
   liền nhau nằm trong 16 đoạn đó. Mọi ứng viên, kết quả từng tiêu chí và lý do loại được ghi ở
   `tasks/feature-feasibility/medium_candidates.json` và commit cùng `prereg-v1.1`.
3. **Tiêu chí, áp dụng như nhau cho mọi ứng viên:**
   - Chung cho hai tầng: các commit liền nhau của cùng một plan; chỉ đổi `backend/`; có test ẩn trượt ở
     `base` và đạt ở `end`; bản vá gốc (`git diff base end`) chấm `task_pass = true`, không hồi quy.
   - Tầng vừa: 2–3 commit liền nhau; 300–700 dòng `backend/src`; đề bài nêu được mọi tên test ẩn cần với
     **tối đa 20 tên**.
   - Tầng lớn: một đoạn commit liền nhau; từ 750 dòng `backend/src` trở lên; **tối đa 35 tên**. Mọi đoạn
     trong 16 đoạn được xét theo cùng ngưỡng này, kể cả F04, F07 và F09.
4. **Không có quyền chọn.** Mọi ứng viên qua tiêu chí đều được nhận. Nếu một tầng có hơn 5 ứng viên qua,
   giữ 5 ứng viên theo thứ tự: không chứa commit của t01–t15 trước, rồi số tên trong đề tăng dần, rồi mã
   commit `end` tăng dần. Hai nhiệm vụ tầng vừa không được chung commit; khi hai ứng viên chung commit,
   giữ ứng viên đứng trước theo thứ tự trên.
5. **Không chạy AI trước khi chốt.** Trước khi tầng của nó được chốt bằng thẻ `prereg-v1.1`, không lượt AI
   nào chạy trên một ứng viên hay một nhiệm vụ chính. Kế hoạch chạy thử `f08` trước đây bị bỏ. Kiểm tra bộ
   chạy cho nhiệm vụ nhiều commit chỉ dùng việc chấm bản vá gốc, không gọi AI. Giới hạn thời gian của tầng
   vừa và tầng lớn đặt theo quy tắc ở mục 4, không theo lượt chạy nào.
6. **Đề bài** qua đúng quy trình của F08, F14, F15: soạn, đối chiếu tên với test ẩn, Fable 5.2 duyệt độc
   lập, An duyệt. Người soạn và người duyệt không xem kết quả chính của tầng nhỏ.
7. **Chồng lấn.** `prereg-v1.1` liệt kê mọi cặp nhiệm vụ chung commit hoặc chung file test ẩn giữa các
   tầng (đã biết: F08 chứa commit của t03 và p02; F14 bắt đầu từ commit của t01 và có test ẩn của t02;
   F15 nối tiếp F14 và có test ẩn của t11). Báo cáo nêu hạn chế này. Phân tích độ nhạy của H5 (mục 9,
   điểm 7) bỏ các nhiệm vụ có commit nằm trong một nhiệm vụ của tầng khác.

## 1. Nhiệm vụ tầng nhỏ

Mã ViPharmind cố định ở commit `3baae61d764f6d83f7205d0d4d97ee52dd8e0dbe` (nhánh main). Mỗi nhiệm vụ là
một commit; mã nền là commit cha; test ẩn là test do commit đó thêm hoặc sửa. Đề bài: `tasks/<id>/prompt.md`
(do AI soạn, An duyệt gộp; t05, t07, t13 được bổ sung tên giao diện sau khi đối chiếu với test ẩn,
`tasks/PROMPT_AUDIT.md`, commit `e92f346`). An duyệt lại ba đề đã sửa cùng ngày duyệt văn bản này (dòng
duyệt ở đầu văn bản).

| Id | Commit | Lớp | Dòng `backend/src` | Nhóm kích thước |
| --- | --- | --- | --- | --- |
| t08 | `8dd6a9cdc9c4` | domain | 43 | nhỏ |
| t12 | `94a54f86965e` | infrastructure | 45 | nhỏ |
| t06 | `77cd48cd2933` | domain | 67 | nhỏ |
| t14 | `86a0dae1a6e1` | infrastructure | 68 | nhỏ |
| t04 | `f2b898af9761` | infrastructure | 73 | nhỏ |
| t11 | `3f87109556c3` | domain | 102 | vừa |
| t09 | `c04c67decc63` | infrastructure | 120 | vừa |
| t15 | `0a6b1f0680aa` | infrastructure | 121 | vừa |
| t10 | `44466f373da6` | infrastructure | 141 | vừa |
| t13 | `7757b6cc65a5` | infrastructure | 148 | vừa |
| t05 | `650abbd0ebec` | domain | 186 | lớn |
| t02 | `f8949eca395e` | application | 197 | lớn |
| t03 | `c3a88b2659d7` | api | 198 | lớn |
| t07 | `cd9ce5833b47` | domain | 232 | lớn |
| t01 | `c2935909a101` | application | 311 | lớn |

Ngưỡng nhóm kích thước trong tầng nhỏ: ≤ 82, 83–173, ≥ 174 dòng. p01, p02 là nhiệm vụ chạy thử, không
tính vào kết quả.

Số test ẩn của từng nhiệm vụ được báo cáo trong bảng nhiệm vụ của báo cáo; t06 và t13 chỉ có 2 test ẩn.

Thẻ `prereg-v1` chốt toàn bộ cây tại commit mang thẻ: `tasks/t01`–`t15` (`task.toml`, `prompt.md`),
`prompts/`, `harness/` (mã, `cohorts.toml`, `uv.lock`), `prereg/labeling-guide.md`. Mọi lượt chính chạy
từ đúng commit này. Sau khi chạy, kiểm tra mỗi (nhiệm vụ, cách làm) có đúng một giá trị `prompt_sha256`
trên mọi lượt và báo cáo kết quả kiểm tra.

## 2. Hai cách làm

Lời dặn nguyên văn, chốt bằng mã băm SHA-256:

- Vibe: `prompts/vibe.md` (`17a6ec6245602f789ab7283bd5cd64f11fb563aab09a85fb60ea6ca4a9d034fe`).
- Theo đặc tả: `prompts/spec.md` (`e6171cac3f2b43831f93aefdef355c40b2ce9562e6f345211b9a5e9031cd9a35`).

Can thiệp là **một gói**: viết thiết kế, viết kế hoạch, viết test trước cho từng phần việc, và chạy cả
bộ test backend trước khi dừng (lời dặn nêu cả lệnh `uv run pytest`). Lời dặn vibe không nêu điều nào
trong số này. Thí nghiệm ước lượng tác dụng của cả gói, không tách được phần của riêng tài liệu đặc tả.
Để mô tả cơ chế, báo cáo số lượt mỗi cách làm có chạy `pytest` trong nhật ký và số test AI viết; hai con
số này là mô tả, không phải phép thử.

**Tuân thủ quy trình.** Một lượt theo đặc tả là "tuân thủ" khi bản vá có cả `docs/design.md` và
`docs/plan.md` (hoặc hai file cùng tên dưới `backend/docs/`), tức `process_artifacts = true`. Phép thử
chính tính **mọi lượt theo cách làm được giao**, kể cả lượt không tuân thủ (phân tích theo phân bổ). Tỉ
lệ tuân thủ được báo cáo theo nhóm và tầng. Phân tích độ nhạy: chạy lại phép thử chính sau khi bỏ lượt
theo đặc tả không tuân thủ (phân tích theo quy trình); kết quả này không thay cho phép thử chính. Số lượt
vibe tự viết file thiết kế hoặc kế hoạch cũng được đếm và báo cáo.

## 3. Nhóm chạy và điều kiện

| Nhóm | Công cụ | Mô hình | Effort | Tài khoản |
| --- | --- | --- | --- | --- |
| `claude-sonnet` | Claude Code 2.1.325 | `claude-sonnet-5-5` | medium | 1 |
| `claude-opus` | Claude Code 2.1.325 | `claude-opus-5-5` | medium | 1 |
| `agy-gemini` | Antigravity CLI 1.5.9 | `gemini-3.8-flash-medium` | medium | 4, đổi khi hết hạn mức |
| `codex-luna` | Codex CLI 0.162.1 | `gpt-6-luna` | medium | 4, đổi khi hết hạn mức |

Điều kiện chung (ruling R11 của sổ ghi bộ chạy):

- Mỗi công cụ chạy agent mặc định với bộ công cụ mặc định, kể cả công cụ web, gọi thẳng CLI, không qua proxy.
- Chỉ bỏ phần cài thêm của người dùng: HOME sạch chỉ chứa thông tin đăng nhập của một tài khoản, không
  skill, plugin, MCP, bộ nhớ hay file hướng dẫn riêng.
- Cây mã không có lịch sử git, đã bỏ `superpowers/`, `skills-lock.json` và file hướng dẫn cho AI.
- Biến môi trường theo danh sách cho phép.
- Phiên bản công cụ thực tế được ghi cho từng lượt. Công cụ tự cập nhật thì ghi lại, không chặn. Báo cáo
  liệt kê mọi phiên bản công cụ đã gặp và số lượt của từng phiên bản theo cách làm. Với `codex-luna`, mô
  hình được phục vụ không ghi được cho từng lượt; báo cáo nêu hạn chế này.

## 4. Thông số chạy và lượt hợp lệ

- 3 lần lặp cho mỗi cặp (nhiệm vụ, cách làm, nhóm). Tầng nhỏ: 15 × 2 × 3 × 4 = **360 lượt**.
- **Giới hạn thời gian của AI, đặt theo quy tắc:** tầng nhỏ 3600 s; tầng vừa gấp 2 (7200 s); tầng lớn
  gấp 3 (10800 s). Như nhau cho hai cách làm và bốn nhóm. Con số 3600 là mặc định của CLI và rộng hơn
  2400 s tính từ chạy thử, vì chạy thử dùng cấu hình cũ (tắt web, agy chạy agent tùy chỉnh;
  `docs/pilot-report.md` mục 0 và 6) và cấu hình R11 chưa có lượt chạy thử đầy đủ. Các con số này
  **không tính lại** sau thẻ, kể cả khi có lượt chạy lâu hơn.
- Giới hạn của bộ chấm: 900 s (mặc định của CLI). Số phiên song song: 8 (`--jobs 8`).
- Hạt giống xáo trộn thứ tự lượt: `20261115`.

Xử lý từng loại kết cục (bộ chạy tại thẻ cài đúng các quy tắc này):

- **Lượt hợp lệ** là lượt có `status = done` (có `grade.json`). Mọi lượt hợp lệ đều vào phân tích.
- **Chạm giới hạn thời gian.** AI bị dừng, thư mục làm việc được chấm ở trạng thái lúc đó. Lượt này là
  lượt hợp lệ: không chạy lại; không đạt thì tính là không đạt. Số lượt hết giờ được báo cáo theo nhóm,
  tầng và cách làm.
- **CLI thoát với mã khác 0 không phải vì hạn mức hay đăng nhập** (lỗi mạng, lỗi máy chủ của nhà cung
  cấp, CLI sập): lượt được chấm như mọi lượt khác và là lượt hợp lệ. Không chạy lại. Số lượt có mã thoát
  khác 0 được báo cáo theo nhóm và cách làm.
- **Hạn mức và đăng nhập.** Lượt bị dừng vì hết hạn mức hoặc lỗi đăng nhập (bộ chạy nhận theo mẫu trong
  `agents.py` tại thẻ này) không phải một lần lặp và được chạy lại từ đầu, sau khi chờ `--quota-backoff-s`
  (mặc định 600 s) và đổi tài khoản nếu nhóm có nhiều tài khoản. Bộ chạy thử lại tối đa 20 lần cho mỗi
  lượt trong một lần gọi lệnh, tính chung hai loại. Lượt hết 20 lần thử được ghi `status = deferred`: đó
  là lượt **chưa chạy**, không phải lượt lỗi. Nó được chạy lại bằng cách gọi lại đúng lệnh ở mục 5 sau
  khi hạn mức hồi, và không bao giờ bị loại một cách lặng lẽ. Lượt còn `deferred` ở hạn chót được liệt kê
  trong báo cáo và làm (nhóm, tầng) đó thành chưa đủ (mục 10).
- **Bộ chấm hết giờ.** Bản vá đã lưu được chấm lại một lần trên một cây mới dựng từ `patch.diff` (AI không
  chạy lại). Hết giờ lần thứ hai thì lượt là lượt hợp lệ, không đạt, ghi chú "grader timeout on agent patch
  (twice)": treo lặp lại là lỗi của bản vá.
- **Bản vá làm hỏng môi trường test.** Nếu bước chạy test cuối không ra báo cáo hoặc `uv sync` hỏng, và bản
  vá sửa `pyproject.toml`, `uv.lock`, `conftest.py` hay file cấu hình pytest còn nằm trong cây được chấm,
  bước đó chạy lại một lần. Hỏng giống hệt lần thứ hai thì lượt hợp lệ, không đạt; khác đi hoặc là lỗi hệ
  điều hành (`OSError`) thì là lỗi hệ thống.
- **Lỗi hệ thống** là lượt bộ chạy ghi `status = error`: ngoại lệ trong bộ chạy (cây bẩn, lệch đề bài,
  lỗi khác), bộ chấm sập, hoặc bước chạy test cuối hỏng mà không do bản vá. Gọi lại lệnh ở mục 5 thì lượt đó được chạy
  lại từ đầu. Mỗi lượt được chạy lại tối đa 2 lần. Vẫn lỗi thì loại khỏi phân tích; báo cáo liệt kê từng
  lượt bị loại kèm lý do, và đếm số lượt bị loại theo cách làm.
- Quyết định chạy lại chỉ dựa trên `status`, không dựa trên `task_pass`. Không lượt hợp lệ nào bị chạy
  lại hay thay thế.
- Nếu bộ chấm phải sửa sau thẻ, mọi lượt đã chấm được chấm lại bằng `sdlc-harness regrade`; mục 11 ghi
  commit sửa và số lượt đổi `task_pass`.

## 5. Lệnh chạy chính

Chạy từ thư mục gốc repo nghiên cứu, tại commit mang thẻ `prereg-v1`. Tầng nhỏ, cả bốn nhóm trong một
lệnh (bốn nhóm có hạn mức riêng nên chạy song song với nhau):

```
cd /home/andv/personal/vipharmind-ai-sdlc-study
harness/.venv/bin/sdlc-harness run \
  --repo /home/andv/personal/vipharmind \
  --cohorts claude-sonnet,claude-opus,agy-gemini,codex-luna \
  --tasks t01,t02,t03,t04,t05,t06,t07,t08,t09,t10,t11,t12,t13,t14,t15 \
  --reps 3 \
  --jobs 8 \
  --seed 20261115 \
  --timeout-s 3600 \
  --out results/raw/main
```

- Danh sách nhiệm vụ ghi rõ 15 mã thay cho `--tasks main`: tại thẻ, `main` chọn mọi nhiệm vụ có
  `pilot = false`, gồm cả `f08`, `f14`, `f15` của tầng lớn.
- Các cờ khác để mặc định: `--grade-timeout-s 900`, `--quota-backoff-s 600`, `--max-quota-retries 20`,
  `--tasks-dir tasks`, `--cohorts-file` và `--accounts-file` mặc định, `--work-root` là `$SDLC_WORK_ROOT`
  hoặc `/tmp/sdlc-runs`. `--timeout-s` luôn ghi rõ dù trùng mặc định.
- Gọi lại đúng lệnh này để chạy tiếp các lượt `deferred` và các lượt lỗi còn lượt chạy lại; lượt đã có
  `grade.json` được bỏ qua.
- Tầng vừa và tầng lớn: cùng lệnh, với `--tasks` là danh sách mã trong `prereg-v1.1` và `--timeout-s 7200`
  (tầng vừa) hoặc `--timeout-s 10800` (tầng lớn), từ commit mang thẻ `prereg-v1.1`.

Lượt chạy thử p01, p02 ở cấu hình R11 được phép trước thẻ, chỉ để biết cấu hình mới chạy trọn một lượt;
chúng không đổi bất kỳ con số nào ở mục 4.

## 6. Chỉ số

- **Chính:** đạt nhiệm vụ (`task_pass`): mọi test ẩn đạt và không có test cũ nào hỏng.
- **Phụ:**
  - Tỉ lệ test ẩn đạt; số test cũ hỏng.
  - Lỗi `ruff`, lỗi `pyrefly`, test kiến trúc.
  - `radon cc` và `radon mi` trên file `backend/src` bị đổi, so với giá trị của mã nền
    (`baseline_radon_cc`, `baseline_radon_mi` trong `task.toml`).
  - Số test AI viết và độ phủ dòng của chúng.
  - Kích thước bản vá.
  - Token vào và ra, thời gian (`wall_s`), số lượt gọi. Chi phí quy đổi: tách token của từng lượt từ
    `transcript.jsonl` thành bốn loại (vào không cache, ghi cache, đọc cache, ra; token suy luận tính
    theo cách nhà cung cấp tính tiền), nhân với giá ở mục 7. Đọc cache và ghi cache được tính giá riêng.
    Công cụ nào không tách được loại token thì tính mọi token vào theo giá vào thường và ghi rõ là cận
    trên. Số lượt gọi không so được giữa các công cụ, chỉ so giữa hai cách làm trong cùng nhóm.

**Cách chấm.** Trước khi chạy test, bộ chấm đưa mọi file test có sẵn về bản của mã nền và chép test ẩn
từ commit gốc, nên AI sửa hay xóa test có sẵn không làm đổi kết quả; test cũ bị AI xóa tính là hồi quy;
test do AI viết mà hỏng không tính là hồi quy. Ở nhiệm vụ một commit, `pyproject.toml` của AI được giữ
nguyên; ở nhiệm vụ nhiều commit, `pyproject.toml` và `uv.lock` lấy từ commit `end`. Lượt có
`pytest_config_touched = true` (bản vá đổi `conftest.py` hoặc cấu hình pytest) vẫn là lượt hợp lệ và
được đếm theo cách làm; phân tích độ nhạy ở mục 9, điểm 7 chạy thêm một lần bỏ các lượt này.

## 7. Bảng giá quy đổi

Một bảng giá cho mọi lượt: giá API công khai niêm yết ngày 2026-11-15, đơn vị đô Mỹ trên 1 triệu token.
Giá đổi sau ngày này không được áp dụng. Nếu thẻ gắn sau ngày này, bảng được kiểm lại trước thẻ; giá đã
đổi thì sửa bảng trước thẻ.

| Mô hình | Vào | Đọc cache | Ghi cache | Ra |
| --- | --- | --- | --- | --- |
| `claude-sonnet-5-5` | 2,00 | 0,10 | 2,50 (giữ 5 phút); 4,00 (giữ 1 giờ) | 10,00 |
| `claude-opus-5-5` | 4,00 | 0,20 | 5,00 (giữ 5 phút); 8,00 (giữ 1 giờ) | 20,00 |
| `gemini-3.8-flash-medium` (giá của Gemini 3.8 Flash) | 0,75 | 0,075 | không tính phí ghi | 3,75 (gồm token suy luận) |
| `gpt-6-luna`, lời gọi ≤ 272.000 token vào | 0,10 | 0,01 | không tính phí ghi | 0,50 |
| `gpt-6-luna`, lời gọi > 272.000 token vào | 0,20 | 0,02 | không tính phí ghi | 0,75 |

Nguồn (đọc ngày 2026-11-15):

- Claude: `https://platform.claude.com/docs/en/about-claude/pricing`. Nhật ký Claude Code tách token ghi
  cache theo thời gian giữ (`ephemeral_5m_input_tokens`, `ephemeral_1h_input_tokens`); mỗi phần nhân với
  giá tương ứng. Giá như nhau trên cả cửa sổ 1 triệu token.
- Gemini: `https://aistudio.google.com/docs/pricing`, gói trả phí, mức chuẩn. Trang ghi giá này áp dụng
  tới 2026-12-31 và tăng gấp đôi từ 2027-01-01; bảng vẫn dùng giá ngày 2026-11-15. Phí lưu cache theo
  giờ chỉ áp dụng cho cache tường minh, công cụ không dùng nên không tính.
- OpenAI: `https://developers.openai.com/api/docs/pricing`, mức chuẩn. Ngưỡng 272.000 token xét theo
  từng lời gọi.
- Phí công cụ phía máy chủ (ví dụ tìm kiếm web tính theo lần) không được tính; báo cáo nêu điều này.

## 8. Giả thuyết (nguyên văn từ bản thiết kế)

- **H1.** Làm theo đặc tả có tỉ lệ đạt nhiệm vụ cao hơn vibe coding.
- **H2.** Làm theo đặc tả tốn nhiều token và thời gian hơn.
- **H3.** Làm theo đặc tả ít lỗi chất lượng tĩnh, ít hồi quy hơn và có chỉ số bảo trì không kém hơn.
- **H4.** Khoảng cách về tỉ lệ đạt giữa hai cách làm ở Sonnet lớn hơn ở Opus, tức làm theo đặc tả giúp
  mô hình yếu hơn nhiều hơn.
- **H5.** Hiệu số tỉ lệ đạt (đặc tả trừ vibe) tăng theo kích thước nhiệm vụ: ở tầng lớn lớn hơn ở tầng
  nhỏ, và tăng theo số dòng của bản vá gốc.

## 9. Kế hoạch phân tích

**Ước lượng chính và quy tắc đọc kết quả.**

- Đơn vị phân tích là nhiệm vụ. Với mỗi (nhóm, nhiệm vụ, cách làm), tỉ lệ đạt là trung bình `task_pass`
  trên các lần lặp hợp lệ. Hiệu số của một nhiệm vụ là tỉ lệ đạt theo đặc tả trừ tỉ lệ đạt vibe. Ước
  lượng của một nhóm là trung bình hiệu số trên các nhiệm vụ, mỗi nhiệm vụ một trọng số.
- **Phép thử chính của H1:** nhóm `claude-sonnet`, tầng nhỏ, 15 nhiệm vụ. Kết quả của `claude-opus`,
  `agy-gemini`, `codex-luna` và của tầng vừa, tầng lớn là phụ, báo cáo cùng định dạng.
- Khi cần gộp nhiều nhóm (H5, hình tổng hợp): lấy trung bình hiệu số của các nhóm trong từng nhiệm vụ,
  mỗi nhóm một trọng số, rồi trung bình trên nhiệm vụ.
- Cách đọc, áp dụng cho mọi giả thuyết có hướng: "được ủng hộ" khi khoảng tin cậy 95% nằm hoàn toàn về
  phía giả thuyết nêu; "trái với giả thuyết" khi nằm hoàn toàn về phía ngược lại; còn lại là "chưa kết
  luận được". Ba kết cục được báo cáo ngang nhau.

**Thứ bậc và so sánh nhiều lần.** Phép thử xác nhận duy nhất là H1 như định nghĩa ở trên. H5 (phép thử
chính ở điểm 4) là phép thử phụ quan trọng nhất. H2, H3, H4, từng nhóm, từng tầng và hiệu quả chi phí là
phụ. Mọi phép thử phụ được báo cáo đủ ước lượng kèm khoảng tin cậy 95%, không hiệu chỉnh so sánh nhiều
lần, và báo cáo nói rõ số phép so đã làm. Không chỉ số nào bị bỏ khỏi báo cáo vì kết quả của nó.

1. **So sánh theo cặp trên từng nhiệm vụ.** Hiệu số tỉ lệ đạt (đặc tả trừ vibe), khoảng tin cậy 95%
   bootstrap lấy mẫu lại theo nhiệm vụ. Báo cáo cỡ hiệu ứng và khoảng tin cậy, không dựa kết luận vào
   ngưỡng p. Báo cáo độ dao động giữa các lần lặp: tỉ lệ ô (nhóm, nhiệm vụ, cách làm) mà các lần lặp
   không cùng kết quả.

   Chi tiết bootstrap: lấy mẫu lại nhiệm vụ có hoàn lại, giữ nguyên mọi lần lặp của nhiệm vụ được chọn;
   10.000 lần; khoảng phân vị 2,5%–97,5%; hạt giống `20261115`. Với phép so giữa hai nhóm (2 × 2), mỗi lần
   lấy mẫu dùng **cùng một** tập nhiệm vụ cho cả hai nhóm. Với phép so giữa hai tầng, mỗi tầng lấy mẫu lại
   riêng. Tầng có dưới 6 nhiệm vụ: ngoài khoảng bootstrap, báo cáo hiệu số của từng nhiệm vụ trong bảng và
   ghi rõ khoảng tin cậy ở cỡ mẫu này chỉ có giá trị tham khảo.
2. **RQ4.** Như điểm 1 cho từng nhóm, so hướng và độ lớn giữa các công cụ.
3. **RQ5 / H4.** Thiết kế 2 × 2 (cách làm × Sonnet/Opus): bốn tỉ lệ đạt, hiệu số ở từng mô hình, hiệu
   của hai hiệu số kèm khoảng tin cậy bootstrap. So thêm Sonnet theo đặc tả với Opus vibe về tỉ lệ đạt
   và chi phí quy đổi.
4. **H5.** Phép thử chính: hiệu của hai hiệu số (tầng lớn trừ tầng nhỏ), gộp các nhóm theo quy tắc ở
   mục 10, bootstrap theo nhiệm vụ trong từng tầng.

   Bổ trợ: hồi quy logistic hỗn hợp trên mọi lượt hợp lệ của ba tầng,
   `pass ~ arm × log(src_lines) + cohort + (1 + arm | task)`, với `src_lines` là trường cùng tên trong
   `task.toml` (số dòng `backend/src` mà bản vá gốc thêm và bớt), `cohort` là hiệu ứng cố định. Ước lượng
   bằng `glmer` của `lme4` (R), phiên bản ghi trong báo cáo. Báo cáo hệ số tương tác, sai số chuẩn và
   khoảng tin cậy 95%. Nếu mô hình không hội tụ hoặc suy biến, lần lượt lùi về: (1) bỏ tương quan giữa hai
   hiệu ứng ngẫu nhiên; (2) `(1 | task)`; (3) hồi quy tuyến tính của hiệu số từng nhiệm vụ (trung bình các
   nhóm) theo `log(src_lines)`. Báo cáo nêu mô hình nào đã dùng và vì sao. Kèm hình hiệu số theo kích
   thước. Ghi rõ là bằng chứng sơ bộ vì tầng vừa và lớn có ít nhiệm vụ. Phân tích theo ba nhóm kích thước
   trong tầng nhỏ (mục 1) là khám phá.

   Phép thử chính của H5 nằm trên thang hiệu số tỉ lệ và có thể dương chỉ vì tỉ lệ đạt ở tầng nhỏ chạm
   trần. Vì vậy H5 chỉ được coi là "được ủng hộ" khi cả phép thử chính lẫn hệ số tương tác của mô hình
   logistic (thang logit) cùng hướng và khoảng tin cậy của phép thử chính không chứa 0. Báo cáo thêm cùng
   phép thử trên chỉ số phụ "tỉ lệ test ẩn đạt". Báo cáo nêu rõ tầng khác nhau không chỉ ở kích thước mà
   cả ở số test ẩn, giới hạn thời gian và cách chấm, nên H5 là bằng chứng về "nhiệm vụ cỡ tính năng", không
   tách riêng được tác dụng của số dòng.
5. **H2, H3.** Mỗi chỉ số lấy trung bình trên các lượt hợp lệ của từng (nhóm, nhiệm vụ, cách làm), rồi
   lấy hiệu theo cặp và bootstrap như điểm 1.
   - H2: tổng token (vào, gồm cả token đọc và ghi cache, cộng ra) và thời gian chạy `wall_s`.
   - H3 tách ba phần, đọc riêng: (a) lỗi tĩnh = số lỗi `ruff` cộng số lỗi `pyrefly` mỗi lượt;
     (b) hồi quy = tỉ lệ lượt có ít nhất một test cũ hỏng; (c) bảo trì = `radon mi` trung bình của file
     `backend/src` bị đổi, trừ `baseline_radon_mi` của nhiệm vụ; "không kém hơn" nghĩa là cận dưới khoảng
     tin cậy của hiệu (đặc tả trừ vibe) lớn hơn **−5 điểm MI**.
   - `radon cc` và test kiến trúc được báo cáo mô tả. Lượt mà công cụ đo không chạy được (giá trị rỗng)
     bị bỏ khỏi chỉ số đó và được đếm.
6. **Hiệu quả chi phí.** Số lượt đạt trên mỗi đô quy đổi, và chi phí quy đổi trung bình cho một lượt
   đạt, theo nhóm và tầng, kèm khoảng tin cậy bootstrap. Nhóm, tầng và cách làm có 0 lượt đạt thì chi phí
   cho một lượt đạt ghi là không xác định, không ghi 0.
7. **Độ nhạy.** Chạy lại phép thử chính (và phép thử chính của H5) trong từng trường hợp sau, mỗi lần
   bỏ một loại:
   - các lượt có `upstream_urls` khác rỗng (nhật ký có đường dẫn tới repo ViPharmind gốc). Cờ này chỉ bắt
     được đường dẫn xuất hiện trong nhật ký; báo cáo nêu đây là cận dưới của mức truy cập mã gốc;
   - các lượt có `pytest_config_touched = true` (mục 6);
   - các lượt theo đặc tả không tuân thủ quy trình (mục 2);
   - riêng H5: các nhiệm vụ có commit nằm trong một nhiệm vụ của tầng khác (ràng buộc 7 ở đầu văn bản).
8. **Phân tích lỗi.** Lợi và Bảo gán nhãn độc lập mọi lượt hợp lệ không đạt của hai nhóm Claude ở cả ba
   tầng, mỗi lượt một nhãn, theo `prereg/labeling-guide.md`. Bảng nhãn khóa tại thẻ này: 7 nhãn khởi đầu
   cộng hai nhãn chạy thử đề xuất (`de_bai_thieu`, `sai_api_co_san`; `docs/pilot-report.md` mục 7). Mỗi
   lượt được trao dưới một mã ngẫu nhiên không chứa nhóm, cách làm hay số lần lặp, theo thứ tự xáo trộn;
   gói gồm đề bài, bản vá đã bỏ `docs/design.md`, `docs/plan.md` và log test. Việc làm mù là **một
   phần**: bản vá có thể để lộ cách làm (ví dụ số test AI viết). Người gán nhãn ghi "lộ cách làm" khi
   nhận ra; báo cáo nêu tỉ lệ lượt bị ghi như vậy. Báo cáo kappa của Cohen trên nhãn đơn của toàn bộ lượt
   được gán, kèm bảng chéo hai người; An phân xử chỗ lệch và ghi lý do. An biết cách làm của từng lượt,
   nên nhãn sau phân xử không được coi là mù.
9. **Ca nghiên cứu định tính** theo quy tắc ở mục 7.5 của bản thiết kế, áp dụng trên **tầng lớn**; nếu
   mọi nhiệm vụ tầng lớn có hiệu số bằng 0 ở `claude-sonnet` thì lấy nhiệm vụ có bản vá gốc lớn nhất.
10. **Đạt test nhưng sai.** Lấy ngẫu nhiên 20 lượt đạt của hai nhóm Claude, 10 lượt mỗi cách làm, phân
    bổ theo tầng tỉ lệ với số lượt đạt, hạt giống `20261115`, lấy trên danh sách lượt sắp theo (nhóm,
    nhiệm vụ, cách làm, lần lặp). An đối chiếu từng bản vá với bản vá gốc và ghi lượt nào đạt test nhưng
    sai hoặc thiếu hành vi đề bài nêu. An không mù cách làm; báo cáo ghi rõ. Kết quả là mô tả, không sửa
    `task_pass`.

**Mã phân tích.** Mã tính mọi bảng và hình của mục này (gói `analysis/`) được commit, có test, và chạy
thử trên dữ liệu `results/raw/pilot`, rồi gắn thẻ `prereg-v1-analysis`. Lượt chạy chính được phép bắt
đầu trước thẻ này, nhưng không kết quả chính nào được mở để phân tích (ngoài số lượt theo trạng thái)
cho tới khi thẻ `prereg-v1-analysis` đã gắn. Commit của mã và mọi lần sửa sau đó được ghi ở mục 11. Phân
tích nào không nằm trong mục 9 thì được ghi nhãn "khám phá, thêm sau khi thấy số liệu" trong báo cáo.

## 10. Thứ tự chạy và quy tắc dừng

Bốn nhóm chạy cùng lúc, vì mỗi nhóm có hạn mức riêng. Trong mỗi nhóm, tầng nhỏ chạy trước; tầng vừa và
tầng lớn chạy sau thẻ `prereg-v1.1`. Trong một lần gọi lệnh, thứ tự lượt do hạt giống quyết định, nên hai
cách làm xen kẽ nhau theo thời gian.

Hạn chót thu dữ liệu: **2026-11-29**. Sau ngày này không chạy thêm lượt nào. Hạn chót chỉ được lùi bằng
một dòng ở mục 11, ghi **trước khi** tính bất kỳ tỉ lệ đạt nào.

Một (nhóm, tầng) là **đủ** khi mọi lượt của nó là lượt hợp lệ hoặc là lỗi hệ thống đã hết lượt chạy lại
(mục 4). (Nhóm, tầng) chưa đủ ở hạn chót (còn lượt chưa chạy hoặc `deferred`):

- bị loại khỏi phép thử xác nhận và khỏi các phép thử gộp nhóm; nếu đó là `claude-sonnet` ở tầng nhỏ thì
  H1 không có phép thử xác nhận và báo cáo nói rõ;
- được báo cáo mô tả: mọi lượt hợp lệ đã chạy, số lượt còn thiếu, ghi rõ là chưa đủ.

Trong một (nhóm, tầng) đủ, một nhiệm vụ chỉ vào ước lượng khi mỗi cách làm có ít nhất một lượt hợp lệ;
tỉ lệ đạt lấy trên số lượt hợp lệ có được. Phép thử gộp nhóm của H5 chỉ gộp các nhóm đủ ở **cả ba** tầng;
báo cáo nêu nhóm nào được gộp. Nếu chỉ còn hai nhóm Claude thì H5 được thử trên hai nhóm đó.

Nếu thiếu hạn mức, ưu tiên hai nhóm Claude; quyết định ngừng một nhóm chỉ dựa trên số lượt còn thiếu và
hạn mức, và được ghi vào mục 11 **trước khi** tính bất kỳ tỉ lệ đạt nào của nhóm đó.

## 11. Thay đổi sau thẻ

Mỗi thay đổi là một dòng: ngày; mục bị đổi; nội dung cũ và mới; lý do; đã xem kết quả nào trước khi
đổi (chưa xem gì, đã xem số lượt theo trạng thái, đã xem tỉ lệ đạt); commit. Văn bản tại thẻ không bị
sửa: thay đổi được thêm vào mục này và gắn thẻ mới (`prereg-v1.1`, `prereg-v1.2`, …). Báo cáo chép lại
toàn bộ bảng này.

Mã băm SHA-256 của `prereg/labeling-guide.md` tại thẻ: `9b124ffaf5816aa04b793366f1d191e943288e4e0897950900e8f87c199b62df` (tính lại nếu file còn đổi trước thẻ).

1. **2026-11-15; ràng buộc 3 (gạch đầu dòng "Tầng vừa") và ràng buộc 4 của mục "Phạm vi và bản bổ sung
   `prereg-v1.1`".** Cũ: tầng vừa gồm ứng viên 2–3 commit, 300–700 dòng, đề nêu được mọi tên cần với tối
   đa 20 tên (đếm trên đề); hơn 5 ứng viên thì giữ theo thứ tự "không chứa commit của t01–t15 trước, rồi
   số tên trong đề, rồi `end`"; hai nhiệm vụ tầng vừa không chung commit. Mới (văn bản ràng buộc:
   `prereg/prereg-v1.1.md`, mục "Quy tắc chọn tầng vừa" và "Nhiệm vụ không qua duyệt đề bài"):
   (a) ứng viên chung commit với t01–t15, p01, p02 bị **loại** thay vì xếp sau, và điều này mở rộng sang
   f08, f14, f15; (b) thêm tiêu chí 2 (không commit `test`, `refactor`, `chore`, `docs`), tiêu chí 7 (ít
   nhất 5 test ẩn được chấm trượt ở `base`) và tiêu chí 8 (tối đa 50% dòng được thực thi chỉ do test
   `integration` thực thi); (c) ngưỡng 20 tên giữ con số nhưng đổi đơn vị, từ số tên nêu trong đề sang số
   tên đếm cơ học N1–N7 (`medium_names.py`); theo đơn vị cũ (mục nêu trong "Required interfaces"), năm đề
   được chọn có m01 13, m02 25, m03 18, m04 21, m05 36; (d) thứ tự mới: số tên cơ học, rồi số dòng
   `backend/src`, rồi `end`, với lượt 1 lấy một cửa sổ cho mỗi lớp domain, application, infrastructure,
   api, lượt 2 điền chỗ còn lại; (e) quy tắc thay thế mới: chỉ trước thẻ `prereg-v1.1`, bỏ khi REJECT, GAP
   không đóng được hoặc `--original-patch` lỗi, thay bằng cửa sổ hợp lệ kế tiếp không chung commit với
   nhiệm vụ đang giữ hay đã bỏ. Lý do: độc lập giữa các tầng, đủ tín hiệu chấm, chỉ commit tính năng, đếm
   tên được trước khi có đề (chi tiết ở `prereg/prereg-v1.1.md`). Đã xem trước khi đổi: số liệu dựng nhiệm
   vụ của các ứng viên (số dòng, kết quả chấm bản vá gốc, số tên, độ phủ) và một danh sách m01–m05 chọn
   tay đầu tiên; **chưa xem kết quả AI nào** (chưa lượt AI nào chạy trên ứng viên tầng vừa hay tầng lớn;
   chưa mở kết quả nào của tầng nhỏ). Commit: commit mang thẻ `prereg-v1.1`.
2. **2026-11-15; ràng buộc 1 (thời điểm).** Lượt chạy chính tầng nhỏ bắt đầu khoảng 19:16 ngày 2026-11-15,
   trước thẻ `prereg-v1.1`, nên trường hợp dự phòng của ràng buộc 1 được áp dụng: không ai mở `grade.json`
   hay tính tỉ lệ đạt tầng nhỏ trước thẻ đó; chỉ xem số lượt theo trạng thái. Ngày gắn thẻ `prereg-v1.1`:
   ngày của commit mang thẻ. Ngày mở kết quả tầng nhỏ: chưa mở; được thêm thành một dòng ở mục này khi mở
   (không sớm hơn thẻ `prereg-v1-analysis`). Đã xem trước khi ghi: nhiều nhất là số lượt theo trạng thái. Commit: commit
   mang thẻ `prereg-v1.1`.

- **2026-11-15, F09.** F09 giữ nguyên quyết định loại của đợt chọn đầu (trước chạy thử), không xét lại theo
  ngưỡng 35 tên; lý do ở `prereg-v1.1.md`. Tầng lớn giữ F08, F14, F15; m03 giữ nguyên.
- **2026-11-15 19:58, vận hành.** Tầng vừa và tầng lớn bắt đầu lúc 19:58 (sau thẻ `prereg-v1.1`), chạy cùng lúc
  với tầng nhỏ còn đang chạy: tổng tối đa 24 phiên thay vì 8. Mỗi lệnh dùng `--work-root` riêng
  (`/tmp/sdlc-runs-medium`, `/tmp/sdlc-runs-large`) vì bộ chạy khóa thư mục làm việc theo từng lệnh; cờ này
  chỉ đổi nơi đặt thư mục tạm, không đổi điều kiện chạy. Khoảng chạy chồng có thể làm tăng `wall_s`; báo cáo
  so số lượt hết giờ trong và ngoài khoảng này.
- **2026-11-15, mục 9 điểm 4 (công cụ ước lượng mô hình hỗn hợp và khoảng tin cậy).** Cũ: `glmer` của
  `lme4` (R), báo cáo hệ số tương tác, sai số chuẩn và khoảng tin cậy 95%; lùi mô hình khi không hội tụ
  hoặc suy biến. Mới: `BinomialBayesMixedGLM` của statsmodels (Python), ước lượng biến phân (variational
  Bayes), hệ số là trung bình hậu nghiệm. Gói này chỉ ước lượng các thành phần phương sai độc lập, nên mô
  hình có tương quan `(1 + arm | task)` không ước lượng được: thứ tự lùi bắt đầu từ bước lùi (1). Khoảng
  tin cậy 95% là **bootstrap cụm theo nhiệm vụ của cả phép ước lượng**: lấy mẫu lại nhiệm vụ có hoàn lại
  trong từng tầng, giữ mọi lượt của nhiệm vụ được chọn, ước lượng lại mô hình đã chọn trên mỗi mẫu (mặc
  định 999 lần, hạt giống `20261115`), khoảng phân vị 2,5%–97,5%; "sai số chuẩn" là độ lệch chuẩn của các
  hệ số bootstrap. "Suy biến" là khi độ lệch chuẩn ước lượng của một thành phần ngẫu nhiên dưới 0,30, ngưỡng
  hiệu chỉnh bằng mô phỏng trên thiết kế 23 nhiệm vụ (`analysis/calibration/singular_sd.py`). Bước lùi
  (3) cho độ dốc trên thang hiệu số, không phải thang logit, nên nếu phải lùi tới đó thì H5 không thể
  "được ủng hộ". Lý do: máy không có R; độ lệch chuẩn hậu nghiệm biến phân hẹp hơn độ dao động thật của
  ước lượng khoảng một phần ba (mô phỏng của Fable 5.2: khoảng ±1,96 độ lệch chuẩn chỉ phủ 65–87%), và
  ngưỡng suy biến cũ (1e-3) không bao giờ đạt được vì phân phối tiên nghiệm của log độ lệch chuẩn. Chi
  tiết: `analysis/README.md`, ghi chú 1–4. Đã xem trước khi đổi: chưa xem kết quả chính nào (chỉ dữ liệu
  chạy thử và dữ liệu mô phỏng). Commit: commit mang thẻ `prereg-v1-analysis`.
- **2026-11-15, mục 9 điểm 4 (dữ liệu của mô hình hỗn hợp).** Cũ: "mọi lượt hợp lệ của ba tầng". Mới: mọi
  lượt hợp lệ của ba tầng thuộc các nhóm đủ ở cả ba tầng, tức đúng các nhóm của phép thử chính H5 (mục
  10). Lý do: hai phép thử của H5 dùng cùng tập nhóm; nhóm chưa đủ chỉ được báo cáo mô tả. Đã xem trước
  khi đổi: chưa xem kết quả chính nào. Commit: commit mang thẻ `prereg-v1-analysis`.
- **2026-11-15, mục 7 (ngưỡng 272.000 token của `gpt-6-luna`).** Cũ: ngưỡng xét theo từng lời gọi. Mới:
  Codex CLI chỉ ghi một bản ghi lượng dùng cho cả lượt (chạy thử: một `turn.completed` với 428.199 token
  vào qua nhiều lời gọi), nên không xét được từng lời gọi. `cost_usd` tính mọi token theo giá lời gọi
  ≤ 272.000 token và là **cận dưới**; `cost_usd_upper` tính theo giá > 272.000 token và là cận trên;
  phân tích hiệu quả chi phí của `codex-luna` được báo cáo theo cả hai (`cost_eff` và `cost_eff_upper`).
  Lý do: dữ liệu công cụ ghi không đủ chi tiết. Đã xem trước khi đổi: chưa xem kết quả chính nào. Commit:
  commit mang thẻ `prereg-v1-analysis`.
- **2026-11-15, mục 7 (token ghi cache Claude không tách thời gian giữ).** Mới: token ghi cache của Claude
  mà nhật ký không tách theo 5 phút / 1 giờ được tính theo giá giữ 1 giờ (cận trên; Claude Code ghi cache
  1 giờ). Lý do: bảng giá có hai giá ghi cache. Đã xem trước khi đổi: chưa xem kết quả chính nào.
  Commit: commit mang thẻ `prereg-v1-analysis`.
- **2026-11-15, ràng buộc 7 và phân tích độ nhạy của H5 (mục 9 điểm 7), làm rõ.** Commit của một nhiệm vụ
  là `git rev-list base..end` (nhiệm vụ một commit: chính commit đó), không gồm `base`. Hai nhiệm vụ khác
  tầng "có commit nằm trong nhau" khi hai tập commit giao nhau, và cả hai bị bỏ trong phân tích độ nhạy.
  Theo cách đọc này chỉ có cặp f08–t03 (commit `c3a88b2659`): `base` của f14 là commit của t01 và `base`
  của m04 là commit của t10, nên f14 và m04 không bị bỏ. Ngoặc "(tầng lớn: f08 và f14 thuộc loại đó)"
  trong `prereg-v1.1.md` được sửa thành "(tầng lớn: f08)". Lý do: câu đó của `prereg-v1.1` tự mâu thuẫn
  (cùng câu nói không nhiệm vụ tầng vừa nào thuộc loại đó, trong khi m04 ở cùng trường hợp với f14); bỏ cả
  f14 sẽ chỉ còn f15 ở tầng lớn. Đã xem trước khi đổi: chưa xem kết quả chính nào. Commit: commit mang
  thẻ `prereg-v1-analysis`.
- **2026-11-16 08:13, vận hành.** Máy khởi động lại trong đêm (khoảng 07:59), dừng cả ba lệnh chạy. Các lượt đã có
  `grade.json` giữ nguyên. Ba lệnh được gọi lại đúng như đã chốt lúc 08:13; lượt chưa xong được chạy lại từ đầu
  theo mục 4. Lúc đó: codex-luna xong 138/138, claude-sonnet 137 (1 hoãn vì hạn mức), claude-opus 130 (8 hoãn),
  agy-gemini 53 (hết hạn mức cả 4 tài khoản). Chưa kết quả nào được mở.
- **2026-11-16, quy tắc đọc bài kiểm tra độ phủ (ghi trước khi thấy kết quả).** Bài kiểm tra độ phủ khoảng tin cậy
  bootstrap của mô hình hỗn hợp (40 bộ dữ liệu mô phỏng theo thiết kế 23 nhiệm vụ, 99 lần lặp mỗi bộ) đang
  chạy. Quy tắc chốt trước: ≥ 32/40 lần trúng thì ghi số đó và khóa mã, không chỉnh gì; ≤ 31/40 thì dừng, xem
  từng dòng và đo lại trên hạt giống mới. Mô phỏng độc lập của Fable cho độ phủ kỳ vọng khoảng 88–90% dù danh
  nghĩa là 95%; báo cáo ghi "danh nghĩa 95%, độ phủ mô phỏng khoảng 88–90%, quan sát k/40". Kết luận H5 chỉ dựa
  vào dấu của hệ số tương tác ở thang logit nên không đổi vì điểm này.
- **2026-11-16, mục 7 (token của mô hình ngoài bảng giá).** Mã mô hình được ghép với bảng giá theo đúng tên, hoặc
  theo tên trong bảng cộng phần đuôi ngày hay nhãn (`-20…`, `[…]`, `@…`; ví dụ `claude-sonnet-5-5-20261101`,
  `claude-opus-5-5[1m]`). Token của một mô hình có tên nhưng không khớp dòng nào trong bảng (ví dụ mô hình nhỏ
  chạy tác vụ phụ) được tính theo giá mô hình của nhóm và được đánh dấu theo từng lượt (`tok_offtable`,
  `cost_has_offtable_model`, `offtable_models`); số lượt bị đánh dấu được báo cáo theo nhóm và cách làm. Lý do:
  bảng giá chỉ có bốn mô hình của bốn nhóm, trong khi công cụ có thể gọi mô hình khác cho tác vụ phụ. Chưa xem
  kết quả chính nào khi đổi.
