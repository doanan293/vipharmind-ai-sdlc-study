# Phản biện độc lập `prereg-v1` (Fable 5.2)

Ngày: 2026-11-15. Đối tượng: `prereg/prereg-v1.md` (128 dòng, chưa commit, chưa gắn thẻ) tại HEAD
`38b7e83` của nhánh `harness`. Đối chiếu với bản thiết kế, `tasks/`, `prompts/`, `harness/`,
`docs/pilot-report.md`, `tasks/PROMPT_AUDIT.md`, `team/labeling/guide.md` (chỉ có trên nhánh `report`) và
hai sổ ghi SDD. Người phản biện chỉ đọc, không chạy lượt AI nào.

## Kết luận

**FREEZE AFTER EDITS.** Mọi con số đã kiểm đều đúng (mục "Đã kiểm, đúng" ở cuối). Phần còn thiếu nằm ở
chỗ một bản đăng ký trước phải khóa mà chưa khóa: ước lượng chính của H1, ràng buộc cho `prereg-v1.1`,
cách xử lý lượt không tuân thủ quy trình, và định nghĩa lượt lỗi. Bốn điểm này để ngỏ quyền chọn sau
khi thấy số liệu, nên phải sửa trước khi gắn thẻ. Không điểm nào đòi chạy lại hay đổi thiết kế.

Số phát hiện: 4 Blocking, 12 Important, 8 Minor.

Quy ước: `P:n` là dòng n của `prereg/prereg-v1.md`; `D:n` là dòng n của bản thiết kế
`docs/superpowers/specs/2026-11-15-spec-vs-vibe-study-design.md`.

---

## Blocking

### B1. H1 chưa có ước lượng chính: không rõ tính trên nhóm nào, tầng nào, và thế nào là "ủng hộ"

**Bằng chứng.** P:89 chỉ nêu "tỉ lệ đạt cao hơn". P:99–101 nêu bootstrap theo nhiệm vụ nhưng không nói
gộp nhóm hay tách nhóm. P:102 "như mục 1 cho từng nhóm" ngụ ý mục 1 là gộp, trong khi P:123 nói "hai nhóm
Claude là kết quả chính" và D:311 ghi riêng Sonnet là "kết quả chính, RQ3". Có ít nhất 5 cách đọc (Sonnet;
Sonnet + Opus; gộp 4 nhóm; mỗi cách × chỉ tầng nhỏ hay cả ba tầng). Chạy thử đã cho thấy Claude chạm trần ở
đề nhỏ (D:241–243: 11/12 và 12/12), nên lựa chọn này quyết định kết luận của H1. Cũng không có quy tắc
quyết định: P:100 nói "không dựa vào ngưỡng p" nhưng không nói khi nào H1 được coi là được ủng hộ.

**Sửa.** Thêm vào đầu mục 7, trước điểm 1:

> **Ước lượng chính và quy tắc đọc kết quả.**
>
> - Đơn vị phân tích là nhiệm vụ. Với mỗi (nhóm, nhiệm vụ, cách làm), tỉ lệ đạt là trung bình `task_pass`
>   trên các lần lặp hợp lệ. Hiệu số của một nhiệm vụ là tỉ lệ đạt theo đặc tả trừ tỉ lệ đạt vibe. Ước
>   lượng của một nhóm là trung bình hiệu số trên các nhiệm vụ, mỗi nhiệm vụ một trọng số.
> - **Phép thử chính của H1:** nhóm `claude-sonnet`, tầng nhỏ, 15 nhiệm vụ. Kết quả của `claude-opus`,
>   `agy-gemini`, `codex-luna` và của tầng vừa, tầng lớn là phụ, báo cáo cùng định dạng.
> - Khi cần gộp nhiều nhóm (H5, hình tổng hợp): lấy trung bình hiệu số của các nhóm trong từng nhiệm vụ,
>   mỗi nhóm một trọng số, rồi trung bình trên nhiệm vụ.
> - Cách đọc, áp dụng cho mọi giả thuyết có hướng: "được ủng hộ" khi khoảng tin cậy 95% nằm hoàn toàn về
>   phía giả thuyết nêu; "trái với giả thuyết" khi nằm hoàn toàn về phía ngược lại; còn lại là "chưa kết
>   luận được". Ba kết cục được báo cáo ngang nhau.

Nếu An muốn phép thử chính là gộp hai nhóm Claude thì đổi đúng một dòng, nhưng phải chọn trước thẻ.

### B2. `prereg-v1.1` chưa bị ràng buộc đủ, trong khi H5 là trục chính của nghiên cứu

**Bằng chứng.**

- P:10–12 cho phép chốt danh sách tầng vừa và tầng lớn "trước lượt chạy đầu tiên của hai tầng đó", tức là
  sau khi đã thấy kết quả chính của tầng nhỏ. Người chọn đề khi đó đã biết hướng của hiệu số.
- Tiêu chí chọn còn mơ hồ: "khoảng 20" tên (D:236); "ưu tiên đoạn không chứa commit của t01–t15" (D:236)
  không phải quy tắc loại.
- Ngưỡng tên đã đổi sau chạy thử: D:216 loại F04 và F09 vì đề phải nêu 30–35 tên, "gần như là một bản thiết
  kế viết sẵn"; D:232 lại cho F04 vào nếu "tối đa 35 tên". F09 cùng lý do loại nhưng không được xét lại.
- `tasks/feature-feasibility/medium_candidates.json` mà D:237 dẫn tới chưa tồn tại (thư mục chỉ có
  `ranges.json`, `coupling.json`, `fakes_contract.json` và mã).
- Kế hoạch `docs/superpowers/plans/2026-11-15-feature-tier.md:48` định chạy thử chính `f08` (một nhiệm vụ
  chính) × 2 cách làm × 4 nhóm rồi "chốt `timeout_s` của tầng này". Việc này trái với P:11–12 ("không dùng
  kết quả của bất kỳ lượt chạy AI nào") và với P:70 (giới hạn đã chốt là 2 lần và 3 lần).
- Các tầng không độc lập: `f14.base` là commit của `t01` (`tasks/f14/task.toml`, `c2935909a101`),
  `f15.base` là `f14.commit`, F08 chứa commit của t03 và p02 (D:217); test ẩn của f14 gồm
  `test_account_settings_service.py` (test ẩn của t02), của f15 gồm `test_retrieval_service.py` (của t11).

Tách v1 và v1.1 là chấp nhận được, vì danh sách nhiệm vụ chỉ phụ thuộc lịch sử git và tiêu chí dựng đề.
Nhưng chỉ chấp nhận được khi v1 khóa luôn quy tắc mà v1.1 phải theo.

**Sửa.** Thay P:9–12 bằng:

> Phạm vi của bản này: **tầng nhỏ** (15 nhiệm vụ một commit) và toàn bộ giả thuyết, chỉ số, phân tích cho
> cả ba tầng. Bản bổ sung `prereg-v1.1` chỉ được thêm: mã nhiệm vụ, commit `base` và `end`, số dòng
> `backend/src`, số tên nêu trong đề, mã băm SHA-256 của từng đề bài tầng vừa và tầng lớn. Nó không được
> đổi giả thuyết, chỉ số, kế hoạch phân tích, số lần lặp, giới hạn thời gian hay quy tắc loại.
>
> Ràng buộc cho `prereg-v1.1`:
>
> 1. **Thời điểm.** Thẻ `prereg-v1.1` được gắn trước lượt chạy chính đầu tiên của bất kỳ tầng nào. Nếu
>    không kịp, lượt chạy chính tầng nhỏ được phép bắt đầu trước, nhưng khi đó không ai mở `grade.json`
>    hay tính tỉ lệ đạt của tầng nhỏ cho tới khi `prereg-v1.1` đã gắn thẻ; mục 9 ghi ngày gắn thẻ và ngày
>    mở kết quả.
> 2. **Tập ứng viên.** Ứng viên tầng lớn là 16 đoạn trong `tasks/feature-feasibility/ranges.json` tại thẻ
>    `prereg-v1`. Ứng viên tầng vừa là mọi đoạn 2–3 commit liền nhau nằm trong 16 đoạn đó, có 300–700 dòng
>    `backend/src`. Mọi ứng viên, kết quả từng tiêu chí và lý do loại được ghi ở
>    `tasks/feature-feasibility/medium_candidates.json` và commit cùng `prereg-v1.1`.
> 3. **Tiêu chí, áp dụng như nhau cho mọi ứng viên:** chỉ đổi `backend/`; có test ẩn trượt ở `base` và đạt
>    ở `end`; bản vá gốc chấm đạt, không hồi quy; đề bài nêu được mọi tên test ẩn cần với **tối đa 20 tên**
>    (tầng vừa) và **tối đa 35 tên** (tầng lớn). F09 được xét lại theo cùng ngưỡng 35 như F04 và F07.
> 4. **Không có quyền chọn.** Mọi ứng viên qua tiêu chí đều được nhận. Nếu một tầng có hơn 5 ứng viên qua,
>    giữ 5 ứng viên theo thứ tự: không chứa commit của t01–t15 trước, rồi số tên trong đề tăng dần, rồi mã
>    commit `end` tăng dần. Hai nhiệm vụ tầng vừa không được chung commit.
> 5. **Không chạy AI trên ứng viên.** Trước thẻ `prereg-v1.1`, không lượt AI nào chạy trên một đoạn là ứng
>    viên. Chạy thử bộ chạy cho nhiệm vụ nhiều commit dùng một đoạn đã bị loại (ghi tên đoạn ở mục 9) và
>    chỉ để kiểm tra bộ chạy; giới hạn thời gian của hai tầng đã chốt ở mục 4 và không đổi theo lượt chạy
>    thử này.
> 6. **Đề bài** qua đúng quy trình của F08, F14, F15: soạn, đối chiếu tên với test ẩn, Fable 5.2 duyệt độc
>    lập, An duyệt. Người soạn và người duyệt không xem kết quả chính của tầng nhỏ.
> 7. **Chồng lấn.** `prereg-v1.1` liệt kê mọi cặp nhiệm vụ chung commit hoặc chung file test ẩn giữa các
>    tầng (đã biết: F08 chứa t03; F14 bắt đầu từ commit của t01; F15 nối tiếp F14). Báo cáo nêu hạn chế
>    này; phân tích độ nhạy của H5 bỏ các nhiệm vụ tầng nhỏ có commit nằm trong một nhiệm vụ tầng lớn.

Đồng thời sửa `feature-tier.md:48` (bỏ chạy thử `f08`) và D:216, D:232, D:236 cho khớp, trong cùng commit.

### B3. Lượt theo đặc tả không để lại `docs/design.md`, `docs/plan.md`: không rõ có tính vào kết quả chính hay không

**Bằng chứng.** D:265–266: lượt như vậy "được đánh dấu không tuân thủ quy trình, vẫn chấm và báo cáo
riêng". "Báo cáo riêng" có thể hiểu là loại khỏi phép thử chính hoặc chỉ thêm một bảng. Bộ chấm đã ghi
`process_artifacts` (`harness/src/sdlc_harness/grade.py:551–554`). Bản đăng ký trước không nhắc tới quy tắc
này ở mục 2, 4, 5 hay 7. Lượt chạm giới hạn thời gian ở cách theo đặc tả là lượt dễ thiếu file nhất, nên
loại chúng sẽ làm lệch kết quả về phía có lợi cho đặc tả.

**Sửa.** Thêm vào cuối mục 2:

> **Tuân thủ quy trình.** Một lượt theo đặc tả là "tuân thủ" khi bản vá có cả `docs/design.md` và
> `docs/plan.md` (hoặc hai file cùng tên dưới `backend/docs/`), tức `process_artifacts = true`. Phép thử
> chính tính **mọi lượt theo cách làm được giao**, kể cả lượt không tuân thủ (phân tích theo phân bổ). Tỉ
> lệ tuân thủ được báo cáo theo nhóm và tầng. Phân tích độ nhạy: chạy lại phép thử chính sau khi bỏ lượt
> theo đặc tả không tuân thủ; kết quả này không thay cho phép thử chính. Số lượt vibe tự viết file thiết
> kế hoặc kế hoạch cũng được đếm và báo cáo.

### B4. "Lượt lỗi hệ thống", chạy lại và loại: định nghĩa chưa đủ để thi hành, và có một đường làm lượt bị loại sai

**Bằng chứng.**

- P:73–74 không định nghĩa "lỗi hệ thống". Trong mã, một lượt chỉ là `error` khi có ngoại lệ trong bộ chạy
  (`runner.py:492–504`: `GradingError`, cây bẩn, lệch đề bài, ngoại lệ khác). CLI thoát với mã lỗi không
  phải hạn mức hay đăng nhập (lỗi mạng, lỗi 5xx của nhà cung cấp, CLI sập) vẫn được chấm và ghi `done`
  (`runner.py:470–491`), tức tính là không đạt.
- Bộ chấm hết giờ hoặc không ra báo cáo test thì chỉ ghi vào `grading_notes` (`grade.py:513–523`), lượt vẫn
  `done` với `task_pass = false`. Đây là lỗi bộ chấm nhưng đang bị tính là AI không đạt.
- Lượt hết 20 lần thử hạn mức bị ghi `status = error` (`runner.py:604–606`, `628–632`). Theo P:73–74 nó
  thành "lỗi hệ thống", chạy lại, rồi "loại khỏi phân tích". Tài khoản agy đầu hết hạn mức tuần sau 3 lượt
  (`docs/pilot-report.md` mục 0, dòng 17; thông báo "Resets in 167h"), trong khi thời gian chờ mặc định là
  600 s (`cli.py:235`). Nhiều lượt agy sẽ đi đúng đường này.
- Mũ 20 dùng chung cho hạn mức và đăng nhập (`runner.py:611`), P:72 không nói.
- "Chạy lại" không có số lần tối đa: lượt `error` không có `grade.json` nên mỗi lần gọi lại lệnh là chạy
  lại, không giới hạn.
- Không nói lượt chạm giới hạn thời gian được xử lý thế nào. Mã chấm trạng thái thư mục lúc bị dừng
  (`runner.py:349–353`, `484–485`); lượt hết giờ vẫn có thể đạt.

**Sửa.** Thay P:72–74 bằng:

> - **Lượt hợp lệ** là lượt có `status = done` và `grading_notes` không chứa ghi chú nào về lần chạy test
>   cuối (`final test run …`). Mọi lượt hợp lệ đều vào phân tích.
> - **Chạm giới hạn thời gian.** AI bị dừng, thư mục làm việc được chấm ở trạng thái lúc đó. Lượt này là
>   lượt hợp lệ: không chạy lại; không đạt thì tính là không đạt. Số lượt hết giờ được báo cáo theo nhóm,
>   tầng và cách làm.
> - **CLI thoát với lỗi không phải hạn mức hay đăng nhập** (lỗi mạng, lỗi máy chủ của nhà cung cấp, CLI
>   sập): lượt được chấm như mọi lượt khác và là lượt hợp lệ. Không chạy lại. Số lượt có mã thoát khác 0
>   được báo cáo theo nhóm và cách làm.
> - **Hạn mức và đăng nhập.** Lượt bị dừng vì hết hạn mức hoặc lỗi đăng nhập (bộ chạy nhận theo mẫu trong
>   `agents.py` tại thẻ này) không phải một lần lặp và được chạy lại từ đầu. Bộ chạy thử lại tối đa 20 lần
>   cho mỗi lượt trong một lần gọi lệnh, tính chung hai loại. Lượt hết 20 lần thử là lượt **chưa chạy**,
>   không phải lượt lỗi: nó được chạy lại ở lần gọi lệnh sau, hoặc rơi vào quy tắc dừng ở mục 8.
> - **Lỗi hệ thống** là: bộ chạy ghi `status = error` vì lý do khác hạn mức và đăng nhập, hoặc lượt `done`
>   có ghi chú `final test run …` (bộ chấm hết giờ, không ra báo cáo). Lỗi bộ chạy thì chạy lại lượt đó;
>   lỗi bộ chấm thì chấm lại từ `patch.diff` bằng `sdlc-harness regrade`, không gọi lại AI. Mỗi lượt được
>   xử lý lại tối đa 2 lần. Vẫn lỗi thì loại khỏi phân tích; báo cáo liệt kê từng lượt bị loại kèm lý do,
>   và đếm số lượt bị loại theo cách làm.
> - Quyết định chạy lại chỉ dựa trên `status` và `grading_notes`, không dựa trên `task_pass`. Không lượt
>   hợp lệ nào bị chạy lại hay thay thế.
> - Nếu bộ chấm phải sửa sau thẻ, mọi lượt đã chấm được chấm lại bằng `regrade`; mục 9 ghi commit sửa và
>   số lượt đổi `task_pass`.

---

## Important

### I1. Giới hạn 2400 s suy ra từ cấu hình không còn dùng, và lệnh chạy chưa được chốt

**Bằng chứng.** `docs/pilot-report.md:345–348`: 2400 = 2 × lượt đạt dài nhất (agy, 1073 s), chỉ có 2 lượt
agy, kèm câu "khi agy chạy đủ, nếu có lượt đạt dài hơn thì phải tính lại". Mọi lượt chạy thử dùng cấu hình
cũ (tắt web, agy chạy agent `sdlc-coder` 3285 token thay vì agent mặc định 8681 token, Codex qua proxy;
`pilot-report.md:24`, `:154`). Cấu hình R11 chưa có lượt chạy thử đầy đủ nào. Mặc định của CLI là 3600
(`cli.py:233`), không phải 2400, nên quên cờ là sai giới hạn. `--jobs` mặc định 1 (`cli.py:232`), chạy thử
dùng 4; số phiên song song ảnh hưởng thời gian từng lượt nên ảnh hưởng số lượt hết giờ.

**Sửa.** Thay P:70 bằng:

> - Giới hạn thời gian của AI: 2400 s (tầng nhỏ), 4800 s (tầng vừa), 7200 s (tầng lớn), như nhau cho hai
>   cách làm và bốn nhóm. Con số 2400 lấy từ chạy thử ở cấu hình cũ (`docs/pilot-report.md` mục 6) và
>   **không tính lại** sau thẻ, kể cả khi có lượt chạy lâu hơn. Giới hạn của bộ chấm: `--grade-timeout-s 900`.
> - Lệnh chạy chính, chạy từ thư mục gốc repo tại commit mang thẻ:
>   `sdlc-harness run --repo <ViPharmind> --cohorts <nhóm> --tasks main --reps 3 --jobs 4 --timeout-s 2400
>   --seed 20261115 --out results/raw/main`. Các cờ khác để mặc định. `--timeout-s` luôn ghi rõ vì mặc định
>   của CLI là 3600.

Nên chạy thêm vài lượt p01, p02 ở cấu hình R11 trước thẻ (được phép theo D:196) để biết cấu hình mới chạy
được trọn một lượt; không dùng chúng để đổi 2400.

### I2. Quy tắc dừng chưa khách quan và chưa nói gì về lượt dở dang, thứ tự đợt, hay H5 khi thiếu nhóm

**Bằng chứng.** P:123–124 không có mốc thời gian; "hết thời gian" có thể được quyết sau khi đã xem hiệu số
của nhóm đó. D:316–317 nói đợt 2, 3 chỉ bắt đầu sau khi đợt 1 "xong và đã phân tích", D:492–493 nói đợt 2
và 3 chạy cùng lúc; bản đăng ký trước không nêu thứ tự. H5 "gộp 4 nhóm" (P:106) không xác định khi một
nhóm bị bỏ hoặc chỉ chạy một tầng. Với hạn mức agy đo được (I1/B4), quy tắc dừng gần như chắc chắn được
kích hoạt cho `agy-gemini`.

**Sửa.** Thay mục 8 bằng:

> ## 8. Thứ tự chạy và quy tắc dừng
>
> Thứ tự ưu tiên: (1) hai nhóm Claude, tầng nhỏ; (2) hai nhóm Claude, tầng lớn rồi tầng vừa;
> (3) `agy-gemini` và `codex-luna`, tầng nhỏ; (4) hai nhóm đó, tầng lớn rồi tầng vừa. Trong một lần gọi
> lệnh, thứ tự lượt do hạt giống quyết định, nên hai cách làm xen kẽ nhau theo thời gian.
>
> Hạn chót thu dữ liệu: **<ngày do An điền trước thẻ>**. Sau ngày này không chạy thêm lượt nào. Nếu không
> đủ thời gian hoặc hạn mức, bỏ theo thứ tự ngược với ưu tiên: `codex-luna` trước, rồi `agy-gemini`; hai
> nhóm Claude chạy đủ. Quyết định bỏ một nhóm chỉ dựa trên số lượt còn thiếu và hạn mức, và được ghi vào
> mục 9 **trước khi** tính bất kỳ tỉ lệ đạt nào của nhóm đó.
>
> Nhóm dở dang: báo cáo mọi lượt hợp lệ đã chạy và ghi rõ là chưa đủ. Một nhiệm vụ chỉ vào ước lượng của
> một nhóm khi mỗi cách làm có ít nhất một lượt hợp lệ; tỉ lệ đạt lấy trên số lượt hợp lệ có được. Phép
> thử gộp nhóm (H5) chỉ gộp các nhóm đã chạy đủ ở cả hai tầng được so; nếu chỉ còn hai nhóm Claude thì H5
> được thử trên hai nhóm đó và báo cáo nêu rõ.

### I3. Bootstrap chưa đủ chi tiết để hai người chạy ra cùng một khoảng tin cậy

**Bằng chứng.** P:99–100, P:104, P:106–107 không nêu: loại khoảng (phân vị, BCa), hạt giống, có lấy mẫu
lại lần lặp hay không, có lấy cùng một mẫu nhiệm vụ cho Sonnet và Opus trong 2 × 2 hay không. Với tầng
lớn 3–5 nhiệm vụ, bootstrap theo nhiệm vụ chỉ có 10–126 mẫu khác nhau, khoảng tin cậy hẹp giả tạo.

**Sửa.** Thêm vào P:101:

> Chi tiết bootstrap: lấy mẫu lại nhiệm vụ có hoàn lại, giữ nguyên mọi lần lặp của nhiệm vụ được chọn;
> 10.000 lần; khoảng phân vị 2,5%–97,5%; hạt giống `20261115`. Với phép so giữa hai nhóm (2 × 2), mỗi lần
> lấy mẫu dùng **cùng một** tập nhiệm vụ cho cả hai nhóm. Với phép so giữa hai tầng, mỗi tầng lấy mẫu lại
> riêng. Tầng có dưới 6 nhiệm vụ: ngoài khoảng bootstrap, báo cáo hiệu số của từng nhiệm vụ trong bảng và
> ghi rõ khoảng tin cậy ở cỡ mẫu này chỉ có giá trị tham khảo.

### I4. Mô hình logistic hỗn hợp: thiếu độ dốc ngẫu nhiên, biến kích thước chưa định nghĩa, chưa có phương án khi không hội tụ

**Bằng chứng.** P:108. (a) Hệ số tương tác `arm × log(dòng)` là hiệu ứng giữa các nhiệm vụ lên một độ
dốc trong nhiệm vụ; chỉ có `(1 | task)` thì sai số chuẩn của nó bị ước lượng thấp. (b) `(1 | cohort)` với
4 mức không ước lượng được phương sai ổn định. (c) "dòng bản vá gốc" chưa gắn với một trường dữ liệu. (d)
Với tỉ lệ đạt gần 100% ở đề nhỏ, mô hình dễ tách hoàn toàn hoặc không hội tụ; chưa có phương án. (e) Chưa
nêu phần mềm. Công thức này nằm trong bản thiết kế (D:400), nên sửa cả hai trong cùng commit.

**Sửa.** Thay câu "Bổ trợ: …" ở P:107–109 bằng:

> Bổ trợ: hồi quy logistic hỗn hợp trên mọi lượt hợp lệ của ba tầng,
> `pass ~ arm × log(src_lines) + cohort + (1 + arm | task)`, với `src_lines` là trường cùng tên trong
> `task.toml` (số dòng `backend/src` mà bản vá gốc thêm và bớt), `cohort` là hiệu ứng cố định. Ước lượng
> bằng `glmer` của `lme4` (R), phiên bản ghi trong báo cáo. Báo cáo hệ số tương tác, sai số chuẩn và
> khoảng tin cậy 95%. Nếu mô hình không hội tụ hoặc suy biến, lần lượt lùi về: (1) bỏ tương quan giữa hai
> hiệu ứng ngẫu nhiên; (2) `(1 | task)`; (3) hồi quy tuyến tính của hiệu số từng nhiệm vụ (trung bình các
> nhóm) theo `log(src_lines)`. Báo cáo nêu mô hình nào đã dùng và vì sao. Kèm hình hiệu số theo kích thước.

### I5. H5 đo trên thang hiệu số tỉ lệ, nên hiệu ứng trần ở đề nhỏ tự tạo ra "tương tác"

**Bằng chứng.** D:241–245 thừa nhận Claude chạm trần ở đề nhỏ. Khi hai cách làm đều gần 100%, hiệu số bị
ép về 0 dù cách làm có tác dụng; ở đề lớn, tỉ lệ đạt rời trần và hiệu số nở ra. Phép thử chính của H5
(P:106) sẽ báo "hiệu số tăng theo kích thước" ngay cả khi tác dụng trên thang logit không đổi. Ngoài ra
tầng lớn khác tầng nhỏ ở nhiều thứ ngoài kích thước: nhiều file test ẩn hơn (7–15 so với 1–2), giới hạn
thời gian gấp 3, khôi phục `pyproject.toml` từ `end` (D:220–222).

**Sửa.** Thêm vào cuối điểm 4 của mục 7:

> Phép thử chính của H5 nằm trên thang hiệu số tỉ lệ và có thể dương chỉ vì tỉ lệ đạt ở tầng nhỏ chạm
> trần. Vì vậy H5 chỉ được coi là "được ủng hộ" khi cả phép thử chính lẫn hệ số tương tác của mô hình
> logistic (thang logit) cùng hướng và khoảng tin cậy của phép thử chính không chứa 0. Báo cáo thêm cùng
> phép thử trên chỉ số phụ "tỉ lệ test ẩn đạt". Báo cáo nêu rõ tầng khác nhau không chỉ ở kích thước mà
> cả ở số test ẩn, giới hạn thời gian và cách chấm, nên H5 là bằng chứng về "nhiệm vụ cỡ tính năng", không
> tách riêng được tác dụng của số dòng.

### I6. Chưa có thứ bậc giữa các phép thử; H3 gộp nhiều chỉ số và "không kém hơn" không có biên

**Bằng chứng.** P:89–95 có 5 giả thuyết; H2 có 2 chỉ số, H3 có ít nhất 6 (ruff, pyrefly, test kiến trúc,
hồi quy, `radon cc`, `radon mi`), nhân với 4 nhóm và 3 tầng. P:100 chỉ nói không dựa vào ngưỡng p. H3 "chỉ
số bảo trì không kém hơn" (P:91) là giả thuyết không kém hơn nhưng không có biên. P:82 "so với bản gốc"
không nói so thế nào.

**Sửa.** Thêm vào mục 7, sau điểm 5:

> **Thứ bậc và so sánh nhiều lần.** Phép thử xác nhận gồm đúng hai phép: H1 (như định nghĩa ở đầu mục 7)
> và phép thử chính của H5. Mọi phép còn lại (H2, H3, H4, từng nhóm, từng tầng, hiệu quả chi phí) là phụ:
> báo cáo đủ mọi ước lượng kèm khoảng tin cậy 95%, không hiệu chỉnh so sánh nhiều lần, và báo cáo nói rõ
> số phép so đã làm. Không chỉ số nào bị bỏ khỏi báo cáo vì kết quả của nó.
>
> **Cách đo H2, H3.** Mỗi chỉ số lấy trung bình trên các lượt hợp lệ của từng (nhóm, nhiệm vụ, cách làm),
> rồi lấy hiệu theo cặp. H2: tổng token (vào, gồm cả token đọc và ghi cache, cộng ra) và thời gian chạy
> `wall_s`. H3 tách ba phần, đọc riêng: (a) lỗi tĩnh = số lỗi `ruff` cộng số lỗi `pyrefly` mỗi lượt;
> (b) hồi quy = tỉ lệ lượt có ít nhất một test cũ hỏng; (c) bảo trì = `radon mi` trung bình của file
> `backend/src` bị đổi, trừ `baseline_radon_mi` của nhiệm vụ; "không kém hơn" nghĩa là cận dưới khoảng tin
> cậy của hiệu (đặc tả trừ vibe) lớn hơn **−5 điểm MI**. `radon cc` và test kiến trúc được báo cáo mô tả.
> Lượt mà công cụ đo không chạy được (giá trị rỗng) bị bỏ khỏi chỉ số đó và được đếm.

Biên −5 là đề xuất của người phản biện; An phải xác nhận hoặc đổi con số trước thẻ.

### I7. Chi phí quy đổi chưa tính được một cách duy nhất

**Bằng chứng.** P:85 "bảng giá API công khai ngày chạy": các lượt trải nhiều tuần (hạn mức agy hồi sau
167 giờ), nên có nhiều "ngày chạy". `meta.usage.input_tokens` gộp token thường, token ghi cache và token
đọc cache (`agents.py:155–161`, `:195`); một lượt Sonnet có khoảng 565.000 token vào
(`pilot-report.md:301`), phần lớn là đọc cache, mà giá đọc cache thấp hơn nhiều lần. Chọn cách tính nào
làm chi phí lệch cỡ một bậc độ lớn, và ảnh hưởng trực tiếp phép so "Sonnet theo đặc tả với Opus vibe"
(P:104–105) và mục hiệu quả chi phí (P:112–113).

**Sửa.** Thay dòng P:85 bằng:

>   - Token vào và ra, thời gian (`wall_s`), số lượt gọi. Chi phí quy đổi: tách token của từng lượt từ
>     `transcript.jsonl` thành bốn loại (vào không cache, ghi cache, đọc cache, ra; token suy luận tính
>     theo cách nhà cung cấp tính tiền), nhân với giá API công khai của đúng mô hình đó. Dùng **một** bảng
>     giá cho mọi lượt, chụp ngày gắn thẻ và commit ở `prereg/prices.toml` kèm đường dẫn nguồn. Công cụ nào
>     không tách được loại token thì tính mọi token vào theo giá vào thường và ghi rõ là cận trên. Số lượt
>     gọi không so được giữa các công cụ, chỉ so giữa hai cách làm trong cùng nhóm.

Mục 6 của kế hoạch phân tích (P:112–113) thêm: "Nhóm, tầng và cách làm có 0 lượt đạt thì chi phí cho một
lượt đạt ghi là không xác định, không ghi 0."

### I8. Gán nhãn: hướng dẫn chưa khóa, không nằm trong thẻ, và tuyên bố làm mù quá mạnh

**Bằng chứng.**

- P:117 dẫn `team/labeling/guide.md`, file này không có trên nhánh `harness` (chỉ có ở
  `report:team/labeling/guide.md`), nên thẻ `prereg-v1` không chứa nó.
- Hướng dẫn tự ghi là "bảng khởi đầu", sẽ chỉnh sau gán thử rồi mới khóa (guide dòng 27–28). Chạy thử đã
  đề xuất thêm hai nhãn (`docs/pilot-report.md:373–386`) chưa có trong bảng.
- P:117–118 khẳng định người gán nhãn "không biết lượt đó thuộc cách làm nào, vì file thiết kế và kế
  hoạch đã bị bỏ". Bộ chấm chỉ bỏ 4 đường dẫn (`grade.py:29–33`, `:492–493`). Lời dặn theo đặc tả còn yêu
  cầu viết test trước cho từng phần việc (`prompts/spec.md`, bước 3), nên bản vá theo đặc tả thường có
  nhiều test hơn và có thể nhắc tới "plan", "task". Hướng dẫn đã lường trước ("lộ cách làm", guide dòng
  22–23) nhưng bản đăng ký trước không đo mức lộ.
- Không nói gán nhãn tầng nào, kappa tính trên gì, mã lượt có ẩn cách làm hay không (thư mục kết quả tên
  `<arm>-r<rep>`, `runner.py:231`).

**Sửa.** Thay điểm 8 của mục 7 (P:116–118) bằng:

> 8. **Phân tích lỗi.** Lợi và Bảo gán nhãn độc lập mọi lượt hợp lệ không đạt của hai nhóm Claude ở cả ba
>    tầng, mỗi lượt một nhãn, theo `team/labeling/guide.md`. Bảng nhãn được khóa sau khi gán thử trên các
>    lượt của p01, p02 và **trước khi** hai người nhận lượt chính nào; bản đã khóa được chép vào
>    `prereg/labeling-guide.md` và ghi mã băm SHA-256 ở mục 9. Mỗi lượt được trao dưới một mã ngẫu nhiên
>    không chứa nhóm, cách làm hay số lần lặp, theo thứ tự xáo trộn; gói gồm đề bài, bản vá đã bỏ
>    `docs/design.md`, `docs/plan.md` và log test. Việc làm mù là **một phần**: bản vá có thể để lộ cách
>    làm (ví dụ số test AI viết). Người gán nhãn ghi "lộ cách làm" khi nhận ra; báo cáo nêu tỉ lệ lượt bị
>    ghi như vậy. Báo cáo kappa của Cohen trên nhãn đơn của toàn bộ lượt được gán, kèm bảng chéo hai người;
>    An phân xử chỗ lệch và ghi lý do. An biết cách làm của từng lượt, nên nhãn sau phân xử không được coi
>    là mù.

### I9. Thiếu bước kiểm "đạt test nhưng sai" mà bản thiết kế yêu cầu

**Bằng chứng.** D:430–431: An đọc mẫu ngẫu nhiên 20 lượt đạt, đối chiếu bản vá gốc. Mục 7 của bản đăng ký
trước không có bước này, không có khung lấy mẫu hay hạt giống. Đây là kiểm tra duy nhất cho độ giá trị
của chỉ số chính.

**Sửa.** Thêm điểm 10 vào mục 7:

> 10. **Đạt test nhưng sai.** Lấy ngẫu nhiên 20 lượt đạt của hai nhóm Claude, 10 lượt mỗi cách làm, phân
>     bổ theo tầng tỉ lệ với số lượt đạt, hạt giống `20261115`, lấy trên danh sách lượt sắp theo (nhóm,
>     nhiệm vụ, cách làm, lần lặp). An đối chiếu từng bản vá với bản vá gốc và ghi lượt nào đạt test nhưng
>     sai hoặc thiếu hành vi đề bài nêu. An không mù cách làm; báo cáo ghi rõ. Kết quả là mô tả, không sửa
>     `task_pass`.

### I10. AI sửa cấu hình test hoặc `pyproject.toml`: bộ chấm có cờ nhưng bản đăng ký trước không nói dùng thế nào

**Bằng chứng.** Bộ chấm khôi phục mọi file test cũ về bản của commit cha và ghi đè test ẩn
(`grade.py:498–504`), nhưng theo ruling R8 không khôi phục `backend/pyproject.toml` ở nhiệm vụ một commit
và không xóa `conftest.py` mới do AI thêm; nó chỉ ghi `pytest_config_touched` (`grade.py:220–232`, `:555`).
Sổ ghi nói "analysis reports such runs" nhưng mục 5 và 7 không có. Ở nhiệm vụ nhiều commit thì
`pyproject.toml` và `uv.lock` lại được khôi phục từ `end` (`grade.py:505–511`), tức hai tầng xử lý khác nhau.

**Sửa.** Thêm vào mục 5, sau định nghĩa chỉ số chính:

> **Cách chấm.** Trước khi chạy test, bộ chấm đưa mọi file test có sẵn về bản của mã nền và chép test ẩn
> từ commit gốc, nên AI sửa hay xóa test có sẵn không làm đổi kết quả; test cũ bị AI xóa tính là hồi quy;
> test do AI viết mà hỏng không tính là hồi quy. Ở nhiệm vụ một commit, `pyproject.toml` của AI được giữ
> nguyên; ở nhiệm vụ nhiều commit, `pyproject.toml` và `uv.lock` lấy từ commit `end`. Lượt có
> `pytest_config_touched = true` (bản vá đổi `conftest.py` hoặc cấu hình pytest) vẫn là lượt hợp lệ và
> được đếm theo cách làm; phân tích độ nhạy ở điểm 7 chạy thêm một lần bỏ các lượt này.

### I11. Hai lời dặn khác nhau nhiều hơn "viết đặc tả trước": phải nói rõ can thiệp là một gói

**Bằng chứng.** `prompts/vibe.md` là một câu. `prompts/spec.md` ngoài thiết kế và kế hoạch còn yêu cầu:
viết test trước cho từng phần việc, chạy để thấy trượt, và cuối cùng chạy cả bộ test backend "(from
`backend/`, `uv run pytest`) and fix any failures". Cách vibe không được bảo chạy test và không được cho
biết lệnh chạy test. D:259 nói "khác biệt duy nhất là lời dặn về quy trình", đúng về hình thức, nhưng một
hiệu số dương có thể đến từ việc chạy bộ test chứ không từ đặc tả. Mã băm đã chốt nên không đề nghị sửa
lời dặn; đề nghị ghi đúng thứ được so.

**Sửa.** Thêm vào mục 2, sau hai dòng mã băm:

> Can thiệp là **một gói**: viết thiết kế, viết kế hoạch, viết test trước cho từng phần việc, và chạy cả
> bộ test backend trước khi dừng (lời dặn nêu cả lệnh `uv run pytest`). Lời dặn vibe không nêu điều nào
> trong số này. Thí nghiệm ước lượng tác dụng của cả gói, không tách được phần của riêng tài liệu đặc tả.
> Để mô tả cơ chế, báo cáo số lượt mỗi cách làm có chạy `pytest` trong nhật ký và số test AI viết; hai con
> số này là mô tả, không phải phép thử.

### I12. Mã phân tích chưa tồn tại lúc gắn thẻ

**Bằng chứng.** Repo không có `results/analysis/` hay mã phân tích nào; D:455 dự kiến có. Bản đăng ký
trước mô tả phân tích bằng lời, nên các lựa chọn nhỏ (làm tròn, cách xử lý ô trống, cách gộp) vẫn được
quyết khi đã có số liệu chính.

**Sửa.** Thêm vào cuối mục 7:

> **Mã phân tích.** Mã tính mọi bảng và hình của mục này được commit trước khi mở kết quả chính đầu tiên
> và được chạy thử trên dữ liệu `results/raw/pilot`. Commit của mã và mọi lần sửa sau đó được ghi ở mục 9.
> Phân tích nào không nằm trong mục 7 thì được ghi nhãn "khám phá, thêm sau khi thấy số liệu" trong báo cáo.

---

## Minor

### M1. Bản thiết kế còn câu chữ trái với điều bản đăng ký trước chốt

Sửa trong cùng commit, để hai văn bản không mâu thuẫn tại thẻ:

- D:313 ghi Antigravity CLI 1.5.8; thực tế và P:55 là 1.5.9 (`pilot-report.md:29–31`). Thêm chú thích
  "1.5.9 lúc chạy thử".
- D:337–360 và D:362–365 còn mô tả proxy, "ghi rõ thí nghiệm chạy qua proxy", và "công cụ nào không tắt
  được truy cập web thì loại", trái với R11 (D:292–296, P:60).
- D:224 chỉ nêu giới hạn 3 lần cho tầng tính năng; con số 2 lần cho tầng vừa (P:70) không có trong bản
  thiết kế.
- D:316–317 so với D:492–493 về thứ tự đợt 2, 3 (xem I2).
- D:409–412 chọn ca định tính "trong tầng tính năng"; với ba tầng, cụm này không rõ. Đề nghị thay điểm 9
  của mục 7 (P:119) bằng: "**Ca nghiên cứu định tính** theo quy tắc ở mục 7.5 của bản thiết kế, áp dụng
  trên **tầng lớn**; nếu mọi nhiệm vụ tầng lớn có hiệu số bằng 0 ở `claude-sonnet` thì lấy nhiệm vụ có bản
  vá gốc lớn nhất."
- D:435 "15 nhiệm vụ" trong phần hạn chế chưa cập nhật theo ba tầng.

### M2. Mục 9 chưa có thủ tục ghi thay đổi

Thay P:126–128 bằng:

> ## 9. Thay đổi sau thẻ
>
> Mỗi thay đổi là một dòng: ngày; mục bị đổi; nội dung cũ và mới; lý do; đã xem kết quả nào trước khi
> đổi (chưa xem gì, đã xem số lượt theo trạng thái, đã xem tỉ lệ đạt); commit. Văn bản tại thẻ không bị
> sửa: thay đổi được thêm vào mục này và gắn thẻ mới (`prereg-v1.1`, `prereg-v1.2`, …). Báo cáo chép lại
> toàn bộ bảng này.
>
> (Chưa có.)

### M3. Thẻ phải phủ đúng những gì bản đăng ký trước nói là đã chốt

`prereg/` hiện chưa được commit (`git status`: `?? prereg/`). Đề bài của 15 nhiệm vụ không có mã băm trong
văn bản; chúng chỉ được chốt nhờ nằm trong commit mang thẻ. Bộ chạy không lưu kiểm tra lệch đề bài qua các
lần chạy tiếp (ruling parked M6, sổ ghi `harness-and-pilot`). Thêm vào cuối mục 1:

> Thẻ `prereg-v1` chốt toàn bộ cây tại commit mang thẻ: `tasks/t01`–`t15` (`task.toml`, `prompt.md`),
> `prompts/`, `harness/` (mã, `cohorts.toml`, `uv.lock`). Mọi lượt chính chạy từ đúng commit này. Sau khi
> chạy, kiểm tra mỗi (nhiệm vụ, cách làm) có đúng một giá trị `prompt_sha256` trên mọi lượt và báo cáo kết
> quả kiểm tra.

### M4. Mô hình và phiên bản thực tế

`meta.model_served` của Codex luôn rỗng (`pilot-report.md:83–87`), nên không kiểm được mô hình được phục
vụ. agy tự cập nhật, không tắt được (`pilot-report.md:29–31`). Thêm vào P:65: "Báo cáo liệt kê mọi phiên
bản công cụ đã gặp và số lượt của từng phiên bản theo cách làm. Với `codex-luna`, mô hình được phục vụ
không ghi được cho từng lượt; báo cáo nêu hạn chế này."

### M5. "Độ dao động giữa 3 lần lặp" chưa có định nghĩa

P:101. Thay bằng: "Báo cáo độ dao động giữa các lần lặp: tỉ lệ ô (nhóm, nhiệm vụ, cách làm) mà các lần
lặp không cùng kết quả."

### M6. Phân tích độ nhạy `upstream_urls` chỉ bắt được đường dẫn

P:114–115. Mẫu chỉ khớp URL chứa `vipharmind` hoặc `doanan293` (`agents.py:14–16`); lệnh tìm kiếm web theo
từ khóa không để lại URL như vậy. Thêm: "Cờ này chỉ bắt được đường dẫn xuất hiện trong nhật ký; báo cáo
nêu đây là cận dưới của mức truy cập mã gốc."

### M7. Nhiệm vụ có rất ít test ẩn

Sổ ghi `harness-and-pilot` ghi t06 và t13 chỉ có 2 test ẩn ("weak signal; note in analysis"). Bản đăng ký
trước không nhắc. Thêm vào mục 1: "Số test ẩn của từng nhiệm vụ được báo cáo trong bảng nhiệm vụ; t06 và
t13 chỉ có 2 test ẩn."

### M8. Câu về lịch sử duyệt đề bài

P:18–19 nói "An duyệt gộp" và t05, t07, t13 được bổ sung sau. Ruling R12 ghi "Prompt edits need An's
re-approval at prereg-v1". Chưa thấy bản ghi nào về lần duyệt lại này (`tasks/REVIEW.md` chỉ có duyệt gộp
ngày 2026-11-15 cho bản nháp đầu). Thêm một câu xác nhận, hoặc ghi vào `tasks/REVIEW.md` trước thẻ: "An
duyệt lại ba đề đã sửa (commit `e92f346`) ngày <ngày>."

---

## Đã kiểm, đúng

- Mã commit ViPharmind `3baae61d…` (P:16) khớp D:81.
- 15 dòng của bảng nhiệm vụ (P:23–37): mã commit (12 ký tự đầu), lớp và `src_lines` khớp
  `tasks/t01`–`t15/task.toml`; cả 15 có `pilot = false`.
- Ngưỡng ≤ 82, 83–173, ≥ 174 (P:39) khớp tam phân vị 82,7 và 173,3 của 15 kích thước
  (`pilot-report.md:349–355`); mỗi nhóm đúng 5 nhiệm vụ như bảng.
- SHA-256 của `prompts/vibe.md` và `prompts/spec.md` (P:46–47) khớp `sha256sum`.
- Bảng nhóm (P:53–56) khớp `harness/cohorts.toml` (mô hình, effort, số tài khoản) và phiên bản công cụ lúc
  chạy thử.
- 15 × 2 × 3 × 4 = 360 (P:69) khớp D:305–306; hạt giống `20261115` khớp `runner.py:56` và `cli.py:237`;
  mặc định `--reps 3`, `--max-quota-retries 20` khớp.
- Năm giả thuyết (P:89–95) đúng nguyên văn D:383–387.
- Điều kiện chung (P:60–65) khớp ruling R10, R11 và `pilot-report.md` mục 0.
- Thứ tự bỏ nhóm (P:123) khớp D:317.
