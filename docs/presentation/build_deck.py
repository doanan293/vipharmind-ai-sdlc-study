"""Build the round-trip page set of the presentation from template-vi.pptx.

Run through build.sh. Reads the round-trip workspace that ppt-master's pptx_to_svg.py --roundtrip made
from template-vi.pptx (docs/presentation/deck/), copies the chosen template slides under new page names,
rewrites their text, adds the few new objects, and writes page_plan.json, notes/*.md and rehearsal.md.
Every number on a slide comes from docs/report/generated/numbers.json through N[...]. Results that the
analysis has not produced yet are the literal PENDING marker, so check_numbers.py can count them.
"""

from __future__ import annotations

import json
import re
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


# ---------------------------------------------------------------- pages
# Each page: stem, template slide, speaker, seconds, edit function, notes (spoken prose only).

PAGES: list[dict] = []


def page(stem, src, speaker, secs, notes):
    def deco(fn):
        PAGES.append(dict(stem=stem, src=src, speaker=speaker, secs=secs, edit=fn, notes=notes))
        return fn
    return deco


LOI, BAO = "Lê Xuân Lợi", "Trần Ngọc Bảo"


@page("p01_title", 1, LOI, 20,
      "Người nói: Lợi, khoảng hai mươi giây. Em chào thầy và các bạn. Nhóm em gồm An, Bảo và em, Lợi. "
      "Đề tài của nhóm hỏi: khi giao việc cho trợ lý lập trình AI, bắt nó làm theo đặc tả có bù được cho đề "
      "bài ngắn của vibe coding không; thí nghiệm trên một dự án phần mềm AI thật cho ngành dược. Em trình bày bối cảnh và phương pháp, Bảo trình bày "
      "kết quả và kết luận.")
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


@page("p02_part1", 4, LOI, 10,
      "Người nói: Lợi, khoảng mười giây. Phần một gồm bối cảnh, kết quả hồi cứu trên lịch sử git của "
      "ViPharmind, và cách nhóm thiết kế thí nghiệm.")
def _(r):
    set_text(r, "shape-1483", ["01"], role="num")
    set_text(r, "shape-1491", ["Phương pháp"], role="title")
    set_text(r, "shape-1484", ["Lê Xuân Lợi · vấn đề, hồi cứu, thiết kế"])


@page("p03_motivation", 7, LOI, 45,
      "Người nói: Lợi, khoảng bốn mươi lăm giây. Coding agent như Claude Code, Codex hay Antigravity tự đọc mã, "
      "sửa file và chạy test. Cách giao việc phổ biến nhất là vibe coding: vài câu ngắn rồi để agent viết mã "
      "ngay; đề ngắn bỏ ngỏ nhiều chi tiết và agent phải tự đoán. Phát triển theo đặc tả, kiểu bộ skill "
      "Superpowers, hứa bù cho chỗ đó: agent viết thiết kế, viết kế hoạch, viết test trước rồi mới cài đặt, và "
      "kiểm lại cả bộ test. Nhưng bằng chứng định lượng còn ít: nghiên cứu quan sát lớn nhất trên pull request "
      "mã nguồn mở không thấy đặc tả làm giảm lỗi, và chưa có thí nghiệm nào giữ nguyên đề, công cụ và mô hình, "
      "chỉ đổi lời dặn, rồi chấm bằng test mà agent không thấy. Nhóm em làm thí nghiệm đó.")
def _(r):
    set_text(r, "shape-1634", ["Đề ngắn, và lời hứa của đặc tả"])
    set_text(r, "shape-1638", ["Vibe coding"])
    set_text(r, "shape-1637", ["Theo đặc tả"])
    set_text(r, "shape-1636", ["Vài câu ngắn; agent", "tự đoán phần đề", "bỏ ngỏ."], size=17)
    set_text(r, "shape-1635", ["Thiết kế → kế hoạch →", "test trước → kiểm lại", "(kiểu Superpowers)."], size=17)
    add(r, text_block("gap", 189, 405, 600, 60,
                      ["Câu hỏi: quy trình có bù được đề thiếu không?",
                       "Chưa có thí nghiệm chỉ đổi lời dặn, chấm bằng test ẩn."],
                      size=16, fill=BLUE, bold=True))


@page("p04_rq", 11, LOI, 40,
      "Người nói: Lợi, khoảng bốn mươi giây. Đề tài có sáu câu hỏi, chốt trước khi chạy. RQ1 và RQ2 là phần hồi cứu: AI đã tham "
      "gia từng khâu của dự án ra sao, và mã AI viết phải sửa lại bao nhiêu. RQ3 đến RQ6 là phần thực "
      "nghiệm: làm theo đặc tả có đạt hơn vibe coding không và tốn thêm bao nhiêu; kết luận có giữ khi đổi "
      "công cụ của hãng khác; khi dùng mô hình mạnh hơn; và khi nhiệm vụ lớn dần. Để chấm được bằng test ẩn, đề "
      "của thí nghiệm chính phải nêu đủ tên và chữ ký, nên nó hỏi: khi đề đã chi tiết, quy trình còn thêm được "
      "gì. Câu hỏi về đề ngắn để dành cho hai thí nghiệm thăm dò ở cuối.")
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


@page("p05_hypotheses", 11, LOI, 40,
      "Người nói: Lợi, khoảng bốn mươi giây. Năm giả thuyết được ghi nguyên văn trước khi chạy. H1: làm "
      "theo đặc tả đạt nhiều hơn. H2: nhưng tốn token và thời gian hơn. H3: mã ít lỗi tĩnh, ít hồi quy hơn. "
      "H4: đặc tả giúp mô hình yếu hơn nhiều hơn. H5: lợi ích tăng theo kích thước nhiệm vụ. Phép thử xác "
      "nhận duy nhất là H1 trên Claude Sonnet ở tầng nhỏ; H5 là phép thử phụ quan trọng nhất, vì nó kiểm "
      "lập luận rằng viết thiết kế chỉ đáng khi việc đủ lớn.")
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


@page("p06_vipharmind", 14, LOI, 30,
      f"Người nói: Lợi, khoảng ba mươi giây. Dự án được nghiên cứu là ViPharmind, trợ lý AI tra cứu thuốc "
      f"cho người Việt do An xây dựng: backend tác tử AI bằng Python, ứng dụng web và kho tri thức từ Dược "
      f"thư Quốc gia. Kho mã có {N['Commits']} commit trong khoảng bốn tháng, {N['CommitsFeat']} commit tính "
      f"năng, và {N['SpecPlanFiles']} file spec, plan còn trong lịch sử git. Nhóm không đánh giá lại chất "
      f"lượng trả lời của ViPharmind; đối tượng đo là quá trình phát triển có AI tham gia.")
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


@page("p07_retro", 14, LOI, 45,
      f"Người nói: Lợi, khoảng bốn mươi lăm giây. Kết quả hồi cứu có ba ý. Một: {N['FeatWithPlanPct']} phần "
      f"trăm commit tính năng có một plan đi trước nêu đúng file mà commit chạm, tức quy trình đặc tả được "
      f"dùng thật. Hai: quy tắc nối commit với plan đúng {N['LinkCorrect']} trên {N['LinkChecked']} lần khi "
      f"An kiểm tay, sai lệch nghiêng về nối thừa, nên con số trên có thể hơi cao. Ba: số commit sửa lại "
      f"trong mười bốn ngày gần như bằng nhau giữa nhóm có plan và không có plan, {N['ReworkWithPlanMean']} so "
      f"với {N['ReworkWithoutPlanMean']}. Đây là quan sát, không phải nhân quả; câu hỏi nhân quả do thực "
      f"nghiệm trả lời.")
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


@page("p08_arms", 24, LOI, 35,
      "Người nói: Lợi, khoảng ba mươi lăm giây. Thí nghiệm có hai cách làm, chỉ khác lời dặn đặt trước đề "
      "bài. Lời dặn vibe coding chỉ có một câu: cài đặt thay đổi sau đây. Lời dặn theo đặc tả yêu cầu, "
      "trong cùng một phiên, viết file thiết kế, rồi file kế hoạch chia việc thành từng phần, rồi làm từng "
      "phần theo kiểu viết test trước, và chạy cả bộ test trước khi dừng. Vì vậy can thiệp là một gói, và "
      "không có người duyệt đặc tả.")
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


@page("p09_cohorts", 9, LOI, 35,
      f"Người nói: Lợi, khoảng ba mươi lăm giây. Thí nghiệm chính có ba nhóm. Hai nhóm Claude dùng cùng Claude "
      f"Code, một với Sonnet, một với Opus, để trả lời câu hỏi về mô hình mạnh hơn. Nhóm Codex với gpt-6-luna để "
      f"xem kết luận có giữ khi đổi hãng. Nhóm thứ tư, Antigravity với Gemini, đã được lên kế hoạch nhưng hết "
      f"hạn mức ở {N['ResAgyDone']} trên {N['ResRunsPerCohort']} lượt nên bị bỏ. Sau khi thấy kết quả chính, "
      f"nhóm thêm hai thí nghiệm thăm dò: E1 chạy Claude Haiku với đề chi tiết, E2 dùng đề sơ sài không quá ba "
      f"mươi từ, chấm bằng danh sách hành vi rút từ test ẩn. Mọi công cụ chạy agent mặc định, effort medium, "
      f"HOME sạch.")
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


@page("p10_tiers", 25, LOI, 35,
      f"Người nói: Lợi, khoảng ba mươi lăm giây. Nhiệm vụ lấy từ commit thật của backend, chia ba tầng. "
      f"Tầng nhỏ có {N['Tasks']} nhiệm vụ, mỗi nhiệm vụ một commit, chọn từ {N['Candidates']} ứng viên qua "
      f"phễu sàng lọc và lấy mẫu phân tầng. Tầng vừa có {N['MediumTasks']} nhiệm vụ hai đến ba commit. Tầng "
      f"lớn có {N['FeatureTasks']} nhiệm vụ cỡ một tính năng. Ba nhóm, hai cách làm, ba lần lặp cho "
      f"{N['ResRuns']} lượt của thí nghiệm chính. Hai thí nghiệm thăm dò thêm {N['ResRunsPerCohort']} lượt "
      f"Haiku và {N['ETwoBriefJudged']} lượt đề sơ sài; E2 được chấm bằng 306 mục hành vi, do Claude Fable 5.2 chấm "
      f"khi không biết cách làm, và Lợi, Bảo chấm tay 24 lượt để đo độ khớp.")
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
                      [f"Thăm dò: E1 Haiku {N['ResRunsPerCohort']} lượt · E2 đề sơ sài {N['ETwoBriefJudged']} lượt, "
                       "chấm 306 mục hành vi (Fable 5.2, che cách làm), kiểm tay 24 lượt"],
                      size=13, fill=BLUE, bold=True))


@page("p11_grading", 19, LOI, 30,
      "Người nói: Lợi, khoảng ba mươi giây. Mỗi nhiệm vụ được chấm bằng test ẩn: các test mà commit gốc thêm "
      "vào, trượt ở mã nền và đạt ở bản gốc, agent không thấy. Một lượt đạt khi mọi test ẩn đạt và không test "
      "cũ nào hỏng. Khi chấm, mọi test có sẵn được đưa về bản gốc, nên agent không đạt được bằng cách sửa "
      "test. Cây mã giao cho agent không có lịch sử git, spec hay plan cũ, để không lộ lời giải.")
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


@page("p12_prereg", 21, LOI, 30,
      "Người nói: Lợi, khoảng ba mươi giây. Để không chọn đề hay chọn cách phân tích sau khi thấy số, mọi thứ "
      "được chốt trước bằng thẻ git. Thẻ prereg-v1 chốt tầng nhỏ, giả thuyết và kế hoạch phân tích. Thẻ "
      "prereg-v1.1 chốt nhiệm vụ tầng vừa và tầng lớn trước mọi lượt AI trên hai tầng này. Một tác tử AI "
      "chạy tách riêng, Fable, phản biện độc lập bản đăng ký, đề bài và mã phân tích. Mã phân tích được chốt "
      "trước khi mở kết quả, và mọi thay đổi sau thẻ đều được ghi lại kèm lý do.")
def _(r):
    set_text(r, "shape-2150", ["Chốt trước khi chạy"])
    steps = [("shape-2151", "shape-2147", "v1", ["Tầng nhỏ, giả thuyết,", "kế hoạch phân tích"]),
             ("shape-2152", "shape-2148", "Chạy", ["Chạy tầng nhỏ; chỉ", "xem trạng thái lượt"]),
             ("shape-2153", "shape-2149", "v1.1", ["Chốt nhiệm vụ tầng", "vừa và tầng lớn"]),
             ("shape-2155", "shape-2154", "Duyệt", ["Fable 5.2 phản biện", "độc lập"]),
             ("shape-2157", "shape-2156", "Mã", ["Chốt mã phân tích", "trước khi mở"]),
             ("shape-2159", "shape-2158", "Mở", ["Mở kết quả; thay", "đổi đều ghi lại"])]
    for head, body, h, b in steps:
        set_text(r, head, [h], size=22, role="head")
        top = body in ("shape-2147", "shape-2148", "shape-2149")
        set_text(r, body, b, size=16, y=(176 - 22 * len(b)) if top else None)


@page("p13_threats", 23, LOI, 30,
      "Người nói: Lợi, khoảng ba mươi giây. Hai rủi ro lớn nhất và cách nhóm kiểm soát. Thứ nhất là rò rỉ: "
      "ViPharmind là repo công khai, lịch sử chứa lời giải. Cây mã không có lịch sử git, mốc dữ liệu huấn "
      "luyện của cả bốn mô hình đều trước commit đầu tiên, và mọi đường dẫn tới repo gốc trong nhật ký được ghi "
      "để phân tích độ nhạy. Thứ hai là thiên vị khi chọn đề hay chọn số: thứ tự duyệt đề được xáo với hạt "
      "giống cố định, và kế hoạch đã chốt bằng thẻ. Em xin chuyển sang Bảo trình bày kết quả.")
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


@page("p14_results", 4, BAO, 10,
      "Người nói: Bảo, khoảng mười giây. Em là Bảo. Em trình bày hai phát hiện: khi đề đã chi tiết thì quy "
      "trình đặc tả thêm được gì, và các lượt hỏng vì đâu; rồi câu hỏi mà chúng mở ra, khi đề chỉ một hai câu.")
def _(r):
    set_text(r, "shape-1483", ["02"], role="num")
    set_text(r, "shape-1491", ["Kết quả"], role="title")
    set_text(r, "shape-1484", ["Trần Ngọc Bảo · hai phát hiện, một câu hỏi mở"])


@page("p15_h1", 13, BAO, 50,
      f"Người nói: Bảo, khoảng năm mươi giây. Đây là phép thử xác nhận duy nhất: Claude Sonnet, tầng nhỏ. "
      f"Theo đặc tả đạt {N['ResHOneSpecPct']} phần trăm, vibe đạt {N['ResHOneVibePct']} phần trăm, hiệu số âm "
      f"{N['ResHOneEstPp'].lstrip('-')} điểm phần trăm, khoảng tin cậy chín mươi lăm phần trăm từ âm "
      f"{N['ResHOneLowPp'].lstrip('-')} đến {N['ResHOneHighPp']}. Khoảng tin cậy chứa không nên theo quy tắc "
      f"chốt trước, H1 chưa kết luận được. Nhưng cận trên bằng không: dữ liệu không để chỗ cho một lợi ích "
      f"dương nào của làm theo đặc tả ở tầng nhỏ với nhóm này. Kết luận giữ nguyên trong mọi phân tích độ nhạy.")
def _(r):
    add(r, title_block("title", "H1 · Đặc tả có đạt nhiều hơn?", w=600))
    set_text(r, "shape-1856", [f"{m(N['ResHOneEstPp'])} đpt"], size=64, role="num")
    set_text(r, "shape-1857", ["Hiệu số tỉ lệ đạt (đặc tả − vibe), Sonnet, tầng nhỏ",
                               f"Đặc tả {N['ResHOneSpecPct']}% · vibe {N['ResHOneVibePct']}% · "
                               f"KTC 95% {ci(N['ResHOneLowPp'], N['ResHOneHighPp'])}"], size=18)
    add(r, text_block("verdict", 75, 420, 640, 50,
                      ["Kết luận: chưa kết luận được (KTC chứa 0).",
                       f"Cận trên {N['ResHOneHighPp']}: không thấy lợi ích dương nào."],
                      size=16, fill=BLUE, bold=True))


@page("p16_rq4", 12, BAO, 35,
      f"Người nói: Bảo, khoảng ba mươi lăm giây. Hình này cho hiệu số của từng nhóm và từng tầng. Nhóm "
      f"Antigravity với Gemini bị bỏ khi mới xong {N['ResAgyDone']} trên {N['ResRunsPerCohort']} lượt vì hết hạn "
      f"mức; số đếm thô đã được xem trước quyết định, điều này ghi trong phụ lục sai lệch. Vì vậy RQ4 chỉ còn hai công cụ: Claude Code và Codex. Nhóm chỉ so hướng và "
      f"độ lớn, không so công cụ này với công cụ kia. Với hai mô hình Claude, hiệu số âm hoặc bằng không ở mọi "
      f"tầng. Với Codex, hiệu số dương ở tầng nhỏ và tầng lớn, âm ở tầng vừa. Ô duy nhất được ủng hộ là Codex "
      f"tầng lớn: đặc tả đạt {N['ResCodexLargeSpecPct']} phần trăm, vibe {N['ResCodexLargeVibePct']} phần trăm. "
      f"Nhưng ô này chỉ có ba nhiệm vụ, và có {N['ResSecondaryComparisons']} phép so phụ không hiệu chỉnh, "
      f"nên có thể là ngẫu nhiên.")
def _(r):
    delete_icon_use(r, "imported/flat_slide_12_ill01")
    set_text(r, "shape-1841", ["RQ4: đổi công cụ,", "kết luận có giữ?"], role="title")
    set_text(r, "shape-1842", ["Hiệu số tỉ lệ đạt theo", "nhóm và tầng, KTC 95%.", "",
                               "Claude: âm hoặc 0, trừ", "Sonnet tầng vừa",
                               f"(+{N['ResSonnetMediumDiffPp']}, chỉ tham khảo).", "",
                               "Codex: dương ở tầng", "nhỏ và lớn; ô lớn",
                               f"({N['ResCodexLargeSpecPct']}% so với {N['ResCodexLargeVibePct']}%)",
                               "chỉ có 3 nhiệm vụ."],
             size=16)
    add(r, figure_slot("figure", "slot_pass_diff_by_cohort.png"))


H3C_OK, H3C_ALL = verdict_count("H3c.", "supported")
H3A_BAD, _ = verdict_count("H3a.", "contrary")


@page("p17_h2h3", 14, BAO, 40,
      f"Người nói: Bảo, khoảng bốn mươi giây. H2 được ủng hộ ở mọi nhóm và mọi tầng: làm theo đặc tả dùng "
      f"gấp {N['ResTokenRatioMin']} đến {N['ResTokenRatioMax']} lần token và gấp {N['ResWallRatioMin']} đến "
      f"{N['ResWallRatioMax']} lần thời gian. H3 lẫn lộn. Lỗi tĩnh có hai ô trái với giả thuyết, Sonnet tầng "
      f"vừa và Codex tầng nhỏ. Ngược lại, ở Codex tầng lớn, nhánh đặc tả không làm hỏng test cũ lượt nào, còn "
      f"nhánh vibe làm hỏng ở {N['ResCodexLargeRegVibePct']} phần trăm số lượt; lỗi tĩnh trung bình "
      f"{N['ResCodexLargeStaticSpec']} so với {N['ResCodexLargeStaticVibe']}. Chỉ số bảo trì không kém hơn quá "
      f"năm điểm ở {H3C_OK} trên {H3C_ALL} ô. Khác biệt rõ "
      f"nhất là test tác tử tự viết: nhánh đặc tả phủ {N['ResSonnetSpecCovPct']} đến {N['ResOpusSpecCovPct']} "
      f"phần trăm dòng mới; nhánh vibe thì Opus {N['ResOpusVibeCovPct']}, Sonnet {N['ResSonnetVibeCovPct']}, "
      f"Codex {N['ResCodexVibeCovPct']} phần trăm. Test ẩn không thưởng cho phần test này.")
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


@page("p18_h4", 23, BAO, 45,
      f"Người nói: Bảo, khoảng bốn mươi lăm giây. H4 dùng thiết kế hai nhân hai: hai mô hình Claude trong cùng "
      f"Claude Code, mỗi mô hình hai cách làm. Ở tầng nhỏ, hiệu số của cả hai mô hình đều âm, và hiệu của hai "
      f"hiệu số là {N['ResHFourDiffOfDiffsPp']} điểm phần trăm, khoảng tin cậy chứa không: H4 chưa kết luận "
      f"được ở cả ba tầng. Sonnet theo đặc tả đạt ngang Opus vibe với khoảng {N['ResHFourCostRatioPct']} phần "
      f"trăm chi phí quy đổi. Điều này không cho thấy đặc tả nâng mô hình yếu lên; Sonnet đã gần trần ở tầng "
      f"nhỏ dù làm theo cách nào.")
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
                       f"Sonnet đặc tả đạt ngang Opus vibe ({N['ResHFourSonnetSpecOpusVibePp']} đpt) "
                       f"với {N['ResHFourCostRatioPct']}% chi phí."],
                      size=14, fill=BLUE, bold=True))


@page("p19_h5", 12, BAO, 35,
      f"Người nói: Bảo, khoảng bốn mươi giây. Đây là H5. Mỗi điểm là một nhiệm "
      f"vụ: trục ngang là số dòng của bản vá gốc, trục dọc là hiệu số tỉ lệ đạt. Hiệu số gộp ba nhóm ở tầng "
      f"lớn trừ tầng nhỏ là {N['ResHFiveEstPp']} điểm phần trăm, khoảng tin cậy từ âm "
      f"{N['ResHFiveLowPp'].lstrip('-')} đến {N['ResHFiveHighPp']}. Hệ số tương tác của mô hình logistic hỗn "
      f"hợp là {N['ResHFiveCoef']} trên thang logit, khoảng tin cậy cũng chứa không. Vậy H5 chưa kết luận "
      f"được. Phần lớn nhiệm vụ có hiệu số bằng không; các nhiệm vụ lệch nằm ở cả hai phía và ở mọi cỡ, riêng "
      f"ba nhiệm vụ tầng lớn của Codex đều lệch về phía đặc tả. Ba nhiệm vụ tầng lớn là quá ít để kết luận.")
def _(r):
    delete_icon_use(r, "imported/flat_slide_12_ill01")
    set_text(r, "shape-1841", ["H5: lợi ích tăng", "theo kích thước?"], role="title")
    set_text(r, "shape-1842", ["Mỗi điểm: một nhiệm vụ.", "",
                               "Tầng lớn trừ tầng nhỏ:", f"+{N['ResHFiveEstPp']} đpt "
                               f"{ci(N['ResHFiveLowPp'], N['ResHFiveHighPp'])}", "",
                               "Tương tác (logit):", f"{N['ResHFiveCoef']} {ci(N['ResHFiveCoefLow'], N['ResHFiveCoefHigh'])}",
                               "", "Chưa kết luận được."], size=16)
    add(r, figure_slot("figure", "slot_effect_vs_size.png"))


@page("p20_cost", 20, BAO, 25,
      "Người nói: Bảo, khoảng ba mươi lăm giây. Vì mọi lượt chạy bằng gói thuê bao, chi phí là số quy đổi từ "
      "token theo bảng giá API công khai chốt trước. Bảng này cho chi phí cho một lượt đạt ở tầng nhỏ và tầng "
      "lớn. Với hai mô hình Claude, nhánh đặc tả đắt hơn ở mọi ô, khoảng gấp đôi với Sonnet. Với Codex chỉ có "
      "cận dưới và cận trên; ở tầng lớn, nhánh đặc tả lại rẻ hơn cho một lượt đạt vì nhánh vibe gần như không "
      "đạt.")
def _(r):
    set_text(r, "shape-2122", ["Chi phí cho một lượt đạt (USD)"])
    rows = [("shape-2124", "shape-2123", "Sonnet", "claude-sonnet"),
            ("shape-2127", "shape-2126", "Opus", "claude-opus"),
            ("shape-2130", "shape-2129", "Luna", "codex-luna")]
    for head, body, h, c in rows:
        set_text(r, head, [h], size=22)
        set_text(r, body, [f"Nhỏ: đặc tả {usd(c, 'small', 'spec')} · vibe {usd(c, 'small', 'vibe')}",
                           f"Lớn: đặc tả {usd(c, 'large', 'spec')} · vibe {usd(c, 'large', 'vibe')}"], size=16)
    set_text(r, "shape-2133", ["Tóm lại"], size=22)
    set_text(r, "shape-2132", ["Claude: đặc tả đắt hơn ở mọi ô.",
                               "Luna tầng lớn: đặc tả rẻ hơn vì vibe ít đạt."], size=16)


@page("p21_case", 26, BAO, 35,
      f"Người nói: Bảo, khoảng ba mươi lăm giây. Ca nghiên cứu là nhiệm vụ tầng lớn có hiệu số lớn nhất ở Claude "
      f"Sonnet, chọn theo quy tắc chốt trước: f15, tập tài liệu có chủ sở hữu và quy tắc hiển thị. Không lượt "
      f"đặc tả nào đạt, một lượt vibe đạt. Lượt đặc tả đạt {N['ResCaseSpecHidden']} trên "
      f"{N['ResCaseHiddenTotal']} test ẩn, sau gấp đôi thời gian lượt vibe. Đề bài nêu tên phương thức deleted_with_releases nhưng không nói nó trả về "
      f"gì. Bản thiết kế chốt là danh sách đối tượng, còn bản gốc trả danh sách mã. Kế hoạch và test của tác tử "
      f"dựa trên quyết định đó nên đều đạt; trên test ẩn, hàm dọn gặp lỗi và khối except của chính tác tử nuốt "
      f"lỗi. Bước thiết kế đã biến một chỗ đề bỏ ngỏ thành quyết định cố định, rồi tự kiểm quyết định đó bằng "
      f"chính giả định của nó.")
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


@page("p22_labels", 6, BAO, 30,
      "Người nói: An, khoảng ba mươi giây. Một phát hiện xem trước. Lợi và Bảo gán nhãn mù nguyên nhân cho mọi "
      "lượt hỏng của hai nhóm Claude. Phần lớn lượt hỏng không phải vì logic sai, mà vì test ẩn kiểm một chi "
      "tiết đề không chốt, hoặc vì agent nối sai với mã có sẵn của dự án, và điều này như nhau ở hai cách làm. "
      "Phân tích đầy đủ để ở báo cáo cuối kỳ.")
def _(r):
    set_text(r, "shape-1622", [f"{N['LabOutside']}/{N['LabRuns']} lượt hỏng:",
                               f"đề không chốt ({N['LabDeBaiThieuTotal']}),",
                               f"nối sai mã có sẵn ({N['LabSaiApiCoSanTotal']})"], size=32)
    set_text(r, "shape-1621", [f"—Như nhau ở hai cách ({N['LabOutsideSpecPct']}% / {N['LabOutsideVibePct']}%);",
                               f"Lợi, Bảo khớp {N['LabAgree']}/{N['LabRuns']}, kappa {N['LabKappa']}"],
             size=20, role="title")


@page("p23_explore", 14, BAO, 45,
      f"Người nói: An, khoảng bốn mươi lăm giây. Đề của thí nghiệm chính phải nêu đủ tên để test ẩn chấm được, "
      f"nên nó chưa trả lời câu hỏi của vibe coding thật: khi người dùng chỉ đưa một hai câu, bắt agent tự viết "
      f"thiết kế, kế hoạch và test có bù được không. Hai thí nghiệm thăm dò, thêm sau khi thấy kết quả chính, đã "
      f"chạy xong. E2 cho hai cách làm cùng một đề sơ sài, chấm bằng danh sách hành vi rút từ test ẩn. Ở tầng "
      f"nhỏ, gộp bốn nhóm, đặc tả hơn vibe {nv('ETwoPooledSmallPp')} điểm, khoảng tin cậy "
      f"{ci_n('ETwoPooledSmallLowPp', 'ETwoPooledSmallHighPp')}: một lợi ích nhỏ. Nhưng chỉ riêng việc đề sơ sài "
      f"đã làm tỉ lệ test ẩn đạt giảm khoảng tám mươi điểm ở cả hai cách làm, nên độ rõ của đề quan trọng hơn quy "
      f"trình nhiều. E1 chạy Haiku với đề chi tiết: đặc tả không đạt hơn mà tốn gấp {nv('EOneTokenRatio')} lần "
      f"token. Vì là thăm dò, nhóm chỉ đọc đây là xu hướng; số theo từng nhóm và tầng để ở báo cáo cuối kỳ.")
def _(r):
    add(r, text_block("kicker", 247.61, 14, 600, 52,
                      ["Câu hỏi mở: đề chỉ một hai câu thì sao?", "Thăm dò, thêm sau kết quả chính · Codex dừng sớm"],
                      size=16, fill=BLUE, bold=True, family=MONO, lead=1.4))
    set_text(r, "shape-1916", [f"{sg('ETwoPooledSmallPp')} điểm"], size=40, role="num")
    set_text(r, "shape-1917", [f"E2 đề sơ sài, tầng nhỏ, gộp: KTC {ci_n('ETwoPooledSmallLowPp', 'ETwoPooledSmallHighPp')}",
                               f"Gộp mọi tầng {sg('ETwoPooledAllPp')} {ci_n('ETwoPooledAllLowPp', 'ETwoPooledAllHighPp')}: chứa 0"],
             size=15)
    set_text(r, "shape-1918", [f"{sg('ETwoXScoreDetailVibe')} điểm"], size=40, role="num")
    set_text(r, "shape-1919", ["Điểm danh sách khi bỏ chi tiết khỏi đề",
                               f"(vibe; đặc tả {sg('ETwoXScoreDetailSpec')}): đề rõ quan trọng hơn"], size=15)
    set_text(r, "shape-1920", ["E1"], size=40, role="num")
    set_text(r, "shape-1921", ["Haiku, đề chi tiết: không đạt hơn,",
                               f"tốn ×{nv('EOneTokenRatio')} token"], size=16)


@page("p24_next", 8, BAO, 30,
      "Người nói: An, khoảng ba mươi giây. Thí nghiệm đã chạy xong. Việc còn lại trước 24/11: Lợi và Bảo đang "
      "chấm tay 24 lượt của E2 để kiểm người chấm máy; nhóm phân tích chi tiết E1, E2, hoàn thiện phần hồi cứu và "
      "phân tích nguyên nhân thất bại, viết kết luận, rồi nộp báo cáo cuối và thuyết trình. Hạn chế chính đã "
      "biết: một dự án, ít nhiệm vụ lớn, và đề chi tiết gần như đã là đặc tả.")
def _(r):
    set_text(r, "shape-1666", ["Việc tiếp theo"])
    set_text(r, "shape-1671", ["Đã xong"])
    set_text(r, "shape-1668", ["Lợi, Bảo chấm tay", "24 lượt E2, kappa 0,93;", "máy khớp 0,88 / 0,90"], size=16)
    set_text(r, "shape-1672", ["Đến 24/11"])
    set_text(r, "shape-1669", ["Lợi kiểm trích dẫn,", "Bảo tính lại số liệu;", "An duyệt, nộp"], size=16)
    set_text(r, "shape-1667", ["Hạn chế"])
    set_text(r, "shape-1670", ["Một dự án; ít", "nhiệm vụ lớn; đề", "gần như đặc tả"], size=16)


@page("p24_limits", 8, BAO, 40,
      f"Người nói: Bảo, khoảng bốn mươi giây. Nhóm nêu rõ ba hạn chế. Một: chỉ một dự án Python, và nhánh "
      f"đặc tả là bản tự động, không có người duyệt như khi An làm thật. Hai: đề bài do AI soạn và An duyệt "
      f"gộp; test ẩn được viết cho bản gốc vốn làm theo đặc tả. Ba: tầng vừa chỉ có {N['MediumTasks']} và "
      f"tầng lớn chỉ có {N['FeatureTasks']} nhiệm vụ, nên khoảng tin cậy ở đó chỉ để tham khảo.")
def _(r):
    set_text(r, "shape-1666", ["Hạn chế"])
    set_text(r, "shape-1671", ["Phạm vi"])
    set_text(r, "shape-1668", ["Một dự án Python;", "đặc tả tự động,", "không người duyệt"], size=16)
    set_text(r, "shape-1672", ["Đề bài"])
    set_text(r, "shape-1669", ["AI soạn, An duyệt;", "test ẩn viết cho", "bản gốc"], size=16)
    set_text(r, "shape-1667", ["Cỡ mẫu"])
    set_text(r, "shape-1670", [f"Tầng vừa {N['MediumTasks']}, lớn {N['FeatureTasks']}",
                               "nhiệm vụ: chỉ để", "tham khảo"], size=16)


@page("p25_conclusion", 7, BAO, 40,
      f"Người nói: Bảo, khoảng bốn mươi giây. Tóm lại hai phát hiện. Một: khi đề đã nêu đủ tên và chữ ký, quy "
      f"trình đặc tả gần như thừa ở việc nhỏ: trên {N['ResRuns']} lượt, nó không đạt test ẩn nhiều hơn, tốn gấp "
      f"{N['ResTokenRatioMin']} đến {N['ResTokenRatioMax']} lần token; dấu hiệu có ích duy nhất là Codex ở ba "
      f"nhiệm vụ lớn nhất, và nó luôn để lại test do agent tự viết. Hai: {N['LabOutside']} trên {N['LabRuns']} "
      f"lượt hỏng của Claude đến từ chi tiết đề không chốt hoặc nối với mã có sẵn, ở cả hai cách làm. Với đề chỉ "
      f"một hai câu, kết quả {nv('ETwoStatus')} của E2, {nv('ETwoLabel')}: {nv('ETwoReading')}. Kết luận chính "
      f"sẽ viết khi E2 đủ dữ liệu.")
def _(r):
    set_text(r, "shape-1634", ["Kết luận"])
    set_text(r, "shape-1638", ["Đề chi tiết"])
    set_text(r, "shape-1636", ["Đặc tả gần như thừa", "ở việc nhỏ, tốn",
                               f"×{N['ResTokenRatioMin']}–{N['ResTokenRatioMax']} token; luôn để", "lại test."],
             size=17)
    set_text(r, "shape-1637", ["Lượt hỏng"])
    set_text(r, "shape-1635", [f"{N['LabOutside']}/{N['LabRuns']}: đề không chốt", "hoặc nối mã có sẵn;",
                               "như nhau ở hai cách."], size=17)
    add(r, text_block("next", 189, 392, 640, 80,
                      [f"Đề một hai câu: {nv('ETwoReadingShort')}", nv("ETwoLabel"),
                       f"Kết luận chính: {PENDING}"], size=15, fill=BLUE, bold=True))


@page("p26_thanks", 15, BAO, 10,
      "Người nói: Bảo, khoảng mười giây. Bài trình bày của nhóm em đến đây là hết. Em cảm ơn thầy và các bạn "
      "đã lắng nghe; nhóm em xin nhận câu hỏi.")
def _(r):
    set_text(r, "shape-1949", ["Xin cảm ơn!"], role="title")
    add(r, text_block("qa", 81, 345, 390, 50, ["Hỏi đáp"], size=20, fill=INK, bold=True))


@page("p27_bk_funnel", 21, "Dự phòng", 0,
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


@page("p28_bk_reading", 24, "Dự phòng", 0,
      "Slide dự phòng, dùng khi được hỏi cách đọc kết quả. Đơn vị phân tích là nhiệm vụ. Khoảng tin cậy là "
      "bootstrap lấy mẫu lại nhiệm vụ. Nhóm không dựa vào ngưỡng p, và chỉ dùng ba cụm từ đã chốt trước.")
def _(r):
    set_text(r, "shape-2217", ["Dự phòng: cách đọc kết quả"])
    set_text(r, "shape-2220", ["Ước lượng"])
    set_text(r, "shape-2218", ["Hiệu số tỉ lệ đạt (đặc tả − vibe) theo nhiệm vụ;",
                               "KTC 95% bootstrap lấy mẫu lại nhiệm vụ."], size=17)
    set_text(r, "shape-2221", ["Đọc kết quả"])
    set_text(r, "shape-2219", ["KTC nằm hẳn phía giả thuyết: được ủng hộ. Phía ngược",
                               "lại: trái với giả thuyết. Còn lại: chưa kết luận được."], size=17)


@page("p29_bk_labels", 24, "Dự phòng", 0,
      f"Slide dự phòng, dùng khi được hỏi về phân loại lỗi. Lợi và Bảo gán nhãn độc lập {N['LabRuns']} lượt "
      f"không đạt của hai nhóm Claude, ở vòng hai với hướng dẫn đã làm rõ thứ tự quyết định; vòng một bị loại "
      f"theo đề nghị của hai bạn vì điền chưa kỹ. Hai người đồng ý {N['LabAgree']} trên {N['LabRuns']} lượt, "
      f"kappa {N['LabKappa']}; An phân xử {N['LabAdjudicated']} lượt lệch. {N['LabDeBaiThieuTotal']} lượt hỏng "
      f"vì test ẩn kiểm chi tiết đề không chốt, {N['LabSaiApiCoSanTotal']} lượt vì nối sai với mã có sẵn của "
      f"dự án; chỉ {N['LabLoiLogicTotal']} lượt là lỗi logic. Tỉ lệ hai loại đầu gần như nhau ở hai cách làm, "
      f"{N['LabOutsideSpecPct']} và {N['LabOutsideVibePct']} phần trăm, nên quy trình đặc tả không ngăn được "
      f"chúng. Cả {N['LabHongChucNangCuTotal']} lượt làm hỏng chức năng cũ đều của Opus. Fable 5.2 gán thêm làm "
      f"người chấm thứ ba, chỉ để đối chiếu: đồng ý với Lợi {N['LabFableAgreeLoi']} và với Bảo "
      f"{N['LabFableAgreeBao']} lượt.")
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


@page("p30_attribution", 30, "Dự phòng", 0,
      "Slide ghi nguồn template Slidesgo, giữ lại theo điều kiện của bản miễn phí.")
def _(r):
    set_text(r, "shape-2412", ["Ghi nguồn"], role="title")
    set_text(r, "shape-2411", ["Mẫu slide: Slidesgo, Freepik", "Nhóm: Doãn Văn An, Lê Xuân Lợi,",
                               "Trần Ngọc Bảo"], size=20)
    set_text(r, "shape-2413", ["Slide này được giữ để ghi nguồn template."])


# Báo cáo lần 1 (17/11): chỉ giữ các trang teaser, theo thứ tự này.
LAN1 = ["p01_title", "p03_motivation", "p04_rq", "p08_arms", "p10_tiers", "p15_h1", "p16_rq4", "p17_h2h3",
        "p22_labels", "p23_explore", "p24_next", "p26_thanks", "p30_attribution"]
PAGES[:] = [next(p for p in PAGES if p["stem"] == stem) for stem in LAN1]


def neg(key: str) -> str:
    """numbers.json value read aloud: '-6,7' -> 'âm 6,7'."""
    v = N[key]
    return "âm " + v[1:] if v.startswith("-") else v


SECS_VI = {10: "mười", 15: "mười lăm", 20: "hai mươi", 25: "hai mươi lăm", 30: "ba mươi", 35: "ba mươi lăm",
           40: "bốn mươi", 45: "bốn mươi lăm", 50: "năm mươi", 55: "năm mươi lăm", 60: "sáu mươi", 65: "sáu mươi lăm"}

# Spoken script for the 17/11 talk: speaker-neutral (whoever presents), about 140 syllables a minute.
# stem -> (seconds, script). The notes start with the timing only, as a stage direction.
TALK = {
    "p01_title": (20,
        "Em chào thầy. Đề tài của nhóm em hỏi: bắt trợ lý lập trình AI làm theo đặc tả có bù được cho đề bài "
        "ngắn của vibe coding không. Em đi qua vấn đề, thiết kế, kết quả chính và kết quả thăm dò."),
    "p03_motivation": (40,
        "Coding agent như Claude Code hay Codex tự đọc mã, sửa file và chạy test. Vibe coding là giao vài câu "
        "ngắn, để agent tự đoán phần đề bỏ ngỏ. Phát triển theo đặc tả, kiểu Superpowers, hứa bù chỗ đó: agent "
        "viết thiết kế, kế hoạch, test trước, rồi kiểm lại. Nhưng chưa có thí nghiệm nào chỉ đổi lời dặn, giữ "
        "nguyên đề, công cụ, mô hình, và chấm bằng test mà agent không thấy. Nhóm em làm thí nghiệm đó."),
    "p04_rq": (35,
        "Nhóm em chốt sáu câu hỏi trước khi chạy. Hồi cứu là RQ1 và RQ2, trên lịch sử git của ViPharmind, trợ lý "
        "tra cứu thuốc mà An xây cùng AI. Thực nghiệm là RQ3 đến RQ6: đặc tả có đạt hơn, tốn hơn bao nhiêu, và "
        "có giữ khi đổi công cụ, mô hình, cỡ nhiệm vụ. Hôm nay em tập trung vào thực nghiệm, với đề chi tiết nêu "
        "đủ tên hàm. Trước hết là hai cách làm."),
    "p08_arms": (30,
        "Hai cách làm chỉ khác lời dặn trước đề bài. Vibe chỉ một câu: cài đặt thay đổi sau. Đặc tả thì agent "
        "viết thiết kế, rồi kế hoạch, làm từng phần với test trước, và chạy cả bộ test trước khi dừng. Còn lại "
        "giống hệt. Một lượt đạt khi qua mọi test ẩn lấy từ commit gốc, mà agent không thấy. Tiếp theo là quy mô."),
    "p10_tiers": (35,
        f"Nhiệm vụ lấy từ commit thật, chia ba tầng: {N['Tasks']} nhỏ, {N['MediumTasks']} vừa, và "
        f"{N['FeatureTasks']} lớn. Ba nhóm là Claude Code với Sonnet, với Opus, và Codex, hai "
        f"cách làm, ba lần lặp, ra {N['ResRuns']} lượt. Thêm hai thí nghiệm thăm dò: E1 chạy "
        f"Haiku {N['ResRunsPerCohort']} lượt, E2 dùng đề sơ sài {N['ETwoBriefJudged']} lượt, chấm theo 306 mục "
        f"hành vi, máy chấm không biết cách làm. Giờ đến kết quả chính."),
    "p15_h1": (40,
        f"Đây là phép thử xác nhận duy nhất, chốt trước: Sonnet ở tầng nhỏ. Đặc tả đạt {N['ResHOneSpecPct']} "
        f"phần trăm, vibe {N['ResHOneVibePct']} phần trăm. Hiệu số {neg('ResHOneEstPp')} điểm, khoảng tin cậy "
        f"95 phần trăm từ {neg('ResHOneLowPp')} đến 0. Khoảng này chứa 0, nên H1 chưa kết luận được. Cận trên "
        f"bằng 0, nên dữ liệu không ủng hộ lợi ích đáng kể nào của đặc tả ở đây. Đổi công cụ thì sao?"),
    "p16_rq4": (35,
        f"Hình là hiệu số theo nhóm và tầng. Với Claude, hiệu số âm hoặc "
        f"0, trừ Sonnet tầng vừa cộng {N['ResSonnetMediumDiffPp']}, chỉ để tham khảo. Codex dương ở tầng nhỏ và "
        f"lớn. Ô tầng lớn, {N['ResCodexLargeSpecPct']} so với {N['ResCodexLargeVibePct']} phần trăm, nghiêng về "
        f"đặc tả, nhưng chỉ có 3 nhiệm vụ, khoảng tin cậy suy biến, và là một trong "
        f"{N['ResSecondaryComparisons']} phép so phụ không hiệu chỉnh. Tiếp theo là chi phí và chất lượng."),
    "p17_h2h3": (40,
        f"H2 ủng hộ ở mọi ô: đặc tả tốn gấp {N['ResTokenRatioMin']} đến {N['ResTokenRatioMax']} lần token, "
        f"{N['ResWallRatioMin']} đến {N['ResWallRatioMax']} lần thời gian. H3 lẫn lộn: lỗi tĩnh có {H3A_BAD} ô "
        f"trái giả thuyết. Ở Codex tầng lớn, nhánh vibe làm hỏng test cũ ở {N['ResCodexLargeRegVibePct']} phần "
        f"trăm, đặc tả thì không lượt nào. Chỉ số bảo trì không kém quá 5 điểm ở {H3C_OK} trên "
        f"{H3C_ALL} ô. Khác rõ nhất: khoảng ba phần tư lượt đặc tả để lại test tự viết. Vậy lượt hỏng vì đâu?"),
    "p22_labels": (30,
        f"Lợi và Bảo gán nhãn độc lập {N['LabRuns']} lượt hỏng của Claude, khớp {N['LabAgree']} trên "
        f"{N['LabRuns']}, kappa {N['LabKappa']}. {N['LabOutside']} lượt là do đề không chốt chi tiết, "
        f"{N['LabDeBaiThieuTotal']} lượt, hoặc dùng sai mã có sẵn, {N['LabSaiApiCoSanTotal']} lượt. Như nhau ở "
        f"hai cách làm, {N['LabOutsideSpecPct']} và {N['LabOutsideVibePct']} phần trăm. Vậy đề ngắn hơn nữa "
        f"thì sao?"),
    "p23_explore": (65,
        f"Hai thí nghiệm này thêm sau kết quả chính, nên chỉ là thăm dò. E2 cho hai cách làm cùng một đề sơ sài. "
        f"Codex hết hạn mức, dừng ở 78 trên 90 lượt tầng nhỏ. Ở tầng "
        f"nhỏ, gộp bốn nhóm, đặc tả hơn vibe {N['ETwoPooledSmallPp']} điểm, khoảng tin cậy từ "
        f"{neg('ETwoPooledSmallLowPp')} đến {neg('ETwoPooledSmallHighPp')}, riêng Sonnet là "
        f"{N['ETwoSonnetSmallPp']}. Gộp mọi tầng chỉ còn {N['ETwoPooledAllPp']}, khoảng tin cậy từ "
        f"{neg('ETwoPooledAllLowPp')} đến {neg('ETwoPooledAllHighPp')}, chứa 0. Tác động của đề lớn hơn nhiều: "
        f"bỏ chi tiết làm điểm giảm {N['ETwoXScoreDetailVibe'].lstrip('-')} điểm với vibe, "
        f"{N['ETwoXScoreDetailSpec'].lstrip('-')} với đặc tả. E1, Haiku với đề chi tiết: đặc tả không đạt "
        f"hơn, tốn gấp {N['EOneTokenRatio']} lần token. Cuối cùng là việc còn lại."),
    "p24_next": (40,
        "Chấm tay đã xong: Lợi và Bảo chấm độc lập 24 lượt E2. Hai bạn khớp nhau với kappa "
        "0,93, máy chấm khớp từng bạn 0,88 và 0,90, lệch chủ yếu do máy khắt khe hơn. Trước 24 tháng 11, "
        "Lợi kiểm lại trích dẫn, Bảo tính lại độc lập số liệu chính, An duyệt lần cuối rồi nộp. Hạn chế: một dự án, ít nhiệm vụ lớn, và đề chi "
        "tiết gần như đã là đặc tả."),
    "p26_thanks": (10,
        "Phần trình bày của nhóm em đến đây là hết. Em cảm ơn thầy và xin nhận câu hỏi."),
}
for p in PAGES:
    p["speaker"] = "Người trình bày"
    if p["stem"] not in TALK:  # slide ghi nguồn: không nói, giữ ghi chú gốc
        continue
    secs, script = TALK[p["stem"]]
    p["secs"] = secs
    p["notes"] = f"Khoảng {SECS_VI[secs]} giây. {script}"

# Result slots still pending: page -> what fills it. The main analysis (data/results/analysis/main) is filled;
# rater labels are filled; the exploratory E1 (Haiku) and E2 (brief prompts) are complete (teaser: headline only).
RESULT_SLOTS: dict[str, str] = {}


# ---------------------------------------------------------------- build


def fmt_secs(s: int) -> str:
    return f"{s // 60}:{s % 60:02d}"


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
        (notes_dir / f"{p['stem']}.md").write_text(p["notes"] + "\n", encoding="utf-8")
        plan.append({"source_slide": p["src"], "svg": out.name})
    (WS / "page_plan.json").write_text(json.dumps(
        {"schema": "ppt-master.roundtrip-page-plan.v1", "pages": plan}, indent=2) + "\n", encoding="utf-8")

    rows, t = [], 0
    for i, p in enumerate(PAGES, 1):
        if p["secs"]:
            t += p["secs"]
            rows.append(f"| {i} | `{p['stem']}` | {p['speaker']} | {fmt_secs(p['secs'])} | {fmt_secs(t)} |")
        else:
            rows.append(f"| {i} | `{p['stem']}` | {p['speaker']} | – | – |")
    by = {s: sum(p["secs"] for p in PAGES if p["speaker"] == s) for s in {p["speaker"] for p in PAGES}}
    (HERE / "rehearsal.md").write_text(
        "# Tập dượt (báo cáo lần 1, 17/11)\n\n"
        "Sinh tự động bởi `build_deck.py`; sửa thời lượng ở đó rồi chạy lại `build.sh`.\n\n"
        f"Tổng thời gian nói: {fmt_secs(t)}; một người trình bày (chưa chốt ai), hỏi đáp sau đó.\n\n"
        "| Slide | Trang | Người nói | Thời lượng | Cộng dồn |\n| --- | --- | --- | --- | --- |\n"
        + "\n".join(rows) + "\n\n## Chỗ chờ kết quả\n\n"
        "Kết quả thí nghiệm chính (Sonnet, Opus, Codex; đề chi tiết) đã điền từ `data/results/analysis/main`. "
        "Nhãn nguyên nhân thất bại đã điền; E2 (đề sơ sài) và E1 (Haiku) đã đủ dữ liệu, làm mới bằng code/refresh-interim.sh. "
        + (f"Các slide sau còn `{PENDING}`:\n\n" if RESULT_SLOTS else f"Không slide nào còn `{PENDING}`.\n")
        + "\n".join(f"- `{k}`: {v}" for k, v in RESULT_SLOTS.items()) + "\n", encoding="utf-8")
    print(f"pages={len(PAGES)} talk={fmt_secs(t)} {by}")


if __name__ == "__main__":
    main()
