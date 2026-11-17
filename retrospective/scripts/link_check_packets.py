"""Second-rater packets for the plan-link check (RQ1 retrospective), for Lợi and Bảo.

usage: uv run python scripts/link_check_packets.py OUT_DIR [--repo REPO]

Raters get 40 `feat` commits: the 20 An already checked (out/link-check.csv, seed 20261115) plus 20 new
ones (seed 20261117, drawn from the remaining feat commits), shuffled together so the two sets cannot
be told apart. Per commit: commit.txt (message + `git show --stat`) and, when the rule found one,
plan.md (the plan file at the commit that added it). The sheet hides An's verdict and the AI
suggestion. The key (code -> sha, set) is written to OUT_DIR/link-key-PRIVATE.csv, outside the
rater folders.
"""

import argparse
import csv
import hashlib
import random
import subprocess
from pathlib import Path

from retro.cli import DEFAULT_REPO, resolve_revs
from retro.gitlog import load_commits
from retro.specplans import has_preceding_plan, load_spec_plan_files, sample_for_manual_check

SEED_NEW = 20261117

GUIDE = """# Kiểm tra quy tắc nối commit với plan (phần hồi cứu, RQ1)

Báo cáo đo "commit tính năng có plan đi trước hay không" bằng một quy tắc tự động. An đã kiểm tay 20 commit
và thấy quy tắc đúng 15/20. Việc này cần **người kiểm thứ hai, độc lập**, và mẫu lớn hơn: mỗi bạn kiểm 40
commit, không bàn với nhau, không xem kết quả của An.

Mỗi thư mục là một commit `feat` của ViPharmind:
- `commit.txt`: thông điệp commit và danh sách file đã đổi.
- `plan.md` (nếu có): file plan mà quy tắc cho là "plan đi trước" của commit này.

Cột `rule_plan` trong sheet: đường dẫn plan quy tắc chọn; trống nghĩa là quy tắc nói "không có plan đi trước".

Với mỗi commit, điền cột `verdict`:
- `correct`: kết luận của quy tắc đúng. Nếu có plan: plan đó thật sự mô tả công việc của commit (nêu cùng
  tính năng, cùng file hoặc cùng module). Nếu trống: bạn không thấy lý do để cho rằng commit có plan.
- `wrong`: plan được chọn không liên quan tới commit, hoặc mô tả một tính năng khác.
- `unclear`: không đủ thông tin để quyết.

Cột `ghi_chu`: một câu, bắt buộc khi `wrong` hoặc `unclear` (ví dụ "plan nói về auth, commit sửa corpus").

Khoảng 3 phút mỗi commit, tổng khoảng 2 giờ. Hạn 20/11. Nội dung ViPharmind là tài liệu nội bộ của An:
không chia sẻ ra ngoài nhóm.
"""


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          text=True).stdout


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path)
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    a = ap.parse_args()
    repo = Path(a.repo)
    revs, _ = resolve_revs(repo, None)
    commits = load_commits(repo, revs)
    plans = [d for d in load_spec_plan_files(repo, revs) if d.kind == "plan"]
    feats = [c for c in commits if c.type == "feat"]
    old = sample_for_manual_check(feats)
    old_shas = {c.sha for c in old}
    rest = sorted((c for c in feats if c.sha not in old_shas), key=lambda c: (c.date, c.sha))
    new = random.Random(SEED_NEW).sample(rest, 20)
    units = [(c, "an_checked") for c in old] + [(c, "new") for c in new]
    random.Random(SEED_NEW).shuffle(units)

    if a.out.exists():
        raise SystemExit(f"{a.out} exists; refusing to overwrite")
    key = []
    for rater in ("loi", "bao"):
        base = a.out / rater
        base.mkdir(parents=True)
        (base / "HUONG-DAN.md").write_text(GUIDE)
        with (base / f"sheet-noi-plan-{rater}.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ma", "subject", "rule_plan", "verdict", "ghi_chu"])
            for c, which in units:
                code = "c" + hashlib.sha256(f"{SEED_NEW}:{c.sha}".encode()).hexdigest()[:8]
                plan = has_preceding_plan(c, plans)
                d = base / code
                d.mkdir()
                (d / "commit.txt").write_text(git(repo, "show", "--stat", "--format=%s%n%n%b", c.sha))
                if plan:
                    (d / "plan.md").write_text(git(repo, "show", f"{plan.added_sha}:{plan.path}"))
                w.writerow([code, c.subject, plan.path if plan else "", "", ""])
                if rater == "loi":
                    key.append({"ma": code, "sha": c.sha, "set": which})
    with (a.out / "link-key-PRIVATE.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ma", "sha", "set"])
        w.writeheader()
        w.writerows(key)
    print(f"{len(units)} commits x2 -> {a.out}")


if __name__ == "__main__":
    main()
