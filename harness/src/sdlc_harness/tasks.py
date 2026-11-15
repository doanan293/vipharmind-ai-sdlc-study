"""Task files (task.toml + prompt.md): load, write and validate."""

import ast
import re
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from sdlc_harness.sample import quotas as compute_quotas
from sdlc_harness.sample import review_order, select
from sdlc_harness.vcs import read_file

REQUIRED_KEYS = ("id", "commit", "parent", "layer", "src_lines", "hidden_tests", "pilot")
MIN_SENTENCES = 5
MAX_SENTENCES = 10

_CODE_SPAN = re.compile(r"```.*?```|`[^`]*`", re.DOTALL)
_SENTENCE_END = re.compile(r"[.!?]+(?=\s|$)")


@dataclass(frozen=True)
class Task:
    id: str
    commit: str
    parent: str
    layer: str
    src_lines: int
    hidden_tests: tuple[str, ...]
    pilot: bool
    prompt: str
    test_names: tuple[str, ...] = ()  # test function names in the hidden test files
    missing_keys: tuple[str, ...] = ()
    baseline_radon_cc: float | None = None  # set by the grader's baseline step
    baseline_radon_mi: float | None = None
    base: str = ""  # range tasks: the commit the agent starts from (commit tasks: the parent)
    kind: str = "commit"  # "commit" (one commit) or "range" (base..commit, commit is the end)

    @property
    def start(self) -> str:
        """The commit the agent's workspace is exported from."""
        return self.base or self.parent


def count_sentences(text: str) -> int:
    """Count sentence ends (. ! ? before whitespace or end), ignoring code spans."""
    return len(_SENTENCE_END.findall(_CODE_SPAN.sub("code", text.strip())))


def _test_functions(source: str) -> tuple[str, ...]:
    """Names of test functions (def test_*) defined anywhere in a test module."""
    names = {
        node.name
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith("test")
    }
    return tuple(sorted(names))


def _opt_float(v: object) -> float | None:
    return None if v is None else float(v)  # type: ignore[arg-type]


def _required(data: dict) -> tuple[str, ...]:
    if data.get("kind") == "range":  # a range starts at `base`; no parent needed
        return tuple("base" if k == "parent" else k for k in REQUIRED_KEYS)
    return REQUIRED_KEYS


def load_task(dir: Path, repo: Path | None = None) -> Task:
    """Read dir/task.toml and dir/prompt.md; with repo, also read hidden test names at the commit."""
    data = tomllib.loads((dir / "task.toml").read_text())
    prompt_file = dir / "prompt.md"
    prompt = prompt_file.read_text() if prompt_file.exists() else ""
    hidden = tuple(data.get("hidden_tests", ()))
    names: tuple[str, ...] = ()
    if repo is not None and "commit" in data:
        found: set[str] = set()
        for path in hidden:
            found.update(_test_functions(read_file(repo, data["commit"], path)))
        names = tuple(sorted(found))
    kind = str(data.get("kind", "commit"))
    if kind not in ("commit", "range"):
        raise ValueError(f"{dir}: unknown task kind {kind!r}")
    return Task(
        id=str(data.get("id", dir.name)),
        commit=str(data.get("commit", "")),
        parent=str(data.get("parent", "")),
        layer=str(data.get("layer", "")),
        src_lines=int(data.get("src_lines", 0)),
        hidden_tests=hidden,
        pilot=bool(data.get("pilot", False)),
        prompt=prompt,
        test_names=names,
        missing_keys=tuple(k for k in _required(data) if k not in data),
        baseline_radon_cc=_opt_float(data.get("baseline_radon_cc")),
        baseline_radon_mi=_opt_float(data.get("baseline_radon_mi")),
        base=str(data.get("base", "")),
        kind=kind,
    )


def write_task(dir: Path, task: Task) -> None:
    dir.mkdir(parents=True, exist_ok=True)
    hidden = ", ".join(f'"{p}"' for p in task.hidden_tests)
    (dir / "task.toml").write_text(
        f'id = "{task.id}"\n'
        f'commit = "{task.commit}"\n'
        + (f'kind = "range"\nbase = "{task.base}"\n' if task.kind == "range" else "")
        + (f'parent = "{task.parent}"\n' if task.kind == "commit" or task.parent else "")
        + f'layer = "{task.layer}"\n'
        f"src_lines = {task.src_lines}\n"
        f"hidden_tests = [{hidden}]\n"
        f"pilot = {'true' if task.pilot else 'false'}\n"
        + (
            f"baseline_radon_cc = {task.baseline_radon_cc!r}\n"
            f"baseline_radon_mi = {task.baseline_radon_mi!r}\n"
            if task.baseline_radon_cc is not None and task.baseline_radon_mi is not None
            else ""
        )
    )
    (dir / "prompt.md").write_text(task.prompt.strip() + "\n")


def _mentions(text: str, name: str) -> bool:
    return re.search(rf"(?<![\w]){re.escape(name)}(?![\w])", text) is not None


def validate_task(task: Task) -> list[str]:
    errors = [f"{task.id}: task.toml missing key '{k}'" for k in task.missing_keys]
    n = count_sentences(task.prompt)
    if not MIN_SENTENCES <= n <= MAX_SENTENCES:
        errors.append(f"{task.id}: prompt has {n} sentences, needs {MIN_SENTENCES}-{MAX_SENTENCES}")
    if "TODO" in task.prompt:
        errors.append(f"{task.id}: prompt contains TODO")
    for path in task.hidden_tests:
        base = path.rsplit("/", 1)[-1]
        for name in (base, base.removesuffix(".py")):
            if _mentions(task.prompt, name):
                errors.append(f"{task.id}: prompt names hidden test file '{name}'")
                break
    for name in task.test_names:
        if _mentions(task.prompt, name):
            errors.append(f"{task.id}: prompt names hidden test '{name}'")
    return errors


_SECTION = re.compile(r"^## \d+\. ", re.MULTILINE)
_SHA = re.compile(r"^- sha: `([0-9a-f]{40})`", re.MULTILINE)
_PROMPT = re.compile(r"```text\n(.*?)\n```", re.DOTALL)
_VERDICT = re.compile(r"^An:[ \t]*(pass|fail)\b", re.MULTILINE)


def parse_review(text: str) -> list[dict]:
    """Sections of REVIEW.md: sha, subject, prompt and An's verdict ('pass', 'fail' or None)."""
    sections = []
    for chunk in _SECTION.split(text)[1:]:
        sha = _SHA.search(chunk)
        prompt = _PROMPT.search(chunk)
        if not sha or not prompt:
            raise ValueError(f"REVIEW.md section without sha or prompt block: {chunk[:60]!r}")
        verdict = _VERDICT.search(chunk)
        sections.append(
            {
                "sha": sha.group(1),
                "prompt": prompt.group(1).strip(),
                "verdict": verdict.group(1) if verdict else None,
            }
        )
    return sections


def generate_tasks(
    review_text: str,
    screening: list[dict],
    parent_of: Callable[[str], str],
    out: Path,
    k: int = 15,
    pilots: int = 2,
) -> list[Task]:
    """Select tasks and pilots from An's verdicts and write task dirs. Fails loudly, never guesses."""
    eligible = [r for r in screening if r.get("failed_criterion") is None]
    order = review_order(eligible)
    sections = parse_review(review_text)
    expected = [r["sha"] for r in order[: len(sections)]]
    if [s["sha"] for s in sections] != expected:
        raise ValueError("REVIEW.md order differs from review_order; do not reorder sections")
    by_sha = {s["sha"]: s for s in sections}
    quota = compute_quotas(eligible, k)
    approved: set[str] = set()
    chosen: tuple[list[dict], list[dict]] | None = None
    last_error: ValueError | None = None
    for i, rec in enumerate(order):
        sec = by_sha.get(rec["sha"])
        if sec is None:
            break  # not drafted: the review stopped here
        if sec["verdict"] is None:
            raise ValueError(f"no An verdict for commit #{i + 1} {rec['sha'][:10]}")
        if sec["verdict"] == "pass":
            approved.add(rec["sha"])
        try:
            chosen = select(order[: i + 1], approved, quota, pilots)
            break
        except ValueError as e:
            last_error = e
    if chosen is None:
        raise ValueError(
            f"quota or pilots cannot be filled from the reviewed commits: {last_error}"
        )
    mains, trial = chosen
    tasks = []
    for tid, rec, pilot in [
        *((f"t{i:02d}", r, False) for i, r in enumerate(mains, 1)),
        *((f"p{i:02d}", r, True) for i, r in enumerate(trial, 1)),
    ]:
        task = Task(
            id=tid,
            commit=rec["sha"],
            parent=parent_of(rec["sha"]),
            layer=rec["layer"],
            src_lines=int(rec["src_lines"]),
            hidden_tests=tuple(rec["hidden_tests"]),
            pilot=pilot,
            prompt=by_sha[rec["sha"]]["prompt"],
        )
        write_task(out / tid, task)
        tasks.append(task)
    return tasks
