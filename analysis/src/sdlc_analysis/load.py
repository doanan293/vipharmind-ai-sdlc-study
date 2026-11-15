"""Read task metadata (tasks/*/task.toml) and run units (results/<cohort>/<task>/<arm>-r<rep>/)
into tidy tables, and work out which (cohort, tier) cells are complete (prereg-v1 section 10)."""

import json
import math
import re
import tomllib
from pathlib import Path

import pandas as pd

from sdlc_analysis.prices import cost_usd
from sdlc_analysis.tokens import ModelTokens, parse_tokens, pytest_ran

ARMS = ("spec", "vibe")
TIERS = ("small", "medium", "large")
COHORTS = ("claude-sonnet", "claude-opus", "agy-gemini", "codex-luna")
MAX_ERROR_RERUNS = 2  # harness: a system-error unit runs at most 1 + 2 times, then is excluded
PROCESS_FILES = {
    "design": ("docs/design.md", "backend/docs/design.md"),
    "plan": ("docs/plan.md", "backend/docs/plan.md"),
}
GRADER_TIMEOUT_NOTE = "grader timeout on agent patch (twice)"
UNIT_RE = re.compile(r"^(spec|vibe)-r(\d+)$")


def size_group(src_lines: int) -> str:
    """Size group inside the small tier (prereg 1): <= 82, 83-173, >= 174 lines."""
    if src_lines <= 82:
        return "small"
    if src_lines <= 173:
        return "medium"
    return "large"


def load_tasks(tasks_dir: Path, task_ids: list[str] | None = None) -> pd.DataFrame:
    """One row per task. Default: every non-pilot task; `task_ids` picks tasks (pilots too)."""
    rows = []
    for toml in sorted(Path(tasks_dir).glob("*/task.toml")):
        d = tomllib.loads(toml.read_text())
        tier = str(d.get("tier", "small"))
        lines = int(d.get("src_lines", 0))
        rows.append(
            {
                "task_id": str(d["id"]),
                "tier": tier,
                "kind": str(d.get("kind", "commit")),
                "commit": str(d.get("commit", "")),
                "base": str(d.get("base") or d.get("parent") or ""),
                "layer": d.get("layer"),
                "src_lines": lines,
                "log_src_lines": math.log(max(lines, 1)),
                "n_hidden_test_files": len(d.get("hidden_tests", [])),
                "pilot": bool(d.get("pilot", False)),
                "baseline_radon_cc": d.get("baseline_radon_cc"),
                "baseline_radon_mi": d.get("baseline_radon_mi"),
                "size_group": size_group(lines) if tier == "small" else None,
            }
        )
    tasks = pd.DataFrame(rows)
    if tasks.empty:
        return tasks
    if task_ids:
        unknown = sorted(set(task_ids) - set(tasks["task_id"]))
        if unknown:
            raise ValueError(f"unknown task ids: {', '.join(unknown)}")
        tasks = tasks[tasks["task_id"].isin(task_ids)]
    else:
        tasks = tasks[~tasks["pilot"]]
    return tasks.reset_index(drop=True)


def _read_json(path: Path) -> dict | None:
    try:
        d = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    return d if isinstance(d, dict) else None


def patch_docs(patch: str) -> dict[str, bool]:
    """Which process documents the patch adds or changes (both arms; vibe runs are counted too)."""
    paths = set()
    deleted = set()
    cur = None
    for line in patch.split("\n"):
        if line.startswith("diff --git "):
            cur = line.split(" b/", 1)[-1]
            paths.add(cur)
        elif line.startswith("deleted file mode") and cur:
            deleted.add(cur)
    live = paths - deleted
    return {name: any(p in live for p in ps) for name, ps in PROCESS_FILES.items()}


def _num(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def _token_fields(agent: str, model: str, transcript: str, meta: dict) -> dict:
    toks: list[ModelTokens] = parse_tokens(agent, transcript) if agent else []
    if not toks:
        usage = meta.get("usage") or {}
        inp, out = _num(usage.get("input_tokens")), _num(usage.get("output_tokens"))
        if inp is not None and out is not None:
            toks = [ModelTokens.unsplit(model, int(inp), int(out))]
    if not toks:
        return {"tokens_source": None, "tokens_split": None}
    cost = cost_usd(toks, model)
    upper = cost_usd(toks, model, long_context=True)
    reasoning = [t.reasoning for t in toks if t.reasoning is not None]
    return {
        "tok_input_uncached": sum(t.input_uncached for t in toks),
        "tok_cache_read": sum(t.cache_read for t in toks),
        "tok_cache_write_5m": sum(t.cache_write_5m for t in toks),
        "tok_cache_write_1h": sum(t.cache_write_1h for t in toks),
        "tok_output": sum(t.output for t in toks),
        "tok_reasoning": sum(reasoning) if reasoning else None,
        "tokens_total_input": sum(t.total_input for t in toks),
        "tokens_total": sum(t.total for t in toks),
        "tokens_split": all(t.split for t in toks),
        "tokens_source": ",".join(sorted({t.source for t in toks})),
        "token_models": ",".join(sorted({str(t.model) for t in toks})),
        "cost_usd": cost,
        "cost_usd_upper": upper,  # codex: every call at the > 272k-token price
    }


def read_unit(unit_dir: Path, tasks: dict[str, dict]) -> dict | None:
    m = UNIT_RE.match(unit_dir.name)
    meta = _read_json(unit_dir / "meta.json")
    if not m or meta is None:
        return None
    cohort, task_id = unit_dir.parent.parent.name, unit_dir.parent.name
    arm, rep = m.group(1), int(m.group(2))
    grade = _read_json(unit_dir / "grade.json")
    attempts = int(meta.get("error_attempts") or 0)
    if grade is not None:
        status = "done"
    elif meta.get("status") == "error" and attempts >= MAX_ERROR_RERUNS + 1:
        status = "excluded"
    else:
        status = str(meta.get("status") or "unknown")
    agent = meta.get("agent") or ""
    model = meta.get("model") or ""
    usage = meta.get("usage") or {}
    urls = meta.get("upstream_urls")
    row: dict = {
        "unit": f"{cohort}/{task_id}/{arm}-r{rep}",
        "cohort": cohort,
        "task_id": task_id,
        "arm": arm,
        "rep": rep,
        "status": status,
        "valid": status == "done",
        "error": meta.get("error"),
        "error_attempts": attempts,
        "agent": agent,
        "model": model,
        "tool_version": meta.get("tool_version"),
        "prompt_sha256": meta.get("prompt_sha256"),
        "started_at": meta.get("started_at"),
        "timed_out": bool(meta.get("timed_out")),
        "returncode": meta.get("returncode"),
        "nonzero_exit": (not meta.get("timed_out")) and (meta.get("returncode") not in (0, None)),
        "wall_s": _num(meta.get("wall_s")),
        "turns": _num(usage.get("turns")),
        "upstream_urls_known": isinstance(urls, list),
        "upstream_urls_n": len(urls) if isinstance(urls, list) else 0,
        "upstream": bool(urls) if isinstance(urls, list) else False,
    }
    task = tasks.get(task_id, {})
    row.update(
        tier=task.get("tier"),
        src_lines=task.get("src_lines"),
        log_src_lines=task.get("log_src_lines"),
        size_group=task.get("size_group"),
    )
    transcript = ""
    try:
        transcript = (unit_dir / "transcript.jsonl").read_text(errors="replace")
    except OSError:
        pass
    row.update(_token_fields(agent, model, transcript, meta))
    row["pytest_ran"] = pytest_ran(agent, transcript) if agent else None
    if grade is not None:
        hp, ht = _num(grade.get("hidden_passed")), _num(grade.get("hidden_total"))
        ruff, pyre = _num(grade.get("ruff_errors")), _num(grade.get("pyrefly_errors"))
        regs = grade.get("regressions") or []
        mi, cc = _num(grade.get("radon_mi_mean")), _num(grade.get("radon_cc_mean"))
        bmi, bcc = task.get("baseline_radon_mi"), task.get("baseline_radon_cc")
        la, ld = _num(grade.get("lines_added")), _num(grade.get("lines_deleted"))
        notes = grade.get("grading_notes") or []
        row.update(
            task_pass=bool(grade.get("task_pass")),
            hidden_passed=hp,
            hidden_total=ht,
            hidden_pass_rate=(hp / ht) if (hp is not None and ht) else None,
            regressions_n=len(regs),
            regression_any=len(regs) > 0,
            ruff_errors=ruff,
            pyrefly_errors=pyre,
            static_errors=(ruff + pyre) if (ruff is not None and pyre is not None) else None,
            architecture_pass=grade.get("architecture_pass"),
            radon_mi_mean=mi,
            radon_cc_mean=cc,
            radon_mi_delta=(mi - bmi) if (mi is not None and bmi is not None) else None,
            radon_cc_delta=(cc - bcc) if (cc is not None and bcc is not None) else None,
            ai_tests_added=_num(grade.get("ai_tests_added")),
            ai_changed_line_coverage=_num(grade.get("ai_changed_line_coverage")),
            lines_added=la,
            lines_deleted=ld,
            patch_lines=(la + ld) if (la is not None and ld is not None) else None,
            process_artifacts=bool(grade.get("process_artifacts")),
            pytest_config_touched=bool(grade.get("pytest_config_touched")),
            grader_timeout=GRADER_TIMEOUT_NOTE in notes,
        )
        try:
            docs = patch_docs((unit_dir / "patch.diff").read_text(errors="replace"))
        except OSError:
            docs = {"design": None, "plan": None}
        row.update(patch_design_doc=docs["design"], patch_plan_doc=docs["plan"])
    return row


BOOL_COLS = ("task_pass", "regression_any", "process_artifacts", "pytest_config_touched",
             "architecture_pass", "patch_design_doc", "patch_plan_doc", "pytest_ran",
             "grader_timeout", "tokens_split")


def load_runs(results_dir: Path, tasks: pd.DataFrame) -> pd.DataFrame:
    """One row per unit directory found under results_dir/<cohort>/<task>/<arm>-r<rep>/."""
    by_id = {r["task_id"]: r for r in tasks.to_dict("records")} if not tasks.empty else {}
    rows = [
        r
        for d in sorted(Path(results_dir).glob("*/*/*"))
        if d.is_dir() and (r := read_unit(d, by_id)) is not None
    ]
    runs = pd.DataFrame(rows)
    if runs.empty:
        return runs
    for c in BOOL_COLS:
        if c not in runs:
            runs[c] = None
        runs[c] = runs[c].astype("object")
    return runs.sort_values(["cohort", "task_id", "arm", "rep"]).reset_index(drop=True)


def expected_units(tasks: pd.DataFrame, cohorts: list[str], reps: int) -> pd.DataFrame:
    """Every unit the design calls for: cohorts x tasks x arms x reps."""
    rows = [
        {"cohort": c, "task_id": t, "tier": tier, "arm": a, "rep": r}
        for c in cohorts
        for t, tier in zip(tasks["task_id"], tasks["tier"])
        for a in ARMS
        for r in range(1, reps + 1)
    ]
    return pd.DataFrame(rows)


def unit_status(expected: pd.DataFrame, runs: pd.DataFrame) -> pd.DataFrame:
    keys = ["cohort", "task_id", "arm", "rep"]
    have = runs[keys + ["status"]] if not runs.empty else pd.DataFrame(columns=keys + ["status"])
    st = expected.merge(have, on=keys, how="left")
    st["status"] = st["status"].fillna("missing")
    return st


def completeness(expected: pd.DataFrame, runs: pd.DataFrame) -> pd.DataFrame:
    """Per (cohort, tier): counts by status and `complete` (prereg 10: every unit is valid or a
    system error with its reruns used up)."""
    st = unit_status(expected, runs)
    st["kind"] = st["status"].map(
        lambda s: s if s in ("done", "excluded", "missing") else "pending_run"
    )
    out = []
    for (c, tier), g in st.groupby(["cohort", "tier"], sort=False):
        valid = int((g["status"] == "done").sum())
        excluded = int((g["status"] == "excluded").sum())
        missing = int((g["status"] == "missing").sum())
        out.append(
            {
                "cohort": c,
                "tier": tier,
                "expected": len(g),
                "valid": valid,
                "excluded": excluded,
                "missing": missing,
                "pending": len(g) - valid - excluded - missing,
                "deferred": int((g["status"] == "deferred").sum()),
                "complete": valid + excluded == len(g),
            }
        )
    return pd.DataFrame(out)
