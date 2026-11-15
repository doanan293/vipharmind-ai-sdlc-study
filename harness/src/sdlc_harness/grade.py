"""Grade a run: hidden tests, regressions, static quality, maintainability, AI tests, size."""

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import asdict, dataclass, field
from importlib.metadata import version
from pathlib import Path

from coverage import Coverage
from coverage.exceptions import CoverageException
from radon.complexity import cc_visit
from radon.metrics import mi_visit

from sdlc_harness.pytest_run import Outcome, find_lock_dir, run_backend_tests
from sdlc_harness.tasks import Task
from sdlc_harness.vcs import export_tree, read_file
from sdlc_harness.workspace import collect_patch

SRC_PREFIX = "backend/src/"
TESTS_PREFIX = "backend/tests/"
ARCH_PREFIX = "tests/architecture/"
# process artifacts the spec arm is told to write; backend/ variant covers an agent working there
PROCESS_FILES = {
    "design": ("docs/design.md", "backend/docs/design.md"),
    "plan": ("docs/plan.md", "backend/docs/plan.md"),
}
ARTIFACT_PATHS = {p for paths in PROCESS_FILES.values() for p in paths}
# restored from the range end when grading a range task (dependencies the feature adds)
MANIFEST_PATHS = ("pyproject.toml", "uv.lock", "backend/pyproject.toml", "backend/uv.lock")
PYTEST_CONFIG_FILES = {"conftest.py", "pytest.ini", "setup.cfg", "tox.ini"}
COPY_IGNORE = shutil.ignore_patterns(
    ".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"
)


class GradingError(RuntimeError):
    """The task itself is not gradable here (reference runs fail); not the agent's fault."""


@dataclass
class Grade:
    task_pass: bool  # every hidden test passes and no old test broke
    hidden_passed: int
    hidden_total: int
    regressions: list[str]  # nodeids of old tests not passing
    ruff_errors: int | None  # ruff check on changed .py files; None if ruff could not run
    pyrefly_errors: int | None  # pyrefly check in backend/; None if pyrefly could not run
    architecture_pass: bool  # tests/architecture passes
    radon_cc_mean: float  # mean radon cc over blocks of changed src files
    radon_mi_mean: float  # mean radon mi over changed src files
    ai_tests_added: int  # test functions the AI added (new names vs the parent version)
    ai_changed_line_coverage: float | None  # AI tests' line coverage of src lines the AI changed
    lines_added: int
    lines_deleted: int
    process_artifacts: bool  # docs/design.md and docs/plan.md both written
    pytest_config_touched: bool = False  # patch changes conftest.py or pytest settings
    grading_notes: list[str] = field(default_factory=list)  # tools that failed or timed out
    # hidden tests that did not pass: nodeid -> outcome ("failed", "error", "missing", ...)
    hidden_failed: dict[str, str] = field(default_factory=dict)


class GraderTimeout(GradingError):
    """The final test run timed out. `grade` is the fail grade for the patch, if it is kept."""

    def __init__(self, grade: Grade):
        super().__init__("final test run timed out")
        self.grade = grade


def grade_to_dict(g: Grade) -> dict:
    return asdict(g)


# --- patch parsing -----------------------------------------------------------------------


@dataclass
class FilePatch:
    path: str  # new path, or old path for a deleted file
    deleted: bool
    added_lines: list[int] = field(default_factory=list)  # new-side line numbers of '+' lines
    removed: int = 0


def parse_patch(patch: str) -> list[FilePatch]:
    """Split a `git diff` into per-file added line numbers and removed-line counts."""
    files: list[FilePatch] = []
    cur: FilePatch | None = None
    in_hunk = False
    new_line = 0
    for line in patch.split("\n"):
        if line.startswith("diff --git "):
            # fallback path (binary files have no ---/+++ lines): "diff --git a/X b/X"
            cur = FilePatch(path=line.split(" b/", 1)[-1], deleted=False)
            files.append(cur)
            in_hunk = False
        elif cur is None:
            continue
        elif not in_hunk and line.startswith("deleted file mode"):
            cur.deleted = True
        elif not in_hunk and line.startswith("+++ "):
            target = line[4:]
            if target.startswith("b/"):
                cur.path = target[2:]
        elif line.startswith("@@"):
            in_hunk = True
            new_line = int(line.split("+", 1)[1].split()[0].split(",")[0])
        elif in_hunk:
            if line.startswith("+"):
                cur.added_lines.append(new_line)
                new_line += 1
            elif line.startswith("-"):
                cur.removed += 1
            elif line.startswith(" ") or line == "":
                new_line += 1
    return files


# --- metrics on the agent's tree ----------------------------------------------------------


def _env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}


def _tool(name: str) -> str:
    local = Path(sys.executable).parent / name
    return str(local) if local.exists() else (shutil.which(name) or name)


def _radon(sources: list[str]) -> tuple[float, float]:
    """Mean cc over every block (functions, classes, methods) and mean mi over files."""
    complexities: list[int] = []
    mis: list[float] = []
    for code in sources:
        try:
            complexities.extend(b.complexity for b in cc_visit(code))
            mis.append(mi_visit(code, multi=True))
        except SyntaxError:
            continue
    cc = sum(complexities) / len(complexities) if complexities else 0.0
    mi = sum(mis) / len(mis) if mis else 0.0
    return float(cc), float(mi)


def _ruff_errors(work: Path, files: list[str]) -> int:
    if not files:
        return 0
    proc = subprocess.run(
        [_tool("ruff"), "check", "--no-cache", "--output-format", "json", *files],
        cwd=work,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode not in (0, 1):
        raise RuntimeError(f"ruff failed: {proc.stderr[-500:]}")
    return len(json.loads(proc.stdout))


def _pyrefly_errors(work: Path, timeout_s: int) -> int:
    backend = work / "backend"
    args = ["check", "--output-format", "json", "--summary=none"]
    if find_lock_dir(work) is not None:
        cmd = ["uv", "run", "--frozen", "--directory", str(backend), "pyrefly", *args]
    else:
        cmd = [_tool("pyrefly"), *args]
    proc = subprocess.run(
        cmd, cwd=backend, env=_env(), capture_output=True, text=True, check=False,
        timeout=timeout_s,
    )  # fmt: skip
    try:
        errors = json.loads(proc.stdout)["errors"]
    except (json.JSONDecodeError, KeyError) as e:
        raise RuntimeError(f"pyrefly failed: {(proc.stdout + proc.stderr)[-500:]}") from e
    return sum(1 for e in errors if e.get("severity", "error") == "error")


def _is_test_file(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return name.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py"))


def _test_ids(source: str | None) -> set[str]:
    """Pytest-style ids (`test_x`, `TestC::test_y`) of test functions in a module's source."""
    if source is None:
        return set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()

    def walk(body: list[ast.stmt], prefix: str) -> set[str]:
        ids: set[str] = set()
        for node in body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                if node.name.startswith("test"):
                    ids.add(prefix + node.name)
            elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                ids |= walk(node.body, f"{prefix}{node.name}::")
        return ids

    return walk(tree.body, "")


def _show(work: Path, rev: str, path: str) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(work), "show", f"{rev}:{path}"],
        check=False,
        capture_output=True,
        text=True,
    )
    return proc.stdout if proc.returncode == 0 else None


def _pytest_table(source: str | None) -> object:
    if source is None:
        return None
    return tomllib.loads(source).get("tool", {}).get("pytest")


def _pytest_config_touched(work: Path, files: list["FilePatch"]) -> bool:
    for f in files:
        name = f.path.rsplit("/", 1)[-1]
        if name in PYTEST_CONFIG_FILES:
            return True
        if name == "pyproject.toml":
            current = None if f.deleted else _show(work, ":0", f.path)  # staged by collect_patch
            try:
                if _pytest_table(_show(work, "baseline", f.path)) != _pytest_table(current):
                    return True
            except tomllib.TOMLDecodeError:
                return True
    return False


def _changed_line_coverage(
    work: Path, nodeids: list[str], changed: dict[str, list[int]], timeout_s: int
) -> float | None:
    """Run only the AI's tests under coverage; share of changed executable src lines hit."""
    backend = work / "backend"
    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp) / ".coverage"
        run = ["run", f"--data-file={data}", f"--include={backend / 'src'}/*"]
        pytest_args = ["-m", "pytest", "-p", "no:cacheprovider", "-q"]
        env = _env()
        if find_lock_dir(work) is not None:
            cov = f"coverage=={version('coverage')}"
            cmd = ["uv", "run", "--frozen", "--with", cov, "coverage", *run]
        else:
            env["PYTHONPATH"] = str(backend / "src")
            cmd = [sys.executable, "-m", "coverage", *run]
        subprocess.run(
            [*cmd, *pytest_args, *nodeids],
            cwd=backend, env=env, capture_output=True, check=False, timeout=timeout_s,
        )  # fmt: skip
        if not data.is_file():
            raise CoverageException("coverage run produced no data")
        cov_api = Coverage(data_file=str(data))
        cov_api.load()
        executable = covered = 0
        for path, lines in changed.items():
            _, statements, _, missing, _ = cov_api.analysis2(str(work / path))
            hit = set(statements) - set(missing)
            for n in set(lines) & set(statements):
                executable += 1
                covered += n in hit
    return covered / executable if executable else None


# --- reference runs -----------------------------------------------------------------------


def _reference(repo: Path, sha: str, cache_dir: Path | None, timeout_s: int) -> dict[str, Outcome]:
    """Test outcomes of the original tree at sha, cached as cache_dir/<sha>.json."""
    cached = cache_dir / f"{sha}.json" if cache_dir else None
    if cached and cached.is_file():
        return json.loads(cached.read_text())
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp)
        export_tree(repo, sha, tree)
        report = run_backend_tests(tree, timeout_s)
    if report.collection_error or not report.outcomes:
        raise GradingError(f"reference run at {sha} failed to collect: {report.stderr_tail}")
    if cached:
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_text(json.dumps(report.outcomes, indent=1, sort_keys=True))
    return report.outcomes


def _ls_tree(repo: Path, sha: str, prefix: str) -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(repo), "ls-tree", "-r", "-z", "--name-only", sha, "--", prefix],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [p for p in out.split("\0") if p]


def _blob(repo: Path, sha: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), "show", f"{sha}:{path}"], check=True, capture_output=True
    ).stdout


def _restore(target: Path, content: bytes) -> None:
    if target.is_dir() and not target.is_symlink():
        shutil.rmtree(target)
    elif target.is_symlink():
        target.unlink()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)


def _range_changes(repo: Path, task: Task) -> list[tuple[str, str]]:
    """(status, path) for every file under backend/tests/ changed in a range task's base..end."""
    out = subprocess.run(
        ["git", "-C", str(repo), "diff", "--name-status", "-z", "--no-renames",
         task.start, task.commit, "--", TESTS_PREFIX],
        check=True, capture_output=True, text=True,
    ).stdout.split("\0")  # fmt: skip
    return list(zip(out[0::2], out[1::2], strict=False))


def range_hidden_tests(repo: Path, task: Task) -> set[str]:
    """Every test_*.py under backend/tests/ added or modified in base..end."""
    return {
        p
        for s, p in _range_changes(repo, task)
        if s != "D" and p.rsplit("/", 1)[-1].startswith("test_") and p.endswith(".py")
    }


def range_hidden_errors(repo: Path, task: Task) -> list[str]:
    """Problems with a range task's hidden_tests list versus the git-computed set."""
    if task.kind != "range":
        return []
    expected = range_hidden_tests(repo, task)
    listed = set(task.hidden_tests)
    errors = [
        f"{task.id}: hidden_tests lacks {p} (added or modified in the range)"
        for p in sorted(expected - listed)
    ]
    errors += [
        f"{task.id}: hidden_tests lists {p}, not an added or modified test in the range"
        for p in sorted(listed - expected)
    ]
    return errors


def _range_support(repo: Path, task: Task) -> tuple[list[str], list[str]]:
    """Support files changed in a range task's base..end: (present at end, deleted at end).

    Support files are every file under backend/tests/ that is changed in the range and is not a
    hidden test (conftest, fakes, factories, fixtures, helper modules).
    """
    if task.kind != "range":
        return [], []
    present: list[str] = []
    deleted: list[str] = []
    for status, path in _range_changes(repo, task):
        if path in task.hidden_tests:
            continue
        (deleted if status == "D" else present).append(path)
    return present, deleted


def original_patch_errors(
    repo: Path, task: Task, run_dir: Path, cache_dir: Path | None = None, timeout_s: int = 900
) -> list[str]:
    """Grade the original `git diff start end` on a fresh workspace; list everything that is not
    a clean pass (failing hidden tests, regressions, grading errors). Empty means gradable."""
    from sdlc_harness.workspace import prepare_workspace

    errors = range_hidden_errors(repo, task)
    if errors:
        return errors
    work = prepare_workspace(repo, task, run_dir, timeout_s)
    diff = subprocess.run(
        ["git", "-C", str(repo), "diff", "--binary", task.start, task.commit],
        check=True, capture_output=True, text=True,
    ).stdout  # fmt: skip
    subprocess.run(["git", "-C", str(work), "apply"], input=diff, text=True, check=True)
    try:
        g = grade(repo, task, work, cache_dir=cache_dir, timeout_s=timeout_s)
    except GradingError as e:
        return [f"{task.id}: {e}"]
    errors = [f"{task.id}: hidden test {n} -> {o}" for n, o in sorted(g.hidden_failed.items())]
    errors += [f"{task.id}: base test fails under the original patch: {n}" for n in g.regressions]
    errors += [
        f"{task.id}: {n}"
        for n in g.grading_notes
        if not n.startswith(("ruff", "pyrefly", "old tests excluded"))
    ]
    return errors


def _in_files(nodeid: str, rels: set[str]) -> bool:
    return nodeid.split("::", 1)[0] in rels


# --- grade --------------------------------------------------------------------------------


def grade(
    repo: Path, task: Task, work: Path, cache_dir: Path | None = None, timeout_s: int = 900
) -> Grade:
    """Grade the agent's workspace. The workspace is left as is; a copy at
    work.parent/"graded" (no docs, the commit's hidden tests) is the one tested and labeled.

    Old tests are the start (parent, or range base) tests outside the hidden files; hidden tests are the commit's
    tests in the hidden files. Both sets come from reference runs of the original trees, so a
    deleted old test still counts as a regression and the hidden total is exact.
    """
    hidden = set(task.hidden_tests)
    hidden_rel = {p.removeprefix("backend/") for p in hidden}

    start = task.start
    mismatch = range_hidden_errors(repo, task)
    if mismatch:
        raise GradingError("; ".join(mismatch))
    support, support_deleted = _range_support(repo, task)
    baseline = _reference(repo, start, cache_dir, timeout_s)
    old = {n: o for n, o in baseline.items() if not _in_files(n, hidden_rel)}
    notes: list[str] = []
    if task.kind == "range":
        # base test files that no longer exist at the end were deleted or moved by the range
        at_end = set(_ls_tree(repo, task.commit, TESTS_PREFIX))
        gone = {n.split("::", 1)[0] for n in old if "backend/" + n.split("::", 1)[0] not in at_end}
        old = {n: o for n, o in old.items() if n.split("::", 1)[0] not in gone}
        notes += [f"old tests excluded, file gone at end: backend/{p}" for p in sorted(gone)]
    broken = sorted(n for n, o in old.items() if o in ("failed", "error"))
    if broken:
        raise GradingError(f"old tests already fail at start {start}: {broken}")
    reference = _reference(repo, task.commit, cache_dir, timeout_s)
    hidden_ids = sorted(n for n in reference if _in_files(n, hidden_rel))
    not_passing = [n for n in hidden_ids if reference[n] != "passed"]
    if not hidden_ids or not_passing:
        raise GradingError(f"hidden tests do not pass at commit {task.commit}: {not_passing}")
    if task.kind == "range":
        # the end tree (with its support files) must itself pass every old test that survives
        broken_end = sorted(n for n in old if reference.get(n) not in ("passed", "skipped"))
        if broken_end:
            raise GradingError(f"old tests do not pass at end {task.commit}: {broken_end}")

    # (1) patch, size, process artifacts, radon, ruff, pyrefly
    all_files = parse_patch(collect_patch(work))
    patch_paths = {f.path for f in all_files if not f.deleted}
    files = [f for f in all_files if f.path not in ARTIFACT_PATHS]
    present = [f for f in files if not f.deleted and (work / f.path).is_file()]
    changed_py = [f.path for f in present if f.path.endswith(".py")]
    changed_src = [p for p in changed_py if p.startswith(SRC_PREFIX)]
    cc_mean, mi_mean = _radon([(work / p).read_text() for p in changed_src])
    ruff_errors: int | None = None
    try:
        ruff_errors = _ruff_errors(work, changed_py)
    except (RuntimeError, ValueError, subprocess.SubprocessError, OSError) as e:
        notes.append(f"ruff failed: {e}")
    pyrefly_errors: int | None = None
    try:
        pyrefly_errors = _pyrefly_errors(work, timeout_s)
    except subprocess.TimeoutExpired:
        notes.append("pyrefly timed out")
    except (RuntimeError, subprocess.SubprocessError, OSError) as e:
        notes.append(f"pyrefly failed: {e}")

    # (2) AI-written tests under coverage, over the src lines the AI changed
    ai_tests = [
        p for p in changed_py if p.startswith(TESTS_PREFIX) and p not in hidden and _is_test_file(p)
    ]
    ai_nodeids = sorted(
        f"{p.removeprefix('backend/')}::{tid}"
        for p in ai_tests
        for tid in _test_ids((work / p).read_text()) - _test_ids(_show(work, "baseline", p))
    )
    ai_tests_added = len(ai_nodeids)
    changed_lines = {f.path: f.added_lines for f in present if f.path in changed_src}
    changed_lines = {p: lines for p, lines in changed_lines.items() if lines}
    coverage = None
    if ai_nodeids and changed_lines:
        try:
            coverage = _changed_line_coverage(work, ai_nodeids, changed_lines, timeout_s)
        except subprocess.TimeoutExpired:
            notes.append("coverage run timed out")
        except (subprocess.SubprocessError, OSError, CoverageException) as e:
            notes.append(f"coverage failed: {e}")

    # (3) the labeling copy, without the process artifacts
    graded = work.parent / "graded"
    if graded.exists():
        shutil.rmtree(graded)
    shutil.copytree(work, graded, symlinks=True, ignore=COPY_IGNORE)
    for rel in ARTIFACT_PATHS:
        (graded / rel).unlink(missing_ok=True)

    # (4) old test files back at the parent version, the commit's hidden tests over the copy,
    # then the whole suite
    # (range tasks: support files and the dependency manifests come from the end instead)
    for path in _ls_tree(repo, start, TESTS_PREFIX):
        if path not in hidden and path not in support and path not in support_deleted:
            _restore(graded / path, _blob(repo, start, path))
    for path in support_deleted:
        (graded / path).unlink(missing_ok=True)
    for path in [*task.hidden_tests, *support]:
        _restore(graded / path, _blob(repo, task.commit, path))
    if task.kind == "range":
        at_end = set(_ls_tree(repo, task.commit, "."))
        for path in MANIFEST_PATHS:
            if path in at_end:
                _restore(graded / path, _blob(repo, task.commit, path))
            else:
                (graded / path).unlink(missing_ok=True)
    final: dict[str, Outcome] = {}
    # a grader timeout or crash says nothing about the AI's work: GradingError, so the unit is a
    # system error and is rerun (not a task_pass = false)
    timed_out = False
    try:
        report = run_backend_tests(graded, timeout_s)
    except subprocess.TimeoutExpired:
        timed_out = True  # the grade below is the fail grade the caller may keep (see below)
        notes.append("final test run timed out")
    except (subprocess.SubprocessError, OSError) as e:
        raise GradingError(f"final test run failed: {e}") from e
    else:
        final = report.outcomes
        if not final:
            raise GradingError(f"final test run produced no report: {report.stderr_tail}")
        if report.collection_error:
            notes.append("final test run had collection errors")

    hidden_passed = sum(final.get(n) == "passed" for n in hidden_ids)
    hidden_failed = {n: final.get(n, "missing") for n in hidden_ids if final.get(n) != "passed"}
    # skipped only counts as fine when the parent run skipped that test too
    regressions = sorted(
        n
        for n, before in old.items()
        if final.get(n) != "passed" and not (before == "skipped" and final.get(n) == "skipped")
    )
    arch = [n for n in old if n.startswith(ARCH_PREFIX)]
    arch += [n for n in final if n.startswith(ARCH_PREFIX) and n not in old]
    architecture_pass = all(final.get(n) == "passed" for n in arch)

    result = Grade(
        task_pass=hidden_passed == len(hidden_ids) and not regressions,
        hidden_passed=hidden_passed,
        hidden_total=len(hidden_ids),
        regressions=regressions,
        ruff_errors=ruff_errors,
        pyrefly_errors=pyrefly_errors,
        architecture_pass=architecture_pass,
        radon_cc_mean=cc_mean,
        radon_mi_mean=mi_mean,
        ai_tests_added=ai_tests_added,
        ai_changed_line_coverage=coverage,
        lines_added=sum(len(f.added_lines) for f in files),
        lines_deleted=sum(f.removed for f in files),
        process_artifacts=all(
            any(p in patch_paths and (work / p).is_file() for p in paths)
            for paths in PROCESS_FILES.values()
        ),
        pytest_config_touched=_pytest_config_touched(work, all_files),
        grading_notes=notes,
        hidden_failed=hidden_failed,
    )
    if timed_out:
        raise GraderTimeout(result)
    return result


# --- baseline maintainability ---------------------------------------------------------------


def baseline_radon(repo: Path, task: Task) -> tuple[float, float]:
    """The same radon means for the original commit, over the src files it changed."""
    patch = subprocess.run(
        ["git", "-C", str(repo), "diff", task.start, task.commit],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    paths = [
        f.path
        for f in parse_patch(patch)
        if not f.deleted and f.path.startswith(SRC_PREFIX) and f.path.endswith(".py")
    ]
    return _radon([read_file(repo, task.commit, p) for p in paths])


def ensure_baseline_radon(task_dir: Path, repo: Path, task: Task) -> tuple[float, float]:
    """Read baseline_radon_cc/mi from task.toml, computing and appending them once."""
    toml = task_dir / "task.toml"
    data = tomllib.loads(toml.read_text())
    if "baseline_radon_cc" in data and "baseline_radon_mi" in data:
        return float(data["baseline_radon_cc"]), float(data["baseline_radon_mi"])
    cc, mi = baseline_radon(repo, task)
    kept = [
        line
        for line in toml.read_text().splitlines()
        if not line.lstrip().startswith(("baseline_radon_cc", "baseline_radon_mi"))
    ]
    kept += [f"baseline_radon_cc = {cc!r}", f"baseline_radon_mi = {mi!r}"]
    toml.write_text("\n".join(kept) + "\n")
    return cc, mi
