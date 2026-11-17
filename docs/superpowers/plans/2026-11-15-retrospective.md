# Phân tích hồi cứu Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trả lời RQ1 và RQ2 bằng số liệu từ lịch sử git, các file spec, plan và nhật ký phiên của ViPharmind, đồng thời trích bộ plan cũ để viết lời dặn cho nhánh theo đặc tả của thực nghiệm.

**Architecture:** Một gói Python nhỏ `retro` trong `code/retrospective/`, đọc repo ViPharmind chỉ bằng `git log` và `git show` trên hai mã commit cố định, không checkout. Mỗi mô-đun lo một phép đo và có test chạy trên một repo git giả dựng trong `tmp_path`. Lệnh `uv run retro all` sinh mọi bảng CSV, hình và `summary.md` vào `data/retrospective/`.

**Tech Stack:** Python 3.12, `uv`, `pytest`, `matplotlib`, thư viện chuẩn (`subprocess`, `csv`, `json`, `dataclasses`, `random`).

**Spec:** `docs/superpowers/specs/2026-11-15-spec-vs-vibe-study-design.md`, mục 5, 7.1, 7.3 ("Tái hiện quy trình thật"), 8.

## Global Constraints

- Repo ViPharmind: `/home/andv/personal/vipharmind-camera-ready`, **chỉ đọc**. Không checkout, không commit, không sửa file ở đó. Mọi lệnh git dùng `git -C <repo>` với mã commit cố định.
- Hai mốc: `main` = `3baae61d764f6d83f7205d0d4d97ee52dd8e0dbe`, `camera-ready` = `61d10db85f0f4d9cb871e8fff89ce06e2c49b930`. Tập commit là hợp của hai mốc, mỗi commit tính một lần (`git log <main> <camera-ready>`). Không tính nhánh khác.
- Giá trị đối chiếu (đo ngày 2026-11-15): 505 commit; ngày tác giả từ 2026-07-23 đến 2026-11-10; 221 feat, 115 docs, 50 fix, 47 refactor, 34 chore, 20 test; 43 file spec, plan từng được thêm vào; 0 commit merge; 0 commit có `Co-Authored-By`.
- Ngày của commit là ngày tác giả (`%aI`). Cửa sổ thời gian: 14 ngày cho cả quy tắc nối commit với plan và đếm mức phải sửa lại.
- Mẫu kiểm tra tay: 20 commit `feat`, hạt giống ngẫu nhiên `20261115`.
- Nhật ký phiên: chỉ lấy thống kê (số lượt, tên công cụ, số tin nhắn người dùng, ngày). Không ghi nội dung tin nhắn, đầu ra công cụ hay đường dẫn tuyệt đối vào bất kỳ file nào trong repo này. Chỉ tính phiên có thời điểm đầu tiên không muộn hơn 2026-11-10.
- Không chép mã hay plan của ViPharmind vào repo này. File nào cần nội dung gốc thì ghi `(mã commit, đường dẫn)` và dựng lại bằng `git show` vào thư mục bị `.gitignore`.
- Kết luận RQ2 viết là quan sát, không viết là nhân quả.
- Tài liệu và `summary.md` viết tiếng Việt; tên hàm, cột CSV viết tiếng Anh.
- Commit không có dòng ghi công Claude hay AI.

## Review Focus

- **Đổi tên file:** `git log --numstat -M` ghi đường dẫn dạng `backend/{old => new}/x.py` hoặc `a.py => b.py` (763 dòng như vậy trong tập commit). Phải quy về đường dẫn mới, không coi là file lạ. Test ở Task 1.
- **File nhị phân:** numstat ghi `-	-`; phải tính 0 dòng, không làm hỏng phân tích. Test ở Task 1.
- **Thư mục đã đổi tên trong lịch sử:** `seed-pipeline/` và `corpus-pipeline/` không còn ở cây hiện tại nhưng chiếm hơn 1.900 lần chạm file; phải được xếp vào khâu, không rơi vào "other". Test ở Task 2.
- **Thông điệp commit không theo quy ước:** có 2 commit (`initial commit`, một commit `Revert "..."`); loại phải là `other`, không làm sai số đếm theo loại. Test ở Task 1.
- **Phiên không thuộc giai đoạn phát triển ViPharmind:** thư mục `-home-andv-personal-vipharmind-camera-ready` có cả phiên ngày 2026-11-15 đã tạo ra nghiên cứu này, và có file không có `timestamp` ở mấy dòng đầu. Phải bị loại và được đếm ở dòng "đã loại". Test ở Task 6.

---

### Task 1: Khung gói và bộ đọc lịch sử git

**Files:**
- Create: `code/retrospective/pyproject.toml`, `code/retrospective/README.md`, `code/retrospective/.gitignore`
- Create: `code/retrospective/src/retro/__init__.py`, `code/retrospective/src/retro/gitlog.py`
- Test: `code/retrospective/tests/conftest.py`, `code/retrospective/tests/test_gitlog.py`, `code/retrospective/tests/test_real_repo.py`

**Interfaces:**
- Produces:
  - `MAIN_SHA: str`, `CAMERA_READY_SHA: str`, `DEFAULT_REPO: Path` trong `retro/__init__.py`.
  - `@dataclass(frozen=True) class FileChange: path: str; added: int; deleted: int`
  - `@dataclass(frozen=True) class Commit: sha: str; date: datetime; subject: str; type: str; files: tuple[FileChange, ...]`
  - `parse_type(subject: str) -> str`: phần trước `(` hoặc `:` theo mẫu `^[a-z]+(\([^)]*\))?!?: `; không khớp thì `"other"`.
  - `load_commits(repo: Path, revs: Sequence[str]) -> list[Commit]`, sắp theo ngày tăng dần.
  - Fixture `make_repo(tmp_path) -> Callable[[list[dict]], Path]` trong `conftest.py`: mỗi dict có `message`, `date` (ISO), `files: dict[str, str | bytes | None]` (`None` là xóa), `rename: dict[str, str]` tùy chọn; đặt `GIT_AUTHOR_DATE` và `GIT_COMMITTER_DATE` theo `date`.

- [ ] **Step 1: Viết test**

```python
def test_parse_type():
    assert parse_type("feat(api): add x") == "feat"
    assert parse_type("fix!: y") == "fix"
    assert parse_type("initial commit") == "other"
    assert parse_type('Revert "docs(paper): z"') == "other"

def test_load_commits_counts_lines_and_renames(make_repo):
    repo = make_repo([
        {"message": "feat: a", "date": "2026-08-01T10:00:00+07:00", "files": {"backend/src/a.py": "x\ny\n", "logo.png": b"\x00\x01"}},
        {"message": "refactor: move", "date": "2026-08-02T10:00:00+07:00", "rename": {"backend/src/a.py": "backend/src/b.py"}},
    ])
    commits = load_commits(repo, ["HEAD"])
    assert [c.type for c in commits] == ["feat", "refactor"]
    first = {f.path: (f.added, f.deleted) for f in commits[0].files}
    assert first == {"backend/src/a.py": (2, 0), "logo.png": (0, 0)}
    assert [f.path for f in commits[1].files] == ["backend/src/b.py"]

def test_union_counts_each_commit_once(make_repo):  # hai nhánh chung tổ tiên
    ...  # tạo 1 commit gốc, 2 nhánh mỗi nhánh 1 commit; load_commits(repo, [b1, b2]) có 3 commit
```

`test_real_repo.py` (đánh dấu `@pytest.mark.real`, tự bỏ qua khi `DEFAULT_REPO` không tồn tại):

```python
def test_reference_values():
    commits = load_commits(DEFAULT_REPO, [MAIN_SHA, CAMERA_READY_SHA])
    assert len(commits) == 505
    assert commits[0].date.date().isoformat() == "2026-07-23"
    assert commits[-1].date.date().isoformat() == "2026-11-10"
    counts = Counter(c.type for c in commits)
    assert {k: counts[k] for k in ["feat", "docs", "fix", "refactor", "chore", "test"]} == \
        {"feat": 221, "docs": 115, "fix": 50, "refactor": 47, "chore": 34, "test": 20}
```

- [ ] **Step 2: Chạy test, xác nhận hỏng**

Run: `cd retrospective && uv run pytest -q`
Expected: FAIL vì chưa có `retro.gitlog`.

- [ ] **Step 3: Viết `pyproject.toml` và `gitlog.py`**

`pyproject.toml`: tên `retro`, bố cục `src/`, phụ thuộc `matplotlib`, nhóm dev `pytest`, script `retro = "retro.cli:main"`, đăng ký marker `real`. `load_commits` gọi một lần `git -C repo log -M --numstat --format=<dấu phân cách>%H%x1f%aI%x1f%s <revs>`. Đường dẫn đổi tên: `pre{a => b}post` thành `pre` + `b` + `post` (bỏ `//` thừa khi `a` hoặc `b` rỗng), `a => b` thành `b`. `-` thành 0. `.gitignore`: `out/plan-corpus/files/`, `.venv/`.

- [ ] **Step 4: Chạy test, xác nhận đạt**

Run: `cd retrospective && uv run pytest -q`
Expected: mọi test đạt, kể cả `test_reference_values`.

- [ ] **Step 5: Commit**

```bash
git add code/retrospective/
git commit -m "feat(retro): load the ViPharmind commit history"
```

### Task 2: Bản đồ vòng đời (RQ1)

**Files:**
- Create: `code/retrospective/src/retro/stages.py`
- Test: `code/retrospective/tests/test_stages.py`

**Interfaces:**
- Consumes: `Commit`, `FileChange` (Task 1).
- Produces:
  - `STAGES = ("research_eval", "data", "backend", "frontend", "test", "deploy", "docs", "other")`
  - `classify_file(path: str) -> str`
  - `commit_stage(commit: Commit) -> str`: khâu có tổng `added + deleted` lớn nhất trong commit; hòa thì lấy khâu đứng trước trong `STAGES`; commit không đổi dòng nào thì xếp theo số file.
  - `lifecycle_tables(commits: list[Commit]) -> dict[str, list[dict]]` với hai khóa: `"by_stage"` (cột `stage, commits, lines_changed`) và `"by_week"` (cột `week` dạng `YYYY-Www`, `stage, commits, lines_changed`).

Luật `classify_file`, áp theo thứ tự, khớp đầu tiên thắng:

| Điều kiện trên đường dẫn | Khâu |
| --- | --- |
| có thành phần `tests/`, `test/`, `e2e/`, hoặc tên file `test_*.py`, `*_test.py`, `*.test.ts(x)`, `*.spec.ts(x)` | `test` |
| bắt đầu `docs/report/`, `docs/presentation/`, `docs/paper/`, hoặc `pharma-lab/` | `research_eval` |
| bắt đầu `seed-pipeline/` hoặc `corpus-pipeline/` | `data` |
| bắt đầu `backend/` | `backend` |
| bắt đầu `frontend/` | `frontend` |
| bắt đầu `devops/`, `.github/`, hoặc tên file `compose*.yaml`, `Dockerfile*`, `.env.example` | `deploy` |
| đuôi `.md` | `docs` |
| còn lại | `other` |

- [ ] **Step 1: Viết test**

```python
@pytest.mark.parametrize("path,stage", [
    ("backend/tests/unit/test_x.py", "test"),
    ("frontend/src/app/page.test.tsx", "test"),
    ("pharma-lab/eval/run.py", "research_eval"),
    ("docs/report/main.tex", "research_eval"),
    ("seed-pipeline/src/a.py", "data"),
    ("corpus-pipeline/x.py", "data"),
    ("backend/src/pharma_agent/api/x.py", "backend"),
    ("backend/docs/superpowers/plans/p.md", "backend"),
    ("devops/k8s/a.yaml", "deploy"),
    ("compose.gemini-proxy.yaml", "deploy"),
    ("README.md", "docs"),
    ("uv.lock", "other"),
])
def test_classify_file(path, stage): assert classify_file(path) == stage

def test_commit_stage_majority_and_tie():
    # 10 dòng backend + 3 dòng test -> "backend"
    # 5 dòng data + 5 dòng backend (hòa) -> "data", vì "data" đứng trước "backend" trong STAGES
    # chỉ có file nhị phân frontend/logo.png (0 dòng) -> "frontend" theo số file

def test_real_repo_has_little_other():  # @pytest.mark.real
    # tỉ lệ commit rơi vào "other" dưới 5%
```

- [ ] **Step 2: Chạy test, xác nhận hỏng**

Run: `cd retrospective && uv run pytest tests/test_stages.py -q`
Expected: FAIL vì chưa có `retro.stages`.

- [ ] **Step 3: Viết `stages.py` theo bảng luật**

- [ ] **Step 4: Chạy test, xác nhận đạt**

Run: `cd retrospective && uv run pytest -q`
Expected: đạt. Nếu `test_real_repo_has_little_other` hỏng, in 20 đường dẫn "other" thường gặp nhất, bổ sung luật vào bảng (và sửa bảng trong plan này), không hạ ngưỡng.

- [ ] **Step 5: Commit**

```bash
git add code/retrospective/
git commit -m "feat(retro): map commits to lifecycle stages"
```

### Task 3: Dấu vết quy trình theo đặc tả và quy tắc nối commit với plan (RQ1)

**Files:**
- Create: `code/retrospective/src/retro/specplans.py`
- Test: `code/retrospective/tests/test_specplans.py`

**Interfaces:**
- Consumes: `load_commits`, `Commit` (Task 1).
- Produces:
  - `@dataclass(frozen=True) class DocFile: path: str; kind: Literal["spec", "plan"]; added_sha: str; added_date: datetime; text: str`
  - `load_spec_plan_files(repo: Path, revs: Sequence[str]) -> list[DocFile]`: mọi file khớp `(^|/)docs/superpowers/(specs|plans)/[^/]+\.md$` có trong một commit `--diff-filter=A`; lần thêm sớm nhất thắng; `text` lấy bằng `git show <added_sha>:<path>`.
  - `referenced_code_paths(plan_text: str) -> set[str]`: các chuỗi trong cặp dấu backtick trông như đường dẫn file (có `/` và có đuôi trong `.py .ts .tsx .js .toml .yaml .yml .sql .sh .tex`), bỏ `./` đầu, bỏ hậu tố `:<số>` hay `:<số>-<số>`.
  - `has_preceding_plan(commit: Commit, plans: list[DocFile], window_days: int = 14) -> DocFile | None`: plan có `added_date` trong `[commit.date - 14 ngày, commit.date)`, nêu ít nhất một file mã mà commit chạm (so khớp đường dẫn đầy đủ, hoặc so khớp hậu tố nếu plan nằm trong `backend/`, `frontend/`, `seed-pipeline/` và đường dẫn trong plan tính từ thư mục đó). Trả plan gần nhất hoặc `None`.
  - `spec_trace_rows(commits, docs) -> list[dict]`: mỗi file một dòng, cột `path, kind, added_sha, added_date, n_feat_linked, first_linked_date, last_linked_date`.
  - `sample_for_manual_check(feats: list[Commit], n: int = 20, seed: int = 20261115) -> list[Commit]`
  - `link_accuracy(sheet: Path) -> tuple[int, int]`: đọc `out/link-check.csv` (cột `sha, subject, rule_plan, an_verdict` với `an_verdict` thuộc `correct|wrong`), trả `(số đúng, số đã chấm)`.

- [ ] **Step 1: Viết test**

```python
def test_referenced_code_paths():
    text = "- Create: `backend/src/a/x.py`\n- Modify: `./frontend/app.tsx:12-30`\nRun `uv run pytest`\n`docs/notes.md`"
    assert referenced_code_paths(text) == {"backend/src/a/x.py", "frontend/app.tsx"}

def test_has_preceding_plan_window(make_repo):
    # plan thêm 2026-09-01 nêu `src/x.py` (plan nằm trong backend/docs/...);
    # feat chạm backend/src/x.py ngày 2026-09-10 -> có plan;
    # feat chạm backend/src/x.py ngày 2026-09-20 -> None (quá 14 ngày);
    # feat chạm backend/src/y.py ngày 2026-09-05 -> None (không nêu file)

def test_first_addition_wins(make_repo):  # thêm, xóa, thêm lại cùng đường dẫn -> added_sha là lần đầu

def test_real_repo_has_43_docs():  # @pytest.mark.real
    docs = load_spec_plan_files(DEFAULT_REPO, [MAIN_SHA, CAMERA_READY_SHA])
    assert len(docs) == 43
```

- [ ] **Step 2: Chạy test, xác nhận hỏng**

Run: `cd retrospective && uv run pytest tests/test_specplans.py -q`
Expected: FAIL vì chưa có `retro.specplans`.

- [ ] **Step 3: Viết `specplans.py`**

- [ ] **Step 4: Chạy test, xác nhận đạt**

Run: `cd retrospective && uv run pytest -q`
Expected: đạt.

- [ ] **Step 5: Commit**

```bash
git add code/retrospective/
git commit -m "feat(retro): trace specs and plans to the commits that follow them"
```

### Task 4: Mức phải sửa lại (RQ2)

**Files:**
- Create: `code/retrospective/src/retro/rework.py`
- Test: `code/retrospective/tests/test_rework.py`

**Interfaces:**
- Consumes: `Commit` (Task 1); `has_preceding_plan`, `DocFile` (Task 3); `classify_file` (Task 2).
- Produces:
  - `rework_count(feat: Commit, later: list[Commit], window_days: int = 14) -> int`: số commit `fix` hoặc `refactor` có ngày trong `(feat.date, feat.date + 14 ngày]` và chạm ít nhất một file mà `feat` chạm, không tính file có khâu `docs` hoặc `other`.
  - `rework_rows(commits: list[Commit], plans: list[DocFile]) -> list[dict]`: mỗi `feat` một dòng, cột `sha, date, stage, lines_changed, has_plan, rework`.
  - `rework_summary(rows) -> list[dict]`: hai dòng `has_plan = true/false`, cột `group, n_feat, mean_rework, median_rework, share_with_rework`.
  - `rework_by_stage(rows) -> list[dict]`: cột `stage, n_feat, mean_rework, share_with_rework` (trả lời "sửa lại ở đâu").

- [ ] **Step 1: Viết test**

```python
def test_rework_window_and_overlap(make_repo):
    # feat chạm a.py ngày 1; fix chạm a.py ngày 5 -> tính; refactor chạm a.py ngày 16 -> không;
    # fix chạm b.py ngày 3 -> không; chore chạm a.py ngày 2 -> không; fix chỉ chạm README.md -> không
    assert rework_count(feat, later) == 1

def test_rework_summary_groups(): ...  # 3 dòng có plan (rework 0,1,2), 2 dòng không (0,0) -> mean 1.0 và 0.0, share 2/3 và 0
```

- [ ] **Step 2: Chạy test, xác nhận hỏng**

Run: `cd retrospective && uv run pytest tests/test_rework.py -q`
Expected: FAIL vì chưa có `retro.rework`.

- [ ] **Step 3: Viết `rework.py`**

- [ ] **Step 4: Chạy test, xác nhận đạt**

Run: `cd retrospective && uv run pytest -q`
Expected: đạt.

- [ ] **Step 5: Commit**

```bash
git add code/retrospective/
git commit -m "feat(retro): count fix and refactor follow-ups per feature"
```

### Task 5: Bộ plan cũ cho lời dặn của nhánh theo đặc tả

Đầu ra của task này là đầu vào cho kế hoạch dựng bộ chạy: người viết `code/prompts/spec-driven.md` dựa vào đây để mô tả quy trình spec, plan, làm theo plan với cách chia việc tự nhiên (bản thiết kế mục 7.3).

**Files:**
- Create: `code/retrospective/src/retro/plan_corpus.py`
- Test: `code/retrospective/tests/test_plan_corpus.py`

**Interfaces:**
- Consumes: `DocFile`, `load_spec_plan_files` (Task 3).
- Produces:
  - `@dataclass(frozen=True) class PlanShape: path: str; added_sha: str; lines: int; tasks: int; steps: int; lines_per_task: tuple[int, ...]; files_per_task: tuple[int, ...]; has_global_constraints: bool; has_file_structure: bool`
  - `plan_shape(doc: DocFile) -> PlanShape`: task là tiêu đề `### Task <số>`; bước là dòng bắt đầu `- [ ] **Step`; số file của task là số dòng `- Create:`, `- Modify:`, `- Test:` trong task đó.
  - `spec_sections(doc: DocFile) -> list[str]`: tiêu đề cấp `##` của một spec, theo thứ tự.
  - `write_plan_corpus(docs: list[DocFile], out_dir: Path, materialize: bool = False) -> None`, ghi:
    - `out_dir/index.csv`: mỗi file một dòng, cột `path, kind, added_sha, added_date, lines, tasks, steps, median_lines_per_task, median_files_per_task`.
    - `out_dir/summary.md` (tiếng Việt): số spec, số plan; trung vị và khoảng tứ phân vị của số task mỗi plan, số bước mỗi task, số dòng mỗi task, số file mỗi task; các mục `##` xuất hiện ở ít nhất một nửa số spec; tỉ lệ plan có `Global Constraints` và `File Structure`; ba plan tiêu biểu (plan có số task gần trung vị nhất trong mỗi thư mục `backend/`, `docs/`, `seed-pipeline/`), ghi bằng `(added_sha, path)` kèm lệnh `git show` để mở.
    - Khi `materialize=True`: nội dung gốc từng file vào `out_dir/files/<path>` (thư mục đã `.gitignore`).

- [ ] **Step 1: Viết test**

```python
PLAN = "# P\n## Global Constraints\n- x\n### Task 1: A\n**Files:**\n- Create: `a.py`\n- Test: `t.py`\n- [ ] **Step 1: w**\n- [ ] **Step 2: r**\n### Task 2: B\n- Modify: `b.py`\n- [ ] **Step 1: w**\n"

def test_plan_shape():
    s = plan_shape(doc(PLAN))
    assert (s.tasks, s.steps, s.files_per_task) == (2, 3, (2, 1))
    assert s.has_global_constraints and not s.has_file_structure

def test_write_plan_corpus_does_not_copy_text(tmp_path):
    write_plan_corpus([doc(PLAN)], tmp_path)
    assert (tmp_path / "index.csv").exists() and (tmp_path / "summary.md").exists()
    assert not (tmp_path / "files").exists()
    assert "Create: `a.py`" not in (tmp_path / "summary.md").read_text()
```

- [ ] **Step 2: Chạy test, xác nhận hỏng**

Run: `cd retrospective && uv run pytest tests/test_plan_corpus.py -q`
Expected: FAIL vì chưa có `retro.plan_corpus`.

- [ ] **Step 3: Viết `plan_corpus.py`**

- [ ] **Step 4: Chạy test, xác nhận đạt**

Run: `cd retrospective && uv run pytest -q`
Expected: đạt.

- [ ] **Step 5: Commit**

```bash
git add code/retrospective/
git commit -m "feat(retro): summarise the shape of the historical plans"
```

### Task 6: Thống kê nhật ký phiên

**Files:**
- Create: `code/retrospective/src/retro/sessions.py`
- Test: `code/retrospective/tests/test_sessions.py`

**Interfaces:**
- Produces:
  - `SESSION_DIRS`: hai thư mục `~/.claude/projects/-home-andv-personal-vipharmind` và `~/.claude/projects/-home-andv-personal-vipharmind-camera-ready`. Không tính `-home-andv-personal-vipharmind-ai-sdlc-study`.
  - `CUTOFF = date(2026, 11, 10)`
  - `@dataclass(frozen=True) class SessionStats: session_no: int; is_subagent: bool; first_ts: date | None; user_messages: int; assistant_turns: int; tool_calls: dict[str, int]; user_interrupts: int`. `session_no` là số thứ tự theo `first_ts`, không phải mã phiên. `user_interrupts` là số tin nhắn người dùng chứa `[Request interrupted by user`; đây là thước đo thay thế cho "số lần người sửa hướng" ở bản thiết kế mục 7.1, báo cáo ghi rõ là thước đo thay thế.
  - `session_stats(path: Path) -> SessionStats`: đọc từng dòng JSON, bỏ qua dòng lỗi; `first_ts` là `timestamp` đầu tiên tìm thấy trong cả file.
  - `collect_sessions(dirs: Sequence[Path] = SESSION_DIRS, cutoff: date = CUTOFF) -> tuple[list[SessionStats], dict[str, int]]`: phần thứ hai đếm số file đã loại theo lý do `after_cutoff`, `no_timestamp`. Nhật ký tác tử con là file trong thư mục con `subagents/`.
  - `session_rows(stats) -> list[dict]` và `tool_rows(stats) -> list[dict]` (cột `tool, calls`), chỉ chứa số.

- [ ] **Step 1: Viết test**

```python
def test_session_stats_counts_only(tmp_path):
    f = tmp_path / "s.jsonl"
    f.write_text("\n".join([
        json.dumps({"type": "user", "timestamp": "2026-09-01T01:00:00Z", "message": {"content": "API_KEY=sk-secret"}}),
        json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {"command": "cat .env"}}]}}),
        json.dumps({"type": "user", "message": {"content": [{"type": "text", "text": "[Request interrupted by user]"}]}}),
        "not json",
    ]))
    s = session_stats(f)
    assert (s.user_messages, s.assistant_turns, s.tool_calls, s.user_interrupts) == (2, 1, {"Bash": 1}, 1)
    assert "sk-secret" not in repr(s) and "cat .env" not in repr(s)

def test_collect_excludes_after_cutoff_and_missing_timestamp(tmp_path):
    # một file 2026-11-04, một file 2026-11-15, một file không có timestamp
    stats, dropped = collect_sessions([tmp_path])
    assert len(stats) == 1 and dropped == {"after_cutoff": 1, "no_timestamp": 1}
```

- [ ] **Step 2: Chạy test, xác nhận hỏng**

Run: `cd retrospective && uv run pytest tests/test_sessions.py -q`
Expected: FAIL vì chưa có `retro.sessions`.

- [ ] **Step 3: Viết `sessions.py`**

- [ ] **Step 4: Chạy test, xác nhận đạt**

Run: `cd retrospective && uv run pytest -q`
Expected: đạt.

- [ ] **Step 5: Commit**

```bash
git add code/retrospective/
git commit -m "feat(retro): count turns and tool calls in the surviving session logs"
```

### Task 7: Lệnh `retro`, chạy trên ViPharmind và kiểm tra tay

**Files:**
- Create: `code/retrospective/src/retro/cli.py`, `code/retrospective/src/retro/figures.py`
- Modify: `code/retrospective/README.md`
- Create (kết quả, commit kèm): `data/retrospective/*.csv`, `data/retrospective/figures/*.png`, `data/retrospective/summary.md`, `data/retrospective/plan-corpus/index.csv`, `data/retrospective/plan-corpus/summary.md`, `data/retrospective/link-check.csv`
- Test: `code/retrospective/tests/test_cli.py`

**Interfaces:**
- Consumes: mọi hàm `Produces` của Task 1–6.
- Produces: `main(argv: list[str] | None = None) -> int` với các lệnh con:
  - `retro all [--repo PATH] [--out DIR]`: ghi `commits.csv` (cột `sha, date, type, stage, files, lines_changed`), `lifecycle_by_stage.csv`, `lifecycle_by_week.csv`, `spec_trace.csv`, `rework.csv`, `rework_summary.csv`, `rework_by_stage.csv`, `sessions.csv`, `session_tools.csv`, `plan-corpus/`, hai hình `figures/lifecycle_by_week.png` (cột chồng theo khâu) và `figures/rework_by_group.png`, và `summary.md`. Nếu `link-check.csv` chưa có thì tạo với `an_verdict` để trống; nếu đã có thì giữ nguyên.
  - `retro link-accuracy [--out DIR]`: in `đúng/đã chấm` và ghi dòng tương ứng vào `summary.md`.
  - `retro plan-corpus --materialize`: dựng lại nội dung plan vào `out/plan-corpus/files/`.

`summary.md` (tiếng Việt) có: các giá trị đối chiếu ở Global Constraints kèm dấu khớp hoặc lệch; bảng theo khâu; tỉ lệ `feat` có plan đi trước; độ chính xác của quy tắc nối (hoặc "chưa chấm"); bảng mức phải sửa lại theo nhóm và theo khâu, kèm câu "Đây là quan sát, không phải quan hệ nhân quả."; thống kê phiên kèm số phiên đã loại; câu giới hạn "0 commit có Co-Authored-By, nên mức tham gia của AI dựa trên lời khai của tác giả và phần nhật ký còn lại."

- [ ] **Step 1: Viết test**

```python
def test_all_on_fixture_repo(make_repo, tmp_path):
    repo = make_repo([...])  # 1 plan, 2 feat, 1 fix
    assert main(["all", "--repo", str(repo), "--out", str(tmp_path)]) == 0
    for name in ["commits.csv", "rework.csv", "summary.md", "plan-corpus/index.csv", "link-check.csv", "figures/lifecycle_by_week.png"]:
        assert (tmp_path / name).exists()

def test_all_keeps_existing_link_check(make_repo, tmp_path):
    # chạy hai lần, sửa an_verdict giữa hai lần -> lần hai không ghi đè

def test_link_accuracy(tmp_path):
    # 3 dòng: correct, wrong, trống -> in "1/2"
```

- [ ] **Step 2: Chạy test, xác nhận hỏng**

Run: `cd retrospective && uv run pytest tests/test_cli.py -q`
Expected: FAIL vì chưa có `retro.cli`.

- [ ] **Step 3: Viết `cli.py`, `figures.py` và cập nhật README**

README: lệnh chạy, nguồn dữ liệu và hai mã commit, cách An chấm `link-check.csv`, ghi chú rằng `out/plan-corpus/files/` không được commit.

- [ ] **Step 4: Chạy test, xác nhận đạt**

Run: `cd retrospective && uv run pytest -q`
Expected: đạt.

- [ ] **Step 5: Chạy trên ViPharmind và đối chiếu**

Run: `cd retrospective && uv run retro all && grep -c "lệch" out/summary.md; git -C /home/andv/personal/vipharmind-camera-ready status --porcelain | wc -l`
Expected: `summary.md` không có dòng "lệch" (in `0`); repo ViPharmind không có thay đổi nào (in `0`).

- [ ] **Step 6: Quét bí mật trên kết quả**

Run: `cd retrospective && grep -rniE 'sk-[a-z0-9]|api[_-]?key|token=|password|/home/andv' out/ ; echo "exit=$?"`
Expected: không in dòng nào, `exit=1`.

- [ ] **Step 7: Commit kết quả**

```bash
git add code/retrospective/
git commit -m "feat(retro): run the retrospective analysis on ViPharmind"
```

- [ ] **Step 8: Giao An chấm mẫu 20 commit**

Gửi An đường dẫn tuyệt đối tới `data/retrospective/link-check.csv`: với mỗi dòng, mở commit và plan được quy tắc chọn, ghi `correct` hoặc `wrong` vào `an_verdict`. Dừng ở đây cho đến khi An chấm xong.

- [ ] **Step 9: Ghi độ chính xác của quy tắc nối**

Run: `cd retrospective && uv run retro link-accuracy`
Expected: in `<đúng>/20`, `summary.md` cập nhật. Commit `out/link-check.csv` và `out/summary.md` với thông điệp `docs(retro): record the manual check of the plan-linking rule`.
