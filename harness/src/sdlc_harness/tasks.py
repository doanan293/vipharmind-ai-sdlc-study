"""Task files (task.toml + prompt.md): load, write and validate."""

import ast
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

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
        missing_keys=tuple(k for k in REQUIRED_KEYS if k not in data),
    )


def write_task(dir: Path, task: Task) -> None:
    dir.mkdir(parents=True, exist_ok=True)
    hidden = ", ".join(f'"{p}"' for p in task.hidden_tests)
    (dir / "task.toml").write_text(
        f'id = "{task.id}"\n'
        f'commit = "{task.commit}"\n'
        f'parent = "{task.parent}"\n'
        f'layer = "{task.layer}"\n'
        f"src_lines = {task.src_lines}\n"
        f"hidden_tests = [{hidden}]\n"
        f"pilot = {'true' if task.pilot else 'false'}\n"
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
