"""Check that every number on the slides comes from docs/report/generated/numbers.json (or its tables).

Usage: python3 check_numbers.py vipharmind-slides.pptx [--final]

Reads the text of every slide (not the notes) and reports each number that is neither a value in
numbers.json, nor a number in the generated results_*.tex tables, nor a fixed design constant listed in
ALLOW. Also counts the [CHỜ KẾT QUẢ] placeholders per slide; with --final any placeholder is an error (deck ready to present only when this passes).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from pptx import Presentation

HERE = Path(__file__).resolve().parent
NUMBERS = json.loads((HERE.parent / "report" / "generated" / "numbers.json").read_text(encoding="utf-8"))
PENDING = "[CHỜ KẾT QUẢ]"

# Fixed design constants and labels, not results. Each needs a reason.
ALLOW = {
    "1": "one commit per small task (design)",
    "2": "two arms (design)",
    "3": "three repetitions (design)",
    "4": "four cohorts (design)", "5": "step number on the prereg timeline", "324,5": "GitHub stars of obra/superpowers, checked 2026-11-23",
    "95": "95% confidence interval (prereg)",
    "01": "list numbering", "02": "list or section numbering", "03": "list numbering", "04": "list numbering",
    "5.5": "model version Claude Sonnet/Opus 5.5", "5.2": "model version Fable 5.2",
    "3.8": "model version Gemini 3.8", "6": "model name gpt-6-luna",
    "2.1.325": "tool version Claude Code", "1.5.9": "tool version Antigravity CLI",
    "0.162.1": "tool version Codex CLI", "1.1": "tag name prereg-v1.1",
    "5421": "course code IT5421", "20252778": "student ID", "20252781": "student ID",
    "20251227": "student ID",
    "1.2": "tag name prereg-v1.2",
    "306": "E2 checklist items (prereg-v1.2)", "30": "E2 brief prompt word limit (prereg-v1.2)",
    "24": "E2 human-check sample (prereg-v1.2)",
}
TOKEN = re.compile(r"\d+(?:[.,]\d+)*")
# Numbers in the report's generated tables (cost per pass and the like), built from the same summary.json.
TABLES = HERE.parent / "report" / "generated" / "tables"
VALUES = {v for v in NUMBERS.values() if v is not None} | {t for f in TABLES.glob("results_*.tex") for t in TOKEN.findall(f.read_text("utf-8"))}


def slide_text(slide) -> str:
    parts = []
    for shape in slide.shapes:
        parts.extend(_shape_text(shape))
    return "\n".join(parts)


def _shape_text(shape):
    if shape.shape_type == 6:  # group
        for s in shape.shapes:
            yield from _shape_text(s)
    if getattr(shape, "has_text_frame", False) and shape.has_text_frame:
        yield shape.text_frame.text
    if getattr(shape, "has_table", False) and shape.has_table:
        for row in shape.table.rows:
            for cell in row.cells:
                yield cell.text


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    final = "--final" in sys.argv
    prs = Presentation(args[0] if args else str(HERE / "vipharmind-slides.pptx"))
    bad, pending = [], {}
    for i, slide in enumerate(prs.slides, 1):
        text = slide_text(slide)
        if PENDING in text:
            pending[i] = text.count(PENDING)
        for tok in TOKEN.findall(text):
            if tok in VALUES or tok in ALLOW:
                continue
            # dates such as 2026-07-23 are values in numbers.json; their parts are fine
            if any(tok in v and "-" in v for v in VALUES):
                continue
            bad.append((i, tok))
    for i, tok in bad:
        print(f"slide {i}: number {tok!r} not in numbers.json or ALLOW")
    total = sum(pending.values())
    print(f"placeholders {PENDING}: {total} on slides {sorted(pending)}")
    if bad:
        print(f"FAIL: {len(bad)} unsourced number(s)")
        return 1
    if final and total:
        print("FAIL: placeholders remain (--final)")
        return 1
    print("OK: every number on the slides is in numbers.json or ALLOW")
    return 0


if __name__ == "__main__":
    sys.exit(main())
