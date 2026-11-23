# Slide bảo vệ: dựng lại theo mạch kể chuyện

Ngày: 2026-11-23. Đi kèm: chỉnh ba chỗ của báo cáo cho cùng thông điệp.

## Ý định

Bộ slide hiện tại (`docs/presentation/`, 26 slide chính + 5 dự phòng, 14:10 phút nói) đúng số liệu nhưng kể theo
thứ tự IMRaD: 13 slide phương pháp (~7 phút) trước khi có kết quả đầu tiên, phát hiện đáng nhớ nhất nằm cuối,
nhiều slide là bảng số khó nghe. Mục tiêu: dựng lại thành một câu chuyện 15 phút, hấp dẫn, để thầy (TS. Nguyễn
Thanh Hùng) nhớ một thông điệp và tin rằng phương pháp chặt chẽ.

**Thông điệp (đã chốt với nhóm):** spec quan trọng, nhưng giá trị nằm ở thông tin người đưa vào, không ở việc
agent tự viết spec. Đề bài chi tiết của thí nghiệm chính là một bản spec do người viết; bỏ nó đi điểm checklist
giảm khoảng 36–39 pp ở cả hai cách làm (`ETwoXScoreShiftSpec`, `ETwoXScoreShiftVibe`), còn spec do agent tự viết
chỉ bù +4,2 pp ở task nhỏ (`ETwoPooledSmallPp`) và không thấy lợi ích khi đề đã chi tiết (H1). Điều này cũng
giải thích vì sao Superpowers có thể vẫn đúng: hai bước nhóm phải bỏ (hỏi lại người dùng, người duyệt spec) là
hai bước đưa ý người vào spec.

## Mục tiêu, không làm, không được làm

- Mục tiêu: 15 phút nói (tổng ≤ 14:15, phần dư cho chuyển slide); mở bằng một ca cụ thể; phương pháp ≤ ~3:30;
  mọi con số trên slide đến từ `docs/report/generated/numbers.json` (qua `check_numbers.py`); ba thành viên có
  thể chia ba phần.
- Không làm: thí nghiệm mới; template mới; đổi số liệu hay phân tích.
- Không được làm (anti-goal): nói hay ngụ ý "spec-driven hiệu quả hơn" hoặc "spec giúp task lớn khi đề sơ sài"
  (dữ liệu: tầng vừa −0,6 [−4,6; 3,0], tầng lớn −1,1 [−3,7; 0,4], Haiku lớn −4,7); giấu kết quả "chưa kết luận
  được"; dùng thuật ngữ thăm dò như kết quả xác nhận.

## Ràng buộc

- Dựng bằng pipeline hiện có: `docs/presentation/build_deck.py` trên `template-vi.pptx` qua ppt-master (route
  Edit Native PPTX), `build.sh` ra `vipharmind-slides.pptx/.pdf`; quality checker 0 lỗi; `check_numbers.py`
  qua (thêm vào `ALLOW` chỉ hằng thiết kế, kèm lý do).
- Thuật ngữ trên slide dùng tiếng Anh cho từ chuyên ngành (spec, plan, TDD, prompt, hidden test, agent, cohort,
  preregistration, checklist, pp); lời thoại tiếng Việt, trung tính ("nhóm em"), nhắc giờ ở đầu mỗi ghi chú.
- Mỗi slide một ý, chữ to đủ đọc khi chiếu (thân ≥ 15pt); không slide nào chỉ là bảng số khi nói được bằng một
  con số chính.

## Các cách đã cân nhắc

1. **Mở bằng ca f15, vòng tròn (chọn).** Hook bằng ca thật, giải mã lại ở giữa, cú lật E2, kết bằng thông điệp.
   Hấp dẫn nhất; phương pháp chỉ xuất hiện khi cần để tin kết quả.
2. Lời hứa và thực tế: liệt kê lời hứa Superpowers rồi kiểm từng cái. Rõ nhưng ít bất ngờ.
3. Giữ IMRaD, rút phương pháp. An toàn, ít hấp dẫn.

Nhóm giao cách làm cho trợ lý; trợ lý chọn cách 1.

## Mạch slide (Reference: builder chỉnh layout, giữ thứ tự và ý)

Thời lượng là gợi ý; tổng phải ≤ 14:15. Cột "Từ slide cũ" chỉ slide hiện có để tái dùng nội dung.

| # | Phần | Ý của slide (page job) | Nội dung chính | Từ slide cũ | Giờ |
|---|---|---|---|---|---|
| 1 | Mở | Tiêu đề | Như hiện tại | p01 | 0:15 |
| 2 | Mở | **Hook f15**: làm đủ quy trình mà vẫn trượt | Chuỗi: spec (`ResCaseDesignLines` dòng) → plan (`ResCasePlanTasks` task) → test tự viết đạt ✓ → hidden test trượt ✗ (`ResCaseSpecPassed`/`ResCaseReps` đạt). Không giải thích vì sao (để slide 13) | p21 | 0:45 |
| 3 | Mở | Câu hỏi | Superpowers (obra/superpowers, 324,5k sao, mô tả nguyên văn) hứa spec-driven bù cho đề ngắn. Thật không? Vibe vs spec-driven một dòng mỗi bên | p03 | 0:40 |
| 4 | Cách kiểm | Sáu RQ gọn + khoảng trống | 6 RQ một dòng; một dòng "chưa có thí nghiệm chỉ đổi prompt, chấm bằng hidden test" | p04, p04b | 0:40 |
| 5 | Cách kiểm | Nghiên cứu liên quan | Như p04b (Hill, Chen, Mock, Agarwal) | p04b | 0:30 |
| 6 | Cách kiểm | ViPharmind và lịch sử git (RQ1–2) | 505 commit; `FeatWithPlanPct`% feat có plan (cận trên); rework ngang nhau | p06+p07 gộp | 0:40 |
| 7 | Cách kiểm | Cùng task, hai prompt | Sơ đồ: cùng đề, mô hình, công cụ, thời gian; chỉ khác prompt quy trình | p08 | 0:35 |
| 8 | Cách kiểm | Quy mô và cách chấm | 23 task × 3 tầng, 3 cohort, 3 lần = `ResRuns` lượt; hidden test, test cũ đưa về bản gốc | p09+p10+p11 gộp | 0:50 |
| 9 | Cách kiểm | Không tự lừa mình | Timeline preregistration (5 mốc + Fable mỗi thẻ) + chống rò rỉ, một dòng | p12+p13 gộp | 0:35 |
| 10 | Phát hiện | Đề chi tiết: spec không đạt hơn (H1) | −2,2 pp, KTC [−6,7; 0,0], "chưa kết luận được"; 88,9% vs 91,1% | p15 | 0:45 |
| 11 | Phát hiện | Đổi công cụ, mô hình, cỡ task: vẫn vậy (RQ4–6) | Biểu đồ forest; một dòng H4, một dòng H5; Codex lớn 44% vs 11% (3 task) | p16 (+ ý p18, p19) | 0:50 |
| 12 | Phát hiện | Cái giá và cái để lại | ×1,3–2,2 token; test ở ~3/4 lượt spec (hidden test không thưởng) | p17, p20 | 0:45 |
| 13 | Phát hiện | **Giải mã f15** | Spec chốt "trả về đối tượng", bản gốc trả mã; test của agent theo cùng giả định nên đạt | p21 | 0:45 |
| 14 | Phát hiện | Không phải chuyện xui | `LabOutside`/`LabRuns` lượt hỏng do đề thiếu hoặc sai mã có sẵn; như nhau 76% / 77%; kappa | p22 | 0:35 |
| 15 | Phát hiện | **Cú lật: spec của người vs spec của agent** | Hai cột: bỏ spec người viết → −36 / −39 pp; spec agent tự viết với đề sơ sài → +4,2 pp (task nhỏ), ~0 ở vừa/lớn. Nhãn "thăm dò" rõ | p23 | 0:55 |
| 16 | Kết | Hạn chế | Một dự án; spec-driven tự động không người duyệt/hỏi lại; tầng vừa 5, lớn 3 task; E2 thêm sau | p24 | 0:30 |
| 17 | Kết | Thông điệp | "Spec quan trọng — giá trị ở thông tin người đưa vào." Ba ý: viết spec rõ hoặc để agent hỏi lại bạn; spec agent tự viết tốn thêm mà ít thêm; vòng sau: thêm bước hỏi lại/duyệt, nhiều task lớn hơn | p25 | 0:50 |
| 18 | Kết | Cảm ơn, hỏi đáp | | p26 | 0:10 |

Tổng gợi ý ≈ 11:55 nói + dư; builder có thể nới các slide 2, 13, 15 nếu cần, giữ ≤ 14:15.

Dự phòng (không tính giờ): H4 lưới Sonnet/Opus (p18); H5 scatter (p19); chi phí mỗi lượt đạt (p20); phễu chọn
task (p27); cách đọc CI (p28); nhãn chi tiết (p29); độ tin LLM judge (kappa người–máy, mới, từ số trong mục 4.3
của báo cáo); ghi nguồn template (p30).

Chia người (gợi ý, đánh dấu trong ghi chú): Phần 1 slide 1–9, Phần 2 slide 10–15, Phần 3 slide 16–18.

## Quyết định sau builder check (trợ lý chốt, nhóm duyệt 2026-11-23)

- Slide 15 so cùng một thước đo (điểm checklist): −36/−39 pp vs +4,2 pp; chú thích nhỏ: tỉ lệ đạt hidden test
  giảm ~80 pp chủ yếu vì hidden test gọi tên đề sơ sài không nêu.
- Slide 17 tách hai vế có nhãn: đề chi tiết (phép thử chính) / đề sơ sài (thăm dò); vế "spec của người" cũng
  gắn nhãn thăm dò.
- Slide 2 chỉ nói "đủ quy trình mà trượt 3/3 lượt", không so với vibe; slide 13 nói đủ (vibe cũng đoán, đạt 1/3).
- Tầng vừa, lớn của E2 ghi "chỉ tham khảo".
- Phạm vi: chỉ slide. Phần báo cáo bên dưới để nhóm làm trên bản báo cáo đang được sửa song song (chưa commit),
  không nằm trong kế hoạch này.

## Chỉnh báo cáo cho cùng thông điệp (ngoài phạm vi kế hoạch này)

Chỉ đổi cách diễn giải, không đổi số: Tóm tắt (câu cuối), mục 4.4 Thảo luận (đoạn "Khi đề sơ sài…" và một câu
"đề chi tiết chính là spec do người viết"), mục 5 Kết luận (câu chốt). Giữ `check.sh` qua, 15–20 trang.

## Để lại cho builder

Layout từng slide, slide template nào dùng cho trang gộp, hình vẽ cho hook và cú lật, câu chữ lời thoại, phân
bổ giây cụ thể trong giới hạn trên.
