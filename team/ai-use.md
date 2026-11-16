# Khai báo sử dụng AI

Học phần: Chuyên đề nghiên cứu 1 (IT5421). Giảng viên: TS. Nguyễn Thanh Hùng.
Nhóm: Doãn Văn An (20252778M), Lê Xuân Lợi (20252781M), Trần Ngọc Bảo (20251227M).

Bản này khai mọi chỗ AI tham gia đề tài. Đề tài có AI ở bốn vai trò khác nhau, và chúng không được lẫn vào
nhau:

1. **Trợ lý nghiên cứu**: AI giúp An tìm tài liệu, soạn đề bài, viết mã bộ chạy, mã phân tích, viết nháp
   văn bản. Đây là phần cần khai báo theo yêu cầu của môn.
2. **Người duyệt độc lập**: một mô hình AI khác (Fable 5.2) đọc lại các văn bản và mã quan trọng trong một
   ngữ cảnh riêng, không thấy lập luận của người soạn.
3. **Đối tượng được đo**: bốn tổ hợp công cụ và mô hình chạy các nhiệm vụ của thí nghiệm.
4. **Công cụ làm ra dự án được nghiên cứu**: ViPharmind được phát triển với trợ lý lập trình AI. Phần hồi
   cứu (RQ1, RQ2) nghiên cứu chính quá trình đó.

Ký hiệu: **[An xác nhận]** là chỗ An phải kiểm lại trước khi nộp. **[An điền: ...]** là chỗ chỉ người
trong nhóm trả lời được. **[chờ Lợi, Bảo chấm tay E2]** là số chưa có. Số liệu khác lấy từ báo cáo
(`docs/report/generated/numbers.json`); "mục 6.1", "Phụ lục G" là mục của báo cáo.

## 1. Công cụ và mô hình

| Vai trò | Công cụ | Mô hình | Ai dùng |
| --- | --- | --- | --- |
| Trợ lý nghiên cứu | Claude Code (CLI), có công cụ tìm kiếm và đọc web, tác tử con | Claude Opus 5.5 (`claude-opus-5-5`) trong các phiên đã ghi nhận [An xác nhận: mô hình của mọi phiên] | An |
| Người duyệt độc lập | Tác tử duyệt chạy riêng | Fable 5.2 [An xác nhận cách gọi và nhà cung cấp] | An giao việc và đọc kết quả |
| Đối tượng được đo | Claude Code 2.1.325 (`claude -p`) | Claude Sonnet 5.5 (`claude-sonnet-5-5`), effort medium | Bộ chạy |
| Đối tượng được đo | Claude Code 2.1.325 (`claude -p`) | Claude Opus 5.5 (`claude-opus-5-5`), effort medium | Bộ chạy |
| Đối tượng được đo | Antigravity CLI 1.5.9 (`agy -p`) | Gemini 3.8 Flash Medium (`gemini-3.8-flash-medium`) | Bộ chạy |
| Đối tượng được đo | Codex CLI 0.162.1 (`codex exec`) | `gpt-6-luna`, suy luận medium | Bộ chạy |
| Đối tượng được đo (E1, E2, thăm dò) | Claude Code 2.1.325 (`claude -p`) | Claude Haiku 5.5 (`claude-haiku-5-5`), effort medium | Bộ chạy |
| Người chấm danh sách hành vi E2; người gán nhãn thứ ba (chỉ đối chiếu) | Tác tử chạy riêng | Fable 5.2, effort high | An giao việc |
| Làm ViPharmind | Trợ lý lập trình AI (chủ yếu Claude Code; nhật ký Codex còn 2 dòng) | [An xác nhận các mô hình đã dùng khi làm ViPharmind] | An |

Phiên bản công cụ thực tế của từng lượt chạy được bộ chạy ghi trong `meta.json`. Mỗi nhóm của thí nghiệm
chính chỉ gặp một phiên bản: Claude Code 2.1.325 và Codex CLI 0.162.1 (báo cáo mục 6.1). E1, E2 cũng chỉ có
hai phiên bản này; mọi lượt `agy-gemini` (đã bỏ) chạy Antigravity 1.5.9. Codex tự cập nhật lên 0.169.0 lúc
18:01 ngày 2026-11-16, sau khi Codex trong E2 đã dừng vì hết hạn mức, nên không lượt nào chạy bằng bản này
(Phụ lục G).

**Lưu ý về xung đột:** trợ lý nghiên cứu (Claude Opus 5.5) cùng mô hình với một nhóm được đo
(`claude-opus`), và cùng hãng với nhóm `claude-sonnet`. Trợ lý đã soạn nháp đề bài và hai lời dặn mà các mô
hình này nhận. Mục 6 nêu rủi ro này và cách đã giảm.

## 2. Nguyên tắc chung

- An quyết định mọi điều về thiết kế, phạm vi, tiêu chí và cách xử lý tình huống. Trợ lý đề xuất; quyết
  định nào do trợ lý đưa ra trong lúc An vắng thì được ghi "(lựa chọn của trợ lý)" hoặc "pending An's
  final approval" trong văn bản, và An duyệt lại sau.
- Mọi con số trong báo cáo và slide được sinh bằng máy từ kết quả thô, không do AI hay người gõ tay.
- Trợ lý không mở kết quả lượt chạy chính trước các thẻ `prereg-v1.1` và `prereg-v1-analysis`, như mọi
  người trong nhóm (`prereg/prereg-v1.1.md`, mục "Lượt chạy chính tầng nhỏ đã bắt đầu trước thẻ này").
- Commit trong repo **không** có dòng ghi công AI. Đây là quy ước của An cho các repo này, không phải để
  che giấu: văn bản này thay cho dòng ghi công. Có thể coi gần như mọi commit của repo nghiên cứu là do trợ
  lý viết theo yêu cầu và dưới sự duyệt của An.

## 3. AI trong từng việc của nghiên cứu

| # | Việc | AI đã làm gì | Người đã làm và quyết gì | Bằng chứng |
| --- | --- | --- | --- | --- |
| 3.1 | Chọn đề tài, câu hỏi nghiên cứu | Trợ lý đề xuất ba hướng tiếp cận và phân tích được mất | An chọn cách 2 (hồi cứu cộng thực nghiệm đối chứng), chọn ba công cụ, hai mô hình Claude, mức effort medium | Bản thiết kế nghiên cứu, mục 6 |
| 3.2 | Tổng quan tài liệu | Trợ lý chạy 10 chuỗi tìm kiếm, mở trang abstract, DOI hoặc trang hội nghị của từng nguồn, chép tên bài, tác giả, năm, nơi đăng, số liệu từ abstract, viết nhật ký tìm kiếm và mục BibTeX | An đọc nhật ký và danh sách 24 nguồn [An xác nhận: đã tự mở và đọc nguồn nào] | `docs/report/literature-log.md`, `docs/report/references.bib` |
| 3.3 | Phân tích hồi cứu ViPharmind | Trợ lý viết mã đọc lịch sử git, phân khâu commit, nối commit với plan, đo mức sửa lại; trợ lý gợi ý nhận định cho từng commit trong mẫu kiểm tra | An kiểm tra tay mẫu ngẫu nhiên 20 commit cho quy tắc nối commit với plan (kết quả 15/20) **có tham khảo gợi ý của AI**, nên đây không phải kiểm tra hoàn toàn độc lập | `retrospective/` (nhánh `retrospective`) |
| 3.4 | Sàng lọc commit | Trợ lý viết lệnh `sdlc-harness screen`, chạy và ghi phễu 110 → 64 → 47 → 47 → 43 | An duyệt tiêu chí sàng lọc (theo bản thiết kế); độ lệch ở tiêu chí 1 (46 thay vì 39) được ghi lại | `tasks/SCREENING.md`, `tasks/screening.json` |
| 3.5 | Tiêu chí 3 và đề bài tầng nhỏ | Trợ lý đề xuất đạt hoặc không đạt tiêu chí 3 và soạn nháp đề bài tiếng Anh cho 32 commit đầu theo thứ tự duyệt ngẫu nhiên | **An duyệt gộp** ngày 2026-11-15: chấp nhận nguyên văn mọi đề xuất và mọi đề bài, không sửa từng mục. Ba mục (#12, #20, #30) bị loại theo khuyến nghị của trợ lý vì test hành vi chỉ thuộc loại `integration`. Một tác tử duyệt đối chiếu mẫu vài đề với commit gốc | `tasks/REVIEW.md` (dòng "Review record") |
| 3.6 | Rà đề bài tầng nhỏ | Trợ lý đối chiếu mọi tên công khai mà test ẩn dùng với đề bài; tìm ra chỗ thiếu chặn ở t05, t07, t13 (và p01) | An duyệt lại ba đề đã bổ sung tên giao diện, cùng ngày duyệt `prereg-v1` | `tasks/PROMPT_AUDIT.md`, commit `e92f346` |
| 3.7 | Tầng lớn (f08, f14, f15) | Trợ lý khảo sát khả thi, cắt 16 đoạn commit, soạn đề bài và bảng đối chiếu tên | Fable 5.2 duyệt độc lập: cả ba APPROVE WITH EDITS, không REJECT; mọi sửa đổi của Fable được áp. An duyệt gộp | `tasks/FEATURE_REVIEW.md`, `tasks/FEATURE_REVIEW_fable.md` |
| 3.8 | Tầng vừa (m01–m05) | Trợ lý soạn quy tắc chọn, mã chọn, đo số tên và độ phủ, soạn đề bài | Fable 5.2 dựng lại việc chọn bằng mã riêng, ra cùng 21 cửa sổ hợp lệ và cùng 5 cửa sổ được chọn; duyệt đề: không REJECT. An duyệt gộp `prereg-v1.1` và năm đề | `prereg/prereg-v1.1.md`, `tasks/EXTRA_REVIEW.md`, `tasks/EXTRA_REVIEW_fable.md` |
| 3.9 | Hai lời dặn (`prompts/spec.md`, `prompts/vibe.md`) | Trợ lý soạn lời dặn theo đặc tả dựa trên quy trình spec, plan trong lịch sử ViPharmind, không chép skill nào [An xác nhận] | An duyệt; nội dung chốt bằng mã băm SHA-256 ở `prereg-v1` | `prereg/prereg-v1.md` mục 2 |
| 3.10 | Bộ chạy và bộ chấm (`harness/`) | Trợ lý viết toàn bộ mã và test theo kế hoạch: xuất cây không lịch sử, lọc file, HOME sạch, danh sách biến môi trường cho phép, xử lý hạn mức, chấm | An duyệt kế hoạch và các quyết định cấu hình. Ruling R11 (không proxy, agent mặc định, mạng mở) là quyết định của An sau khi đọc báo cáo chạy thử | `harness/`, `docs/pilot-report.md` mục 0 |
| 3.11 | Chạy thử và báo cáo chạy thử | Trợ lý chạy 2 nhiệm vụ thử, viết báo cáo; đọc điều khoản dịch vụ của ba nhà cung cấp và tóm tắt (ghi rõ "không phải ý kiến pháp lý"); gán thử nhãn thất bại cho 6 lượt hỏng | An quyết định cách dùng tài khoản và mạng. Nhãn thử do AI gán, một người, không mù, chỉ dùng để thử bảng nhãn, không dùng làm số liệu | `docs/pilot-report.md` mục 3, 7 |
| 3.12 | Đăng ký trước | Trợ lý soạn `prereg-v1`, `prereg-v1.1` và mọi dòng ở mục 11; Fable 5.2 phản biện bản nháp `prereg-v1` (4 Blocking, 12 Important, 8 Minor, kết luận FREEZE AFTER EDITS); trợ lý đề xuất cách xử lý từng điểm | An duyệt văn bản và các quyết định ngày 2026-11-15, xác nhận hạn thu dữ liệu 2026-11-29 và ngưỡng −5 điểm MI | `prereg/prereg-v1-review-fable.md`, `prereg/decisions-for-v1.md` |
| 3.13 | Hướng dẫn gán nhãn | Trợ lý soạn nháp và ví dụ dựng từ đề bài thật | An là người soạn chịu trách nhiệm; bảng nhãn khóa tại thẻ `prereg-v1` | `prereg/labeling-guide.md` |
| 3.14 | Mã phân tích (`analysis/`) | Trợ lý viết toàn bộ mã và test, chạy thử trên dữ liệu chạy thử; Fable 5.2 duyệt độc lập (2 Blocking, 6 Important, 10 Minor, FREEZE AFTER FIXES); trợ lý sửa theo duyệt | An duyệt các thay đổi so với đăng ký trước (đổi `lme4` sang statsmodels, khoảng tin cậy bootstrap cụm, ngưỡng suy biến 0,30), ghi ở mục 11 | `analysis/README.md`, `analysis/REVIEW_fable.md` |
| 3.15 | Gán nhãn chính thức | **Không dùng AI** ở nhãn của người. Ngoài bản đăng ký, Fable 5.2 gán độc lập trên cùng gói che cách làm làm người chấm thứ ba, chỉ để đối chiếu | Lợi và Bảo gán nhãn độc lập, mù một phần (vòng 2; vòng 1 bị loại theo đề nghị của hai người vì điền chưa kỹ); An phân xử 1 lượt lệch. Kappa 0,95 | `results/analysis/main/labeling/final-labels.csv` |
| 3.16 | Kiểm tra "đạt test nhưng sai" | Mẫu 20 lượt và gói che cách làm do mã (trợ lý viết) chọn và dựng theo hạt giống cố định | Lợi và Bảo đọc và đối chiếu từng bản vá, mỗi người 10 lượt, mù cách làm; An soát lại. Kết quả 20/20 đúng thật | `results/analysis/main/labeling/returned/passcheck-*.csv` |
| 3.17 | Báo cáo viết | Trợ lý viết nháp các mục, viết script sinh bảng, hình, macro số liệu từ `summary.json`, viết `check.sh` | An đọc, sửa, quyết định nội dung và kết luận [An điền: An đã sửa bản nháp của trợ lý đến mức nào, ví dụ mục nào tự viết lại, mục nào chỉ sửa câu chữ, kết luận nào do An đổi] | `docs/report/` |
| 3.18 | Slide và speaker notes | Trợ lý dựng slide bằng ppt-master trên template Slidesgo, viết speaker notes, script kiểm số trên slide | An duyệt; Lợi, Bảo góp ý lời nói phần mình [An điền: Lợi, Bảo có góp ý slide hoặc speaker notes không; nếu có, góp ý gì và đã sửa slide nào] | `docs/presentation/` |
| 3.19 | Tài liệu nhóm | Trợ lý soạn nháp bản kê đóng góp, mẫu đánh giá chéo, bản khai này và tài liệu hỏi đáp | Ba thành viên đọc và xác nhận bản kê; **phiếu đánh giá chéo do từng người tự điền, không dùng AI** | `team/` |
| 3.20 | Tập dượt và hỏi đáp | Trợ lý soạn câu hỏi dự kiến và câu trả lời mẫu | Lợi, Bảo học, tự diễn đạt lại, tập trả lời | `team/qa-prep.md` |

## 4. AI là đối tượng được đo

- Bốn nhóm ở bảng mục 1, mỗi nhóm chạy 23 nhiệm vụ × 2 cách làm × 3 lần lặp: tầng nhỏ 360 lượt, tầng vừa
  120, tầng lớn 72, tổng 552 lượt dự kiến. Số lượt hợp lệ thật: thí nghiệm chính 414 (ba nhóm; `agy-gemini` bị bỏ vì hết
  hạn mức); E1 (Haiku, đề chi tiết) 138/138; E2 (đề sơ sài) 492/552 được chấm: ba nhóm Claude đủ 414, Codex
  dừng ở 78/90 lượt tầng nhỏ vì hết hạn mức. Lượt đề chi tiết của Haiku chỉ được Fable chấm danh sách hành vi
  42/138 vì hết hạn mức Fable (chỉ số chính của E1 là test ẩn). Chấm tay mẫu kiểm tra E2 (Lợi, Bảo, 24
  lượt): [chờ Lợi, Bảo chấm tay E2].
- Chạy bằng gói thuê bao của An, không dùng khóa API trả theo lượng. Claude Code dùng 1 tài khoản; agy và
  Codex xoay vòng nhiều tài khoản của An khi hết hạn mức (ruling R11). Chi phí bằng tiền là số **quy đổi**
  từ token theo bảng giá API công khai ngày 2026-11-15, không phải tiền đã trả.
- Mỗi lượt chạy trong HOME sạch: không skill, plugin, MCP, bộ nhớ, file hướng dẫn riêng. Agent mặc định với
  bộ công cụ mặc định, kể cả công cụ web.
- Đầu vào gửi tới các dịch vụ này: mã ViPharmind (repo công khai) tại commit cha, đề bài, lời dặn. Không có
  dữ liệu cá nhân nào khác. Claude Code tự chèn email tài khoản vào system-reminder; không có cờ tắt. Email
  không xuất hiện trong kết quả đã lưu (kiểm bằng `gitleaks` và so khớp chính xác, `docs/pilot-report.md`
  mục 8) . Quét lại ngày 2026-11-17 trên `results/raw` của thí nghiệm chính, E1, E2 (`gitleaks detect --no-git`, 8.24.3): 183 cảnh báo, 58 chuỗi khác nhau, đều là token thử của chính ứng dụng ViPharmind khi agent chạy test (JWT có `aud`, `exp`, `user_id`/`sub`; cookie CSRF của fastapi-users; khóa giả trong test); không chuỗi nào trùng thông tin đăng nhập thật của các tài khoản Claude, Codex. Email tài khoản: 0 lần. Email git của An: 11 lần trong 6 transcript tầng nhỏ t04 (đề sơ sài), do agent đọc một tài liệu của repo ViPharmind có ghi email này; cần lọc trước khi công khai dữ liệu thô..

## 5. AI trong ViPharmind (đối tượng của phần hồi cứu)

ViPharmind được An phát triển với trợ lý lập trình AI ở mọi khâu: nghiên cứu, dữ liệu, mã, kiểm thử, triển
khai. Commit của ViPharmind không mang dấu ghi công AI (0 commit có `Co-Authored-By`), và nhật ký phiên chỉ
còn một phần (13 phiên Claude Code; nhật ký Codex 2 dòng). Vì vậy báo cáo **không** đo được tỉ lệ mã do AI
viết; nhận định "AI tham gia mọi khâu" dựa trên lời khai của tác giả và phần nhật ký còn lại. Báo cáo nêu
điều này ở phần hạn chế.

## 6. Rủi ro do dùng AI và cách đã giảm

| Rủi ro | Cách giảm | Còn lại |
| --- | --- | --- |
| Đề bài do AI soạn, An duyệt gộp không sửa từng mục | Rà tên giao diện so với test ẩn (`PROMPT_AUDIT.md`), sửa t05, t07, t13; Fable duyệt độc lập đề tầng vừa và lớn; hai cách làm nhận **cùng** đề bài, nên chất lượng đề ảnh hưởng hai nhánh như nhau | Báo cáo nêu ở phần hạn chế: đề bài do AI soạn, tác giả không sửa từng đề |
| Trợ lý (Claude Opus 5.5) cùng mô hình với một nhóm được đo, có thể vô tình soạn đề "hợp" với Claude | Đề viết từ thông điệp commit và test ẩn, không nêu cách cài đặt; ba nhóm khác hãng và khác công cụ làm đối chứng (RQ4); phép so luôn là hai cách làm trong cùng nhóm | Không loại hết được; báo cáo nêu |
| Lời dặn theo đặc tả do AI soạn | Dựa trên quy trình spec, plan thật của ViPharmind; chốt bằng mã băm trước khi chạy | Can thiệp là một gói (thiết kế, kế hoạch, test trước, chạy cả bộ test); báo cáo nêu không tách được phần của riêng tài liệu đặc tả |
| Mã bộ chạy, mã phân tích do AI viết có lỗi | Test tự động; chạy thử 2 nhiệm vụ; `regrade` cho ra kết quả không đổi (38 lượt, 0 thay đổi); Fable duyệt mã phân tích, các lỗi chặn đã sửa trước thẻ `prereg-v1-analysis` | Phép thử độ phủ của khoảng bootstrap cho mô hình hỗn hợp đã chạy xong ngay trước thẻ `prereg-v1-analysis` (2026-11-16 08:58): 33/40 (82,5%), thấp hơn danh nghĩa 95%, đạt quy tắc ≥ 32/40 ghi trước. Khoảng của hệ số tương tác vì vậy hẹp hơn thực tế; kết luận H5 chỉ dựa vào dấu (báo cáo mục 7.5) |
| Người duyệt độc lập cũng là AI | Fable chạy trong ngữ cảnh riêng, đọc trực tiếp mã và test, tự dựng lại tính toán; An đọc và quyết từng điểm | Độc lập với người soạn, không độc lập với AI nói chung |
| Trích dẫn sai do AI | Mọi nguồn được mở trực tiếp, số liệu chỉ lấy từ abstract hoặc trang đã mở; không trích theo trí nhớ | [An xác nhận việc tự kiểm tra] |
| Báo cáo thổi phồng kết luận | Số liệu sinh bằng máy; quy tắc đọc ba kết cục chốt trước; mọi phép thử phụ được báo cáo dù kết quả thế nào | |

## 7. Những việc không giao cho AI

- Quyết định đề tài, câu hỏi nghiên cứu, cách làm, công cụ, mô hình, tài khoản và cách dùng mạng.
- Duyệt đề bài, duyệt đăng ký trước, quyết định thay đổi sau thẻ.
- Gán nhãn nguyên nhân thất bại chính thức (Lợi, Bảo) và phân xử (An).
- Điền phiếu đánh giá chéo.
- Thuyết trình và trả lời câu hỏi trên lớp.

## 8. Xác nhận

Nhóm xác nhận bản khai này đầy đủ và đúng sự thật tại ngày ký.

| Thành viên | Ngày | Ký |
| --- | --- | --- |
| Doãn Văn An | | |
| Lê Xuân Lợi | | |
| Trần Ngọc Bảo | | |
