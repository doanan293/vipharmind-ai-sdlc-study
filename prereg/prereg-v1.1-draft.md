# Bản nháp `prereg-v1.1`: quy tắc chọn nhiệm vụ tầng vừa (sửa đổi) và danh sách tầng vừa

Ngày viết: 2026-11-15. Trạng thái: **nháp**, chưa gắn thẻ, chưa được An duyệt.

An duyệt văn bản này ngày: **<An điền trước khi gắn thẻ>**.

## Vị trí của văn bản này

- Văn bản này **thay quy tắc chọn tầng vừa** của `prereg-v1` (đã gắn thẻ): gạch đầu dòng "Tầng vừa"
  của ràng buộc 3 và toàn bộ ràng buộc 4 trong mục "Phạm vi và bản bổ sung `prereg-v1.1`". Quy tắc tầng
  lớn (ràng buộc 3, gạch đầu dòng "Tầng lớn") giữ nguyên. Các ràng buộc 1, 2, 5, 6, 7 giữ nguyên.
- Văn bản được viết **trước mọi lượt AI trên ứng viên hay nhiệm vụ tầng vừa và tầng lớn**. Chưa lượt AI
  nào chạy trên bất kỳ ứng viên nào. Việc chọn chỉ dùng tiêu chí dựng nhiệm vụ: commit, số dòng, bản vá
  gốc, test ẩn và độ phủ test của mã gốc. Người soạn chưa xem kết quả lượt chạy chính nào.
- `prereg-v1` cho phép `prereg-v1.1` chỉ *thêm* dữ liệu nhiệm vụ. Sửa quy tắc chọn là một thay đổi
  sau thẻ, nên khi gắn thẻ `prereg-v1.1` thay đổi này được ghi thành một dòng ở mục 11 của `prereg-v1`,
  theo đúng mẫu của mục đó (ngày 2026-11-15; mục bị đổi: ràng buộc 3 tầng vừa và ràng buộc 4; nội dung
  cũ và mới: như dưới đây; lý do: như dưới đây; đã xem: chưa xem kết quả AI nào; commit).

## Lý do sửa (2026-11-15, sau khi quét ứng viên, trước mọi lượt AI)

1. **Độc lập giữa các tầng.** Quy tắc cũ chỉ xếp sau, không loại, ứng viên chứa commit của t01–t15 và
   không xét chồng lấn với tầng lớn. Áp nguyên văn, 3 trong 5 ứng viên đứng đầu nằm trong f08, f14 hoặc
   f15, và phân tích độ nhạy của H5 (ràng buộc 7) sẽ phải bỏ chúng. Một nhiệm vụ tầng vừa chung commit
   với nhiệm vụ tầng khác đo lại cùng một thay đổi mã, nên hiệu số của nó không độc lập.
2. **Đủ tín hiệu chấm.** Có ứng viên chỉ 1–4 test ẩn được chấm trượt ở `base`, hoặc phần lớn mã chỉ
   được test mang dấu `integration` kiểm (không được chấm). Với ứng viên như vậy `task_pass` gần như
   không đo phần việc của tầng vừa.
3. **Chỉ commit tính năng.** Commit chỉ thêm test hoặc chỉ tái cấu trúc không phải một bước tính năng;
   cửa sổ chứa chúng không còn là "2–3 commit tính năng".
4. **Đếm tên cơ học.** Quy tắc cũ dựa vào "số tên trong đề", chỉ biết sau khi soạn đề, và các lần đếm
   trước không cùng một cách. Quy tắc mới đếm tên bằng một thủ tục cố định trên test ẩn, chạy được trên
   mọi ứng viên trước khi soạn đề.
5. Danh sách m01–m05 soạn trước đó được chọn tay theo lớp và khu vực, không theo quy tắc cơ học nào.
   Nó bị thay bằng kết quả áp quy tắc dưới đây, **kể cả ở chỗ khác với danh sách cũ**. Quy tắc không
   được chỉnh để giữ hay bỏ ứng viên nào.

## Quy tắc chọn tầng vừa (thay ràng buộc 3 tầng vừa và ràng buộc 4)

**Tập ứng viên** như ràng buộc 2: mọi đoạn 2–3 commit first-parent liền nhau nằm trong 16 đoạn của
`ranges.json`. `medium_candidates.json` ghi 93 cửa sổ: mọi cửa sổ có thể hợp lệ (đã kiểm tra: không
cửa sổ nào trong 188 cửa sổ của 16 đoạn mà toàn commit `feat`, chỉ đổi `backend/` và có 300–700 dòng bị
thiếu), cộng các cửa sổ đã xét trước đó.

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
9. Tối đa **20** tên bắt buộc (cách đếm ở dưới).

**Cách đo tỉ lệ integration (tiêu chí 8).** Tại `end`, chạy hai lượt pytest với pytest-cov và
`--cov-context=test`: lượt chấm (mặc định của dự án, `-m "not integration"`) và lượt integration
(`-m integration`, có Docker). S là các câu lệnh (theo coverage.py) nằm trên dòng mà diff `base..end` thêm
hoặc sửa trong `backend/src/**.py`, bỏ những dòng chỉ chạy lúc import hay thu thập test ở cả hai lượt
(ngữ cảnh rỗng). G là phần của S chạy trong một test của lượt chấm, I là phần chạy trong một test của
lượt integration. Tỉ lệ bằng |I − G| / |S|. Mã: `tasks/feature-feasibility/medium_coverage.py`.

**Cách đếm tên (tiêu chí 9 và thứ tự chọn).** Trên các file test ẩn và file hỗ trợ được khôi phục từ
`end` (cả test được chấm lẫn test `integration`), một tên được đếm khi test cần nó và nó chưa có ở
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
  được khôi phục đã cài.

Trường, tham số từ khóa, phương thức của chính các lớp mới và chuỗi văn bản tự do không được đếm; đề bài
vẫn phải nêu chúng khi test ghim chúng (kiểm ở bước đối chiếu tên, ràng buộc 6). Mã:
`tasks/feature-feasibility/medium_names.py`.

**Lớp của cửa sổ** là lớp (`domain`, `application`, `infrastructure`, `api` dưới
`backend/src/pharma_agent/`) chứa nhiều dòng `backend/src` của cửa sổ nhất; file ngoài bốn thư mục này
(ví dụ `cli.py`) không tính; hòa thì theo thứ tự domain, application, infrastructure, api.

**Chọn:** tham lam, tối đa 5 nhiệm vụ, không hai cửa sổ được chọn nào chung commit. Thứ tự xếp: số tên
tăng dần, rồi số dòng `backend/src` tăng dần, rồi mã commit `end` tăng dần.

- Lượt 1: lần lượt với domain, application, infrastructure, api, lấy cửa sổ hợp lệ đứng đầu thứ tự xếp
  trong lớp đó mà không chung commit với cửa sổ đã chọn.
- Lượt 2: điền các chỗ còn lại từ mọi cửa sổ hợp lệ theo cùng thứ tự xếp, bỏ cửa sổ chung commit với
  cửa sổ đã chọn.
- Đánh mã m01, m02, … theo thứ tự chọn.

**Không có quyền chọn.** Kết quả áp quy tắc được nhận nguyên. Mọi ứng viên, giá trị từng tiêu chí, lý
do loại, lớp, số tên, tỉ lệ integration và lượt chọn được ghi ở
`tasks/feature-feasibility/medium_candidates.json` (trường `eligible`, `reason`, `selected`,
`selection_pass`, `selected_as`, `required_names`, `integration_coverage`); mã áp quy tắc:
`tasks/feature-feasibility/medium_select.py`. Đề bài của các nhiệm vụ được chọn qua quy trình ở ràng
buộc 6.

## Tầng lớn

Quy tắc tầng lớn giữ nguyên (một đoạn liền nhau, từ 750 dòng `backend/src`, tối đa 35 tên). F07 và F04
đã được xét theo đúng quy tắc này và **bị loại vì vượt 35 tên**: F07 (`adf89a7b62..c36b6e91e9`, 7 commit,
1.364 dòng) cần khoảng 70 tên, F04 (`432d790170..5445f66dbb`, 7 commit, 1.187 dòng) khoảng 60 tên (bản
vá gốc của cả hai chấm sạch; chi tiết ở `tasks/EXTRA_REVIEW.md` và `large_rechecks` trong
`medium_candidates.json`). Tầng lớn giữ **f08, f14, f15**. Số tên của tầng lớn là số đếm tay theo đề đã
soạn như trước; cách đếm cơ học ở trên chỉ dùng cho tầng vừa.

## Kết quả áp quy tắc

Áp quy tắc lên 93 cửa sổ: **21 cửa sổ hợp lệ**, chọn 5 (chi tiết từng cửa sổ trong
`medium_candidates.json`, tóm tắt và đề bài nháp trong `tasks/EXTRA_REVIEW.md`).

| mã | cửa sổ | `base..end` | commit | lớp | dòng `backend/src` | số tên | test ẩn được chấm (trượt ở `base`) | tỉ lệ integration | lượt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| m01 | F05_69-70 | `af9d4173a9f4..507a4ae31ea4` | 2 | domain | 478 | 7 | 23 (23) | 0% | 1 |
| m02 | F03_44-45 | `a133d4cd1cba..68edeac53e8e` | 2 | application | 335 | 5 | 6 (6) | 32% | 1 |
| m03 | F09_107-109 | `a24bd490804c..95d69130cd22` | 3 | infrastructure | 413 | 3 | 17 (14) | 44% | 1 |
| m04 | F03_47-48 | `44466f373da6..4ba674d35988` | 2 | api | 362 | 11 | 9 (7) | 4% | 1 |
| m05 | F06_80-81 | `067e56274091..adf89a7b629a` | 2 | application | 515 | 5 | 13 (13) | 0% | 2 |

Số cửa sổ theo tiêu chí đầu tiên không đạt: ngoài 16 đoạn 1; có commit `test` 5; chung commit với
nhiệm vụ tầng khác 42; đổi file ngoài `backend/` 2; ngoài 300–700 dòng 11; dưới 5 test ẩn được chấm
trượt ở `base` 4; tỉ lệ integration trên 50% 5; trên 20 tên 2. Trong 16 cửa sổ hợp lệ không được chọn,
7 chung commit với một cửa sổ đã chọn, 9 đứng sau trong thứ tự xếp.

So với danh sách m01–m05 soạn tay trước đó: chỉ F03_47-48 còn lại (nay là m04). F03_43-44 (m01 cũ)
chung commit `2541825` với m02 mới (ít tên hơn); F05_71-73 (m03 cũ) và F02_29-30 (m04 cũ) hợp lệ nhưng
13 tên, đứng sau các cửa sổ được chọn; F12_370-371 (m05 cũ) không hợp lệ vì tỉ lệ integration 57%.

Ghi chú về bộ chạy: F03_47-48 (m04) sửa `backend/docs/superpowers/plans/*.md`; bộ chấm bản vá gốc trước
commit `6b5bbf9` của bộ chạy dừng ở `git apply` vì thư mục `superpowers` bị bỏ khỏi cây; cửa sổ được
chấm với diff bỏ các đường dẫn đó. Cần chạy lại `sdlc-harness tasks validate --original-patch` cho m04
sau khi dựng thư mục nhiệm vụ.

## Chồng lấn với tầng khác (ràng buộc 7)

Theo tiêu chí 5, không nhiệm vụ tầng vừa nào chung commit với nhiệm vụ tầng nhỏ, chạy thử hay tầng lớn.
Các file test ẩn trùng **đường dẫn** (khác phiên bản) với nhiệm vụ tầng khác:

| nhiệm vụ | file test ẩn trùng đường dẫn | nhiệm vụ tầng khác |
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
tầng vừa nào thuộc loại đó.

## Nhiệm vụ không qua duyệt đề bài

Nếu một nhiệm vụ đã chọn không viết được đề bài đạt yêu cầu (còn tên test cần mà không nêu được trong
giới hạn 20 tên, hoặc người duyệt độc lập kết luận REJECT), nhiệm vụ đó bị bỏ và thay bằng cửa sổ hợp lệ
kế tiếp theo đúng thứ tự chọn ở trên (vẫn không chung commit với nhiệm vụ đã chọn). Lý do bỏ được ghi
lại. Không sửa quy tắc để giữ một nhiệm vụ.

## Ghi chú vận hành

Từ khoảng 19:16 đến 19:45 ngày 2026-11-15, các lần đo độ phủ để chọn tầng vừa chạy cùng lúc với những
lượt đầu của lượt chạy chính tầng nhỏ, nên chia CPU. Điều này có thể ảnh hưởng `wall_s` của các lượt bắt
đầu trong khoảng đó; báo cáo ghi chú và kiểm tra số lượt hết giờ trong khoảng này.
