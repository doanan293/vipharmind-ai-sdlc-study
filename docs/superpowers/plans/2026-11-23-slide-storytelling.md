# Slide storytelling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dựng lại bộ slide bảo vệ thành mạch kể 18 slide chính (hook f15 → cách kiểm → phát hiện → thông điệp "spec của người vs spec của agent"), ≤ 14:15 phút nói.

**Architecture:** Giữ pipeline hiện có: `docs/presentation/build_deck.py` sửa các slide SVG lấy từ `template-vi.pptx` (ppt-master, route Edit Native PPTX) và `build.sh` xuất PPTX/PDF. Thêm một danh sách `ORDER` quyết định slide nào lên deck và theo thứ tự nào; các trang mới/gộp viết như các `@page` hiện có.

**Tech Stack:** Python 3 + lxml (build_deck.py), ppt-master scripts, LibreOffice (PDF), pdftoppm (xem ảnh).

**Spec:** `docs/superpowers/specs/2026-11-23-slide-storytelling-design.md`

## Global Constraints

- Chỉ sửa `docs/presentation/` (và `check_numbers.py` `ALLOW` nếu thật cần, kèm lý do). Không đụng `docs/report/` (đang được sửa song song).
- Mọi số trên slide lấy từ `N[...]` (numbers.json); `check_numbers.py` phải in `OK`.
- Quality checker: `[ERROR] With errors: 0`.
- Tổng thời gian nói ≤ 855 giây (14:15); thân chữ ≥ 15pt.
- Slide dùng thuật ngữ tiếng Anh (spec, plan, TDD, prompt, hidden test, agent, cohort, preregistration, checklist, pp); lời thoại tiếng Việt, trung tính.
- Không được viết/ngụ ý "spec-driven hiệu quả hơn" hay "spec giúp task lớn khi đề sơ sài"; kết quả thăm dò (E1, E2) luôn gắn nhãn "thăm dò"; tầng vừa/lớn của E2 gắn "chỉ tham khảo".
- Slide 2 không so với vibe; slide 13 nói vibe đạt `ResCaseVibePassed`/`ResCaseReps`.
- Slide 15 chỉ so điểm checklist (−`ETwoXScoreShiftSpec`/−`ETwoXScoreShiftVibe` vs +`ETwoPooledSmallPp`), chú thích hidden test giảm ~80 pp vì tên.

## Review Focus

- Chữ tràn khung khi số dài hơn (ví dụ KTC có dấu âm): quality checker phải 0 lỗi sau mỗi task.
- Slide gộp chật: mỗi slide xem ảnh 72 dpi, không chồng chữ lên hình trang trí.
- Lời thoại nhắc số khác số trên slide: lời thoại dùng cùng khóa `N[...]`/`say(...)`.
- Dự phòng vô tình bị tính giờ: trang dự phòng `secs=0`.
- Trang cũ không còn trong `ORDER` vẫn được build: `ORDER` là nguồn duy nhất của deck.

---

### Task 1: ORDER, phần mới, giới hạn giờ

**Files:** Modify `docs/presentation/build_deck.py` (khối `PAGES`/`PARTS` ~dòng 225; `main()` ~dòng 840).

- [ ] Thêm `ORDER: list[str]` (stem theo thứ tự deck, chính rồi dự phòng) và trong `main()` dựng deck từ `ORDER`: stem không tồn tại → `sys.exit("unknown page <stem>")`; trang không có trong `ORDER` không được build.
- [ ] Đổi nhãn phần: `OPEN="Mở đầu"`, `METHOD="Cách kiểm"`, `RESULTS="Phát hiện"`, `CLOSE="Kết luận"`; sau khi tính tổng, `sys.exit` nếu tổng > 855.
- [ ] Đặt `ORDER` tạm bằng các trang hiện có theo mạch spec (bỏ `p02_part1`, `p14_results`; `p05_hypotheses`, `p18_h4`, `p19_h5`, `p20_cost` sang dự phòng `secs=0`).
- [ ] Chạy `SKILL_DIR=/home/andv/personal/HUST/research-topic-1/.claude/skills/ppt-master bash build.sh`. Kỳ vọng: in `pages=`, `[ERROR] With errors: 0`, `OK: every number…`, tổng ≤ 14:15.
- [ ] Commit `slides: page order list, part names, 14:15 guard`.

### Task 2: Mở đầu (slide 1–4)

**Files:** Modify `build_deck.py` (trang mới `p02_hook`; sửa `p03_motivation`, `p04_rq`).

- [ ] `p02_hook` (template của `p21_case`, 0:45): tiêu đề "Làm đủ quy trình, vẫn trượt"; chuỗi 4 bước spec `ResCaseDesignLines` dòng → plan `ResCasePlanTasks` task → test tự viết đạt → hidden test trượt (`ResCaseSpecPassed`/`ResCaseReps` lượt đạt); không giải thích nguyên nhân, không nhắc vibe. Lời thoại kết bằng câu hỏi.
- [ ] `p03_motivation` (0:40): giữ Superpowers + vibe/spec-driven; lời thoại nối từ hook.
- [ ] `p04_rq` (0:40): 6 RQ một dòng + một dòng khoảng trống (lấy từ khối "gap" cũ).
- [ ] Build như Task 1; xem ảnh slide 1–4 (`pdftoppm -r 72 -f 1 -l 4`). Kỳ vọng: không lỗi, không chữ chồng.
- [ ] Commit `slides: f15 hook and opening`.

### Task 3: Cách kiểm (slide 5–9)

**Files:** Modify `build_deck.py` (`p04b_related` giữ; gộp `p06+p07` → `p06_project`; `p08_arms` giữ; gộp `p09+p10+p11` → `p08_scale`; gộp `p12+p13` → `p09_rigor`).

- [ ] `p06_project` (0:40): `Commits` commit, `FeatWithPlanPct`% feat có plan (cận trên), rework `ReworkWithPlanMean` ≈ `ReworkWithoutPlanMean`.
- [ ] `p08_scale` (0:50): `TasksMain` task × 3 tầng, 3 cohort, 3 lần = `ResRuns` lượt; chấm bằng hidden test, test cũ đưa về bản gốc; agy bị loại (một dòng).
- [ ] `p09_rigor` (0:35): timeline preregistration (5 mốc + "Mỗi thẻ: Fable 5.2") + một dòng chống rò rỉ.
- [ ] Build; xem ảnh slide 5–9; tổng Mở đầu + Cách kiểm ≤ 5:30.
- [ ] Commit `slides: method compressed to five slides`.

### Task 4: Phát hiện (slide 10–15)

**Files:** Modify `build_deck.py` (`p15_h1`; `p16_rq4` thêm một dòng H4 `ResHFourDiffOfDiffsPp` và H5 `ResHFiveEstPp`; gộp `p17+p20` → `p12_cost_tests`; `p21_case` → giải mã; `p22_labels`; trang mới `p15_human_spec` từ template `p23_explore`).

- [ ] `p12_cost_tests` (0:45): ×`ResTokenRatioMin`–`ResTokenRatioMax` token; test ở `ResSonnetSpecTestsAnyPct`–`ResCodexSpecTestsAnyPct`% lượt spec; "hidden test không thưởng phần này".
- [ ] `p21_case` (0:45) đổi tiêu đề "Giải mã f15": spec chốt kiểu trả về đối tượng, bản gốc trả mã; test của agent theo cùng giả định; vibe cũng đoán, đạt `ResCaseVibePassed`/`ResCaseReps`.
- [ ] `p15_human_spec` (0:55): hai cột "Bỏ spec người viết: −X / −Y pp điểm checklist" và "Spec agent tự viết, đề sơ sài: +`ETwoPooledSmallPp` pp task nhỏ [CI]; vừa/lớn ≈ 0 (chỉ tham khảo)"; nhãn "thăm dò (thêm sau kết quả chính)"; chú thích hidden test giảm ~80 pp vì tên.
- [ ] Build; xem ảnh slide 10–15.
- [ ] Commit `slides: findings arc ending in human spec vs agent spec`.

### Task 5: Kết, dự phòng, kiểm cuối

**Files:** Modify `build_deck.py` (`p24_limits`, `p25_conclusion`, `p26_thanks`; dự phòng mới `p31_bk_judge`).

- [ ] `p24_limits` (0:30): thêm "không bước hỏi lại/duyệt spec"; "E2 thêm sau".
- [ ] `p25_conclusion` (0:50): tiêu đề "Spec quan trọng — giá trị ở thông tin người đưa vào"; hai vế có nhãn (đề chi tiết: phép thử chính; đề sơ sài: thăm dò); một dòng vòng sau.
- [ ] `p31_bk_judge` (dự phòng): kappa LLM judge với hidden test `ETwoJudgeKappa`, với người `ETwoHumanLoiJudgeKappa`/`ETwoHumanBaoJudgeKappa`, người–người `ETwoHumanLoiBaoKappa`.
- [ ] Lời thoại đầu slide 1, 10, 16 có "(Chuyển người nếu chia ba phần.)".
- [ ] Build; xem ảnh toàn deck (lưới 2×3); kiểm `rehearsal.md` tổng ≤ 14:15.
- [ ] Commit `slides: closing message, judge backup, presenter split marks`; push.
