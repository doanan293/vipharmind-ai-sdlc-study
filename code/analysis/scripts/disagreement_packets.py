"""Packets for the human-vs-judge disagreement review of the E2 hand check (descriptive, after kappa).

usage: python disagreement_packets.py KEY_CSV PACKETS_DIR SHEET_LOI SHEET_BAO OUT_DIR

Every checklist item where Lợi or Bảo gave a different verdict from the judge goes on one shared sheet,
with the item text, the three verdicts and the judge's one-line reason. Both raters review all items
independently and pick a cause. Units keep their hand-check codes (the arm stays hidden); judge reasons
that mention design/plan files are redacted so the arm cannot be read off them.
"""

import csv
import json
import re
import sys
from pathlib import Path

LEAK = re.compile(r"\b(design|plan|spec|vibe)(\.md)?\b", re.IGNORECASE)

GUIDE = """# Xem lại chỗ lệch giữa người chấm và máy chấm (E2)

Sheet `sheet-lech-<tên>.csv` liệt kê mọi mục mà Lợi hoặc Bảo chấm khác người chấm máy (Fable 5.2). Mỗi
dòng có: mã lượt, số mục, nội dung mục, kết quả của Lợi, của Bảo, của máy, và lý do máy ghi. Bài làm của
lượt nằm trong thư mục cùng mã ở gói chấm tay cũ (`brief.md`, `change.diff`, `checklist.md`).

Với mỗi dòng, đọc lại bản vá và chọn **một** nguyên nhân ở cột `nguyen_nhan`:

- `may_khat_khe`: máy đòi chặt hơn điều mục ghi; người chấm đúng.
- `nguoi_bo_sot`: người chấm bỏ sót hoặc đọc nhầm bản vá; máy đúng.
- `muc_mo_ho`: câu chữ của mục cho phép hiểu hai cách; cả hai cách đều có lý.
- `kho_kiem_tu_diff`: chỉ đọc diff không đủ để quyết (cần chạy mã hoặc xem mã ngoài diff).
- `khac`: lý do khác, ghi rõ trong `ghi_chu`.

Cột `ghi_chu`: một câu, ví dụ "mục đòi audit khi lỗi, bản vá có ghi audit ở nhánh except".

Làm một mình, không bàn với người kia cho tới khi cả hai nộp. Khoảng 3–5 phút mỗi dòng.
"""


def checklist_items(text: str) -> dict[int, str]:
    out = {}
    for line in text.splitlines():
        m = re.match(r"(\d+)\.\s+(.*)", line.strip())
        if m:
            out[int(m.group(1))] = re.sub(r"\s*\[exact\]", "", m.group(2))
    return out


def load(path: Path) -> dict[tuple[str, int], str]:
    with path.open(encoding="utf-8-sig") as f:
        return {(r["unit_code"], int(r["item_n"])): r["verdict"].strip() for r in csv.DictReader(f)}


def main() -> None:
    key_csv, packets, s_loi, s_bao, out = map(Path, sys.argv[1:6])
    loi, bao = load(s_loi), load(s_bao)
    rows = []
    for k in csv.DictReader(key_csv.open()):
        code = k["unit_code"]
        judge = json.loads((Path(k["root"]) / k["unit"] / "judge.json").read_text())
        items = checklist_items((packets / "loi" / code / "checklist.md").read_text())
        for it in judge["items"]:
            n, jv = int(it["n"]), str(it["verdict"])
            lv, bv = loi.get((code, n), ""), bao.get((code, n), "")
            if lv == jv and bv == jv:
                continue
            rows.append(
                {
                    "unit_code": code,
                    "item_n": n,
                    "noi_dung_muc": items.get(n, ""),
                    "loi": lv,
                    "bao": bv,
                    "may": jv,
                    "ly_do_may": LEAK.sub("[…]", str(it.get("reason", ""))),
                    "nguyen_nhan": "",
                    "ghi_chu": "",
                }
            )
    rows.sort(key=lambda r: (r["unit_code"], r["item_n"]))
    for rater in ("loi", "bao"):
        d = out / rater
        if d.exists():
            raise SystemExit(f"{d} exists; refusing to overwrite")
        d.mkdir(parents=True)
        (d / "HUONG-DAN.md").write_text(GUIDE)
        with (d / f"sheet-lech-{rater}.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    print(f"{len(rows)} items -> {out}")


if __name__ == "__main__":
    main()
