"""Round-2 failure-label packets (prereg-v1 9.8, second round, logged in 11).

usage: python relabel_packets.py ANALYSIS_DIR TASKS_DIR REPO PACKETS_DIR

Same 30 units as round 1, under NEW codes and a new order (seed 20261116), so the round-1 sheet cannot
be copied over. Each unit: prompt.md, patch.diff, test-log.txt from round 1, plus the hidden test files
(hidden-tests/) so the rater can see exactly what the failing test asserts. The guide is round 1's,
plus section 3b (a fixed decision order) and the het_gio location fix. The new key is written to
ANALYSIS_DIR/labeling/key-round2-PRIVATE.csv.
"""

import csv
import hashlib
import random
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

SEED = 20261116

ADDENDUM = """
## 3b. Thứ tự quyết định (vòng 2, bắt buộc theo đúng thứ tự)

Vòng 1 cho thấy hai bạn hiểu khác nhau ở cùng một chỗ, nên vòng 2 thêm thứ tự quyết định dưới đây. Bảng
nhãn ở mục 3 **không đổi**. Mỗi lượt giờ có thêm thư mục `hidden-tests/`: mã nguồn của các test ẩn, để
bạn đọc đúng dòng `assert` hoặc `pytest.raises` của test hỏng.

1. **Hết giờ?** Nếu `test-log.txt` có dòng `NOTE: the agent hit the time limit (het_gio)` và bản vá còn
   dở, chọn `khong_hoan_thanh`. (Vòng 1 ghi nhầm là `het_gio` nằm ở cột `note`; thực ra nó nằm trong
   `test-log.txt`.)
2. **Test ẩn đều đạt?** Nếu dòng `hidden tests passed` là đủ (ví dụ 10/10) và dòng
   `old tests broken (regressions)` lớn hơn 0, thì nguyên nhân là test cũ: chọn `hong_chuc_nang_cu`
   (hoặc `loi_moi_truong` nếu bản vá không đụng tới mã mà test cũ đó dùng). Nếu một test **ẩn** hỏng thì
   **không** chọn `hong_chuc_nang_cu`, dù tên test nghe như test cũ.
3. **Tìm test ẩn hỏng đầu tiên** trong `test-log.txt`, mở file tương ứng trong `hidden-tests/`, đọc đúng
   điều nó khẳng định (giá trị, kiểu, loại lỗi, tên).
4. **Đề có nêu điều đó không?** Mở `prompt.md`.
   - Đề nêu rõ tên, vị trí hay chữ ký mà agent làm khác: `sai_giao_dien`.
   - Đề **không** nêu điều test khẳng định (ví dụ đề chỉ nói "phải báo lỗi", test đòi đúng loại lỗi
     `ValueError`), và cách agent làm là một cách hợp lý theo câu chữ của đề: xét bước 5 trước, nếu bước
     5 không khớp thì chọn `de_bai_thieu`.
5. **Mã có sẵn trong dự án có quyết định điều đó không?** Nếu điều test khẳng định là hệ quả tự nhiên
   của việc dùng đúng kiểu, hàm hay lớp **đã có trong mã nền** (nhìn thấy được trong `patch.diff`, ví dụ
   agent tự tạo lớp lỗi mới thay vì để kiểu có sẵn tự báo lỗi, hoặc gọi hàm có sẵn sai chữ ký), chọn
   `sai_api_co_san`.
6. Còn lại: agent làm sai việc đề nêu rõ thì `hieu_sai`; bỏ sót phần đề nêu thì `lam_thieu`; đúng việc,
   đúng giao diện nhưng sai chi tiết cài đặt mà đề **có** nêu hoặc hiển nhiên phải đúng thì `loi_logic`.

Ghi vào cột `note` một câu: test khẳng định gì, và đề có nêu điều đó không.
"""


def hidden_tests(repo: Path, task_toml: Path) -> dict[str, str]:
    meta = tomllib.loads(task_toml.read_text())
    out = {}
    for path in meta["hidden_tests"]:
        out[Path(path).name] = subprocess.run(
            ["git", "-C", str(repo), "show", f"{meta['commit']}:{path}"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    return out


def main() -> None:
    analysis, tasks, repo, packets = map(Path, sys.argv[1:5])
    key1 = list(csv.DictReader((analysis / "labeling" / "key-PRIVATE.csv").open()))
    rng = random.Random(SEED)
    rows = key1[:]
    rng.shuffle(rows)
    guide = (packets / "loi" / "HUONG-DAN.md").read_text()
    guide = guide.replace("## 5. Quy tắc làm việc", ADDENDUM.strip() + "\n\n## 5. Quy tắc làm việc")
    out = packets / "round2"
    if out.exists():
        raise SystemExit(f"{out} exists; refusing to overwrite")
    key2 = []
    for rater in ("loi", "bao"):
        base = out / rater
        base.mkdir(parents=True)
        (base / "HUONG-DAN.md").write_text(guide)
        with (base / f"sheet-{rater}-vong2.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["unit_id", "label", "note"])
            for row in rows:
                code = "v" + hashlib.sha256(f"{SEED}:{row['unit']}".encode()).hexdigest()[:8]
                src = packets / "loi" / row["unit_id"]
                d = base / code
                shutil.copytree(src, d)
                (d / "hidden-tests").mkdir()
                for name, text in hidden_tests(repo, tasks / row["task_id"] / "task.toml").items():
                    (d / "hidden-tests" / name).write_text(text)
                w.writerow([code, "", ""])
                if rater == "loi":
                    key2.append({"code2": code, **row})
    with (analysis / "labeling" / "key-round2-PRIVATE.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(key2[0]))
        w.writeheader()
        w.writerows(key2)
    print(f"{len(key2)} units x2 -> {out}")


if __name__ == "__main__":
    main()
