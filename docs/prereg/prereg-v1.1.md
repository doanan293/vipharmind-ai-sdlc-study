# Đăng ký trước, bản bổ sung `prereg-v1.1`: nhiệm vụ tầng vừa và tầng lớn

Ngày: 2026-11-15. Văn bản này bổ sung `docs/prereg/prereg-v1.md` (thẻ `prereg-v1`). Nó chốt danh sách nhiệm vụ
tầng vừa và tầng lớn, dữ liệu của từng nhiệm vụ, mã băm đề bài và lệnh chạy chính của hai tầng này. Mọi
điều `prereg-v1` không nói khác ở đây thì giữ nguyên.

An duyệt văn bản này ngày: **2026-11-15** (duyệt gộp cùng năm đề m01–m05 đã sửa theo
`data/tasks/EXTRA_REVIEW_fable.md`; dòng duyệt của từng đề ở `data/tasks/EXTRA_REVIEW.md`).

## Vị trí của văn bản này

- `prereg-v1` cho phép `prereg-v1.1` chỉ *thêm* dữ liệu nhiệm vụ. Văn bản này còn **thay quy tắc chọn
  tầng vừa** (gạch đầu dòng "Tầng vừa" của ràng buộc 3 và toàn bộ ràng buộc 4 trong mục "Phạm vi và bản
  bổ sung `prereg-v1.1`" của `prereg-v1`). Đây là thay đổi sau thẻ; nó được ghi ở mục 11 của
  `prereg-v1` (dòng ngày 2026-11-15, thay đổi 1). Quy tắc tầng lớn, giả thuyết, chỉ số, kế hoạch phân
  tích, số lần lặp, giới hạn thời gian và quy tắc loại giữ nguyên.
- Quy tắc mới được viết **sau khi** đã xem số liệu dựng nhiệm vụ của các ứng viên (số dòng, kết quả chấm
  bản vá gốc, số tên, độ phủ) và sau một danh sách m01–m05 chọn tay đầu tiên, nhưng **trước mọi lượt AI**
  trên bất kỳ ứng viên hay nhiệm vụ tầng vừa, tầng lớn nào. Người soạn chưa xem kết quả lượt chạy chính
  nào.
- Người duyệt độc lập (Fable) dựng lại toàn bộ việc chọn bằng mã riêng và ra đúng 21 cửa sổ hợp lệ và
  đúng năm cửa sổ được chọn, cùng thứ tự (`data/tasks/EXTRA_REVIEW_fable.md`, phần 2).

## Lượt chạy chính tầng nhỏ đã bắt đầu trước thẻ này (ràng buộc 1 của `prereg-v1`)

Lượt chạy chính tầng nhỏ bắt đầu khoảng **19:16 ngày 2026-11-15**, trước khi thẻ `prereg-v1.1` được gắn.
Vì vậy trường hợp dự phòng của ràng buộc 1 được áp dụng. Xác nhận tại thời điểm viết:

- chưa ai mở `grade.json` hay bất kỳ kết quả nào của các lượt tầng nhỏ, và chưa tính tỉ lệ đạt nào; người
  soạn và người duyệt đề tầng vừa không mở thư mục kết quả hay cây làm việc của lượt chạy chính;
- trong lúc chờ chỉ được xem số lượt theo trạng thái (`sdlc-harness status`);
- kết quả tầng nhỏ tiếp tục bị che cho tới khi **cả** thẻ `prereg-v1.1` **và** thẻ `prereg-v1-analysis`
  (mục 9 của `prereg-v1`, đoạn "Mã phân tích") đã gắn.

Mục 11 của `prereg-v1` ghi ngày gắn thẻ `prereg-v1.1` và ngày mở kết quả (thay đổi 2 ngày 2026-11-15; ngày
mở kết quả được thêm thành một dòng khi việc mở xảy ra).

## Nhiệm vụ tầng lớn

Quy tắc tầng lớn giữ nguyên (một đoạn liền nhau, từ 750 dòng `backend/src`, tối đa 35 tên). Tầng lớn là
**f08, f14, f15** (`data/tasks/<id>/task.toml`, đề bài qua quy trình ở `data/tasks/FEATURE_REVIEW.md` và
`data/tasks/FEATURE_REVIEW_fable.md`).

| Id | Đoạn | `base` | `end` | Commit | Lớp | Dòng `backend/src` | File test ẩn | Tên nêu trong đề: mục (dòng) | Tên cơ học |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| f08 | F08 | `45271fddc0236bc3f3336b30d99771abf626f14c` | `cc0f06a67bfa888ef5d7e1ebd1715a517079bbc9` | 6 | api | 764 | 15 | 53 (14) | 13 |
| f14 | F14 | `c2935909a101b7274c58ec0e678371c0a13b3d07` | `11079ab21c7fa8299bd59f73b7e6a901ba98ffc4` | 4 | application | 1.464 | 7 | 93 (16) | 32 |
| f15 | F15 | `11079ab21c7fa8299bd59f73b7e6a901ba98ffc4` | `ef23fe8cb40354573c362e570f8a399ad4328c42` | 5 | infrastructure | 1.367 | 14 | 85 (20) | 24 |

F07 (`adf89a7b62..c36b6e91e9`, 7 commit, 1.364 dòng) và F04 (`432d790170..5445f66dbb`, 7 commit, 1.187
dòng) được xét lại theo quy tắc tầng lớn và bị loại vì cần khoảng 70 và 60 tên (đếm tay số tên test được
chấm cần, gồm cả phương thức dịch vụ và phương thức port mà fake được khôi phục cài; chi tiết ở
`data/tasks/EXTRA_REVIEW.md` và `large_rechecks` trong `medium_candidates.json`). Bản vá gốc của cả hai chấm
sạch. Không lượt AI nào chạy trên hai đoạn này.

**F09 không vào tầng lớn (quyết định 2026-11-15, An ủy quyền).** F09 (`cc0f06a67b..bbeed71482`, 7 commit gồm
một commit `test`, 1.096 dòng `backend/src`) đã bị loại trong đợt chọn đầu, trước chạy thử, vì đề phải nêu
30–35 tên và gần như là một bản thiết kế viết sẵn (bản thiết kế, mục 7.2b). Quyết định đó được giữ nguyên:
đưa F09 trở lại lúc này là đảo một quyết định cũ sau khi đã thấy các con số chọn tầng vừa, và F09 chứa cả
ba commit của m03. F09 không được chấm bản vá gốc và không được đếm tay số tên; báo cáo ghi rõ điều này.

**Cách đếm tên trong bảng (dùng cho cả hai tầng).**

- *Tên nêu trong đề, mục*: số mục đặt trong dấu `` ` `` ở phần "Required interfaces" của `prompt.md`, mỗi
  lần xuất hiện một mục (lớp, hàm, phương thức, tham số từ khóa, trường, route, lệnh CLI, mã lỗi, tên
  file, khóa JSON…), không tính đường dẫn module hay lớp đứng ngay trước dấu hai chấm chỉ để định vị.
  Số trong ngoặc là số dòng của phần đó (đơn vị của cột "required-interface entries" trong
  `data/tasks/FEATURE_REVIEW.md`). Đây là số đếm theo đề đã soạn; `prereg-v1` yêu cầu báo cáo số này.
- *Tên cơ học*: số tên N1–N7 của `data/tasks/feature-feasibility/medium_names.py` (định nghĩa ở mục "Quy
  tắc chọn tầng vừa"), chạy trên test ẩn và file hỗ trợ được khôi phục của nhiệm vụ. Với tầng lớn con số
  này chỉ để tham khảo.

**Hạn chế phải nêu trong báo cáo.** Ngưỡng 35 tên của tầng lớn không có đơn vị đếm cố định. Theo đơn vị
"mục nêu trong đề", cả ba nhiệm vụ tầng lớn vượt 35; theo đơn vị "dòng" (14, 16, 20) và theo cách đếm cơ
học (13, 32, 24) thì không. F04 và F07 bị loại theo số tên test cần đếm tay (khoảng 60 và 70); theo cách
đếm cơ học, F04 có 39 và F07 có 24 tên. Như vậy việc loại F07 phụ thuộc vào đơn vị đếm. Văn bản này không
đổi danh sách tầng lớn (f08, f14, f15 đã có trong ràng buộc 7 của `prereg-v1` tại thẻ), và báo cáo ghi
rõ rằng ngưỡng tên của tầng lớn được áp bằng phán đoán của người soạn, không bằng một thủ tục cố định.

## Quy tắc chọn tầng vừa (thay ràng buộc 3 tầng vừa và ràng buộc 4)

**Tập ứng viên** như ràng buộc 2: mọi đoạn 2–3 commit first-parent liền nhau nằm trong 16 đoạn của
`ranges.json`. `medium_candidates.json` ghi 93 cửa sổ: mọi cửa sổ có thể hợp lệ (đã kiểm: không cửa sổ
nào trong 188 cửa sổ của 16 đoạn mà toàn commit `feat`, chỉ đổi `backend/` và có 300–700 dòng bị thiếu),
cộng các cửa sổ đã xét trước đó.

**Một cửa sổ hợp lệ khi thỏa mọi điều sau:**

1. 2–3 commit first-parent liền nhau của cùng một plan (một trong 16 đoạn).
2. Không commit nào có loại conventional `test`, `refactor`, `chore` hoặc `docs`.
3. Chỉ đổi file dưới `backend/`.
4. 300–700 dòng `backend/src` (dòng thêm cộng dòng bớt, `git diff --numstat base end`).
5. Không chung commit nào với t01–t15, p01, p02, f08, f14, f15.
6. Bản vá gốc (`git diff base end`) chấm `task_pass = true` trên cây mới, không hồi quy.
7. Ít nhất **5** test ẩn được chấm (không mang dấu `integration`) trượt ở `base`.
8. Tối đa **50%** dòng `backend/src` được thực thi của cửa sổ chỉ do test `integration` thực thi
   (cách đo ở dưới).
9. Tối đa **20** tên theo cách đếm cơ học ở dưới.

**Cách đo tỉ lệ integration (tiêu chí 8).** Tại `end`, chạy hai lượt pytest với pytest-cov và
`--cov-context=test`: lượt chấm (mặc định của dự án, `-m "not integration"`) và lượt integration
(`-m integration`, có Docker). S là các câu lệnh (theo coverage.py) nằm trên dòng mà diff `base..end` thêm
hoặc sửa trong `backend/src/**.py`, bỏ những dòng chỉ chạy lúc import hay thu thập test ở cả hai lượt
(ngữ cảnh rỗng). G là phần của S chạy trong một test của lượt chấm, I là phần chạy trong một test của
lượt integration. Tỉ lệ bằng |I − G| / |S|. Mã: `data/tasks/feature-feasibility/medium_coverage.py`.

**Cách đếm tên cơ học (tiêu chí 9 và thứ tự chọn).** Trên các file test ẩn và file hỗ trợ được khôi phục
từ `end` (cả test được chấm lẫn test `integration`), một tên được đếm khi test cần nó và nó chưa có ở
`base`:

- N1: mỗi (module, tên) được import từ `pharma_agent.*` mà ở `base` không phải định nghĩa cấp module hay
  module con;
- N3: mỗi route mới (file, router, phương thức HTTP, đường dẫn) trong `backend/src` ở `end`;
- N4: mỗi lệnh CLI mới (hàm có decorator `.command(...)`) trong `backend/src` ở `end`;
- N5: mỗi chuỗi dạng `CHỮ_HOA` (từ hai phần) trong test có trong `backend/src` ở `end` mà không có ở
  `base` (mã lỗi, hành động audit), trừ tên đã đếm ở N1;
- N6: mỗi thành viên enum mới `X.THÀNH_VIÊN` mà test dùng trên một lớp `X` đã có ở `base`;
- N7: mỗi tên phương thức công khai của lớp giả (fake) trong file test hoặc file hỗ trợ mà
  `backend/src` định nghĩa (`def tên`) ở `end` nhưng không ở `base`, tức phương thức port mới mà fake
  được khôi phục đã cài. N7 khớp `def tên` ở bất kỳ đâu trong `backend/src`, nên một hàm mới không liên
  quan trùng tên cũng được đếm; điều này không ảnh hưởng cửa sổ nào được chọn.

(Không có N2: một loại đếm bị bỏ trước khi áp quy tắc lên bất kỳ cửa sổ nào; các mã còn lại giữ số cũ.)
Trường, tham số từ khóa, phương thức của chính các lớp mới và chuỗi văn bản tự do không được đếm; đề bài
vẫn phải nêu chúng khi test ghim chúng (kiểm ở bước đối chiếu tên, ràng buộc 6). Mã:
`data/tasks/feature-feasibility/medium_names.py`.

**Đơn vị của ngưỡng 20 tên đã đổi.** Ngưỡng của `prereg-v1` là "đề bài nêu được mọi tên test ẩn cần với
tối đa 20 tên", tức đếm trên đề. Quy tắc mới giữ con số 20 nhưng áp lên số đếm cơ học, chạy được trước khi
có đề. Theo đơn vị cũ (mục nêu trong đề, như bảng tầng lớn), ba trong năm đề được chọn vượt 20: m02 (25),
m04 (21), m05 (36). Ngưỡng tên chỉ áp ở tiêu chí 9; nó không phải điều kiện bỏ một đề đã soạn (mục "Nhiệm
vụ không qua duyệt đề bài").

**Lớp của cửa sổ** là lớp (`domain`, `application`, `infrastructure`, `api` dưới
`backend/src/pharma_agent/`) chứa nhiều dòng `backend/src` của cửa sổ nhất; file ngoài bốn thư mục này
(ví dụ `cli.py`) không tính; hòa thì theo thứ tự domain, application, infrastructure, api.

**Chọn:** tham lam, tối đa 5 nhiệm vụ, không hai cửa sổ được chọn nào chung commit. Thứ tự xếp: số tên
cơ học tăng dần, rồi số dòng `backend/src` tăng dần, rồi mã commit `end` tăng dần.

- Lượt 1: lần lượt với domain, application, infrastructure, api, lấy cửa sổ hợp lệ đứng đầu thứ tự xếp
  trong lớp đó mà không chung commit với cửa sổ đã chọn.
- Lượt 2: điền các chỗ còn lại từ mọi cửa sổ hợp lệ theo cùng thứ tự xếp, bỏ cửa sổ chung commit với
  cửa sổ đã chọn.
- Đánh mã m01, m02, … theo thứ tự chọn.

**Không có quyền chọn.** Kết quả áp quy tắc được nhận nguyên. Mọi ứng viên, giá trị từng tiêu chí, lý
do loại, lớp, số tên, tỉ lệ integration và lượt chọn được ghi ở
`data/tasks/feature-feasibility/medium_candidates.json` (trường `eligible`, `reason`, `selected`,
`selection_pass`, `selected_as`, `required_names`, `integration_coverage`). Mã áp quy tắc:
`data/tasks/feature-feasibility/medium_select.py`; chạy không đối số (`python medium_select.py`) thì nó đọc
số tên và độ phủ đã ghi trong `medium_candidates.json`, nên chạy lại được từ một bản checkout sạch và ra
đúng 21 cửa sổ hợp lệ và năm cửa sổ dưới đây.

## Nhiệm vụ không qua duyệt đề bài (quy tắc thay thế)

Quy tắc này chỉ áp dụng **trước** thẻ `prereg-v1.1`. Sau thẻ, không nhiệm vụ nào bị thay; vấn đề phát
hiện sau thẻ được ghi ở mục 11 của `prereg-v1` và báo cáo.

1. Một nhiệm vụ tầng vừa đã chọn bị bỏ khi và chỉ khi: (a) người duyệt độc lập kết luận REJECT; hoặc
   (b) còn một tên công khai mà test được chấm cần, chưa có ở `base`, mà đề bài không nêu được (GAP không
   đóng được); hoặc (c) `sdlc-harness tasks validate --original-patch` báo lỗi cho nhiệm vụ đó tại commit
   sẽ gắn thẻ. Không có giới hạn số tên nào ở bước này: ngưỡng 20 tên chỉ là tiêu chí 9 (đếm cơ học), đã
   được kiểm khi chọn.
2. Thay bằng cửa sổ hợp lệ chưa được chọn đứng đầu thứ tự xếp (số tên cơ học, rồi số dòng, rồi `end`) mà
   **không chung commit với bất kỳ nhiệm vụ tầng vừa nào đang giữ và với bất kỳ nhiệm vụ đã bị bỏ nào**.
   Không có lượt theo lớp cho cửa sổ thay thế. Các nhiệm vụ còn lại giữ nguyên mã; cửa sổ thay thế nhận
   mã của nhiệm vụ bị bỏ và đi qua đủ quy trình đề bài (ràng buộc 6). Không chạy lại toàn bộ việc chọn.
3. Lý do bỏ được ghi lại. Không sửa quy tắc để giữ hay bỏ một nhiệm vụ.

Với năm nhiệm vụ hiện có, hàng chờ thay thế là: F13_391-392 (12 tên), F05_71-73 (13), F05_72-74 (13),
F02_29-30 (13), F04_54-55 (13), F12_368-369 (14), F04_55-56 (15), F04_54-56 (18), F12_371-372 (20), mỗi
lần lấy cửa sổ đầu tiên còn thỏa điều 2. Bảy cửa sổ hợp lệ còn lại chung commit với một nhiệm vụ đã chọn
(F05_69-71 chứa cả hai commit của m01) nên không bao giờ được lấy thay cho nhiệm vụ đó. Quy tắc **không
được dùng**: cả năm đề được duyệt (không REJECT, không GAP) và cả năm qua `--original-patch` (mục "Kiểm
tra bộ chạy").

## Nhiệm vụ tầng vừa

Áp quy tắc lên 93 cửa sổ: **21 cửa sổ hợp lệ**, chọn 5.

| Id | Cửa sổ | `base` | `end` | Commit | Lớp | Dòng `backend/src` | Dòng `backend/src` trong file có test được chấm chạy tới | Tên nêu trong đề: mục (dòng) | Tên cơ học | Test ẩn được chấm (trượt ở `base`) | Tỉ lệ integration | Lượt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| m01 | F05_69-70 | `af9d4173a9f4578ff2040a8cb73e6ce95372cf26` | `507a4ae31ea47eef1a195ac074aca1f5515a9ba0` | 2 | domain | 478 | 478 | 13 (3) | 7 | 23 (23) | 0% | 1 |
| m02 | F03_44-45 | `a133d4cd1cbaf8926aeb90d7e2d0eed5f7c6668e` | `68edeac53e8e8fe94c8d8952130448397ad9c40b` | 2 | application | 335 | 182 | 25 (6) | 5 | 6 (6) | 32% | 1 |
| m03 | F09_107-109 | `a24bd490804c90b6c5d007d534606ef9527ec973` | `95d69130cd22b4a08738a5ab49e19c61dfe2ae49` | 3 | infrastructure | 413 | 140 | 18 (5) | 3 | 17 (14) | 44% | 1 |
| m04 | F03_47-48 | `44466f373da672594dbf8a4d419505f662c712f1` | `4ba674d359882c639724ee413fd87044c66597b5` | 2 | api | 362 | 337 | 21 (4) | 11 | 9 (7) | 4% | 1 |
| m05 | F06_80-81 | `067e562740912786b77a7ee3d22de65e536f0a65` | `adf89a7b629a06a5d864c7b3f78d8f4f5c149b01` | 2 | application | 515 | 515 | 36 (3) | 5 | 13 (13) | 0% | 2 |

Cột "trong file có test được chấm chạy tới": tổng dòng `backend/src` (thêm cộng bớt) của những file mà
lượt chấm của `medium_coverage.py` thực thi ít nhất một câu lệnh trên dòng cửa sổ thêm hay sửa; file bị
xóa ở `end` không tính. Cột này mô tả; biến của H5 vẫn là `src_lines`.

Số cửa sổ theo tiêu chí đầu tiên không đạt: ngoài 16 đoạn 1; có commit `test` 5; chung commit với
nhiệm vụ tầng khác 42; đổi file ngoài `backend/` 2; ngoài 300–700 dòng 11; dưới 5 test ẩn được chấm
trượt ở `base` 4; tỉ lệ integration trên 50% 5; trên 20 tên 2. Trong 16 cửa sổ hợp lệ không được chọn,
7 chung commit với một cửa sổ đã chọn, 9 đứng sau trong thứ tự xếp.

So với danh sách m01–m05 soạn tay trước đó: chỉ F03_47-48 còn lại (nay là m04). F03_43-44 (m01 cũ)
chung commit `2541825` với m02 mới (ít tên hơn); F05_71-73 (m03 cũ) và F02_29-30 (m04 cũ) hợp lệ nhưng
13 tên, đứng sau các cửa sổ được chọn; F12_370-371 (m05 cũ) không hợp lệ vì tỉ lệ integration 57%.

**Độ nhạy của việc chọn theo tham số tự do của quy tắc** (Fable, cùng dữ liệu, đổi một tham số mỗi lần):

| Thay đổi | Kết quả |
| --- | --- |
| bỏ lượt theo lớp (chỉ xếp hạng) | cùng năm cửa sổ, khác số thứ tự |
| tối thiểu 1, 3 hoặc 5 test trượt ở `base` | không đổi |
| tối thiểu 8 hoặc 10 test trượt ở `base` | m02 và m04 ra (F03_43-44 và F13_391-392 vào) |
| ngưỡng integration 60%, 75%, 100% | không đổi |
| ngưỡng integration 33% hoặc 40% | m03 ra (F02_29-30 vào) |
| ngưỡng integration 25% | m02 và m03 ra |
| cho phép commit `test`/`refactor` | không đổi |
| xếp hòa không theo số dòng (tên, rồi `end`) | không đổi |

Ngưỡng 5 test và 50% được đặt sau khi đã thấy số liệu dựng nhiệm vụ của ứng viên (không phải kết quả
AI). m03 (44%) phụ thuộc vào ngưỡng 50% và vào định nghĩa tỉ lệ (bỏ dòng chỉ chạy lúc import); báo cáo
nêu điều này.

## Đề bài

Đề bài của mỗi nhiệm vụ là `data/tasks/<id>/prompt.md`, qua đúng quy trình ở ràng buộc 6: soạn, đối chiếu tên
với test ẩn (`data/tasks/EXTRA_REVIEW.md`, `data/tasks/FEATURE_REVIEW.md`), Fable duyệt độc lập
(`data/tasks/EXTRA_REVIEW_fable.md`, `data/tasks/FEATURE_REVIEW_fable.md`), An duyệt. Đề tầng vừa là bản nháp cộng
mọi sửa đổi của Fable (kể cả sửa đổi không bắt buộc M01-4 và gợi ý ở m03); An duyệt gộp ngày 2026-11-15.

Mã băm SHA-256 của `prompt.md` (bộ chạy ghi `prompt_sha256` cho từng lượt; sau khi chạy, kiểm tra mỗi
(nhiệm vụ, cách làm) có đúng một giá trị trên mọi lượt và giá trị đó khớp bảng này):

| Id | SHA-256 của `data/tasks/<id>/prompt.md` |
| --- | --- |
| m01 | `02397792c32996a67f1a2ce0962126f3bd2a18e1f9ec1b88b0037a14ebb115e7` |
| m02 | `956880ec17c2dc3d8122d59dfe952f44fa081515ba27637b1182d60be4126caa` |
| m03 | `c256d8d561d505f5893bb024e3e2b5848c4aa8a6a31ad293ea6aff57ca5344a3` |
| m04 | `24495bae479055eab12057d84b38c024f8898e0ddb2d226ac7b8500c3283bb5f` |
| m05 | `339612888103f12fff4d39154b387f613cb363f16f361b1cc4ee2b7162e23da0` |
| f08 | `e6eac4e95280b1eae15f1e5bce0886b48936d1724394126fbafa52881371da2f` |
| f14 | `15c80f6b41c3e182a675c7a18340f15ac4c0e2e7e24aec780e408ca9715330a9` |
| f15 | `07fec15c17c3b21f8e387d02947a005e550354a5859dbd00f78724d118ac2a21` |

Thẻ `prereg-v1.1` chốt toàn bộ cây tại commit mang thẻ, như thẻ `prereg-v1` chốt tầng nhỏ:
`data/tasks/m01`–`m05`, `data/tasks/f08`, `data/tasks/f14`, `data/tasks/f15` (`task.toml`, `prompt.md`), `code/prompts/`,
`code/harness/`.

## Kiểm tra bộ chạy (không gọi AI)

Tại commit mang thẻ (bộ chạy gồm commit `527d7e1`, bỏ hunk của đường dẫn bị loại khỏi cây khi áp bản vá
gốc của đoạn):

- `sdlc-harness tasks validate --repo /home/andv/personal/vipharmind` thoát với mã 0 (mọi thư mục nhiệm
  vụ, gồm m01–m05; danh sách `hidden_tests` của mỗi nhiệm vụ đoạn khớp tập do git tính).
- `sdlc-harness tasks validate --repo /home/andv/personal/vipharmind --original-patch` chấm bản vá gốc
  `git diff base end` của m01–m05, f08, f14, f15 trên cây mới:
  cả tám nhiệm vụ chấm sạch (mọi test ẩn đạt, không hồi quy, không lỗi chấm), lệnh thoát với mã 0
  (2026-11-15, khoảng 19:42–19:52, tại commit `3ae4252` cộng các thay đổi của bản này; m04 chấm trên
  bản vá không sửa tay). Quy tắc thay thế vì vậy không được dùng.

## Chồng lấn với tầng khác (ràng buộc 7)

**Chung commit.** Theo tiêu chí 5, không nhiệm vụ tầng vừa nào chung commit với nhiệm vụ tầng nhỏ, chạy
thử hay tầng lớn. Chồng lấn của tầng lớn (giữ từ `prereg-v1`): f08 chứa commit của t03 (`c3a88b2659`) và
p02; f14 bắt đầu từ commit của t01 (`base` của f14 là commit t01) và có file test ẩn của t02; f15 bắt đầu ở
`end` của f14 và có file test ẩn của t11.

**Chung đường dẫn file test ẩn** (khác phiên bản):

| Nhiệm vụ | File test ẩn trùng đường dẫn | Nhiệm vụ tầng khác |
| --- | --- | --- |
| m02 | `application/test_queries.py`, `application/test_summarize.py` | f08, p02 |
| m02 | `infrastructure/test_container.py` | f08, t13 |
| m02 | `infrastructure/test_migrations.py` (integration) | f08, f15 |
| m03 | `api/test_e2e_postgres.py`, `infrastructure/test_conversation_repository.py` (integration) | f08 |
| m03 | `infrastructure/test_migrations.py` (integration) | f08, f15 |
| m04 | `api/test_conversations_api.py` | f08, f15, p02 |
| m04 | `api/test_e2e_postgres.py` (integration) | f08 |
| m04 | `test_cli.py` | f08, p02, t03 |

Trong tầng vừa: m02 và m03 cùng có `infrastructure/test_migrations.py`; m03 và m04 cùng có
`api/test_chat_api.py` và `api/test_e2e_postgres.py` (mỗi nhiệm vụ dùng phiên bản ở `end` của mình).
Phân tích độ nhạy của H5 bỏ "nhiệm vụ có commit nằm trong một nhiệm vụ của tầng khác"; không nhiệm vụ
tầng vừa nào thuộc loại đó (tầng lớn: f08 và f14 thuộc loại đó).

## Giới hạn thời gian và lệnh chạy chính

Giới hạn thời gian của AI theo mục 4 của `prereg-v1`, không tính lại: tầng vừa **7200 s**, tầng lớn
**10800 s**. Các thông số khác như tầng nhỏ: 3 lần lặp, `--jobs 8`, hạt giống `20261115`, bộ chấm 900 s.
Tầng vừa: 5 × 2 × 3 × 4 = **120 lượt**; tầng lớn: 3 × 2 × 3 × 4 = **72 lượt**.

Chạy từ thư mục gốc repo nghiên cứu, tại commit mang thẻ `prereg-v1.1`. Mỗi tầng một lệnh vì giới hạn thời
gian khác nhau; cả bốn nhóm trong một lệnh. Tầng vừa:

```
cd /home/andv/personal/vipharmind-ai-sdlc-study
code/harness/.venv/bin/sdlc-harness run \
  --repo /home/andv/personal/vipharmind \
  --cohorts claude-sonnet,claude-opus,agy-gemini,codex-luna \
  --tasks m01,m02,m03,m04,m05 \
  --reps 3 \
  --jobs 8 \
  --seed 20261115 \
  --timeout-s 7200 \
  --out data/results/raw/main-tiers
```

Tầng lớn:

```
cd /home/andv/personal/vipharmind-ai-sdlc-study
code/harness/.venv/bin/sdlc-harness run \
  --repo /home/andv/personal/vipharmind \
  --cohorts claude-sonnet,claude-opus,agy-gemini,codex-luna \
  --tasks f08,f14,f15 \
  --reps 3 \
  --jobs 8 \
  --seed 20261115 \
  --timeout-s 10800 \
  --out data/results/raw/main-tiers
```

- Các cờ khác để mặc định như mục 5 của `prereg-v1`. Danh sách nhiệm vụ ghi rõ, không dùng `--tasks main`.
- Mọi quy tắc xử lý kết cục ở mục 4 của `prereg-v1` áp dụng nguyên. Gọi lại đúng lệnh của tầng đó để chạy
  tiếp các lượt `deferred` và các lượt lỗi còn lượt chạy lại; lượt đã có `grade.json` được bỏ qua.
- Thứ tự (mục 10 của `prereg-v1`): trong mỗi nhóm, tầng vừa và tầng lớn chỉ bắt đầu sau thẻ này. Hai lệnh
  dùng chung thư mục `--out`; nếu chạy cùng lúc thì tổng số phiên là 16 thay vì 8, và mục 11 ghi lại
  khoảng thời gian chạy chồng (vì nó có thể làm tăng `wall_s`).

## Phân tích độ nhạy thêm cho H5: số dòng được chấm

Lý do (Fable, V-5): ở m02 và m03, phần lớn mã của cửa sổ chỉ do test `integration` kiểm, nên theo
`task_pass` hai nhiệm vụ này gần với tầng nhỏ hơn số dòng gợi ý.

- **Biến** `graded_src_lines` của một nhiệm vụ: số dòng `backend/src/**.py` mà bản vá gốc (`parent..commit`
  ở tầng nhỏ, `base..end` ở tầng vừa và lớn) thêm hoặc sửa, là câu lệnh theo coverage.py, và được thực thi
  bên trong ít nhất một test ẩn được chấm (thuộc file test ẩn, không mang dấu `integration`) khi chạy lượt
  chấm tại commit gốc với pytest-cov và `--cov-context=test`; bỏ dòng chỉ chạy lúc import hay thu thập
  test. Đây là cách đo G của tiêu chí 8, giới hạn vào ngữ cảnh của test ẩn.
- **Đo khi nào:** cho đủ 23 nhiệm vụ chính (t01–t15, m01–m05, f08, f14, f15), chỉ trên mã gốc, không dùng
  kết quả AI nào; kết quả và mã đo được commit **trước** thẻ `prereg-v1-analysis`. Nhiệm vụ nào đo không
  được thì ghi lý do và bỏ khỏi phân tích này.
- **Phân tích:** chạy lại mô hình logistic hỗn hợp của mục 9, điểm 4 (`prereg-v1`), với
  `log(graded_src_lines)` thay `log(src_lines)`, cùng thứ tự lùi mô hình (bước lùi cuối cũng dùng
  `log(graded_src_lines)`). Tầng của mỗi nhiệm vụ giữ nguyên. Báo cáo hệ số tương tác và khoảng tin cậy 95%
  cạnh kết quả chính. Đây là phân tích độ nhạy, không thay phép thử
  chính; nó được báo cáo dù kết quả thế nào.

## Hạn chế phải nêu trong báo cáo

- **m01 là nhiệm vụ chép đặc tả.** Đề m01 (khoảng 860 từ) nêu 34 mẫu thông báo lỗi và thứ tự báo cáo
  chúng, vì test so khớp cả danh sách lỗi và đặc tả gốc bị bỏ khỏi cây. Với m01, đề bài đã là đặc tả, nên
  cách làm theo đặc tả có ít điều để thêm. Đây là tính chất chung của tầng vừa và tầng lớn, ở mức cao nhất.
- **Kích thước được chấm của m02 và m03 nhỏ hơn số dòng.** m02: 6 test được chấm; 182 trong 335 dòng nằm ở
  file có test được chấm chạy tới, còn checkpointer, container và môi trường migration chỉ do test
  `integration` kiểm. m03: test được chấm chạy tới 140 trong 413 dòng
  (luồng UI message và route; file `sse.py` bị xóa không tính); 247 dòng hạ tầng (`message_citations`) không được chấm, dù lớp của cửa sổ là
  infrastructure.
- **Đơn vị đếm tên khác nhau giữa các tầng** (xem mục "Nhiệm vụ tầng lớn" và "Đơn vị của ngưỡng 20 tên").
- **Bộ chạy:** m04 sửa `backend/docs/superpowers/plans/*.md`; bộ chạy bỏ các đường dẫn `superpowers` khỏi
  cây, và từ commit `527d7e1` bỏ luôn hunk của chúng khi áp bản vá gốc.

## Ghi chú vận hành

- Từ khoảng 19:16 đến 19:45 ngày 2026-11-15, các lần đo độ phủ để chọn tầng vừa chạy cùng lúc với những
  lượt đầu của lượt chạy chính tầng nhỏ, nên chia CPU. Từ khoảng 19:42 cùng ngày, việc chấm bản vá gốc của
  tám nhiệm vụ đoạn (mục "Kiểm tra bộ chạy") cũng chạy cùng lúc (tới khoảng 19:52). Điều này có thể ảnh
  hưởng `wall_s` của các lượt tầng nhỏ chạy trong các khoảng đó; báo cáo ghi chú và kiểm tra số lượt hết
  giờ trong các khoảng này.
- Thư mục nhiệm vụ m01–m05 được bộ chạy nhận là nhiệm vụ đoạn tùy chọn (`code/harness/src/sdlc_harness/cli.py`,
  `FEATURE_TASKS`); thay đổi này chỉ chạm lệnh `tasks validate`, không chạm việc chạy hay chấm.
