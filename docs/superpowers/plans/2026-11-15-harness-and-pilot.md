# Bộ nhiệm vụ, bộ chạy và chạy thử Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Có 15 nhiệm vụ và 2 nhiệm vụ thử đã duyệt, hai lời dặn, một bộ chạy gọi được Claude Code, Antigravity và Codex rồi chấm bằng test ẩn; chạy thử xong và gắn thẻ `prereg-v1`.

**Architecture:** Một gói Python `sdlc_harness` trong `harness/`, chỉ đọc repo ViPharmind qua `git -C` tại commit cố định. Sàng lọc commit chạy tự động (tiêu chí 1, 2, 4, 5), tiêu chí 3 và đề bài do An duyệt. Mỗi lượt chạy: xuất mã commit cha ra thư mục mới không có `.git`, gọi trợ lý ở chế độ không tương tác trong thư mục cấu hình riêng, chép test ẩn vào rồi chấm. Các lượt chạy song song, thứ tự xáo theo hạt giống.

**Tech Stack:** Python 3.12, `uv`, pytest, `tomllib`; công cụ chấm: pytest (junit XML), `ruff`, `pyrefly`, `radon`, `coverage`; trợ lý: `claude` 2.1.325, `agy` 1.5.8, `codex` 0.162.1.

**Spec:** `docs/superpowers/specs/2026-11-15-spec-vs-vibe-study-design.md` (mục 7.2 đến 7.5 và 9).

## Global Constraints

- Repo ViPharmind `/home/andv/personal/vipharmind-camera-ready` chỉ đọc: chỉ dùng `git -C <repo> log|show|ls-tree|archive|diff` với mã commit; không checkout, không sửa, không tạo nhánh ở đó.
- Mốc nguồn nhiệm vụ: `main` tại `3baae61d764f6d83f7205d0d4d97ee52dd8e0dbe`.
- Ứng viên: commit `feat` trên mốc đó chạm cả `backend/src` và `backend/tests` (110 commit lúc thiết kế).
- Tiêu chí sàng lọc đúng thứ tự mục 7.2; ghi số commit bị loại ở mỗi bước.
- Kích thước: phần thay đổi ở `backend/src` từ 30 đến 400 dòng (thêm cộng bớt).
- 15 nhiệm vụ phân tầng theo lớp `api`, `application`, `domain`, `infrastructure`, cộng 2 nhiệm vụ thử; hạt giống cố định `20261115`.
- Test `integration` không dùng ở bất kỳ bước nào (pytest của backend đã có `-m "not integration"` trong `addopts`).
- Đề bài tiếng Anh, 5–10 câu, hai cách làm nhận cùng đề bài; khác biệt duy nhất là lời dặn trong `prompts/spec.md` và `prompts/vibe.md`.
- Nhánh theo đặc tả tái hiện quy trình An dùng (spec, plan chia việc theo kích thước tự nhiên, làm theo plan, tự viết test); không đặt số bước.
- Mỗi lượt là một phiên duy nhất, không người can thiệp, tắt công cụ truy cập web, thư mục cấu hình sạch (không plugin, skill, bộ nhớ, MCP, file hướng dẫn riêng) nhưng giữ thông tin đăng nhập.
- Bốn nhóm chạy: `claude-sonnet` (`claude-sonnet-5-5`), `claude-opus` (`claude-opus-5-5`), `agy-gemini` (`gemini-3.8-flash-medium`), `codex-luna` (`gpt-6-luna`); mọi nhóm effort hoặc mức suy luận `medium`.
- Lượt bị ngắt vì hạn mức không tính là thất bại, không tính vào 3 lần lặp, được chạy lại.
- Không chép khóa, token, file cấu hình của proxy vào repo; ghi tài khoản bằng số thứ tự, không ghi email.
- Commit không có dòng ghi công Claude hay AI.

## Review Focus

- Đề bài để lộ lời giải hoặc tên file test ẩn: `validate_task` từ chối đề bài nhắc tới đường dẫn test ẩn (Task 4).
- AI đọc được lịch sử hay test ẩn: thư mục làm việc không có `.git`, không có file test ẩn mới; test ở Task 6 khẳng định cả hai.
- Lượt chạy treo hoặc trợ lý không bao giờ dừng: bộ chạy giết tiến trình khi quá giới hạn thời gian và vẫn chấm phần đã làm (Task 8).
- Lỗi hạn mức bị tính nhầm là thất bại: lượt đó được đánh dấu `quota` và đưa lại vào hàng đợi (Task 8).
- Nhật ký lượt chạy chứa khóa hay token trước khi repo công khai: `results/raw/` qua `gitleaks` trước mỗi commit kết quả (Task 9).

---

### Task 1: Gói `sdlc_harness`, đọc repo ViPharmind và tìm ứng viên

**Files:**
- Create: `harness/pyproject.toml`, `harness/src/sdlc_harness/__init__.py`, `harness/src/sdlc_harness/vcs.py`
- Test: `harness/tests/conftest.py`, `harness/tests/test_vcs.py`

**Interfaces:**
- Produces:
  - `harness/tests/conftest.py::toy_repo(tmp_path) -> ToyRepo` — repo git nhỏ có `backend/src/pkg/{api,domain}/…`, `backend/tests/…`, `backend/pyproject.toml` với marker `integration`; `ToyRepo.commit(message, files: dict[str, str | None]) -> str` (None là xóa file). Dùng lại ở mọi task sau.
  - `@dataclass(frozen=True) class FileChange: path: str; status: Literal["A","M","D","R"]; added: int; deleted: int`
  - `@dataclass(frozen=True) class Candidate: sha: str; parent: str; subject: str; changes: tuple[FileChange, ...]`
  - `list_candidates(repo: Path, ref: str) -> list[Candidate]` — commit trên first-parent của `ref`, subject khớp `^feat(\(.+\))?!?:`, chạm cả `backend/src/` và `backend/tests/`; bỏ merge commit.
  - `export_tree(repo: Path, sha: str, dest: Path) -> None` — `git archive <sha> | tar -x -C dest`; `dest` không có `.git`.
  - `read_file(repo: Path, sha: str, path: str) -> str`

- [ ] **Step 1: Viết test** `test_list_candidates_filters_feat_touching_src_and_tests` (toy repo có 4 commit: `feat` chạm cả hai → nhận; `feat` chỉ chạm src → loại; `fix` chạm cả hai → loại; `feat(api)!:` chạm cả hai → nhận), `test_candidate_records_numstat` (added/deleted khớp), `test_export_tree_has_no_git_dir` (cây xuất ra có file nguồn, không có `.git`).
- [ ] **Step 2: Chạy** `cd harness && uv run pytest tests/test_vcs.py -v` → FAIL (module chưa có).
- [ ] **Step 3: Viết `harness/pyproject.toml`** (`requires-python = ">=3.12"`, dev deps `pytest`, `radon`, `coverage`, `ruff`; entry point `sdlc-harness = "sdlc_harness.cli:main"`) **và `vcs.py`** dùng `subprocess.run(["git","-C",…], check=True, text=True)`; numstat lấy từ `git show --numstat --format= -M <sha>`.
- [ ] **Step 4: Chạy lại** → PASS. Chạy thử trên repo thật: `uv run python -c "from sdlc_harness.vcs import list_candidates; print(len(list_candidates(Path('/home/andv/personal/vipharmind-camera-ready'), '3baae61d764f6d83f7205d0d4d97ee52dd8e0dbe')))"` → in ra `110`. Nếu khác 110, ghi số thật và lý do vào `tasks/SCREENING.md` (tạo ở Task 3), không chỉnh bộ lọc cho khớp.
- [ ] **Step 5: Commit** `git add harness && git commit -m "feat(harness): list candidate commits from ViPharmind"`

### Task 2: Sàng lọc tĩnh (tiêu chí 1, 4, 5) và lớp mã

**Files:**
- Create: `harness/src/sdlc_harness/screen.py`
- Test: `harness/tests/test_screen.py`

**Interfaces:**
- Consumes: `Candidate`, `FileChange` (Task 1).
- Produces:
  - `SHARED_TEST_FILE(path: str) -> bool` — đúng với file dưới `backend/tests/` mà tên không khớp `test_*.py` (gồm `conftest.py`, `fakes.py`, `harness.py`, `memory_repository.py`, fixtures).
  - `src_lines(c: Candidate) -> int` — tổng added+deleted của file dưới `backend/src/`.
  - `is_rename_only(c: Candidate) -> bool` — mọi thay đổi ở `backend/src/` là `R` với added+deleted ≤ 2 mỗi file.
  - `layer_of(c: Candidate) -> Literal["api","application","domain","infrastructure"]` — lớp có nhiều dòng thay đổi nhất dưới `backend/src/pharma_agent/<layer>/`; hòa thì theo thứ tự `domain > application > infrastructure > api`.
  - `@dataclass class Verdict: sha: str; passed: bool; failed_criterion: int | None; reason: str`
  - `screen_static(c: Candidate) -> Verdict` — áp tiêu chí 1, rồi 4 (30 ≤ `src_lines` ≤ 400), rồi 5; dừng ở tiêu chí đầu tiên bị trượt.
  - `hidden_tests(c: Candidate) -> list[str]` — file `backend/tests/**/test_*.py` có status `A` hoặc `M` trong commit.

- [ ] **Step 1: Viết test** cho từng hàm: commit sửa `backend/tests/conftest.py` → `failed_criterion == 1`; 29 dòng src → `4`; 401 dòng → `4`; 30 và 400 dòng → qua; chỉ đổi tên → `5`; `layer_of` chọn lớp nhiều dòng nhất và theo luật hòa; `hidden_tests` bỏ file `D` và file không phải `test_*.py`.
- [ ] **Step 2: Chạy** `uv run pytest tests/test_screen.py -v` → FAIL.
- [ ] **Step 3: Viết `screen.py`.**
- [ ] **Step 4: Chạy** → PASS. Chạy trên repo thật, xác nhận tiêu chí 1 loại 39 commit như bản thiết kế ghi; lệch thì ghi số thật vào `tasks/SCREENING.md`.
- [ ] **Step 5: Commit** `feat(harness): screen candidates by shared test files, size and renames`

### Task 3: Kiểm tra hỏng-thành-đạt (tiêu chí 2) và chạy test

**Files:**
- Create: `harness/src/sdlc_harness/pytest_run.py`, `harness/src/sdlc_harness/verify.py`, `harness/src/sdlc_harness/cli.py`
- Create (kết quả): `tasks/screening.json`, `tasks/SCREENING.md`
- Test: `harness/tests/test_pytest_run.py`, `harness/tests/test_verify.py`

**Interfaces:**
- Consumes: `export_tree`, `Candidate`, `screen_static`, `hidden_tests`.
- Produces:
  - `@dataclass class TestReport: outcomes: dict[str, Literal["passed","failed","error","skipped"]]; duration_s: float; collection_error: bool` — khóa là nodeid pytest dạng `tests/…::test_x`.
  - `run_backend_tests(tree: Path, timeout_s: int = 900) -> TestReport` — `uv sync --frozen` trong `tree` (lần đầu), rồi `uv run pytest -p no:cacheprovider --junitxml=<tmp> -q` trong `tree/backend`; đọc junit XML.
  - `@dataclass class F2PResult: sha: str; passed: bool; reason: str; hidden_failing_at_parent: list[str]; old_failing: list[str]`
  - `check_fail_to_pass(repo: Path, c: Candidate, workroot: Path) -> F2PResult` — xuất commit cha và commit gốc; ở commit cha xóa file test ẩn mới, giữ bản cũ của file bị sửa, rồi chép bản của commit gốc vào để chạy; điều kiện: ít nhất một test ẩn hỏng ở cha, mọi test ẩn đạt ở gốc, mọi test còn lại đạt ở cả hai.
  - CLI `sdlc-harness screen --repo <path> --ref <sha> --out tasks/screening.json --jobs N` — chạy tiêu chí 1, 4, 5 rồi 2 (song song `N` tiến trình), ghi mỗi ứng viên một bản ghi `{sha, subject, layer, src_lines, hidden_tests, failed_criterion, reason}`.

- [ ] **Step 1: Viết test** `test_run_backend_tests_parses_junit` trên toy repo (một test đạt, một hỏng, một mang marker `integration` không xuất hiện trong kết quả); `test_check_fail_to_pass_accepts_real_f2p`, `test_rejects_when_hidden_test_already_passes_at_parent`, `test_rejects_when_old_test_breaks` (dựng ba commit tương ứng trong toy repo).
- [ ] **Step 2: Chạy** → FAIL.
- [ ] **Step 3: Viết `pytest_run.py`, `verify.py`, lệnh `screen` trong `cli.py`** (argparse, `concurrent.futures.ProcessPoolExecutor`).
- [ ] **Step 4: Chạy test** → PASS. **Chạy trên repo thật:** `uv run sdlc-harness screen --repo /home/andv/personal/vipharmind-camera-ready --ref 3baae61d764f6d83f7205d0d4d97ee52dd8e0dbe --out ../tasks/screening.json --jobs 8`. Ghi `tasks/SCREENING.md`: bảng số commit còn lại sau từng tiêu chí (110 → … ) và ba lý do loại phổ biến nhất ở tiêu chí 2. Nếu còn dưới 30 commit sau tiêu chí 2, dừng và báo An trước khi đi tiếp.
- [ ] **Step 5: Commit** `feat(harness): verify fail-to-pass and record the screening funnel` (gồm `tasks/screening.json`, `tasks/SCREENING.md`).

### Task 4: Lấy mẫu, đề bài và duyệt của An

**Files:**
- Create: `harness/src/sdlc_harness/sample.py`, `harness/src/sdlc_harness/tasks.py`
- Create (kết quả): `tasks/<task-id>/task.toml`, `tasks/<task-id>/prompt.md` cho 17 nhiệm vụ; `tasks/REVIEW.md`
- Test: `harness/tests/test_sample.py`, `harness/tests/test_tasks.py`

**Interfaces:**
- Consumes: `tasks/screening.json`.
- Produces:
  - `review_order(eligible: list[dict], seed: int = 20261115) -> list[dict]` — xáo ngẫu nhiên các commit qua tiêu chí 1, 2, 4, 5. An duyệt tiêu chí 3 theo đúng thứ tự này; dừng khi đủ hạn ngạch.
  - `quotas(eligible: list[dict], k: int = 15) -> dict[str, int]` — hạn ngạch mỗi lớp tỉ lệ với số commit đủ điều kiện của lớp đó, làm tròn theo phương pháp phần dư lớn nhất, mỗi lớp có ứng viên ít nhất 1.
  - `select(order: list[dict], approved: set[str], quotas: dict[str,int], pilots: int = 2) -> tuple[list[dict], list[dict]]` — đi theo `order`, nhận commit được duyệt vào lớp của nó khi lớp còn hạn ngạch; 2 commit được duyệt đầu tiên không vào được hạn ngạch nào thành nhiệm vụ thử (nếu thiếu, lấy 2 commit được duyệt kế tiếp).
  - `task.toml`: `id = "t01"…"t15"`, `"p01"`, `"p02"`; `commit`, `parent`, `layer`, `src_lines`, `hidden_tests = [...]`, `pilot = true|false`.
  - `load_task(dir: Path) -> Task` và `validate_task(task: Task) -> list[str]` — lỗi khi: `prompt.md` dưới 5 hoặc trên 10 câu; nhắc tới tên file hay tên hàm test nào trong `hidden_tests`; chứa `TODO`; thiếu khóa trong `task.toml`.
  - CLI `sdlc-harness tasks validate` → thoát 0 khi cả 17 nhiệm vụ hợp lệ.

- [ ] **Step 1: Viết test** `test_review_order_is_deterministic`, `test_quotas_sum_to_k_and_cover_layers` (ví dụ 4 lớp với 20/10/6/4 ứng viên → tổng 15, mỗi lớp ≥ 1), `test_select_fills_quotas_in_order_and_picks_pilots`, `test_validate_rejects_prompt_naming_hidden_test`, `test_validate_rejects_four_sentences`.
- [ ] **Step 2: Chạy** → FAIL.
- [ ] **Step 3: Viết `sample.py`, `tasks.py`, lệnh `tasks validate`.**
- [ ] **Step 4: Chạy test** → PASS.
- [ ] **Step 5: Soạn nháp duyệt.** Với các commit theo `review_order`, AI soạn vào `tasks/REVIEW.md` một mục mỗi commit: đề xuất đạt hay không đạt tiêu chí 3 kèm một câu lý do (giao diện test ẩn dùng có nêu được trong đề bài không), và nháp đề bài 5–10 câu viết từ thông điệp commit và hành vi test ẩn kiểm tra: việc cần làm, giao diện phải giữ (đường dẫn API, chữ ký hàm, lớp công khai), không nêu cách cài đặt. Soạn đến khi số đề xuất đạt vượt hạn ngạch cộng 2 nhiệm vụ thử thêm 5 commit dự phòng.
- [ ] **Step 6: Dừng, giao An duyệt `tasks/REVIEW.md`.** An đánh dấu đạt hay không đạt tiêu chí 3 và sửa đề bài. Không đi tiếp khi An chưa duyệt.
- [ ] **Step 7: Sinh thư mục nhiệm vụ** từ phần An đã duyệt bằng `select`, chạy `uv run sdlc-harness tasks validate` → exit 0.
- [ ] **Step 8: Commit** `feat(tasks): select 15 tasks and 2 pilots with reviewed prompts`

### Task 5: Hai lời dặn

**Files:**
- Create: `prompts/spec.md`, `prompts/vibe.md`, `harness/src/sdlc_harness/prompting.py`
- Test: `harness/tests/test_prompting.py`

**Interfaces:**
- Consumes: `Task` (Task 4); bản tóm tắt cách chia việc trong các plan cũ của ViPharmind ở `retrospective/out/plan-corpus/summary.md` (Task 5 của kế hoạch hồi cứu); bản gốc các plan dựng lại cục bộ bằng `uv run retro plan-corpus --materialize` vào thư mục bị gitignore. Nếu phần đó chưa xong, đọc trực tiếp 3 plan cũ bất kỳ từ lịch sử ViPharmind bằng `git -C … show`.
- Produces: `render_prompt(task: Task, arm: Literal["spec","vibe"]) -> str` — ghép `{arm_instructions}` từ file lời dặn với đề bài nguyên văn; cùng khung cho cả hai cách.

Nội dung bắt buộc:
- `vibe.md`: một câu, nghĩa "Implement the following change in this repository." Không nhắc quy trình, không nhắc test.
- `spec.md`: yêu cầu AI (1) viết tài liệu thiết kế vào `docs/design.md`: mục tiêu, phạm vi, giao diện, cách tiếp cận; (2) viết kế hoạch vào `docs/plan.md`, chia việc thành các phần trọn vẹn theo kích thước tự nhiên, mỗi phần có file cần sửa và test chứng minh; (3) cài đặt theo kế hoạch, viết test trước cho từng phần, chạy bộ test của backend. Không đặt số bước hay độ nhỏ của bước. Câu chữ rút từ cách các plan cũ của ViPharmind viết, không chép nguyên văn skill nào. Dài tối đa 25 dòng.
- Cả hai file không nhắc tới test ẩn, cách chấm hay việc đây là thí nghiệm.

- [ ] **Step 1: Viết test** `test_both_arms_contain_identical_task_text`, `test_arms_differ_only_in_instruction_block` (bỏ khối lời dặn đi thì hai chuỗi bằng nhau), `test_spec_prompt_names_design_and_plan_files`, `test_prompts_do_not_mention_hidden_or_experiment` (không chứa `hidden`, `experiment`, `grade`, `benchmark`).
- [ ] **Step 2: Chạy** → FAIL.
- [ ] **Step 3: Viết hai file lời dặn và `prompting.py`.**
- [ ] **Step 4: Chạy** → PASS.
- [ ] **Step 5: Commit** `feat(prompts): add the spec-driven and vibe coding instructions`

### Task 6: Chuẩn bị thư mục làm việc và thư mục cấu hình sạch

**Files:**
- Create: `harness/src/sdlc_harness/workspace.py`
- Test: `harness/tests/test_workspace.py`

**Interfaces:**
- Consumes: `export_tree`, `Task`.
- Produces:
  - `prepare_workspace(repo: Path, task: Task, run_dir: Path) -> Path` — trả về `run_dir/work`: cây mã ở `task.parent`, không `.git`; xóa các test ẩn có status `A`; chạy `uv sync --frozen` trong đó để AI chạy được test; khởi tạo một repo git mới với một commit "baseline" để sau này lấy bản vá bằng `git diff` (lịch sử chỉ có commit này).
  - `prepare_config(agent: Literal["claude","agy","codex"], run_dir: Path, account: int) -> dict[str, str]` — tạo `run_dir/config`, chép riêng file đăng nhập của tài khoản số `account` vào đó, trả về biến môi trường trỏ tới nó (`CLAUDE_CONFIG_DIR`, `CODEX_HOME`, và biến tương ứng của `agy` xác định ở Task 9). Không chép settings, plugin, skill, bộ nhớ, MCP.
  - `collect_patch(work: Path) -> str` — `git -C work add -A && git diff --cached baseline`.

- [ ] **Step 1: Viết test** `test_workspace_has_no_original_history` (chỉ một commit `baseline`, không có SHA nào của toy repo), `test_new_hidden_tests_removed_modified_kept_at_parent_version`, `test_collect_patch_shows_agent_edits`, `test_prepare_config_copies_only_credentials` (thư mục nguồn giả có `credentials`, `settings.json`, `plugins/` → chỉ `credentials` sang).
- [ ] **Step 2: Chạy** → FAIL.
- [ ] **Step 3: Viết `workspace.py`.** Nguồn file đăng nhập của từng tài khoản đọc từ `harness/accounts.local.toml` (đã có trong `.gitignore`, dạng `[claude] 1 = "/path/…"`); file này không commit.
- [ ] **Step 4: Chạy** → PASS.
- [ ] **Step 5: Commit** `feat(harness): prepare isolated workspaces and clean config dirs` (kèm dòng `harness/accounts.local.toml` trong `.gitignore`).

### Task 7: Chấm điểm

**Files:**
- Create: `harness/src/sdlc_harness/grade.py`
- Test: `harness/tests/test_grade.py`

**Interfaces:**
- Consumes: `run_backend_tests`, `read_file`, `Task`, `collect_patch`.
- Produces: `grade(repo: Path, task: Task, work: Path) -> Grade`, với

```python
@dataclass
class Grade:
    task_pass: bool            # mọi test ẩn đạt và không test cũ nào hỏng
    hidden_passed: int
    hidden_total: int
    regressions: list[str]     # nodeid test cũ không đạt
    ruff_errors: int           # ruff check trên file .py bị thay đổi
    pyrefly_errors: int        # pyrefly check trong backend/
    architecture_pass: bool    # tests/architecture đạt
    radon_cc_mean: float       # radon cc trung bình trên file src bị thay đổi
    radon_mi_mean: float       # radon mi trung bình trên file src bị thay đổi
    ai_tests_added: int        # số hàm test trong file test AI thêm hoặc sửa
    ai_changed_line_coverage: float | None  # phủ dòng của test do AI viết trên dòng src AI đổi
    lines_added: int
    lines_deleted: int
    process_artifacts: bool    # có docs/design.md và docs/plan.md
```

Thứ tự trong `grade`: (1) lấy bản vá, đo kích thước, `process_artifacts`, radon, ruff, pyrefly; (2) chạy riêng test do AI viết dưới `coverage run` để tính phủ dòng trên các dòng src AI đổi; (3) xóa `docs/design.md`, `docs/plan.md` khỏi bản sao dùng để gán nhãn; (4) chép bản test ẩn của `task.commit` đè vào và chạy toàn bộ bộ test. Cùng chỉ số radon được tính cho bản gốc (`task.commit`) một lần và lưu trong `task.toml` dưới khóa `baseline_radon_cc`, `baseline_radon_mi`.

- [ ] **Step 1: Viết test** trên toy repo: bản vá đúng → `task_pass` và `regressions == []`; bản vá làm hỏng một test cũ → `task_pass is False`, nodeid đó nằm trong `regressions`; không sửa gì → `hidden_passed == 0`; AI sửa luôn file test ẩn bị sửa → khi chấm dùng bản của commit gốc; có `docs/plan.md` → `process_artifacts`.
- [ ] **Step 2: Chạy** → FAIL.
- [ ] **Step 3: Viết `grade.py`.**
- [ ] **Step 4: Chạy** → PASS. Chấm thử bản vá gốc của `p01` (áp `git diff parent commit` vào thư mục làm việc) → `task_pass is True`.
- [ ] **Step 5: Commit** `feat(harness): grade runs with hidden tests and quality metrics`

### Task 8: Gọi trợ lý và bộ chạy song song

**Files:**
- Create: `harness/src/sdlc_harness/agents.py`, `harness/src/sdlc_harness/runner.py`, `harness/cohorts.toml`
- Modify: `harness/src/sdlc_harness/cli.py`
- Test: `harness/tests/test_agents.py`, `harness/tests/test_runner.py`

**Interfaces:**
- Consumes: `prepare_workspace`, `prepare_config`, `render_prompt`, `grade`, `load_task`.
- Produces:
  - `harness/cohorts.toml`: bốn mục `[cohort.claude-sonnet]`, `[cohort.claude-opus]`, `[cohort.agy-gemini]`, `[cohort.codex-luna]` với `agent`, `model`, `effort = "medium"`, `accounts = [1, …]`.
  - `build_command(agent: str, model: str, effort: str, prompt_file: Path) -> list[str]`:
    - claude: `claude -p --model <model> --effort medium --output-format stream-json --verbose --permission-mode bypassPermissions --disallowedTools WebFetch WebSearch --strict-mcp-config --setting-sources "" --no-session-persistence` với đề bài qua stdin.
    - agy: `agy -p --model <model> --effort medium --output-format stream-json --dangerously-skip-permissions --disable-slash-commands`, cộng cờ tắt web xác định ở Task 9.
    - codex: `codex exec -m gpt-6-luna -c model_reasoning_effort="medium" --sandbox workspace-write --json`, cộng cờ tắt web xác định ở Task 9; nhóm này trỏ tới proxy bằng profile trong `CODEX_HOME`.
  - `parse_usage(agent: str, transcript: str) -> Usage` với `Usage(input_tokens: int|None, output_tokens: int|None, turns: int|None, model_served: str|None)`.
  - `is_quota_error(agent: str, returncode: int, transcript: str) -> bool` — mẫu nhận diện ghi trong `agents.py`, chốt bằng thông báo lỗi thật thu được ở Task 9.
  - `@dataclass class RunUnit: cohort: str; task_id: str; arm: str; rep: int` và `plan_units(cohorts: list[str], task_ids: list[str], reps: int = 3, seed: int = 20261115) -> list[RunUnit]` — tích Descartes, xáo theo hạt giống.
  - `run_unit(unit: RunUnit, cfg, out_root: Path) -> Literal["done","quota","error"]` — ghi vào `results/raw/<cohort>/<task_id>/<arm>-r<rep>/`: `prompt.txt`, `transcript.jsonl`, `patch.diff`, `grade.json`, `meta.json` (`tool_version`, `model`, `model_served`, `effort`, `account`, `started_at`, `wall_s`, `timed_out`, `usage`). Giết tiến trình khi quá `timeout_s`, vẫn chấm; `timed_out = true`.
  - CLI `sdlc-harness run --cohorts claude-sonnet,claude-opus --tasks pilot|main|t01,t02 --reps 3 --jobs N --timeout-s S` — bỏ qua đơn vị đã có `grade.json`; đơn vị `quota` đổi sang tài khoản kế tiếp của nhóm và đưa lại cuối hàng đợi, không tính lần lặp.

- [ ] **Step 1: Viết test** `test_build_command_claude_disables_web_and_sets_medium`, `test_build_command_codex_sets_reasoning_medium`, `test_plan_units_is_deterministic_and_complete` (2 nhóm × 2 nhiệm vụ × 2 cách × 3 lần = 24 đơn vị, cùng hạt giống cùng thứ tự), `test_runner_requeues_quota_without_counting` (trợ lý giả trả lỗi hạn mức lần đầu, thành công lần hai → một `grade.json`, `meta.account` là tài khoản thứ hai), `test_runner_kills_on_timeout_and_still_grades`, `test_runner_skips_done_units`. Trợ lý giả là một script Python nhỏ trong `tests/fakes/fake_agent.py` được truyền qua biến môi trường `SDLC_FAKE_AGENT`.
- [ ] **Step 2: Chạy** → FAIL.
- [ ] **Step 3: Viết `agents.py`, `runner.py`, `cohorts.toml`, lệnh `run`.** Song song bằng `ThreadPoolExecutor(max_workers=jobs)`; mỗi luồng gọi tiến trình con.
- [ ] **Step 4: Chạy** → PASS.
- [ ] **Step 5: Commit** `feat(harness): run agents in parallel with quota requeue and timeouts`

### Task 9: Chạy thử trên 2 nhiệm vụ thử

**Files:**
- Modify: `harness/src/sdlc_harness/agents.py` (cờ tắt web, mẫu lỗi hạn mức, biến cấu hình của `agy`), `harness/cohorts.toml`
- Create: `results/raw/pilot/…`, `docs/pilot-report.md`

- [ ] **Step 1: Kiểm tra từng công cụ trước khi chạy hàng loạt,** mỗi mục ghi kết quả vào `docs/pilot-report.md`:
  - Đăng nhập chạy được trong thư mục cấu hình sạch (`claude` với `CLAUDE_CONFIG_DIR`; thử cả `--bare` nếu cách đầu không đọc được đăng nhập).
  - Tắt được truy cập web: giao đề bài "fetch https://example.com and print its title"; đạt khi trợ lý không lấy được trang. Tìm cờ hoặc setting cho `agy` (`--settings`) và `codex` (`-c`).
  - Có trả số token trong nhật ký JSON.
  - Codex qua proxy: profile trong `CODEX_HOME` trỏ tới proxy ở `infra/proxy/` của `principle-technique-program-analysis`, cấu hình không ép mức suy luận; ghi `model_served`.
  - Điều khoản của từng gói về chạy tự động và xoay nhiều tài khoản: đọc và ghi đường dẫn nguồn.
  - Mốc dữ liệu huấn luyện của bốn mô hình, tra từ trang chính thức của hãng; ghi mô hình nào có mốc trước 2026-07-23 (chỉ với mô hình đó báo cáo mới được viết "chưa từng thấy mã này").
  Công cụ nào không tắt được web hoặc không cho chạy tự động: loại khỏi thí nghiệm, ghi lý do, báo An.
- [ ] **Step 2: Chạy thử:** `uv run sdlc-harness run --cohorts claude-sonnet,claude-opus,agy-gemini,codex-luna --tasks pilot --reps 3 --jobs 8 --timeout-s 3600` (giới hạn rộng để đo thời gian thật).
- [ ] **Step 3: Chốt giới hạn và ngưỡng,** ghi vào `docs/pilot-report.md`: `timeout_s` = 2 lần thời gian dài nhất của các lượt đạt, làm tròn lên bội số 5 phút; ngưỡng kích thước nhỏ, vừa, lớn = tam phân vị `src_lines` của 15 nhiệm vụ; tỉ lệ đạt từng nhóm và từng cách; số lượt `quota`, `error`, `timed_out`. Nếu mọi lượt của `claude-sonnet` đều hỏng ở cả hai cách, báo An để xem lại bộ nhiệm vụ.
- [ ] **Step 4: Gán thử nhãn nguyên nhân thất bại** trên các lượt không đạt của nhiệm vụ thử theo bảng nhãn khởi đầu ở mục 7.6, ghi các nhãn cần sửa vào `docs/pilot-report.md` (bảng nhãn chính thức thuộc kế hoạch gán nhãn).
- [ ] **Step 5: Lọc bí mật và commit:** `gitleaks detect --no-git --source results/raw/pilot` → không có phát hiện; rồi `git add results/raw/pilot docs/pilot-report.md harness && git commit -m "test(pilot): run the pilot tasks and fix limits"`.

### Task 10: Chốt trước khi chạy và gắn thẻ `prereg-v1`

**Files:**
- Create: `prereg/prereg-v1.md`

- [ ] **Step 1: Viết `prereg/prereg-v1.md`** gồm: danh sách 15 nhiệm vụ (id, commit, lớp, `src_lines`); đường dẫn hai lời dặn; bốn nhóm chạy với mô hình, effort, phiên bản công cụ; `timeout_s`, ngưỡng kích thước; hạt giống `20261115`; chỉ số chính và phụ (mục 7.5); H1 đến H4 nguyên văn từ bản thiết kế; kế hoạch phân tích (so sánh theo cặp, bootstrap theo nhiệm vụ với 10.000 lần lấy mẫu lại, khoảng tin cậy 95%, phân tích 2 × 2 cho RQ5, phân tích theo kích thước là khám phá); quy tắc dừng (bỏ đợt 3 trước rồi đợt 2); mọi thay đổi sau thẻ phải ghi kèm lý do.
- [ ] **Step 2: Kiểm tra** `uv run sdlc-harness tasks validate` → exit 0 và `cd harness && uv run pytest` → mọi test đạt.
- [ ] **Step 3: Dừng, giao An duyệt `prereg/prereg-v1.md`.**
- [ ] **Step 4: Commit và gắn thẻ** sau khi An duyệt: `git add prereg && git commit -m "docs(prereg): freeze tasks, prompts, hypotheses and analysis" && git tag -a prereg-v1 -m "Pre-registration before the first main run"`.
