# Tầng tính năng (F08, F14, F15) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bộ chạy hỗ trợ nhiệm vụ là một đoạn commit `base..end`; có 3 nhiệm vụ tính năng F08, F14, F15 với đề bài đã duyệt; chạy thử 1 nhiệm vụ trước thẻ `prereg-v1`.

**Architecture:** Mở rộng `Task` bằng trường tùy chọn `base` (mặc định là `parent`) và `kind = "commit" | "range"`. Với `range`: mã nền là `base`, test ẩn là mọi `backend/tests/**/test_*.py` thêm hoặc sửa trong `base..end`, file hỗ trợ là các file khác dưới `backend/tests/` đổi trong đoạn; khi chấm khôi phục test ẩn, file hỗ trợ và `pyproject.toml`/`uv.lock` (gốc và `backend/`) từ `end`. Đề bài có thêm mục "Required interfaces" sinh từ `tasks/feature-feasibility/coupling.json` và `fakes_contract.json`.

**Tech Stack:** như kế hoạch `2026-11-15-harness-and-pilot.md`.

**Spec:** `docs/superpowers/specs/2026-11-15-spec-vs-vibe-study-design.md` mục 7.2b.

## Global Constraints

- Ba đoạn cố định: F08 `45271fddc0236bc3f3336b30d99771abf626f14c..cc0f06a67bfa888ef5d7e1ebd1715a517079bbc9`, F14 `c2935909a101b7274c58ec0e678371c0a13b3d07..11079ab21c7fa8299bd59f73b7e6a901ba98ffc4`, F15 `11079ab21c7fa8299bd59f73b7e6a901ba98ffc4..ef23fe8cb40354573c362e570f8a399ad4328c42`.
- Id nhiệm vụ: `f08`, `f14`, `f15`; `kind = "range"`; không đổi hành vi của nhiệm vụ `commit` hiện có (153+ test hiện có vẫn đạt).
- Mọi biện pháp chống rò rỉ của tầng nhỏ áp dụng nguyên (R10: bỏ `superpowers/`, `skills-lock.json`, file hướng dẫn cho AI khỏi cây mã).
- Đề bài tiếng Anh; phần mô tả 5–12 câu cộng mục "Required interfaces" liệt kê tên, không nêu cách cài đặt, không nhắc test.
- Chạy cả 4 nhóm (`claude-sonnet`, `claude-opus`, `agy-gemini`, `codex-luna`); 5 lần lặp; giới hạn thời gian là 3 lần `timeout_s` của tầng nhỏ (spec mục 7.2b, H5).
- Commit không có dòng ghi công AI.

## Review Focus

- Bản vá gốc của cả đoạn (`git diff base end`) phải được chấm `task_pass=True`, không hồi quy, cho cả 3 nhiệm vụ.
- File hỗ trợ khôi phục từ `end` không được làm hỏng test cũ của mã nền khi bản vá đúng.
- Mục "Required interfaces" không được chứa tên test hay tên file test.

---

### Task 1: Nhiệm vụ dạng đoạn commit trong bộ chạy

**Files:** Modify `harness/src/sdlc_harness/{tasks.py,workspace.py,grade.py}`; Test `harness/tests/test_range_tasks.py`.

- [ ] Test trước trên toy repo (đoạn 3 commit, có file hỗ trợ đổi và dependency mới): `test_range_workspace_starts_at_base`, `test_range_hidden_and_support_files_restored_from_end`, `test_range_manifests_restored_from_end`, `test_original_range_patch_passes`, `test_commit_tasks_unchanged`.
- [ ] Cài đặt; chạy toàn bộ test và ruff; commit `feat(harness): support multi-commit range tasks`.

### Task 2: Ba nhiệm vụ tính năng và đề bài

**Files:** Create `tasks/f08`, `tasks/f14`, `tasks/f15` (`task.toml`, `prompt.md`), `tasks/FEATURE_REVIEW.md`.

- [ ] AI soạn đề bài cho từng đoạn từ thông điệp các commit, diff `backend/src` và danh sách tên trong `coupling.json`/`fakes_contract.json`; ghi vào `tasks/FEATURE_REVIEW.md` như `REVIEW.md`.
- [ ] Dừng, giao An duyệt (được duyệt gộp như tầng nhỏ; ghi lại cách duyệt).
- [ ] Sinh 3 thư mục nhiệm vụ, `tasks validate` exit 0; chấm bản vá gốc của cả 3 → `task_pass=True`, không hồi quy.
- [ ] Commit `feat(tasks): add three feature-level range tasks`.

### Task 3: Chạy thử một nhiệm vụ tính năng

- [ ] Chạy `f08` × 2 cách làm × 1 lần × 4 nhóm; ghi thời gian, token, kết quả vào `docs/pilot-report.md` mục tầng tính năng; chốt `timeout_s` của tầng này.
- [ ] Commit kết quả chạy thử sau khi quét bí mật.
