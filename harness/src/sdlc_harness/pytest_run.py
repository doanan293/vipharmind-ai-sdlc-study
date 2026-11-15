"""Run the backend test suite of an exported tree and parse the junit report."""

import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Outcome = Literal["passed", "failed", "error", "skipped"]


@dataclass
class TestReport:
    __test__ = False  # not a pytest class

    outcomes: dict[str, Outcome]
    duration_s: float
    collection_error: bool
    stderr_tail: str = ""


def _nodeid(backend: Path, classname: str, name: str) -> str:
    """Rebuild a pytest nodeid (tests/x.py::Class::test) from junit classname + name."""
    if not classname:
        # collection error: name is the dotted module path
        rel = name.replace(".", "/") + ".py"
        return rel if (backend / rel).is_file() else name
    parts = classname.split(".")
    for i in range(len(parts), 0, -1):
        rel = "/".join(parts[:i]) + ".py"
        if (backend / rel).is_file():
            return "::".join([rel, *parts[i:], name])
    return f"{classname}::{name}"


def _parse_junit(backend: Path, xml_path: Path) -> tuple[dict[str, Outcome], float]:
    outcomes: dict[str, Outcome] = {}
    duration = 0.0
    for case in ET.parse(xml_path).getroot().iter("testcase"):
        key = _nodeid(backend, case.get("classname", ""), case.get("name", ""))
        duration += float(case.get("time", 0) or 0)
        outcome: Outcome = "passed"
        if case.find("error") is not None:
            outcome = "error"
        elif case.find("failure") is not None:
            outcome = "failed"
        elif case.find("skipped") is not None:
            outcome = "skipped"
        outcomes[key] = outcome
    return outcomes, duration


def run_backend_tests(tree: Path, timeout_s: int = 900) -> TestReport:
    """Run pytest in tree/backend. Uses uv when a uv.lock exists, else this interpreter."""
    backend = tree / "backend"
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    # uv.lock sits at the workspace root, or in backend/ when the backend is its own project
    lock_dir = next((d for d in (tree, backend) if (d / "uv.lock").is_file()), None)
    if lock_dir is not None:
        subprocess.run(
            ["uv", "sync", "--frozen"],
            cwd=lock_dir,
            env=env,
            check=True,
            capture_output=True,
            timeout=timeout_s,
        )
        cmd = ["uv", "run", "--frozen", "pytest"]
    else:
        env["PYTHONPATH"] = str(backend / "src")
        cmd = [sys.executable, "-m", "pytest"]
    with tempfile.TemporaryDirectory() as tmp:
        xml_path = Path(tmp) / "junit.xml"
        proc = subprocess.run(
            [
                *cmd,
                "-p",
                "no:cacheprovider",
                f"--junitxml={xml_path}",
                "--continue-on-collection-errors",
                "-q",
            ],
            check=False,
            cwd=backend,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        if not xml_path.is_file():
            tail = (proc.stdout + proc.stderr)[-500:]
            return TestReport({}, 0.0, True, tail)
        outcomes, duration = _parse_junit(backend, xml_path)
    # exit code 2 = interrupted, 3 = internal error, 4 = usage error
    file_level_error = any(v == "error" and "::" not in k for k, v in outcomes.items())
    return TestReport(outcomes, duration, file_level_error or proc.returncode in (2, 3, 4))
