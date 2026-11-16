"""Build the round-trip page set of the presentation from template-vi.pptx.

Run through build.sh. Reads the round-trip workspace that ppt-master's pptx_to_svg.py --roundtrip made
from template-vi.pptx (docs/presentation/deck/), copies the chosen template slides under new page names,
rewrites their text, adds the few new objects, and writes page_plan.json, notes/*.md and rehearsal.md.
Every number on a slide comes from docs/report/generated/numbers.json through N[...]. Results that the
analysis has not produced yet are the literal PENDING marker, so check_numbers.py can count them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from lxml import etree
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
WS = HERE / "deck"
SVG_DIR = WS / "authoring-svg-flat"
NUMBERS = HERE.parent / "report" / "generated" / "numbers.json"
LOGO = HERE.parent / "report" / "images" / "logo-hust.png"
SVGNS = "http://www.w3.org/2000/svg"
PENDING = "[CHỜ KẾT QUẢ]"

N = json.loads(NUMBERS.read_text(encoding="utf-8"))

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


def placeholder_png(name: str, figure: str, keys: str):
    """A plain placeholder image for a figure slot; replace the file with the real figure later."""
    w, h = 940, 840
    im = Image.new("RGB", (w, h), "#F5F8FF")
    d = ImageDraw.Draw(im)
    for i in range(0, w, 28):
        d.line([(i, 6), (i + 14, 6)], fill=PURPLE, width=4)
        d.line([(i, h - 7), (i + 14, h - 7)], fill=PURPLE, width=4)
    for j in range(0, h, 28):
        d.line([(6, j), (6, j + 14)], fill=PURPLE, width=4)
        d.line([(w - 7, j), (w - 7, j + 14)], fill=PURPLE, width=4)
    fonts = Path.home() / ".local/share/fonts/QA-VN"
    big = ImageFont.truetype(str(fonts / "IBMPlexMono-Bold.ttf"), 64)
    small = ImageFont.truetype(str(fonts / "BeVietnamPro-Regular.ttf"), 30)
    d.text((w / 2, h / 2 - 70), PENDING, font=big, fill=BLUE, anchor="mm")
    d.text((w / 2, h / 2 + 20), figure, font=small, fill=INK, anchor="mm")
    d.text((w / 2, h / 2 + 70), keys, font=small, fill=INK, anchor="mm")
    im.save(WS / "images" / name)


def figure_slot(gid, href, x=440, y=58, w=470, h=420):
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
      "Đề tài của nhóm so sánh hai cách giao việc cho trợ lý lập trình AI: làm theo đặc tả và vibe coding, "
      "trên một dự án phần mềm AI thật cho ngành dược. Em trình bày bối cảnh và phương pháp, Bảo trình bày "
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


@page("p02_motivation", 7, LOI, 45,
      "Người nói: Lợi, khoảng bốn mươi lăm giây. Ngày nay coding agent như Claude Code, Codex hay "
      "Antigravity tự đọc mã, sửa file và chạy test. Có hai cách giao việc phổ biến. Vibe coding là mô tả "
      "ngắn rồi để agent viết mã ngay. Làm theo đặc tả là bắt agent viết thiết kế và kế hoạch trước, rồi "
      "mới cài đặt. Nhiều người khuyên nên viết đặc tả, nhưng bằng chứng định lượng còn ít: nghiên cứu "
      "quan sát lớn nhất trên pull request mã nguồn mở không thấy đặc tả làm giảm lỗi. Chưa có thí nghiệm "
      "nào giữ nguyên đề bài, công cụ và mô hình, chỉ đổi lời dặn, rồi chấm bằng test mà agent không thấy. "
      "Nhóm em làm đúng thí nghiệm đó.")
def _(r):
    set_text(r, "shape-1634", ["Hai cách giao việc cho coding agent"])
    set_text(r, "shape-1638", ["Vibe coding"])
    set_text(r, "shape-1637", ["Theo đặc tả"])
    set_text(r, "shape-1636", ["Mô tả ngắn việc cần làm,", "để agent viết mã ngay."], size=17)
    set_text(r, "shape-1635", ["Agent viết thiết kế và", "kế hoạch trước, rồi", "mới cài đặt."], size=17)
    add(r, text_block("gap", 189, 405, 600, 60,
                      ["Khoảng trống: chưa có thí nghiệm chỉ đổi lời dặn,",
                       "giữ nguyên đề, công cụ, mô hình, chấm bằng test ẩn."],
                      size=16, fill=BLUE, bold=True))


@page("p03_rq", 11, LOI, 40,
      "Người nói: Lợi, khoảng bốn mươi giây. Đề tài có sáu câu hỏi. RQ1 và RQ2 là phần hồi cứu: AI đã tham "
      "gia từng khâu của dự án ra sao, và mã AI viết phải sửa lại bao nhiêu. RQ3 đến RQ6 là phần thực "
      "nghiệm: làm theo đặc tả có đạt hơn vibe coding không và tốn thêm bao nhiêu; kết luận có giữ khi đổi "
      "công cụ của hãng khác; khi dùng mô hình mạnh hơn; và khi nhiệm vụ lớn dần.")
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


@page("p04_hypotheses", 11, LOI, 40,
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


@page("p05_vipharmind", 14, LOI, 30,
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


@page("p06_retro", 14, LOI, 45,
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


@page("p07_arms", 24, LOI, 35,
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


@page("p08_cohorts", 9, LOI, 30,
      "Người nói: Lợi, khoảng ba mươi giây. Có bốn nhóm chạy. Hai nhóm Claude dùng cùng Claude Code, một "
      "với Sonnet, một với Opus, để trả lời câu hỏi về mô hình mạnh hơn. Hai nhóm còn lại là Antigravity với "
      "Gemini và Codex với gpt-6-luna, để xem kết luận có giữ khi đổi hãng. Mọi công cụ chạy agent mặc định, "
      "mức effort medium, với thư mục HOME sạch: không skill, plugin hay MCP của người dùng.")
def _(r):
    set_text(r, "shape-1734", ["Bốn nhóm chạy, agent mặc định"])
    set_text(r, "shape-1735", ["claude-sonnet"], size=22)
    set_text(r, "shape-1740", ["Claude Code 2.1.325", "Claude Sonnet 5.5"], size=16)
    set_text(r, "shape-1736", ["claude-opus"], size=22)
    set_text(r, "shape-1732", ["Claude Code 2.1.325", "Claude Opus 5.5"], size=16)
    set_text(r, "shape-1739", ["agy-gemini"], size=22)
    set_text(r, "shape-1737", ["Antigravity CLI 1.5.9", "Gemini 3.8 Flash"], size=16)
    set_text(r, "shape-1733", ["codex-luna"], size=22)
    set_text(r, "shape-1738", ["Codex CLI 0.162.1", "gpt-6-luna"], size=16)
    add(r, text_block("stock", 189, 458, 600, 36,
                      ["Effort medium · HOME sạch: không skill, plugin, MCP"],
                      size=15, fill=BLUE, bold=True))


@page("p09_tiers", 25, LOI, 35,
      f"Người nói: Lợi, khoảng ba mươi lăm giây. Nhiệm vụ lấy từ commit thật của backend, chia ba tầng. "
      f"Tầng nhỏ có {N['Tasks']} nhiệm vụ, mỗi nhiệm vụ một commit, chọn từ {N['Candidates']} ứng viên qua "
      f"phễu sàng lọc và lấy mẫu phân tầng. Tầng vừa có {N['MediumTasks']} nhiệm vụ hai đến ba commit. Tầng "
      f"lớn có {N['FeatureTasks']} nhiệm vụ cỡ một tính năng. Bốn nhóm, hai cách làm, ba lần lặp cho tổng "
      f"{N['RunsTotal']} lượt chạy.")
def _(r):
    set_text(r, "shape-2228", [f"Ba tầng nhiệm vụ, {N['RunsTotal']} lượt"])
    cols = [("shape-2263", "shape-2259", "shape-2260", N["Tasks"], "Nhỏ",
             ["1 commit", f"{N['TaskSrcLinesMin']}–{N['TaskSrcLinesMax']} dòng", f"{N['RunsSmallTotal']} lượt"]),
            ("shape-2268", "shape-2261", "shape-2262", N["MediumTasks"], "Vừa",
             [f"{N['MediumCommitsMin']}–{N['MediumCommitsMax']} commit",
              f"{N['MediumSrcLinesMin']}–{N['MediumSrcLinesMax']} dòng", f"{N['RunsMediumTotal']} lượt"]),
            ("shape-2269", "shape-2264", "shape-2265", N["FeatureTasks"], "Lớn",
             [f"{N['FeatureCommitsMin']}–{N['FeatureCommitsMax']} commit",
              f"{N['FeatureSrcLinesMin']}–{N['FeatureSrcLinesMax']} dòng", f"{N['RunsLargeTotal']} lượt"]),
            ("shape-2270", "shape-2266", "shape-2267", N["RunsTotal"], "Tổng",
             ["4 nhóm × 2 cách", "× 3 lần lặp", f"{N['TasksMain']} nhiệm vụ"])]
    for num, head, body, k, h, b in cols:
        set_text(r, num, [k], role="numo")
        set_text(r, head, [h])
        set_text(r, body, b, size=17)


@page("p10_grading", 19, LOI, 30,
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


@page("p11_prereg", 21, LOI, 30,
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


@page("p12_threats", 23, LOI, 30,
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


@page("p13_results", 4, BAO, 10,
      "Người nói: Bảo, khoảng mười giây. Em là Bảo, em trình bày kết quả thực nghiệm cho RQ3 đến RQ6, rồi "
      "hạn chế và kết luận.")
def _(r):
    set_text(r, "shape-1483", ["02"], role="num")
    set_text(r, "shape-1491", ["Kết quả"], role="title")
    set_text(r, "shape-1484", ["Trần Ngọc Bảo · RQ3 đến RQ6"])


@page("p14_h1", 13, BAO, 50,
      "Người nói: Bảo, khoảng năm mươi giây. Đây là phép thử xác nhận duy nhất: hiệu số tỉ lệ đạt giữa làm "
      "theo đặc tả và vibe coding, ở nhóm Claude Sonnet, tầng nhỏ, kèm khoảng tin cậy chín mươi lăm phần trăm "
      "bootstrap theo nhiệm vụ. Số liệu đang chờ phân tích. Khi có số, em đọc kết luận theo đúng một trong ba "
      "cụm của quy tắc chốt trước: được ủng hộ, trái với giả thuyết, hoặc chưa kết luận được.")
def _(r):
    add(r, title_block("title", "H1 · Đặc tả có đạt nhiều hơn?", w=600))
    set_text(r, "shape-1856", [PENDING], size=64, role="num")
    set_text(r, "shape-1857", ["Hiệu số tỉ lệ đạt (đặc tả − vibe), Sonnet, tầng nhỏ, KTC 95%"], size=18)
    add(r, text_block("verdict", 75, 400, 600, 50,
                      [f"Kết luận: {PENDING}", "được ủng hộ / chưa kết luận được / trái với giả thuyết"],
                      size=16, fill=BLUE, bold=True))


@page("p15_rq4", 12, BAO, 35,
      "Người nói: Bảo, khoảng ba mươi lăm giây. Hình này cho hiệu số của từng nhóm chạy và từng tầng. Ba công "
      "cụ khác hãng và khác hạng mô hình, nên nhóm chỉ so hướng và độ lớn của hiệu số, không so công cụ này "
      "với công cụ kia. Số liệu đang chờ phân tích.")
def _(r):
    delete_icon_use(r, "imported/flat_slide_12_ill01")
    set_text(r, "shape-1841", ["RQ4: đổi công cụ,", "kết luận có giữ?"], role="title")
    set_text(r, "shape-1842", ["Hiệu số tỉ lệ đạt theo", "nhóm và tầng, KTC 95%.", "",
                               "So hướng và độ lớn,", "không so công cụ với", "công cụ.", "", PENDING],
             size=17)
    add(r, figure_slot("figure", "slot_pass_diff_by_cohort.png"))


@page("p16_h2h3", 14, BAO, 45,
      "Người nói: Bảo, khoảng bốn mươi lăm giây. H2 và H3 nói về cái giá và chất lượng. Làm theo đặc tả được "
      "dự đoán tốn nhiều token và thời gian hơn, nhưng cho mã ít lỗi tĩnh, ít hồi quy, và chỉ số bảo trì không "
      "kém hơn quá năm điểm. Ba con số này đang chờ phân tích.")
def _(r):
    add(r, text_block("kicker", 247.61, 14, 493, 52,
                      ["H2, H3 · Chi phí và chất lượng", "Hiệu theo cặp: đặc tả − vibe"],
                      size=16, fill=BLUE, bold=True, family=MONO, lead=1.4))
    set_text(r, "shape-1916", [PENDING], size=44, role="num")
    set_text(r, "shape-1917", ["Token và thời gian (H2)"], size=18)
    set_text(r, "shape-1918", [PENDING], size=44, role="num")
    set_text(r, "shape-1919", ["Lỗi tĩnh, hồi quy (H3)"], size=18)
    set_text(r, "shape-1920", [PENDING], size=44, role="num")
    set_text(r, "shape-1921", ["Chỉ số bảo trì, không kém hơn (H3)"], size=18)


@page("p17_h4", 23, BAO, 45,
      "Người nói: Bảo, khoảng bốn mươi lăm giây. H4 dùng thiết kế hai nhân hai: hai mô hình Claude trong cùng "
      "Claude Code, mỗi mô hình hai cách làm. Nếu đặc tả giúp mô hình yếu hơn nhiều hơn, khoảng cách ở Sonnet "
      "sẽ lớn hơn ở Opus. Nhóm cũng so Sonnet theo đặc tả với Opus vibe, cả tỉ lệ đạt lẫn chi phí. Số liệu "
      "đang chờ phân tích.")
def _(r):
    set_text(r, "shape-2199", ["H4 · Sonnet và Opus, tầng nhỏ"])
    set_text(r, "shape-2204", ["Sonnet"], role="head")
    set_text(r, "shape-2205", ["Opus"], role="head")
    set_text(r, "shape-2210", ["Đặc tả"], size=22, role="head")
    set_text(r, "shape-2208", [PENDING], size=16)
    set_text(r, "shape-2207", ["Vibe"], size=22, role="head")
    set_text(r, "shape-2209", [PENDING], size=16)
    set_text(r, "shape-2203", ["Đặc tả"], size=22, role="head")
    set_text(r, "shape-2201", [PENDING], size=16)
    set_text(r, "shape-2200", ["Vibe"], size=22, role="head")
    set_text(r, "shape-2202", [PENDING], size=16)
    add(r, text_block("diff", 113, 468, 740, 44,
                      [f"Hiệu của hai hiệu số: {PENDING} · Sonnet đặc tả so với Opus vibe: {PENDING}"],
                      size=14, fill=BLUE, bold=True))


@page("p18_h5", 12, BAO, 50,
      "Người nói: Bảo, khoảng năm mươi giây. Đây là H5, phép thử phụ quan trọng nhất. Mỗi điểm là một nhiệm "
      "vụ: trục ngang là số dòng của bản vá gốc, trục dọc là hiệu số tỉ lệ đạt. Phép thử chính là hiệu số ở "
      "tầng lớn trừ tầng nhỏ, gộp các nhóm chạy đủ cả ba tầng. H5 chỉ được ủng hộ khi khoảng tin cậy nằm hẳn "
      "trên không và mô hình logistic cùng hướng. Tầng lớn chỉ có ba nhiệm vụ, nên đây là bằng chứng sơ bộ. "
      "Số liệu đang chờ phân tích.")
def _(r):
    delete_icon_use(r, "imported/flat_slide_12_ill01")
    set_text(r, "shape-1841", ["H5: lợi ích tăng", "theo kích thước?"], role="title")
    set_text(r, "shape-1842", ["Mỗi điểm: một nhiệm vụ.", "",
                               "Phép thử: hiệu số tầng", "lớn trừ tầng nhỏ.", "", PENDING], size=17)
    add(r, figure_slot("figure", "slot_effect_vs_size.png"))


@page("p19_cost", 20, BAO, 35,
      "Người nói: Bảo, khoảng ba mươi lăm giây. Vì mọi lượt chạy bằng gói thuê bao, chi phí là số quy đổi từ "
      "token theo bảng giá API công khai chốt trước. Bảng này cho chi phí cho một lượt đạt theo từng nhóm và "
      "cách làm. Với Codex chỉ có cận dưới và cận trên. Số liệu đang chờ phân tích.")
def _(r):
    set_text(r, "shape-2122", ["Chi phí cho một lượt đạt (USD)"])
    rows = [("shape-2124", "shape-2123", "Sonnet"), ("shape-2127", "shape-2126", "Opus"),
            ("shape-2130", "shape-2129", "Gemini"), ("shape-2133", "shape-2132", "Luna")]
    for head, body, h in rows:
        set_text(r, head, [h], size=22)
        set_text(r, body, [f"Đặc tả {PENDING}", f"Vibe {PENDING}"], size=17)


@page("p20_case", 26, BAO, 40,
      "Người nói: Bảo, khoảng bốn mươi giây. Ca nghiên cứu lấy nhiệm vụ tầng lớn có hiệu số lớn nhất ở Claude "
      "Sonnet. Nhóm đặt cạnh nhau hai lượt, một theo đặc tả và một vibe: thiết kế và kế hoạch AI đã viết, chỗ "
      "sai, test ẩn nào trượt, và chi phí của mỗi lượt. Phần này đang chờ kết quả.")
def _(r):
    set_text(r, "shape-2285", ["Ca nghiên cứu"])
    set_text(r, "shape-2287", ["Nhiệm vụ"], role="head")
    set_text(r, "shape-2286", ["Tầng lớn, hiệu", "số lớn nhất ở", "Sonnet:", PENDING], size=16)
    set_text(r, "shape-2289", ["Hai lượt"], role="head")
    set_text(r, "shape-2288", ["Đặc tả:", PENDING, "", "Vibe:", PENDING], size=16)
    set_text(r, "shape-2291", ["Thiết kế, kế hoạch", "AI viết"], role="head")
    set_text(r, "shape-2290", [PENDING], size=16)
    set_text(r, "shape-2293", ["Chỗ sai, test trượt,", "chi phí"], role="head")
    set_text(r, "shape-2292", [PENDING], size=16)


@page("p21_agy", 6, BAO, 25,
      f"Người nói: Bảo, khoảng hai mươi lăm giây. Riêng nhóm Antigravity với Gemini: cả bốn tài khoản đã hết "
      f"hạn mức tuần, nên các lượt còn lại đang chờ hạn mức hồi. Ở chạy thử, mỗi lượt của nhóm này dùng "
      f"khoảng {N['PilotAgyInputMedianM']} triệu token vào, gấp khoảng {N['PilotAgyInputRatio']} lần Claude "
      f"Sonnet. Nếu nhóm này chưa đủ ở hạn chót thu dữ liệu, nhóm chỉ mô tả, không đưa vào phép thử.")
def _(r):
    set_text(r, "shape-1622", ["agy-gemini:", PENDING, "Hết hạn mức, chờ hạn mức hồi."], size=32)
    set_text(r, "shape-1621",
             [f"—Chạy thử: token vào ≈ {N['PilotAgyInputRatio']}× Claude Sonnet"], size=20, role="title")


@page("p22_limits", 8, BAO, 40,
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


@page("p23_conclusion", 7, BAO, 40,
      f"Người nói: Bảo, khoảng bốn mươi giây. Tóm lại, phần hồi cứu cho thấy ViPharmind thật sự được làm theo "
      f"quy trình spec, plan, với {N['FeatWithPlanPct']} phần trăm commit tính năng có plan đi trước, nhưng "
      f"mức sửa lại không khác nhóm không có plan. Kết luận cho H1, H5 và chi phí em sẽ đọc khi có kết quả. "
      f"Hướng tiếp theo là nhánh đặc tả có người duyệt, thêm dự án và thêm nhiệm vụ cỡ tính năng.")
def _(r):
    set_text(r, "shape-1634", ["Kết luận"])
    set_text(r, "shape-1638", ["Hồi cứu"])
    set_text(r, "shape-1636", [f"{N['FeatWithPlanPct']}% commit feat", "có plan; sửa lại",
                               "như nhau."], size=17)
    set_text(r, "shape-1637", ["Thực nghiệm"])
    set_text(r, "shape-1635", [f"H1: {PENDING}", f"H5: {PENDING}", f"Chi phí: {PENDING}"], size=15)
    add(r, text_block("next", 189, 405, 600, 60,
                      ["Hướng tiếp: đặc tả có người duyệt, thêm dự án,",
                       "thêm nhiệm vụ cỡ tính năng."], size=16, fill=BLUE, bold=True))


@page("p24_thanks", 15, BAO, 10,
      "Người nói: Bảo, khoảng mười giây. Bài trình bày của nhóm em đến đây là hết. Em cảm ơn thầy và các bạn "
      "đã lắng nghe; nhóm em xin nhận câu hỏi.")
def _(r):
    set_text(r, "shape-1949", ["Xin cảm ơn!"], role="title")
    add(r, text_block("qa", 81, 345, 390, 50, ["Hỏi đáp · Lợi và Bảo"], size=20, fill=INK, bold=True))


@page("p25_bk_funnel", 21, "Dự phòng", 0,
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


@page("p26_bk_reading", 24, "Dự phòng", 0,
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


@page("p27_bk_labels", 24, "Dự phòng", 0,
      "Slide dự phòng, dùng khi được hỏi về phân loại lỗi. Lợi và Bảo gán nhãn độc lập nguyên nhân thất bại "
      "cho mọi lượt không đạt của hai nhóm Claude, An phân xử chỗ lệch. Kappa và phân bố nhãn đang chờ kết quả.")
def _(r):
    set_text(r, "shape-2217", ["Dự phòng: nguyên nhân thất bại"])
    set_text(r, "shape-2220", ["Gán nhãn"])
    set_text(r, "shape-2218", ["Lợi và Bảo gán độc lập mọi lượt không đạt của hai",
                               "nhóm Claude; chín nhãn; An phân xử chỗ lệch."], size=17)
    set_text(r, "shape-2221", ["Kết quả"])
    set_text(r, "shape-2219", [f"Kappa của Cohen: {PENDING}", f"Phân bố nhãn theo cách làm: {PENDING}"],
             size=17)


@page("p28_attribution", 30, "Dự phòng", 0,
      "Slide ghi nguồn template Slidesgo, giữ lại theo điều kiện của bản miễn phí.")
def _(r):
    set_text(r, "shape-2412", ["Ghi nguồn"], role="title")
    set_text(r, "shape-2411", ["Mẫu slide: Slidesgo, Freepik", "Nhóm: Doãn Văn An, Lê Xuân Lợi,",
                               "Trần Ngọc Bảo"], size=20)
    set_text(r, "shape-2413", ["Slide này được giữ để ghi nguồn template."])


# Result slots: page -> keys of results/analysis/summary.json (analysis/README.md) that fill it. To fill a
# slot, have the report script export the value into numbers.json, then replace PENDING by N[...] here;
# replace images/slot_*.png by the real figure (PNG) of the same name.
RESULT_SLOTS = {
    "p14_h1": "h1.primary (estimate, ci_low, ci_high); verdicts.H1",
    "p15_rq4": "pass_diff.<cohort>.<tier> (estimate, ci_low, ci_high); verdicts.pass_diff.*; "
               "figure figures/pass_diff_by_cohort.pdf -> images/slot_pass_diff_by_cohort.png",
    "p16_h2h3": "secondary.tokens_total.*, secondary.wall_s.*, verdicts.H2.*; secondary.static_errors.*, "
                "secondary.regression_any.*, verdicts.H3a.*, verdicts.H3b.*; secondary.radon_mi_delta.*, "
                "verdicts.H3c.*",
    "p17_h4": "h4.small.rate.* (four cells), h4.small.diff.*, h4.small.diff_of_diffs, verdicts.H4.small; "
              "h4.small.sonnet_spec_minus_opus_vibe.{pass,cost_usd}, h4.small.sonnet_spec_over_opus_vibe.cost_ratio",
    "p18_h5": "h5.primary, verdicts.H5, h5.mixed_model; task_diffs.csv, pooled_task_diffs.csv; "
              "figure figures/effect_vs_size.pdf -> images/slot_effect_vs_size.png",
    "p19_cost": "cost_eff.<cohort>.small.<arm>.cost_per_pass (and passes_per_usd); cost_eff_upper.codex-luna.*",
    "p20_case": "case_study: task, the two runs, AI design and plan, what went wrong, failing hidden tests, cost",
    "p21_agy": "completeness, not_run_units; descriptive_incomplete.agy-gemini.* or pass_diff.agy-gemini.*",
    "p23_conclusion": "verdicts.H1, verdicts.H5; cost_eff summary",
    "p27_bk_labels": "labels: Cohen's kappa, label distribution by arm",
}


# ---------------------------------------------------------------- build


def fmt_secs(s: int) -> str:
    return f"{s // 60}:{s % 60:02d}"


def main():
    if not SVG_DIR.is_dir():
        sys.exit(f"missing workspace {SVG_DIR}; run build.sh")
    (WS / "images" / "logo-hust.png").write_bytes(LOGO.read_bytes())
    placeholder_png("slot_pass_diff_by_cohort.png", "figures/pass_diff_by_cohort.pdf", "pass_diff.<cohort>.<tier>")
    placeholder_png("slot_effect_vs_size.png", "figures/effect_vs_size.pdf", "h5.primary, task_diffs.csv")
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
    by = {s: sum(p["secs"] for p in PAGES if p["speaker"] == s) for s in (LOI, BAO)}
    (HERE / "rehearsal.md").write_text(
        "# Tập dượt\n\n"
        "Sinh tự động bởi `build_deck.py`; sửa thời lượng ở đó rồi chạy lại `build.sh`.\n\n"
        f"Tổng thời gian nói: {fmt_secs(t)} ({LOI} {fmt_secs(by[LOI])}, {BAO} {fmt_secs(by[BAO])}); "
        "phần còn lại của 15 phút dành cho chuyển slide và chuyển người nói. Hỏi đáp 5 phút sau đó.\n\n"
        "| Slide | Trang | Người nói | Thời lượng | Cộng dồn |\n| --- | --- | --- | --- | --- |\n"
        + "\n".join(rows) + "\n\n## Chỗ chờ kết quả\n\n"
        f"Các slide sau còn `{PENDING}`; khóa của `results/analysis/summary.json` sẽ điền vào:\n\n"
        + "\n".join(f"- `{k}`: {v}" for k, v in RESULT_SLOTS.items()) + "\n", encoding="utf-8")
    print(f"pages={len(PAGES)} talk={fmt_secs(t)} {by}")


if __name__ == "__main__":
    main()
