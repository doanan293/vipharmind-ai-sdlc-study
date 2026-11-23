"""Build the round-trip page set of the presentation from template-vi.pptx.

Run through build.sh. Reads the round-trip workspace that ppt-master's pptx_to_svg.py --roundtrip made
from template-vi.pptx (docs/presentation/deck/), copies the chosen template slides under new page names,
rewrites their text, adds the few new objects, and writes page_plan.json, notes/*.md and rehearsal.md.
Every number on a slide comes from docs/report/generated/numbers.json through N[...]. Results that the
analysis has not produced yet are the literal PENDING marker, so check_numbers.py can count them.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from lxml import etree

HERE = Path(__file__).resolve().parent
WS = HERE / "deck"
SVG_DIR = WS / "authoring-svg-flat"
NUMBERS = HERE.parent / "report" / "generated" / "numbers.json"
LOGO = HERE.parent / "report" / "images" / "logo-hust.png"
SVGNS = "http://www.w3.org/2000/svg"
PENDING = "[CHỜ KẾT QUẢ]"

N = json.loads(NUMBERS.read_text(encoding="utf-8"))
# The main analysis (Sonnet, Opus, Codex; detailed prompts). Values the report did not export to numbers.json
# (cost per pass, verdict counts) are read here; check_numbers.py also accepts the report's generated tables.
SUMMARY = json.loads((HERE.parents[1] / "data" / "results" / "analysis" / "main" / "summary.json").read_text(encoding="utf-8"))
FIGURES = HERE.parent / "report" / "generated" / "figures"


def m(v: str) -> str:
    """numbers.json value with a typographic minus sign."""
    return v.replace("-", "−")


def ci(lo: str, hi: str) -> str:
    return f"[{m(lo)}; {m(hi)}]"


def nv(key: str) -> str:
    """numbers.json value, or the PENDING marker while the source (E1, E2) is missing."""
    v = N.get(key)
    return PENDING if v is None else v


def sg(key: str) -> str:
    """Signed value (+x / −x) for differences; PENDING while missing."""
    v = N.get(key)
    if v is None:
        return PENDING
    return m(v) if v.startswith("-") else ("+" + v if v.strip("0,") else v)


def ci_n(lo: str, hi: str) -> str:
    return PENDING if N.get(lo) is None or N.get(hi) is None else ci(N[lo], N[hi])


def usd(cohort: str, tier: str, arm: str) -> str:
    """Cost per pass in USD as in the report's cost table; Codex as lower–upper bound."""
    est = SUMMARY["estimates"]
    lo = est[f"cost_eff.{cohort}.{tier}.{arm}.cost_per_pass"]["estimate"]
    out = f"{lo:.2f}".replace(".", ",")
    if cohort == "codex-luna":
        hi = est[f"cost_eff_upper.{cohort}.{tier}.{arm}.cost_per_pass"]["estimate"]
        out += "–" + f"{hi:.2f}".replace(".", ",")
    return out


def verdict_count(prefix: str, value: str) -> tuple[int, int]:
    cells = [v for k, v in SUMMARY["verdicts"].items() if k.startswith(prefix)]
    return sum(v == value for v in cells), len(cells)

BLUE = "#0C0A9E"
INK = "#1D1D1D"
PURPLE = "#8208D5"
ORANGE = "#EB9109"
MONO = "'IBM Plex Mono', monospace"
SANS = "'Be Vietnam Pro', sans-serif"


# ---------------------------------------------------------------- SVG helpers


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


ROLES = {
    "title": (MONO, BLUE, True),
    "num": (MONO, BLUE, True),
    "numo": (MONO, ORANGE, True),
    "body": (SANS, INK, False),
    "head": (MONO, INK, True),
}


def set_text(root, sid: str, lines: list[str], size: float | None = None, y: float | None = None,
             role: str | None = None):
    """Replace the text of one imported text frame, keeping the frame and its shape id.

    The frame stops being a layout placeholder (its text would otherwise inherit the layout's hanging
    indent), so font, colour and weight are written explicitly from the template's look: titles in IBM
    Plex Mono bold blue, labels in IBM Plex Mono bold, body text in Be Vietnam Pro.
    """
    g = root.find(f".//{{{SVGNS}}}g[@id='{sid}']")
    if g is None:
        raise SystemExit(f"no shape {sid}")
    ph = g.get("data-ph-type")
    texts = g.findall(f".//{{{SVGNS}}}text")
    t = texts[0]
    if role is None:
        if ph in ("title", "ctrTitle"):
            role = "title"
        elif "Plex Mono" in (t.get("font-family") or ""):
            role = "head"
        else:
            role = "body"
    family, fill, bold = ROLES[role]
    for el in g.iter():
        for a in ("data-ph-type", "data-pptx-placeholder-index", "data-pptx-placeholder-local-geometry",
                  "data-pptx-placeholder-size", "data-pptx-placeholder-orientation"):
            el.attrib.pop(a, None)
    for extra in texts[1:]:
        extra.getparent().remove(extra)
    run = {"fill-opacity": "1", "font-style": "normal", "text-decoration": "none"}
    old_size = float(t.get("font-size", "18.67"))
    new_size = size or old_size
    t.set("font-size", f"{new_size:g}")
    t.set("font-family", family)
    t.set("fill", fill)
    t.set("font-weight", "bold" if bold else "normal")
    if y is not None:
        t.set("y", f"{y:g}")
    for child in list(t):
        t.remove(child)
    t.text = None
    t.set("data-pptx-text-model", "lines")
    t.set("data-paragraph-line-height", f"{new_size * 1.38:.2f}")
    for i, line in enumerate(lines):
        if i == 0:
            outer = etree.SubElement(t, f"{{{SVGNS}}}tspan")
            inner = etree.SubElement(outer, f"{{{SVGNS}}}tspan", run)
            inner.text = line
        else:
            ts = etree.SubElement(t, f"{{{SVGNS}}}tspan", run)
            ts.set("data-paragraph-line-break", "1")
            ts.text = line


def delete(root, sid: str):
    g = root.find(f".//{{{SVGNS}}}g[@id='{sid}']")
    if g is None:
        raise SystemExit(f"no shape {sid}")
    g.getparent().remove(g)


def delete_icon_use(root, icon: str):
    for u in root.iter(f"{{{SVGNS}}}use"):
        if u.get("data-icon") == icon:
            u.getparent().remove(u)
            return
    raise SystemExit(f"no icon use {icon}")


def text_block(gid, x, y, w, h, lines, size=16.0, fill=INK, bold=False, family=SANS, lead=1.45):
    """A new bounded text group: one paragraph per line item, all in one text frame."""
    base = y + size
    weight = "bold" if bold else "normal"
    parts = [f'<g id="{gid}" data-pptx-bounds="{x:g} {y:g} {w:g} {h:g}">',
             f'<text x="{x:g}" y="{base:g}" font-family="{family}" font-size="{size:g}" '
             f'font-weight="{weight}" fill="{fill}">{esc(lines[0])}']
    for line in lines[1:]:
        parts.append(f'<tspan x="{x:g}" dy="{size * lead:g}">{esc(line)}</tspan>')
    parts.append("</text></g>")
    return "".join(parts)


def add(root, fragment: str):
    el = etree.fromstring(f'<svg xmlns="{SVGNS}">{fragment}</svg>')
    for child in el:
        root.append(child)


def title_block(gid, text, x=75.59, y=46.72, w=808.82):
    return text_block(gid, x, y + 8, w, 52, [text], size=28, fill=BLUE, bold=True, family=MONO)


# ---------------------------------------------------------------- figure slots


def figure_png(name: str, figure: str):
    """Render a figure of the report (generated/figures/*.pdf) to the PNG the slide shows."""
    out = WS / "images" / name
    subprocess.run(["pdftoppm", "-r", "300", "-png", "-singlefile", str(FIGURES / figure), str(out.with_suffix(""))],
                   check=True)


def figure_slot(gid, href, x=380, y=70, w=550, h=400):
    return (f'<g id="{gid}" data-pptx-bounds="{x} {y} {w} {h}">'
            f'<image href="../images/{href}" x="{x}" y="{y}" width="{w}" height="{h}" '
            f'preserveAspectRatio="xMidYMid meet"/></g>')




def say(key: str) -> str:
    """numbers.json value as it is read aloud in the notes: "âm 2,2", "0" for "0,0", "81" for "81,0"."""
    v = N[key]
    if "," in v and not v.split(",")[1].strip("0"):
        v = v.split(",")[0]
    if v.startswith("-"):
        v = v[1:]
        return "0" if v == "0" else "âm " + v
    return v


# ---------------------------------------------------------------- pages
# Each page: stem, template slide, part of the talk, seconds, edit function, notes (spoken prose only).
# The presenter is not assigned yet, so notes are speaker-neutral ("nhóm em", "em"); team members are
# named only for their work. build adds the timing cue ("Khoảng ba mươi giây.") in front of each note.

PAGES: list[dict] = []
OPEN, METHOD, RESULTS, CLOSE, BACKUP = "Mở đầu", "Phương pháp", "Kết quả", "Kết luận", "Dự phòng"
PARTS = (OPEN, METHOD, RESULTS, CLOSE)


def page(stem, src, part, secs, notes):
    def deco(fn):
        PAGES.append(dict(stem=stem, src=src, part=part, secs=secs, edit=fn, notes=notes))
        return fn
    return deco


@page("p01_title", 1, OPEN, 20,
      f"Em chào thầy và các bạn. Nhóm em gồm An, Lợi và Bảo. Đề tài hỏi: bắt trợ lý lập trình AI làm theo "
      f"đặc tả có bù được cho đề bài ngắn kiểu vibe coding không. Trước hết là phương pháp.")
def _(r):
    set_text(r, "shape-1431", ["Phát triển theo đặc tả", "so với vibe coding"], size=46, role="title")
    set_text(r, "shape-1430", ["Nghiên cứu tình huống và thực nghiệm đối chứng trên",
                               "một dự án phần mềm AI cho ngành dược Việt Nam"], size=17, y=380)
    add(r, '<g id="school" data-pptx-bounds="124 18 520 58">'
           '<image href="../images/logo-hust.png" x="124" y="20" width="36" height="53"/>'
           f'<text x="172" y="40" font-family="{MONO}" font-size="15" font-weight="bold" fill="{BLUE}">'
           'Đại học Bách khoa Hà Nội</text>'
           f'<text x="172" y="64" font-family="{SANS}" font-size="14" fill="{INK}">'
           'Chuyên đề nghiên cứu 1 · IT5421</text></g>')
    add(r, text_block("members", 124, 432, 530, 80,
                      ["Giảng viên: TS. Nguyễn Thanh Hùng",
                       "Doãn Văn An (20252778M) · Lê Xuân Lợi (20252781M)",
                       "Trần Ngọc Bảo (20251227M)"], size=14, lead=1.5))


@page("p02_part1", 4, METHOD, 10,
      f"Phần một gồm bối cảnh, các nghiên cứu liên quan, kết quả hồi cứu trên lịch sử git của dự án, và "
      f"thiết kế thí nghiệm.")
def _(r):
    set_text(r, "shape-1483", ["01"], role="num")
    set_text(r, "shape-1491", ["Phương pháp"], role="title")
    set_text(r, "shape-1484", ["Bối cảnh, nghiên cứu liên quan, thiết kế"])


@page("p03_motivation", 7, METHOD, 40,
      f"Coding agent tự đọc mã, sửa file, chạy test. Phổ biến nhất là vibe coding: vài câu ngắn, phần đề bỏ "
      f"ngỏ thì agent tự đoán. Phát triển theo đặc tả, kiểu bộ skill Superpowers, hứa bù chỗ đó: agent viết "
      f"thiết kế, kế hoạch, viết test trước rồi cài đặt và kiểm lại. Nhưng bằng chứng còn ít, chưa có thí "
      f"nghiệm nào chỉ đổi lời dặn rồi chấm bằng test mà agent không thấy. Nhóm em làm thí nghiệm đó, với "
      f"sáu câu hỏi sau.")
def _(r):
    set_text(r, "shape-1634", ["Đề ngắn và lời hứa của đặc tả"])
    set_text(r, "shape-1638", ["Vibe coding"])
    set_text(r, "shape-1637", ["Theo đặc tả"])
    set_text(r, "shape-1636", ["Vài câu ngắn; agent", "tự đoán phần đề", "bỏ ngỏ."], size=17)
    set_text(r, "shape-1635", ["Thiết kế → kế hoạch →", "test trước → kiểm lại", "(kiểu Superpowers)."], size=17)
    add(r, text_block("gap", 189, 405, 600, 60,
                      ["Câu hỏi: quy trình có bù được đề thiếu không?",
                       "Chưa có thí nghiệm chỉ đổi lời dặn, chấm bằng test ẩn."],
                      size=16, fill=BLUE, bold=True))


@page("p04_rq", 11, METHOD, 40,
      f"Sáu câu hỏi chốt trước. RQ1, RQ2 là hồi cứu: AI tham gia từng khâu ra sao, mã AI viết phải sửa lại "
      f"bao nhiêu. RQ3 đến RQ6 là thực nghiệm: đặc tả có đạt hơn vibe, tốn thêm bao nhiêu, và kết luận có "
      f"giữ khi đổi công cụ, đổi mô hình, khi nhiệm vụ lớn dần. Để chấm bằng test ẩn, đề chính phải nêu đủ "
      f"tên hàm; đề ngắn để dành cho phần thăm dò. Trước đó, các nghiên cứu gần nhất đã làm gì.")
def _(r):
    set_text(r, "shape-1762", ["Sáu câu hỏi nghiên cứu"])
    grid = [("shape-1763", "shape-1759", "RQ1", ["AI tham gia từng khâu", "của dự án ra sao?"]),
            ("shape-1764", "shape-1760", "RQ2", ["Mã AI viết phải sửa", "lại ở đâu, bao nhiêu?"]),
            ("shape-1770", "shape-1767", "RQ3", ["Đặc tả có đạt hơn vibe,", "tốn thêm bao nhiêu?"]),
            ("shape-1769", "shape-1765", "RQ4", ["Kết luận có giữ khi", "đổi công cụ, đổi hãng?"]),
            ("shape-1761", "shape-1766", "RQ5", ["Mô hình mạnh hơn thì", "lợi ích đổi ra sao?"]),
            ("shape-1771", "shape-1768", "RQ6", ["Nhiệm vụ lớn dần thì", "khoảng cách đổi ra sao?"])]
    for head, body, h, b in grid:
        set_text(r, head, [h])
        set_text(r, body, b, size=16)


@page("p04b_related", 20, METHOD, 35,
      f"Bốn nghiên cứu gần nhất. Hill quan sát pull request mã nguồn mở: có tài liệu đặc tả cũng không ít lỗi "
      f"hơn, nhưng đó là quan sát. FeatBench của Chen và cộng sự chấm tác tử bằng test ẩn nhưng so mô hình với nhau. Mock và Russo "
      f"so bốn cách tương tác khi viết test trước. Agarwal và cộng sự phỏng vấn người làm nghề: đặc tả đáng tin "
      f"hơn nhưng tốn công. Nhóm em giữ nguyên tác tử, mô hình và đề, chỉ đổi lời dặn, rồi đo bằng test ẩn và "
      f"token. Từ đó có năm giả thuyết.")
def _(r):
    set_text(r, "shape-2122", ["Nghiên cứu liên quan"])
    rows = [("shape-2124", "shape-2123", "Hill", ["Quan sát PR mã nguồn mở: có đặc tả", "không ít lỗi hơn"]),
            ("shape-2127", "shape-2126", "Chen", ["FeatBench: test ẩn cho tính năng;", "so mô hình với nhau"]),
            ("shape-2130", "shape-2129", "Mock", ["Mock và Russo: bốn cách tương", "tác khi viết test trước"])]
    for head, body, h, b in rows:
        set_text(r, head, [h], size=22)
        set_text(r, body, b, size=16)
    set_text(r, "shape-2133", ["Agarwal"], size=22)
    set_text(r, "shape-2132", ["Phỏng vấn: đặc tả đáng tin hơn, tốn công.",
                               "Nhóm em: chỉ đổi lời dặn, đo test ẩn, token."], size=16)


@page("p05_hypotheses", 11, METHOD, 30,
      f"Năm giả thuyết cũng ghi trước. H1: đặc tả đạt nhiều hơn. H2: nhưng tốn token và thời gian hơn. H3: "
      f"ít lỗi tĩnh, ít hồi quy hơn. H4: giúp Sonnet nhiều hơn Opus. H5: lợi ích tăng theo cỡ nhiệm vụ. Phép "
      f"thử xác nhận duy nhất là H1 trên Sonnet, tầng nhỏ. Tiếp theo là dự án.")
def _(r):
    set_text(r, "shape-1762", ["Năm giả thuyết, chốt trước khi chạy"])
    grid = [("shape-1763", "shape-1759", "H1", ["Đặc tả có tỉ lệ đạt", "cao hơn vibe."]),
            ("shape-1764", "shape-1760", "H2", ["Đặc tả tốn token và", "thời gian hơn."]),
            ("shape-1770", "shape-1767", "H3", ["Đặc tả ít lỗi tĩnh,", "ít hồi quy hơn."]),
            ("shape-1769", "shape-1765", "H4", ["Đặc tả giúp Sonnet", "nhiều hơn giúp Opus."]),
            ("shape-1761", "shape-1766", "H5", ["Lợi ích tăng theo", "kích thước nhiệm vụ."]),
            ("shape-1771", "shape-1768", "Chính", ["H1 trên Sonnet, tầng", "nhỏ; còn lại là phụ."])]
    for head, body, h, b in grid:
        set_text(r, head, [h])
        set_text(r, body, b, size=16)


@page("p06_vipharmind", 14, METHOD, 30,
      f"Dự án là ViPharmind, trợ lý AI tra cứu thuốc do An xây dựng: backend tác tử bằng Python, ứng dụng "
      f"web, kho tri thức từ Dược thư Quốc gia. Kho mã có {N['Commits']} commit trong bốn tháng, "
      f"{N['CommitsFeat']} commit tính năng và {N['SpecPlanFiles']} file spec, plan. Lịch sử đó cho kết quả "
      f"hồi cứu sau.")
def _(r):
    add(r, text_block("kicker", 247.61, 14, 493, 52,
                      ["ViPharmind: trợ lý AI tra cứu thuốc", "AI tham gia mọi khâu, theo lời tác giả"],
                      size=16, fill=BLUE, bold=True, family=MONO, lead=1.4))
    set_text(r, "shape-1916", [f"{N['Commits']} commit"], role="num")
    set_text(r, "shape-1917", [f"từ {N['FirstDate']} đến {N['LastDate']}"])
    set_text(r, "shape-1918", [f"{N['CommitsFeat']} feat"], role="num")
    set_text(r, "shape-1919", ["commit thêm tính năng"])
    set_text(r, "shape-1920", [f"{N['SpecPlanFiles']} file"], role="num")
    set_text(r, "shape-1921", ["spec và plan trong lịch sử git"])


@page("p07_retro", 14, METHOD, 35,
      f"Hồi cứu có ba ý. {N['FeatWithPlanPct']} phần trăm commit tính năng, {N['FeatWithPlan']} trên "
      f"{N['CommitsFeat']}, có plan đi trước nêu đúng file. Quy tắc nối đúng {N['LinkCorrect']} trên "
      f"{N['LinkChecked']} lần An kiểm tay, hay nối thừa, nên đó là cận trên. Số commit sửa lại gần như bằng "
      f"nhau, {say('ReworkWithPlanMean')} khi có plan, {say('ReworkWithoutPlanMean')} khi không. Đây là quan "
      f"sát; nhân quả cần thực nghiệm.")
def _(r):
    add(r, text_block("kicker", 247.61, 14, 493, 52,
                      ["Kết quả hồi cứu (RQ1, RQ2)", f"{N['Commits']} commit, lịch sử git của ViPharmind"],
                      size=16, fill=BLUE, bold=True, family=MONO, lead=1.4))
    set_text(r, "shape-1916", [f"{N['FeatWithPlanPct']}%"], role="num")
    set_text(r, "shape-1917", [f"commit feat có plan đi trước ({N['FeatWithPlan']}/{N['CommitsFeat']})"],
             size=18)
    set_text(r, "shape-1918", [f"{N['LinkCorrect']}/{N['LinkChecked']}"], role="num")
    set_text(r, "shape-1919", ["quy tắc nối đúng khi kiểm tay"], size=18)
    set_text(r, "shape-1920", [f"{N['ReworkWithPlanMean']} ≈ {N['ReworkWithoutPlanMean']}"], role="num")
    set_text(r, "shape-1921", ["commit sửa lại: có plan ≈ không plan"], size=18)


@page("p08_arms", 24, METHOD, 25,
      f"Thực nghiệm có hai cách làm, chỉ khác lời dặn trước đề bài. Vibe: một câu, hãy cài đặt thay đổi sau. "
      f"Theo đặc tả: trong cùng phiên, viết file thiết kế, file kế hoạch, làm từng phần theo kiểu viết test "
      f"trước, rồi chạy cả bộ test. Không có người duyệt. Ba nhóm chạy như sau.")
def _(r):
    set_text(r, "shape-2217", ["Hai cách làm: chỉ khác lời dặn"])
    set_text(r, "shape-2220", ["Vibe coding"])
    set_text(r, "shape-2218", ["Một câu: “Implement the following change in this repository.”"], size=17)
    set_text(r, "shape-2221", ["Theo đặc tả"])
    set_text(r, "shape-2219", ["docs/design.md → docs/plan.md → làm từng phần,",
                               "viết test trước → chạy cả bộ test backend."], size=17)
    add(r, text_block("same", 75, 440, 600, 40,
                      ["Giống nhau: đề bài, mô hình, công cụ, giới hạn thời gian."],
                      size=16, fill=BLUE, bold=True))


@page("p09_cohorts", 9, METHOD, 40,
      f"Thí nghiệm chính có ba nhóm: Claude Code với Sonnet và với Opus, để so mô hình; Codex với mô hình "
      f"Luna của OpenAI, để so hãng. Antigravity với Gemini hết hạn mức ở {N['ResAgyDone']} trên "
      f"{N['ResRunsPerCohort']} lượt nên bị bỏ. Sau kết quả chính có thêm hai thăm dò: E1 là Haiku, đề chi "
      f"tiết; E2 là đề dưới ba mươi từ, bốn nhóm. Tiếp theo là nhiệm vụ.")
def _(r):
    set_text(r, "shape-1734", ["Ba nhóm chạy, agent mặc định"])
    set_text(r, "shape-1735", ["claude-sonnet"], size=22)
    set_text(r, "shape-1740", ["Claude Code 2.1.325", "Claude Sonnet 5.5"], size=16)
    set_text(r, "shape-1736", ["claude-opus"], size=22)
    set_text(r, "shape-1732", ["Claude Code 2.1.325", "Claude Opus 5.5"], size=16)
    set_text(r, "shape-1739", ["agy-gemini: bỏ"], size=22)
    set_text(r, "shape-1737", ["Gemini 3.8 Flash; hết hạn",
                               f"mức ở {N['ResAgyDone']}/{N['ResRunsPerCohort']} lượt, loại"], size=16)
    set_text(r, "shape-1733", ["codex-luna"], size=22)
    set_text(r, "shape-1738", ["Codex CLI 0.162.1", "gpt-6-luna"], size=16)
    add(r, text_block("stock", 189, 452, 640, 80,
                      ["Effort medium · HOME sạch: không skill, plugin, MCP",
                       "Thăm dò, thêm sau kết quả chính (prereg-v1.2): E1 Haiku 5.5, đề",
                       f"chi tiết; E2 đề ≤30 từ, không tên hàm, 4 nhóm."],
                      size=14, fill=BLUE, bold=True))


@page("p10_tiers", 25, METHOD, 40,
      f"Nhiệm vụ lấy từ commit thật, chia ba tầng: nhỏ {N['Tasks']} nhiệm vụ, một commit, "
      f"{N['TaskSrcLinesMin']} đến {N['TaskSrcLinesMax']} dòng; vừa {N['MediumTasks']} nhiệm vụ, hai đến ba "
      f"commit; lớn {N['FeatureTasks']} nhiệm vụ cỡ một tính năng. Ba nhóm, hai cách, ba lần lặp: "
      f"{N['ResRuns']} lượt. Thăm dò thêm {N['EOneRuns']} lượt Haiku và {N['ETwoBriefJudged']} lượt đề sơ "
      f"sài, chấm theo danh sách hành vi rút từ test ẩn; {N['ETwoHumanUnits']} lượt được chấm tay để kiểm máy "
      f"chấm. Còn đề chính thì chấm thế này.")
def _(r):
    set_text(r, "shape-2228", [f"Ba tầng nhiệm vụ, {N['ResRuns']} lượt"])
    cols = [("shape-2263", "shape-2259", "shape-2260", N["Tasks"], "Nhỏ",
             ["1 commit", f"{N['TaskSrcLinesMin']}–{N['TaskSrcLinesMax']} dòng"]),
            ("shape-2268", "shape-2261", "shape-2262", N["MediumTasks"], "Vừa",
             [f"{N['MediumCommitsMin']}–{N['MediumCommitsMax']} commit",
              f"{N['MediumSrcLinesMin']}–{N['MediumSrcLinesMax']} dòng"]),
            ("shape-2269", "shape-2264", "shape-2265", N["FeatureTasks"], "Lớn",
             [f"{N['FeatureCommitsMin']}–{N['FeatureCommitsMax']} commit",
              f"{N['FeatureSrcLinesMin']}–{N['FeatureSrcLinesMax']} dòng"]),
            ("shape-2270", "shape-2266", "shape-2267", N["ResRuns"], "Tổng",
             ["3 nhóm × 2 cách", "× 3 lần lặp", f"× {N['TasksMain']} nhiệm vụ"])]
    for num, head, body, k, h, b in cols:
        set_text(r, num, [k], role="numo")
        set_text(r, head, [h])
        set_text(r, body, b, size=17)
    add(r, text_block("explore", 75, 494, 820, 30,
                      [f"Thăm dò: E1 Haiku {N['EOneRuns']} lượt · E2 đề sơ sài {N['ETwoBriefJudged']} lượt "
                       f"(Codex dừng sớm), chấm theo danh sách hành vi, kiểm tay {N['ETwoHumanUnits']} lượt"],
                      size=13, fill=BLUE, bold=True))


@page("p11_grading", 19, METHOD, 30,
      f"Test ẩn là test commit gốc thêm vào: trượt ở mã nền, đạt ở bản gốc, agent không thấy. Một lượt đạt "
      f"khi mọi test ẩn đạt và không test cũ nào hỏng. Test cũ được đưa về bản gốc trước khi chấm, nên không "
      f"lách được. Cây mã không có lịch sử git hay spec, plan cũ. Mọi thứ được chốt trước.")
def _(r):
    set_text(r, "shape-2101", ["Chấm bằng test ẩn"])
    set_text(r, "shape-2104", ["Test ẩn"], role="head")
    set_text(r, "shape-2113", ["Trượt ở mã nền, đạt", "ở commit gốc; agent", "không thấy"], size=16)
    set_text(r, "shape-2105", ["Đạt"], role="head")
    set_text(r, "shape-2102", ["Mọi test ẩn đạt và", "không test cũ hỏng"], size=16)
    set_text(r, "shape-2108", ["Không lách"], role="head")
    set_text(r, "shape-2106", ["Test cũ đưa về bản", "gốc trước khi chấm"], size=16)
    set_text(r, "shape-2103", ["Không lộ"], role="head")
    set_text(r, "shape-2107", ["Không lịch sử git,", "không spec, plan cũ"], size=16)


@page("p12_prereg", 21, METHOD, 25,
      f"Để không chọn đề hay phép phân tích sau khi thấy số, thẻ git chốt trước tầng nhỏ, giả thuyết và kế "
      f"hoạch phân tích, rồi tầng vừa, tầng lớn, rồi mã phân tích, tất cả trước khi mở kết quả. Trước mỗi "
      f"thẻ, Fable, một tác tử AI riêng, phản biện độc lập. Dù vậy vẫn còn rủi ro.")
def _(r):
    set_text(r, "shape-2150", ["Chốt trước khi chạy"])
    steps = [("shape-2151", "shape-2147", "1 · v1", ["Tầng nhỏ, giả thuyết,", "kế hoạch phân tích"]),
             ("shape-2152", "shape-2148", "2 · Chạy", ["Chạy tầng nhỏ; chỉ", "xem trạng thái lượt"]),
             ("shape-2153", "shape-2149", "3 · v1.1", ["Chốt nhiệm vụ tầng", "vừa và tầng lớn"]),
             ("shape-2155", "shape-2154", "4 · Mã", ["Chốt mã phân tích", "trước khi mở"]),
             ("shape-2157", "shape-2156", "5 · Mở", ["Mở kết quả; thay", "đổi đều ghi lại"]),
             ("shape-2159", "shape-2158", "Mỗi thẻ", ["Fable 5.2 phản biện", "độc lập trước khi chốt"])]
    for head, body, h, b in steps:
        set_text(r, head, [h], size=20, role="head")
        top = body in ("shape-2147", "shape-2148", "shape-2149")
        set_text(r, body, b, size=16, y=(176 - 22 * len(b)) if top else None)


@page("p13_threats", 23, METHOD, 30,
      f"Hai rủi ro lớn nhất. Lộ lời giải, vì repo công khai: cây mã không có lịch sử git, mốc dữ liệu huấn "
      f"luyện của các mô hình chính đều trước commit đầu tiên, và lượt lộ đường dẫn tới repo gốc được tách "
      f"ra phân tích độ nhạy. Thiên vị khi chọn đề, chọn số: thứ tự đề xáo với hạt giống cố định. Sang kết "
      f"quả.")
def _(r):
    set_text(r, "shape-2199", ["Rủi ro và cách kiểm soát"])
    set_text(r, "shape-2204", ["Rủi ro"], role="head")
    set_text(r, "shape-2205", ["Kiểm soát"], role="head")
    set_text(r, "shape-2210", ["Rò rỉ lời giải"], size=22, role="head")
    set_text(r, "shape-2208", ["Repo công khai, lịch", "sử chứa lời giải"], size=16)
    set_text(r, "shape-2207", ["Thiên vị"], size=22, role="head")
    set_text(r, "shape-2209", ["Chọn đề, chọn số", "sau khi thấy kết quả"], size=16)
    set_text(r, "shape-2203", ["Cây sạch"], size=22, role="head")
    set_text(r, "shape-2201", ["Không lịch sử git;", "ghi upstream_urls"], size=16)
    set_text(r, "shape-2200", ["Chốt trước"], size=22, role="head")
    set_text(r, "shape-2202", ["Xáo đề, hạt cố định;", "thẻ git; độ nhạy"], size=16)


@page("p14_results", 4, RESULTS, 10,
      f"Phần hai: hai phát hiện khi đề đã chi tiết, và một câu hỏi mở khi đề chỉ một hai câu.")
def _(r):
    set_text(r, "shape-1483", ["02"], role="num")
    set_text(r, "shape-1491", ["Kết quả"], role="title")
    set_text(r, "shape-1484", ["Hai phát hiện, một câu hỏi mở"])


@page("p15_h1", 13, RESULTS, 45,
      f"Đây là phép thử xác nhận duy nhất: Sonnet, tầng nhỏ. Đặc tả đạt {N['ResHOneSpecPct']} phần trăm, "
      f"vibe {N['ResHOneVibePct']}, hiệu số {say('ResHOneEstPp')} điểm phần trăm, khoảng tin cậy chín mươi "
      f"lăm phần trăm từ {say('ResHOneLowPp')} đến {say('ResHOneHighPp')}. Khoảng chứa 0 nên H1 chưa kết "
      f"luận được. Cận trên bằng 0, nên dữ liệu không ủng hộ một lợi ích đáng kể, nhưng với {N['Tasks']} "
      f"nhiệm vụ chưa loại được một lợi ích nhỏ. Các phân tích độ nhạy cho cùng kết luận. Còn ở các nhóm và "
      f"tầng khác?")
def _(r):
    add(r, title_block("title", "H1 · Đặc tả có đạt nhiều hơn?", w=600))
    set_text(r, "shape-1856", [f"{m(N['ResHOneEstPp'])} đpt"], size=64, role="num")
    set_text(r, "shape-1857", ["Hiệu số tỉ lệ đạt (đặc tả − vibe), Sonnet, tầng nhỏ",
                               f"Đặc tả {N['ResHOneSpecPct']}% · vibe {N['ResHOneVibePct']}% · "
                               f"KTC 95% {ci(N['ResHOneLowPp'], N['ResHOneHighPp'])}"], size=18)
    add(r, text_block("verdict", 75, 420, 640, 75,
                      ["Kết luận: chưa kết luận được (KTC chứa 0).",
                       f"Cận trên {N['ResHOneHighPp']}: không ủng hộ lợi ích đáng kể;",
                       "chưa loại được một lợi ích nhỏ."],
                      size=16, fill=BLUE, bold=True))


@page("p16_rq4", 12, RESULTS, 40,
      f"Mỗi hàng là một nhóm ở một tầng; chấm là hiệu số, vạch ngang là khoảng tin cậy, đường dọc là 0. Với "
      f"Claude, hiệu số âm hoặc bằng 0 ở mọi tầng, trừ Sonnet tầng vừa, cộng {say('ResSonnetMediumDiffPp')} "
      f"điểm, từ 0 đến 20, chỉ tham khảo. Ô duy nhất được ủng hộ là Codex tầng lớn, "
      f"{N['ResCodexLargeSpecPct']} so với {N['ResCodexLargeVibePct']} phần trăm, nhưng chỉ ba nhiệm vụ, "
      f"khoảng co về một điểm, và là một trong {N['ResSecondaryComparisons']} phép so phụ không hiệu chỉnh. "
      f"Về chi phí và chất lượng:")
def _(r):
    delete_icon_use(r, "imported/flat_slide_12_ill01")
    set_text(r, "shape-1841", ["RQ4: đổi công cụ,", "kết luận có giữ?"], role="title")
    set_text(r, "shape-1842", ["Hiệu số tỉ lệ đạt theo", "nhóm và tầng, KTC 95%.", "",
                               "Claude: ≤ 0 ở mọi tầng,", "trừ Sonnet tầng vừa",
                               f"(+{N['ResSonnetMediumDiffPp']} đpt, tham khảo).", "",
                               "Codex: chỉ ô tầng lớn", f"“ủng hộ” ({N['ResCodexLargeSpecPct']}% so với "
                               f"{N['ResCodexLargeVibePct']}%),", "chỉ 3 nhiệm vụ."],
             size=16)
    add(r, figure_slot("figure", "slot_pass_diff_by_cohort.png"))


H3C_OK, H3C_ALL = verdict_count("H3c.", "supported")
H3A_BAD, _ = verdict_count("H3a.", "contrary")


@page("p17_h2h3", 14, RESULTS, 40,
      f"H2 được ủng hộ ở mọi ô: đặc tả tốn gấp {N['ResTokenRatioMin']} đến {N['ResTokenRatioMax']} lần "
      f"token, {N['ResWallRatioMin']} đến {N['ResWallRatioMax']} lần thời gian. H3 lẫn lộn: lỗi tĩnh có hai "
      f"ô trái giả thuyết; ở Codex tầng lớn, đặc tả không hỏng test cũ lượt nào, vibe hỏng "
      f"{N['ResCodexLargeRegVibePct']} phần trăm, nhưng chỉ ba nhiệm vụ. Chỉ số bảo trì không kém quá năm "
      f"điểm ở tám trên chín ô. Rõ nhất là test agent tự viết: khoảng ba phần tư lượt đặc tả để lại test, "
      f"vibe từ 0 đến {N['ResOpusVibeTestsAnyPct']} phần trăm.")
def _(r):
    add(r, text_block("kicker", 247.61, 14, 493, 52,
                      ["H2, H3 · Chi phí và chất lượng", "Đặc tả so với vibe, mọi nhóm và tầng"],
                      size=16, fill=BLUE, bold=True, family=MONO, lead=1.4))
    set_text(r, "shape-1916", [f"×{N['ResTokenRatioMin']}–{N['ResTokenRatioMax']} token"], size=44, role="num")
    set_text(r, "shape-1917", [f"Thời gian ×{N['ResWallRatioMin']}–{N['ResWallRatioMax']}; H2 ủng hộ ở mọi ô"],
             size=18)
    set_text(r, "shape-1918", [f"{N['ResCodexLargeRegSpecPct']}% / {N['ResCodexLargeRegVibePct']}%"],
             size=44, role="num")
    set_text(r, "shape-1919", ["Hồi quy, Codex tầng lớn (đặc tả / vibe);",
                               f"lỗi tĩnh: {H3A_BAD} ô trái với H3"], size=18)
    set_text(r, "shape-1920", [f"{H3C_OK}/{H3C_ALL} ô"], size=44, role="num")
    set_text(r, "shape-1921", ["Chỉ số bảo trì không kém hơn quá 5 điểm (H3)"], size=18)


@page("p18_h4", 23, RESULTS, 40,
      f"H4 ở tầng nhỏ: Sonnet đặc tả {N['ResSonnetSmallSpecPct']}, vibe {N['ResSonnetSmallVibePct']} phần "
      f"trăm; Opus {N['ResOpusSmallSpecPct']} và {N['ResOpusSmallVibePct']}. Cả hai hiệu số đều âm; hiệu của "
      f"hai hiệu số là cộng {say('ResHFourDiffOfDiffsPp')} điểm, từ {say('ResHFourDiffOfDiffsLowPp')} đến "
      f"{say('ResHFourDiffOfDiffsHighPp')}: chưa kết luận được. Sonnet đặc tả và Opus vibe cùng ước lượng "
      f"điểm, khoảng rộng, với {N['ResHFourCostRatioPct']} phần trăm chi phí; Sonnet vốn đã gần trần. Còn "
      f"theo kích thước?")
def _(r):
    set_text(r, "shape-2199", ["H4 · Sonnet và Opus, tầng nhỏ"])
    set_text(r, "shape-2204", ["Sonnet"], role="head")
    set_text(r, "shape-2205", ["Opus"], role="head")
    set_text(r, "shape-2210", ["Đặc tả"], size=22, role="head")
    set_text(r, "shape-2208", [f"{N['ResSonnetSmallSpecPct']}% đạt"], size=20)
    set_text(r, "shape-2207", ["Vibe"], size=22, role="head")
    set_text(r, "shape-2209", [f"{N['ResSonnetSmallVibePct']}% đạt"], size=20)
    set_text(r, "shape-2203", ["Đặc tả"], size=22, role="head")
    set_text(r, "shape-2201", [f"{N['ResOpusSmallSpecPct']}% đạt"], size=20)
    set_text(r, "shape-2200", ["Vibe"], size=22, role="head")
    set_text(r, "shape-2202", [f"{N['ResOpusSmallVibePct']}% đạt"], size=20)
    add(r, text_block("diff", 113, 462, 760, 50,
                      [f"Hiệu của hai hiệu số: +{N['ResHFourDiffOfDiffsPp']} đpt "
                       f"{ci(N['ResHFourDiffOfDiffsLowPp'], N['ResHFourDiffOfDiffsHighPp'])}: H4 chưa kết luận được.",
                       f"Sonnet đặc tả và Opus vibe: cùng ước lượng điểm ({N['ResHFourSonnetSpecOpusVibePp']} đpt, "
                       f"KTC rộng), {N['ResHFourCostRatioPct']}% chi phí."],
                      size=14, fill=BLUE, bold=True))


@page("p19_h5", 12, RESULTS, 35,
      f"Mỗi điểm là một nhiệm vụ: đậm là trung bình ba nhóm, nhạt là từng nhóm; trục ngang là số dòng bản vá "
      f"gốc. Tầng lớn trừ tầng nhỏ là cộng {say('ResHFiveEstPp')} điểm, từ {say('ResHFiveLowPp')} đến "
      f"{say('ResHFiveHighPp')}. Hệ số tương tác {say('ResHFiveCoef')} trên thang logit, từ "
      f"{say('ResHFiveCoefLow')} đến {say('ResHFiveCoefHigh')}. Cả hai chứa 0: H5 chưa kết luận được. Còn "
      f"chi phí:")
def _(r):
    delete_icon_use(r, "imported/flat_slide_12_ill01")
    set_text(r, "shape-1841", ["H5: lợi ích tăng", "theo kích thước?"], role="title")
    set_text(r, "shape-1842", ["Mỗi điểm: một nhiệm vụ.", "",
                               "Tầng lớn trừ tầng nhỏ:", f"+{N['ResHFiveEstPp']} đpt "
                               f"{ci(N['ResHFiveLowPp'], N['ResHFiveHighPp'])}", "",
                               "Tương tác (logit):", f"{N['ResHFiveCoef']} {ci(N['ResHFiveCoefLow'], N['ResHFiveCoefHigh'])}",
                               "", "Chưa kết luận được."], size=16)
    add(r, figure_slot("figure", "slot_effect_vs_size.png"))


@page("p20_cost", 20, RESULTS, 20,
      f"Chi phí quy đổi từ token theo giá API công khai, cho một lượt đạt. Với Claude, đặc tả đắt hơn ở mọi "
      f"ô; Sonnet tầng nhỏ {usd('claude-sonnet', 'small', 'spec')} so với {usd('claude-sonnet', 'small', 'vibe')} "
      f"đô, gấp đôi. Ở Codex tầng lớn, đặc tả lại rẻ hơn vì vibe gần như không đạt. Giờ là một ca cụ thể.")
def _(r):
    set_text(r, "shape-2122", ["Chi phí cho một lượt đạt (USD)"])
    rows = [("shape-2124", "shape-2123", "Sonnet", "claude-sonnet"),
            ("shape-2127", "shape-2126", "Opus", "claude-opus"),
            ("shape-2130", "shape-2129", "Codex", "codex-luna")]
    for head, body, h, c in rows:
        set_text(r, head, [h], size=22)
        set_text(r, body, [f"Nhỏ: đặc tả {usd(c, 'small', 'spec')} · vibe {usd(c, 'small', 'vibe')}",
                           f"Lớn: đặc tả {usd(c, 'large', 'spec')} · vibe {usd(c, 'large', 'vibe')}"], size=16)
    set_text(r, "shape-2133", ["Tóm lại"], size=22)
    set_text(r, "shape-2132", ["Claude: đặc tả đắt hơn ở mọi ô.",
                               "Codex tầng lớn: đặc tả rẻ hơn vì vibe ít đạt."], size=16)


@page("p21_case", 26, RESULTS, 40,
      f"Theo quy tắc chốt trước, đây là nhiệm vụ lớn của Sonnet có hiệu số trị tuyệt đối lớn nhất, âm 33 "
      f"điểm. Đặc tả không đạt lượt nào; lượt được chọn đạt {N['ResCaseSpecHidden']} trên "
      f"{N['ResCaseHiddenTotal']} test ẩn, {N['ResCaseSpecMin']} phút, {N['ResCaseSpecTokensM']} triệu "
      f"token. Vibe đạt một trên ba, lượt chọn {N['ResCaseVibeMin']} phút, {N['ResCaseVibeTokensM']} triệu. "
      f"Thiết kế {N['ResCaseDesignLines']} dòng, kế hoạch {N['ResCasePlanLines']} dòng, chốt kiểu trả về là "
      f"đối tượng, điều đề không nói, còn bản gốc trả mã. Test của agent cùng giả định nên đạt.")
def _(r):
    set_text(r, "shape-2285", ["Ca nghiên cứu: f15"])
    set_text(r, "shape-2287", ["Nhiệm vụ"], role="head")
    set_text(r, "shape-2286", ["Tập tài liệu có", "chủ, quyền xem.", "Tầng lớn, Sonnet;",
                               f"hiệu {m(N['ResCaseDiffPp'])} đpt."], size=15)
    set_text(r, "shape-2289", ["Hai lượt"], role="head")
    set_text(r, "shape-2288", [f"Đặc tả: {N['ResCaseSpecPassed']}/{N['ResCaseReps']} đạt;",
                               f"{N['ResCaseSpecHidden']}/{N['ResCaseHiddenTotal']} test ẩn;",
                               f"{N['ResCaseSpecMin']} phút;", f"{N['ResCaseSpecTokensM']} triệu token.", "",
                               f"Vibe: {N['ResCaseVibePassed']}/{N['ResCaseReps']} đạt;", "đủ test ẩn;",
                               f"{N['ResCaseVibeMin']} phút;", f"{N['ResCaseVibeTokensM']} triệu token."], size=15)
    set_text(r, "shape-2291", ["Thiết kế, kế hoạch", "AI viết"], role="head")
    set_text(r, "shape-2290", [f"Thiết kế {N['ResCaseDesignLines']} dòng, kế hoạch "
                               f"{N['ResCasePlanLines']} dòng,",
                               f"{N['ResCasePlanTasks']} task. Thiết kế chốt kiểu trả về",
                               "là đối tượng; bản gốc trả mã."], size=16)
    set_text(r, "shape-2293", ["Chỗ sai, test trượt"], role="head")
    set_text(r, "shape-2292", ["Test của tác tử theo cùng giả định",
                               "nên đạt; test ẩn trượt, except nuốt lỗi."], size=16)


@page("p22_labels", 6, RESULTS, 35,
      f"Phát hiện thứ hai từ gán nhãn. Lợi và Bảo gán độc lập {N['LabRuns']} lượt hỏng của Claude, đồng ý "
      f"{N['LabAgree']}. {N['LabOutside']} trên {N['LabRuns']} lượt hỏng vì đề không nêu chi tiết, "
      f"{N['LabDeBaiThieuTotal']} lượt, hoặc dùng sai mã có sẵn, {N['LabSaiApiCoSanTotal']} lượt; chỉ "
      f"{N['LabLoiLogicTotal']} lượt là lỗi logic. Tỉ lệ như nhau ở hai cách, {N['LabOutsideSpecPct']} và "
      f"{N['LabOutsideVibePct']} phần trăm: thiết kế chỉ chốt một cách đoán. Vậy nếu đề còn ngắn hơn?")
def _(r):
    set_text(r, "shape-1622", [f"{N['LabOutside']}/{N['LabRuns']} lượt hỏng:", "đề không nêu chi tiết,",
                               "hoặc dùng sai mã có sẵn"], size=32)
    set_text(r, "shape-1621",
             [f"Như nhau ở hai cách làm: {N['LabOutsideSpecPct']}% / {N['LabOutsideVibePct']}%"],
             size=20, role="title")


@page("p23_explore", 14, RESULTS, 40,
      f"E2 là thăm dò, thêm sau kết quả chính; Codex dừng ở tầng nhỏ. Bỏ chi tiết đề, điểm hành vi giảm "
      f"{say('ETwoXScoreShiftSpec')} điểm ở đặc tả, {say('ETwoXScoreShiftVibe')} ở vibe; đạt hết test ẩn "
      f"giảm khoảng tám mươi, phần lớn vì test gọi tên đề không nêu. Với đề sơ sài, đặc tả hơn vibe "
      f"{say('ETwoPooledSmallPp')} điểm ở tầng nhỏ, từ {say('ETwoPooledSmallLowPp')} đến "
      f"{say('ETwoPooledSmallHighPp')}; gộp mọi tầng "
      f"{say('ETwoPooledAllPp')}, khoảng chứa 0. E1 với Haiku: {N['EOneSmallSpecPct']} so với "
      f"{N['EOneSmallVibePct']} phần trăm, {N['EOneSmallSpecTokensM']} so với {N['EOneSmallVibeTokensM']} "
      f"triệu, cùng hướng.")
def _(r):
    add(r, text_block("kicker", 247.61, 14, 600, 52,
                      ["Câu hỏi mở: đề chỉ một hai câu thì sao?", "E1, E2: thăm dò, thêm sau kết quả chính"],
                      size=16, fill=BLUE, bold=True, family=MONO, lead=1.4))
    set_text(r, "shape-1916", [f"−{nv('ETwoXScoreShiftSpec')} / −{nv('ETwoXScoreShiftVibe')}"], size=36,
             role="num")
    set_text(r, "shape-1917", ["E2 · bỏ chi tiết đề: điểm danh sách giảm (đpt), đặc tả / vibe",
                               f"Đạt hết test ẩn giảm {nv('ETwoXPassShiftSpec')} / {nv('ETwoXPassShiftVibe')} đpt,",
                               "phần lớn vì test gọi tên mà đề không nêu"],
             size=15)
    set_text(r, "shape-1918", [f"{sg('ETwoPooledSmallPp')} đpt"], size=40, role="num")
    set_text(r, "shape-1919", ["E2 · đề sơ sài, tầng nhỏ: điểm danh sách, đặc tả − vibe",
                               f"KTC {ci_n('ETwoPooledSmallLowPp', 'ETwoPooledSmallHighPp')} · Sonnet "
                               f"{sg('ETwoSonnetSmallPp')} · gộp mọi tầng {sg('ETwoPooledAllPp')} "
                               f"{ci_n('ETwoPooledAllLowPp', 'ETwoPooledAllHighPp')}"], size=15)
    e1 = N.get("EOneSmallSpecPct") is not None
    set_text(r, "shape-1920", [f"{nv('EOneSmallSpecPct')}/{nv('EOneSmallVibePct')}%" if e1 else PENDING],
             size=40, role="num")
    set_text(r, "shape-1921", ["E1 · Haiku, đề chi tiết, tầng nhỏ: tỉ lệ đạt đặc tả / vibe;",
                               f"token mỗi lượt {nv('EOneSmallSpecTokensM')} / {nv('EOneSmallVibeTokensM')} triệu"],
             size=16)


@page("p24_limits", 8, RESULTS, 25,
      f"Ba hạn chế. Một dự án Python, đặc tả tự động không người duyệt. Đề do AI soạn, nhóm duyệt; test ẩn "
      f"viết cho bản gốc vốn làm theo đặc tả. Tầng vừa chỉ {N['MediumTasks']}, tầng lớn {N['FeatureTasks']} "
      f"nhiệm vụ, nên chỉ để tham khảo. Để kết lại.")
def _(r):
    set_text(r, "shape-1666", ["Hạn chế"])
    set_text(r, "shape-1671", ["Phạm vi"])
    set_text(r, "shape-1668", ["Một dự án Python;", "đặc tả tự động,", "không người duyệt"], size=16)
    set_text(r, "shape-1672", ["Đề bài"])
    set_text(r, "shape-1669", ["AI soạn, nhóm duyệt;", "test ẩn viết cho", "bản gốc"], size=16)
    set_text(r, "shape-1667", ["Cỡ mẫu"])
    set_text(r, "shape-1670", [f"Tầng vừa {N['MediumTasks']}, lớn {N['FeatureTasks']}",
                               "nhiệm vụ: chỉ để", "tham khảo"], size=16)


@page("p25_conclusion", 7, CLOSE, 40,
      f"Tóm lại. Khi đề đã chi tiết, quy trình đặc tả tốn gấp {N['ResTokenRatioMin']} đến "
      f"{N['ResTokenRatioMax']} lần token mà không cho thấy đạt nhiều hơn. {N['LabOutside']} trên "
      f"{N['LabRuns']} lượt hỏng đến từ chi tiết đề không nêu hoặc sai mã có sẵn, ở cả hai cách. Khi đề sơ "
      f"sài, quy trình có thể bù một phần ở việc nhỏ, {say('ETwoPooledSmallPp')} điểm, rõ nhất với Sonnet, "
      f"nhưng không thay được thông tin đề thiếu; đây là thăm dò. Vì vậy nên viết đề rõ trước.")
def _(r):
    set_text(r, "shape-1634", ["Kết luận"])
    set_text(r, "shape-1638", ["Đề chi tiết"])
    set_text(r, "shape-1636", [f"Đặc tả tốn ×{N['ResTokenRatioMin']}–{N['ResTokenRatioMax']}",
                               "token, không cho thấy", "đạt nhiều hơn."], size=17)
    set_text(r, "shape-1637", ["Lượt hỏng"])
    set_text(r, "shape-1635", [f"{N['LabOutside']}/{N['LabRuns']}: đề không nêu", "hoặc sai mã có sẵn;",
                               "như nhau ở hai cách."], size=17)
    add(r, text_block("next", 189, 392, 640, 80,
                      [f"Đề sơ sài (thăm dò): đặc tả có thể bù một phần ở việc",
                       f"nhỏ ({sg('ETwoPooledSmallPp')} đpt), rõ nhất với Sonnet, nhưng không thay",
                       "được thông tin đề thiếu. Nên viết đề rõ trước."],
                      size=15, fill=BLUE, bold=True))


@page("p26_thanks", 15, CLOSE, 10,
      f"Phần trình bày của nhóm em đến đây là hết. Em cảm ơn thầy và các bạn; nhóm em xin nhận câu hỏi.")
def _(r):
    set_text(r, "shape-1949", ["Xin cảm ơn!"], role="title")
    add(r, text_block("qa", 81, 345, 390, 50, ["Hỏi đáp"], size=20, fill=INK, bold=True))


@page("p27_bk_funnel", 21, BACKUP, 0,
      f"Slide dự phòng, chỉ dùng khi được hỏi cách chọn đề. Từ {N['Candidates']} commit tính năng chạm cả mã "
      f"và test, các tiêu chí tự động giữ lại {N['Eligible']} commit, rồi nhóm chọn {N['Tasks']} nhiệm vụ "
      f"bằng lấy mẫu phân tầng theo lớp mã với hạt giống cố định.")
def _(r):
    set_text(r, "shape-2150", ["Dự phòng: phễu chọn tầng nhỏ"])
    steps = [("shape-2151", "shape-2147", N["Candidates"], ["Commit feat chạm", "src và tests"]),
             ("shape-2152", "shape-2148", N["AfterCritOne"], ["Qua tiêu chí 1"]),
             ("shape-2153", "shape-2149", N["AfterCritFour"], ["Qua tiêu chí 4"]),
             ("shape-2155", "shape-2154", N["AfterCritFive"], ["Qua tiêu chí 5"]),
             ("shape-2157", "shape-2156", N["AfterCritTwo"], ["Qua tiêu chí 2:", "chạy test thật"]),
             ("shape-2159", "shape-2158", N["Tasks"], ["Chọn phân tầng", "theo lớp mã"])]
    for head, body, h, b in steps:
        set_text(r, head, [h], size=24, role="numo")
        top = body in ("shape-2147", "shape-2148", "shape-2149")
        set_text(r, body, b, size=16, y=(176 - 22 * len(b)) if top else None)


@page("p28_bk_reading", 24, BACKUP, 0,
      "Slide dự phòng, dùng khi được hỏi cách đọc kết quả. Đơn vị phân tích là nhiệm vụ. Khoảng tin cậy là "
      "bootstrap lấy mẫu lại nhiệm vụ. Nhóm không dựa vào ngưỡng p, và chỉ dùng ba cách đọc đã chốt trước: "
      "được ủng hộ, trái với giả thuyết, chưa kết luận được.")
def _(r):
    set_text(r, "shape-2217", ["Dự phòng: cách đọc kết quả"])
    set_text(r, "shape-2220", ["Ước lượng"])
    set_text(r, "shape-2218", ["Hiệu số tỉ lệ đạt (đặc tả − vibe) theo nhiệm vụ;",
                               "KTC 95% bootstrap lấy mẫu lại nhiệm vụ."], size=17)
    set_text(r, "shape-2221", ["Đọc kết quả"])
    set_text(r, "shape-2219", ["KTC nằm hẳn phía giả thuyết: được ủng hộ. Phía ngược",
                               "lại: trái với giả thuyết. Còn lại: chưa kết luận được."], size=17)


@page("p29_bk_labels", 24, BACKUP, 0,
      f"Slide dự phòng, dùng khi được hỏi về phân loại lỗi. Lợi và Bảo gán nhãn độc lập {N['LabRuns']} lượt "
      f"không đạt của hai nhóm Claude, ở vòng hai với hướng dẫn đã làm rõ thứ tự quyết định; vòng một bị loại "
      f"theo đề nghị của chính hai người gán vì điền chưa kỹ. Hai người đồng ý {N['LabAgree']} trên "
      f"{N['LabRuns']} lượt, kappa {N['LabKappa']}; An phân xử {N['LabAdjudicated']} lượt lệch. "
      f"{N['LabDeBaiThieuTotal']} lượt hỏng vì test ẩn kiểm chi tiết đề không nêu, {N['LabSaiApiCoSanTotal']} "
      f"lượt vì dùng sai mã có sẵn của dự án; chỉ {N['LabLoiLogicTotal']} lượt là lỗi logic. Tỉ lệ hai loại đầu "
      f"gần như nhau ở hai cách làm, {N['LabOutsideSpecPct']} và {N['LabOutsideVibePct']} phần trăm, nên quy "
      f"trình đặc tả không ngăn được chúng. Cả {N['LabHongChucNangCuTotal']} lượt làm hỏng chức năng cũ đều của "
      f"Opus. Fable gán thêm làm người chấm thứ ba, chỉ để đối chiếu: đồng ý với Lợi {N['LabFableAgreeLoi']} và "
      f"với Bảo {N['LabFableAgreeBao']} lượt.")
def _(r):
    set_text(r, "shape-2217", ["Dự phòng: nguyên nhân thất bại"])
    set_text(r, "shape-2220", ["Gán nhãn"])
    set_text(r, "shape-2218", [f"Lợi và Bảo gán độc lập {N['LabRuns']} lượt không đạt của hai",
                               "nhóm Claude; chín nhãn; An phân xử chỗ lệch."], size=17)
    set_text(r, "shape-2221", ["Kết quả"])
    set_text(r, "shape-2219", [f"Kappa của Cohen: {N['LabKappa']} (đồng ý {N['LabAgree']}/{N['LabRuns']})",
                               f"Đề thiếu {N['LabDeBaiThieuTotal']} · API có sẵn {N['LabSaiApiCoSanTotal']} · "
                               f"hỏng cũ {N['LabHongChucNangCuTotal']} · khác {N['LabOther']}",
                               f"Hai loại đầu: đặc tả {N['LabOutsideSpecPct']}%, vibe {N['LabOutsideVibePct']}%"],
             size=17)


@page("p30_attribution", 30, BACKUP, 0,
      "Slide ghi nguồn template Slidesgo, giữ lại theo điều kiện của bản miễn phí.")
def _(r):
    set_text(r, "shape-2412", ["Ghi nguồn"], role="title")
    set_text(r, "shape-2411", ["Mẫu slide: Slidesgo, Freepik", "Nhóm: Doãn Văn An, Lê Xuân Lợi,",
                               "Trần Ngọc Bảo"], size=20)
    for sid in ("shape-2413", "shape-2414", "shape-2417", "shape-2424"):  # ghi chú nội bộ, icon mạng xã hội của mẫu
        delete(r, sid)


# Result slots still pending: page -> what fills it. Every result is filled now; kept so a rebuild against
# an older numbers.json still lists what is missing.
RESULT_SLOTS: dict[str, str] = {}


# ---------------------------------------------------------------- build


def fmt_secs(s: int) -> str:
    return f"{s // 60}:{s % 60:02d}"


SECS_SPOKEN = {10: "mười", 15: "mười lăm", 20: "hai mươi", 25: "hai mươi lăm", 30: "ba mươi",
               35: "ba mươi lăm", 40: "bốn mươi", 45: "bốn mươi lăm", 50: "năm mươi", 55: "năm mươi lăm",
               60: "sáu mươi"}


def note_text(p: dict) -> str:
    """Speaker notes: a timing cue for timed pages, then the spoken script."""
    return f"Khoảng {SECS_SPOKEN[p['secs']]} giây. {p['notes']}" if p["secs"] else p["notes"]


def main():
    if not SVG_DIR.is_dir():
        sys.exit(f"missing workspace {SVG_DIR}; run build.sh")
    (WS / "images" / "logo-hust.png").write_bytes(LOGO.read_bytes())
    figure_png("slot_pass_diff_by_cohort.png", "pass_diff_by_cohort.pdf")
    figure_png("slot_effect_vs_size.png", "effect_vs_size.pdf")
    notes_dir = WS / "notes"
    notes_dir.mkdir(exist_ok=True)
    for old in SVG_DIR.glob("p[0-9][0-9]_*.svg"):
        old.unlink()
    for old in notes_dir.glob("*.md"):
        old.unlink()
    plan = []
    parser = etree.XMLParser(remove_blank_text=False, huge_tree=True)
    for p in PAGES:
        tree = etree.parse(str(SVG_DIR / f"slide_{p['src']:02d}.svg"), parser)
        p["edit"](tree.getroot())
        out = SVG_DIR / f"{p['stem']}.svg"
        tree.write(str(out), xml_declaration=True, encoding="utf-8")
        (notes_dir / f"{p['stem']}.md").write_text(note_text(p) + "\n", encoding="utf-8")
        plan.append({"source_slide": p["src"], "svg": out.name})
    (WS / "page_plan.json").write_text(json.dumps(
        {"schema": "ppt-master.roundtrip-page-plan.v1", "pages": plan}, indent=2) + "\n", encoding="utf-8")

    rows, t = [], 0
    for i, p in enumerate(PAGES, 1):
        if p["secs"]:
            t += p["secs"]
            rows.append(f"| {i} | `{p['stem']}` | {p['part']} | {fmt_secs(p['secs'])} | {fmt_secs(t)} |")
        else:
            rows.append(f"| {i} | `{p['stem']}` | {p['part']} | – | – |")
    by = {s: sum(p["secs"] for p in PAGES if p["part"] == s) for s in PARTS}
    split = ", ".join(f"{s} {fmt_secs(v)}" for s, v in by.items())
    (HERE / "rehearsal.md").write_text(
        "# Tập dượt\n\n"
        "Sinh tự động bởi `build_deck.py`; sửa thời lượng ở đó rồi chạy lại `build.sh`.\n\n"
        f"Tổng thời gian nói: {fmt_secs(t)} ({split}); phần còn lại của 15 phút ({fmt_secs(900 - t)}) dành "
        "cho chuyển slide. Hỏi đáp 5 phút sau đó. Người thuyết trình chưa phân công: ghi chú viết trung tính "
        "(\"nhóm em\", \"em\"), một người hay nhiều người đọc đều được; nếu chia người, chuyển người ở đầu một "
        "phần. Câu \"Khoảng … giây.\" đầu mỗi ghi chú là nhắc giờ, không đọc thành tiếng.\n\n"
        "| Slide | Trang | Phần | Thời lượng | Cộng dồn |\n| --- | --- | --- | --- | --- |\n"
        + "\n".join(rows) + "\n\n## Số liệu\n\n"
        "Mọi số trên slide lấy từ `docs/report/generated/numbers.json`: thí nghiệm chính (Sonnet, Opus, Codex; "
        "đề chi tiết), nhãn nguyên nhân thất bại, E2 (đề sơ sài; thu thập đã kết thúc, Codex dừng ở tầng nhỏ) "
        "và E1 (Haiku). Làm mới bằng `code/refresh-interim.sh`. "
        + (f"Các slide sau còn `{PENDING}`:\n\n" + "\n".join(f"- `{k}`: {v}" for k, v in RESULT_SLOTS.items())
           if RESULT_SLOTS else "Không còn chỗ chờ kết quả.") + "\n", encoding="utf-8")
    print(f"pages={len(PAGES)} talk={fmt_secs(t)} {by}")


if __name__ == "__main__":
    main()
