"""Blinded packets for the passing-sample check (prereg-v1 9.10), handed to Loi and Bao instead of An.

usage: python passing_packets.py ANALYSIS_DIR TASKS_DIR REPO OUT_DIR RESULTS_ROOT [RESULTS_ROOT ...]

The 20 drawn passing runs (ANALYSIS_DIR/passing_sample.csv) are shuffled with seed 20261115 and split
10/10 (each rater gets 5 spec + 5 vibe). Per unit, under a random-looking code: prompt.md, patch.diff
without design/plan docs, reference.diff (the original commit, non-test files only). The code -> unit
key is written to ANALYSIS_DIR/labeling/passing-key-PRIVATE.csv and never goes in a packet.
"""

import csv
import hashlib
import random
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

from build_packets import find, strip_process

SEED = 20261115

GUIDE = """# Kiểm tra "đạt test nhưng sai" (prereg-v1 mục 9.10)

Mỗi thư mục là một lượt AI đã **đạt mọi test ẩn**. Câu hỏi: bản vá có thật sự làm đúng điều đề bài yêu
cầu không, hay chỉ qua được test?

Trong mỗi thư mục:
- `prompt.md`: đề bài giao cho AI.
- `patch.diff`: thay đổi AI đã làm.
- `reference.diff`: bản vá gốc của lập trình viên (chỉ mã nguồn, không có test), để đối chiếu.

Cách chấm, điền vào sheet CSV:
- `dung_that` = `yes` nếu bản vá làm đủ và đúng hành vi đề bài nêu (đặt tên, cách tổ chức khác bản gốc
  vẫn là đúng); `no` nếu sai, thiếu hành vi đề nêu, hard-code để qua test, hoặc sửa/né test.
- `ghi_chu`: một câu, bắt buộc khi `no` hoặc khi phân vân.
- Bỏ qua style, tài liệu, test do AI viết.

Làm một mình, không bàn với người kia. Khoảng 3-5 phút mỗi lượt.
"""


def reference_diff(repo: Path, task_toml: Path) -> str:
    meta = tomllib.loads(task_toml.read_text())
    commit = meta["commit"]
    parent = meta.get("parent") or f"{commit}^"
    files = subprocess.run(
        ["git", "-C", str(repo), "diff", "--name-only", parent, commit],
        check=True, capture_output=True, text=True,
    ).stdout.split()
    src = [f for f in files if "/tests/" not in f and not f.startswith("tests/")]
    return subprocess.run(
        ["git", "-C", str(repo), "diff", parent, commit, "--", *src],
        check=True, capture_output=True, text=True,
    ).stdout


def main() -> None:
    analysis, tasks, repo, out = map(Path, sys.argv[1:5])
    roots = [Path(p) for p in sys.argv[5:]]
    rows = list(csv.DictReader((analysis / "passing_sample.csv").open()))
    rng = random.Random(SEED)
    split: dict[str, list[dict]] = {"loi": [], "bao": []}
    for arm in ("spec", "vibe"):
        group = [r for r in rows if r["arm"] == arm]
        rng.shuffle(group)
        half = len(group) // 2
        split["loi"] += group[:half]
        split["bao"] += group[half:]
    key = []
    for rater, units in split.items():
        rng.shuffle(units)
        base = out / rater
        if base.exists():
            raise SystemExit(f"{base} exists; refusing to overwrite")
        base.mkdir(parents=True)
        (base / "HUONG-DAN.md").write_text(GUIDE)
        with (base / f"sheet-{rater}.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ma_luot", "dung_that(yes/no)", "ghi_chu"])
            for row in units:
                code = "p" + hashlib.sha256(f"{SEED}:{row['unit']}".encode()).hexdigest()[:8]
                d = base / code
                d.mkdir()
                src = find(row["unit"], roots)
                shutil.copy(tasks / row["task_id"] / "prompt.md", d / "prompt.md")
                (d / "patch.diff").write_text(strip_process((src / "patch.diff").read_text()))
                (d / "reference.diff").write_text(
                    reference_diff(repo, tasks / row["task_id"] / "task.toml")
                )
                w.writerow([code, "", ""])
                key.append({"code": code, "rater": rater, **row})
    with (analysis / "labeling" / "passing-key-PRIVATE.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(key[0]))
        w.writeheader()
        w.writerows(key)
    print(f"{len(key)} units -> {out} (loi {len(split['loi'])}, bao {len(split['bao'])})")


if __name__ == "__main__":
    main()
