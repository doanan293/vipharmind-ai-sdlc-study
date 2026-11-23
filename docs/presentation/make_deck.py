"""Build the defense deck (vipharmind-slides.pptx) with python-pptx, no template.

Every number on a slide comes from docs/report/generated/numbers.json through N[...]; check_numbers.py checks
the built file. Speaker notes (Vietnamese, speaker-neutral) carry a timing cue; rehearsal.md lists the timing.
Run through build.sh, which also renders the PDF and runs the number check.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
REPORT = HERE.parent / "report"
N = json.loads((REPORT / "generated" / "numbers.json").read_text(encoding="utf-8"))
SUMMARY = json.loads((HERE.parents[1] / "data" / "results" / "analysis" / "main" / "summary.json")
                     .read_text(encoding="utf-8"))
WORK = HERE / "deck"  # git-ignored scratch: rendered figure PNGs
OUT = HERE / "vipharmind-slides.pptx"

FONT = "Be Vietnam Pro"
TITLE_FONT = "IBM Plex Mono"
TEMPLATE = HERE / "template-vi.pptx"
K = 10 / 13.333  # the grid below is drawn in 13.333 x 7.5 in; the template slide is 10 x 5.625 in


def I(v: float):  # noqa: E743
    return Inches(v * K)


def P(v: float):
    return Pt(v * K)
NAVY = RGBColor(0x0C, 0x0A, 0x9E)  # template blue
INK = RGBColor(0x1D, 0x1D, 0x1D)
GRAY = RGBColor(0x6B, 0x72, 0x80)
LIGHT = RGBColor(0xFF, 0xFF, 0xFF)  # panels: white on the template's pale background
LINE = RGBColor(0xD6, 0xD2, 0xF4)
PURPLE = RGBColor(0x82, 0x08, 0xD5)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
SPEC = RGBColor(0x2C, 0x28, 0xC8)  # spec-driven arm, everywhere (template blue, a shade lighter)
VIBE = RGBColor(0xEB, 0x91, 0x09)  # vibe arm, everywhere (template orange)
OK = RGBColor(0x2E, 0x9E, 0x6A)
BAD = RGBColor(0xC0, 0x39, 0x2B)

W, H = 13.333, 7.5
X0, X1 = 0.6, 12.73  # content margins (inches)
MAX_TALK = 20 * 60


def m(v: str) -> str:
    return v.replace("-", "−")


def ci(lo: str, hi: str) -> str:
    return f"[{m(N[lo])}; {m(N[hi])}]"


def sg(key: str) -> str:
    v = N[key]
    return m(v) if v.startswith("-") else "+" + v


def fnum(key: str) -> float:
    return float(N[key].replace(".", "").replace(",", "."))


def say(key: str) -> str:
    v = N[key]
    if "," in v and not v.split(",")[1].strip("0"):
        v = v.split(",")[0]
    return ("âm " + v[1:]) if v.startswith("-") else v


def usd(cohort: str, tier: str, arm: str) -> str:
    est = SUMMARY["estimates"]
    lo = est[f"cost_eff.{cohort}.{tier}.{arm}.cost_per_pass"]["estimate"]
    out = f"{lo:.2f}".replace(".", ",")
    if cohort == "codex-luna":
        out += "–" + f"{est[f'cost_eff_upper.{cohort}.{tier}.{arm}.cost_per_pass']['estimate']:.2f}".replace(".", ",")
    return out


H3A_BAD = sum(v == "contrary" for k, v in SUMMARY["verdicts"].items() if k.startswith("H3a."))

# ---------------------------------------------------------------- drawing helpers

PRS = Presentation(str(TEMPLATE))
for _sid in list(PRS.slides._sldIdLst):  # keep masters and layouts (the template's look), drop its slides
    PRS.part.drop_rel(_sid.rId)
    PRS.slides._sldIdLst.remove(_sid)
LAYOUT = {l.name: l for l in PRS.slide_layouts}
# Layouts whose decoration stays clear of the content area and the footer strip (measured on renders).
CONTENT_LAYOUTS = ["TITLE_ONLY", "CUSTOM_10_1_1", "CUSTOM_6_1", "CUSTOM_7", "CUSTOM_9", "CUSTOM_10_1_1_1"]


def new_slide(layout: str):
    s = PRS.slides.add_slide(LAYOUT[layout])
    for ph in list(s.placeholders):
        ph._element.getparent().remove(ph._element)
    return s
PAGES: list[dict] = []


def _runs(p, text: str, size: float, color, bold: bool, font: str = FONT):
    """**bold** spans become bold runs."""
    for i, part in enumerate(re.split(r"\*\*", text)):
        if not part:
            continue
        r = p.add_run()
        r.text = part
        f = r.font
        f.name, f.size, f.color.rgb = font, P(size), color
        f.bold = bold or i % 2 == 1


def text(slide, x, y, w, h, paras, size=16, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
         space=6, line=1.12, bullet=False, name=None, font=None):
    tb = slide.shapes.add_textbox(I(x), I(y), I(w), I(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    for i, item in enumerate([paras] if isinstance(paras, str) else paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line
        p.space_after = P(space)
        c, b, s = color, bold, size
        if isinstance(item, tuple):
            item, opt = item
            c, b, s = opt.get("color", c), opt.get("bold", b), opt.get("size", s)
        _runs(p, ("•  " if bullet else "") + item, s, c, b, font or FONT)
    return tb


def rect(slide, x, y, w, h, fill=LIGHT, line=None, shape=MSO_SHAPE.RECTANGLE, radius=None):
    sh = slide.shapes.add_shape(shape, I(x), I(y), I(w), I(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = P(1.25)
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        sh.adjustments[0] = radius
    style = sh._element.find(qn("p:style"))  # drop the theme style: no shadow, no default effects
    if style is not None:
        sh._element.remove(style)
    return sh


def panel(slide, x, y, w, h, title, items, accent=SPEC, size=15, bullet=True, title_size=16):
    rect(slide, x, y, w, h, fill=LIGHT, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
    rect(slide, x, y + 0.12, 0.07, h - 0.24, fill=accent)
    text(slide, x + 0.28, y + 0.18, w - 0.45, 0.4, title, size=title_size, color=accent, bold=True,
         font=TITLE_FONT)
    if items:
        text(slide, x + 0.28, y + 0.62, w - 0.45, h - 0.75, items, size=size, bullet=bullet)


def arrow(slide, x, y, w=0.36, h=0.3, color=GRAY):
    sh = rect(slide, x, y, w, h, fill=color, shape=MSO_SHAPE.RIGHT_ARROW)
    return sh


def bignum(slide, x, y, w, value, label, color=SPEC, size=40, label_size=14):
    text(slide, x, y, w, 0.75, value, size=size, color=color, bold=True, font=TITLE_FONT)
    text(slide, x, y + 0.8, w, 0.9, label, size=label_size, color=INK)


def chip(slide, x, y, label, color=VIBE, w=None):
    w = w or 0.12 * len(label) + 0.35
    sh = rect(slide, x, y, w, 0.32, fill=color, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
    tf = sh.text_frame
    tf.margin_left = tf.margin_right = I(0.08)
    tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _runs(p, label, 11, WHITE, True)
    return sh


def picture(slide, png: Path, x, y, w=None, h=None):
    return slide.shapes.add_picture(str(png), I(x), I(y),
                                    I(w) if w else None, I(h) if h else None)


def vn(v: float, dec: int = 1, suffix: str = "") -> str:
    return f"{v:.{dec}f}".replace(".", ",") + suffix


def bar_chart(slide, x, y, w, h, cats, series, colors, vmax=100, fmt='0.0', legend=True, size=12, dec=1,
              suffix=""):
    data = CategoryChartData()
    data.categories = cats
    for name, vals in series:
        data.add_series(name, vals)
    gf = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, I(x), I(y), I(w), I(h), data)
    ch = gf.chart
    ch.font.name, ch.font.size, ch.font.color.rgb = FONT, P(size), INK
    ch.has_legend = legend and len(series) > 1
    if ch.has_legend:
        ch.legend.position = XL_LEGEND_POSITION.TOP
        ch.legend.include_in_layout = False
    va = ch.value_axis
    va.maximum_scale, va.minimum_scale = vmax, 0
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = LINE
    va.format.line.fill.background()
    va.tick_labels.font.size = P(size - 1)
    ch.category_axis.format.line.color.rgb = LINE
    plot = ch.plots[0]
    plot.gap_width = 60
    plot.overlap = -10
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.number_format, dl.number_format_is_linked = fmt, False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    dl.font.size, dl.font.bold = P(size), True
    for (name, vals), s, c in zip(series, plot.series, colors):
        s.format.fill.solid()
        s.format.fill.fore_color.rgb = c
        for i, v in enumerate(vals):  # labels with a decimal comma
            tf = s.points[i].data_label.text_frame
            tf.text = vn(v, dec, suffix)
            r = tf.paragraphs[0].runs[0]
            r.font.size, r.font.bold, r.font.name = P(size), True, FONT
            s.points[i].data_label.position = XL_LABEL_POSITION.OUTSIDE_END
    ch.has_title = False
    return ch


def notes_cue(secs: int) -> str:
    return f"[Khoảng {secs} giây.] " if secs else ""


def content(section: str, title: str, claim: str | None, secs: int, notes: str, footer: str | None = None):
    """A content slide on the grid: section tag, title, claim sentence, footer note, page number."""
    s = new_slide(CONTENT_LAYOUTS[len(PRS.slides) % len(CONTENT_LAYOUTS)])
    text(s, X0, 0.42, 6, 0.32, section.upper(), size=11, color=VIBE, bold=True, anchor=MSO_ANCHOR.MIDDLE,
         font=TITLE_FONT)
    text(s, X0, 0.82, X1 - X0, 0.7, title, size=26, color=NAVY, bold=True, font=TITLE_FONT)
    if claim:
        text(s, X0, 1.52, X1 - X0, 0.7, claim, size=17, color=INK)
    rect(s, X0, 6.42, X1 - X0, 0.012, fill=LINE)
    if footer:
        text(s, X0, 6.5, X1 - X0 - 0.6, 0.5, footer, size=11.5, color=GRAY)
    text(s, X1 - 0.5, 6.5, 0.5, 0.3, str(len(PRS.slides)), size=11, color=GRAY, align=PP_ALIGN.RIGHT,
         name="pageno")
    s.notes_slide.notes_text_frame.text = notes_cue(secs) + notes
    PAGES.append(dict(title=title, section=section, secs=secs))
    return s


def dark(title: str, sub: list[str], secs: int, notes: str, section: str, layout: str = "TITLE"):
    s = new_slide(layout)
    s.notes_slide.notes_text_frame.text = notes_cue(secs) + notes
    PAGES.append(dict(title=title, section=section, secs=secs))
    return s


# ---------------------------------------------------------------- figures from the report

def figure_png(name: str) -> Path:
    WORK.mkdir(exist_ok=True)
    out = WORK / name
    subprocess.run(["pdftoppm", "-r", "250", "-png", "-singlefile",
                    str(REPORT / "generated" / "figures" / f"{name}.pdf"), str(out)], check=True)
    return out.with_suffix(".png")


# ---------------------------------------------------------------- slides

OPEN, CONTEXT, METHOD, FIND, CLOSE, BACKUP = ("Giới thiệu", "Nghiên cứu liên quan", "Phương pháp", "Kết quả",
                                              "Kết luận", "Dự phòng")


def s01_title():
    s = dark("Tiêu đề", [], 20,
             "(Chuyển người nếu chia ba phần: đây là phần một.) Em chào thầy và các bạn. Nhóm em gồm An, Lợi và "
             "Bảo. Đề tài hỏi: bắt coding agent làm theo quy trình spec-driven có bù được cho đề bài ngắn kiểu vibe "
             "coding không. Trước hết, một ca cụ thể.", OPEN)
    picture(s, REPORT / "images" / "logo-hust.png", 1.3, 0.75, h=0.95)
    text(s, 2.2, 0.83, 9, 0.4, "Đại học Bách khoa Hà Nội · Chuyên đề nghiên cứu 1 (IT5421)", size=14,
         color=NAVY, bold=True, font=TITLE_FONT)
    text(s, 2.2, 1.23, 9, 0.4, "Giảng viên: TS. Nguyễn Thanh Hùng", size=13, color=INK)
    text(s, 1.3, 2.35, 11, 1.8, ["Spec-driven development", "so với vibe coding"], size=46, color=NAVY,
         bold=True, space=0, line=1.05, font=TITLE_FONT)
    rect(s, 1.3, 4.3, 2.2, 0.06, fill=VIBE)
    text(s, 1.3, 4.55, 10.5, 0.9, "Nghiên cứu tình huống và thực nghiệm đối chứng trên một dự án phần mềm AI "
         "cho ngành dược Việt Nam", size=18, color=INK)
    text(s, 1.3, 5.6, 11, 0.9, ["Doãn Văn An (20252778M) · Lê Xuân Lợi (20252781M) · Trần Ngọc Bảo "
                                "(20251227M)"], size=15, color=INK, bold=True)


def s02_hook():
    s = content(OPEN, "Một ví dụ: nhiệm vụ f15",
                "Claude Sonnet làm đúng quy trình spec-driven nhưng vẫn không đạt hidden test.", 50,
                f"Nhóm em bắt đầu bằng một ví dụ: nhiệm vụ f15, cỡ một tính năng, Claude Sonnet làm theo quy trình "
                f"spec-driven. Ở một lượt, agent viết spec {N['ResCaseDesignLines']} dòng, chia plan thành "
                f"{N['ResCasePlanTasks']} task, tự viết {N['ResCaseSpecTests']} test và tất cả đều đạt. Nhưng khi "
                f"chấm bằng hidden test, test mà agent không thấy, bài vẫn trượt; cả ba lượt spec của f15 đều trượt "
                f"cùng một test. Làm đủ quy trình mà vẫn trượt, vì sao? Nhóm em sẽ quay lại ở phần kết quả.",
                footer="Hidden test: test mà commit gốc thêm vào, agent không thấy khi làm.")
    steps = [("1 · Spec", f"Viết spec {N['ResCaseDesignLines']} dòng cho tính năng", SPEC),
             ("2 · Plan", f"Chia {N['ResCasePlanTasks']} task, làm lần lượt theo TDD", SPEC),
             ("3 · Test agent", f"Tự viết {N['ResCaseSpecTests']} test mới: tất cả đạt", OK),
             ("4 · Hidden test", f"Trượt: {N['ResCaseSpecPassed']}/{N['ResCaseReps']} lượt đạt", BAD)]
    bw = 2.68
    for i, (t, d, c) in enumerate(steps):
        x = X0 + i * (bw + 0.47)
        panel(s, x, 2.45, bw, 1.75, t, [d], accent=c, size=15, bullet=False)
        if i < 3:
            arrow(s, x + bw + 0.06, 3.2)
    text(s, X0, 4.6, X1 - X0, 1.8,
         ["Agent làm đúng từng bước của quy trình, và test của chính nó đều đạt.",
          "Nhưng bài chấm độc lập vẫn trượt: cả ba lượt spec của f15 trượt **cùng một hidden test**.",
          ("Vì sao làm đủ quy trình mà vẫn trượt?", {"color": BAD, "bold": True})], size=18, bullet=False,
         space=10)


def s03_promise():
    s = content(OPEN, "Vibe coding và spec-driven development",
                "Spec-driven development được kỳ vọng bù cho phần đề bài còn thiếu bằng các bước spec, plan và test.", 50,
                "Ca này liên quan trực tiếp tới cách spec-driven được giới thiệu. Cách giao việc phổ biến nhất cho coding agent là vibe coding: vài "
                "câu ngắn, phần đề bỏ ngỏ thì agent tự đoán. Spec-driven development được kỳ vọng bù chỗ đó: viết spec, plan, "
                "viết test trước rồi mới cài đặt và kiểm lại. Một hiện thực được dùng rộng rãi là Superpowers, repo "
                "GitHub khoảng ba trăm hai mươi tư nghìn sao. Nhóm em kiểm tra kỳ vọng này đúng đến đâu.",
                footer="Superpowers: github.com/obra/superpowers (324,5k sao): “An agentic skills framework & software "
                       "development methodology that works.”")
    panel(s, X0, 2.4, 5.85, 2.9, "Vibe coding",
          ["Giao việc bằng vài câu; agent viết mã ngay.", "Chi tiết đề bỏ ngỏ thì agent tự đoán.",
           "Nhanh, nhưng dễ lệch khỏi ý người giao việc."], accent=VIBE, size=17)
    panel(s, X0 + 6.28, 2.4, 5.85, 2.9, "Spec-driven (Superpowers)",
          ["Spec (thiết kế) → plan → viết test trước (TDD) → cài đặt → chạy lại toàn bộ test.",
           "Kỳ vọng: agent ít đoán sai hơn và để lại bộ test.", "Chi phí: thêm thời gian và token."],
          accent=SPEC, size=17)
    text(s, X0, 5.6, X1 - X0, 1.0, [("Câu hỏi: quy trình này có thật sự làm agent làm đúng hơn không, và đổi lại "
                                     "tốn bao nhiêu?", {"bold": True, "color": NAVY})], size=18)


def s04_rq():
    s = content(OPEN, "Câu hỏi nghiên cứu",
                "Lịch sử git của một dự án thật trả lời RQ1–2; thực nghiệm đối chứng trả lời RQ3–6.", 45,
                "Nhóm em chia thành hai phần. Phần một đọc lịch sử git của một dự án thật để trả lời RQ1 và RQ2. "
                "Phần hai là thực nghiệm đối chứng cho RQ3 đến RQ6: spec có đạt hơn không, tốn bao nhiêu, và kết luận "
                "có giữ khi đổi công cụ, đổi mô hình, khi nhiệm vụ lớn dần. Phép thử chính được chốt trước khi chạy: "
                "giả thuyết H1, trên Sonnet, nhiệm vụ nhỏ.",
                footer="Phép thử chính, chốt trước khi chạy: H1 (spec đạt nhiều hơn vibe) trên Claude Sonnet, nhiệm vụ "
                       "nhỏ. Mọi phép so khác là phụ.")
    panel(s, X0, 2.4, 4.6, 3.1, "Lịch sử git",
          ["**RQ1.** AI tham gia các khâu ra sao; quy trình spec để lại dấu vết gì?",
           "**RQ2.** Mã tính năng phải sửa lại bao nhiêu; có plan thì ít sửa hơn không?"], accent=VIBE, size=16)
    panel(s, X0 + 4.95, 2.4, 7.18, 3.1, "Thực nghiệm đối chứng",
          ["**RQ3.** Spec có đạt hidden test nhiều hơn vibe không, tốn thêm bao nhiêu?",
           "**RQ4.** Kết luận có giữ khi đổi công cụ (Claude Code, Codex)?",
           "**RQ5.** Mô hình mạnh hơn (Opus so với Sonnet) thì sao?",
           "**RQ6.** Nhiệm vụ lớn dần, từ một commit tới một tính năng, thì sao?"], accent=SPEC, size=16)
    text(s, X0, 5.8, X1 - X0, 0.8, "Phần git là quan sát; câu hỏi nhân quả (spec có làm agent làm đúng hơn không) "
         "được trả lời bằng thực nghiệm.", size=16, color=GRAY)


def s05_related():
    s = content(CONTEXT, "Nghiên cứu liên quan",
                "Chưa có thí nghiệm nào giữ nguyên đề, agent và mô hình, chỉ đổi prompt quy trình, rồi chấm bằng "
                "hidden test.", 50,
                "Bốn nghiên cứu gần nhất. Hill quan sát pull request mã nguồn mở: có tài liệu spec cũng không ít lỗi "
                "hơn, nhưng đó là quan sát. FeatBench chấm agent bằng hidden test nhưng so mô hình với nhau, không so "
                "quy trình. Mock và Russo so bốn cách tương tác khi viết test trước. Agarwal và cộng sự phỏng vấn "
                "người làm nghề: spec đáng tin hơn nhưng tốn công. Khoảng trống là một thí nghiệm có đối chứng chỉ đổi "
                "prompt quy trình.",
                footer="Bằng chứng định lượng còn ít và trái chiều: chấm bằng mô hình thấy cải thiện nhỏ (Taghavi và "
                       "cs.); nghiên cứu quan sát lớn nhất không thấy giảm lỗi (Hill).")
    rows = [("Hill", "Quan sát pull request mã nguồn mở: có spec không ít lỗi hơn", "Thí nghiệm có đối chứng"),
            ("FeatBench (Chen và cs.)", "Hidden test cho tính năng mới; so các mô hình", "Giữ mô hình, so quy trình"),
            ("Mock và Russo", "Bốn cách tương tác khi làm theo TDD", "Spec vs vibe, không người can thiệp"),
            ("Agarwal và cs.", "Phỏng vấn: spec đáng tin hơn nhưng tốn công", "Đo bằng tỉ lệ đạt và token")]
    cols = [(X0, 3.0, "Nghiên cứu"), (X0 + 3.15, 5.2, "Họ làm gì"), (X0 + 8.6, 3.5, "Nghiên cứu này khác ở")]
    for x, w, h_ in cols:
        text(s, x, 2.4, w, 0.35, h_, size=13, color=GRAY, bold=True)
    for i, row in enumerate(rows):
        y = 2.85 + i * 0.92
        rect(s, X0, y - 0.08, X1 - X0, 0.82, fill=LIGHT if i % 2 == 0 else WHITE)
        for (x, w, _), val, c, b in zip(cols, row, (NAVY, INK, SPEC), (True, False, True)):
            text(s, x + 0.12, y + 0.06, w - 0.2, 0.7, val, size=15, color=c, bold=b, anchor=MSO_ANCHOR.MIDDLE)


def s06_project():
    s = content(METHOD, "Dự án ViPharmind",
                "Nhiệm vụ của thí nghiệm lấy từ một dự án được làm bằng chính quy trình cần kiểm.", 45,
                f"Dự án nhóm em dùng là ViPharmind, trợ lý AI tra cứu thuốc cho người Việt, do An xây dựng theo quy "
                f"trình Superpowers. Kho mã có {N['Commits']} commit trong khoảng bốn tháng và {N['SpecPlanFiles']} "
                f"file spec, plan. Nhóm chọn dự án này vì nó được làm bằng chính quy trình cần kiểm, có test thật để "
                f"chấm, và lịch sử bắt đầu sau mốc dữ liệu huấn luyện của các mô hình, nên ít rủi ro mô hình đã thấy "
                f"lời giải.",
                footer="Đối tượng đo là quá trình phát triển có AI tham gia; chất lượng trả lời của ViPharmind nằm ngoài "
                       "phạm vi.")
    text(s, X0, 2.45, 7.1, 4.0,
         ["Trợ lý AI tra cứu thuốc cho người Việt: backend agent bằng Python, ứng dụng web, kho tri thức từ Dược "
          "thư Quốc gia.",
          "Làm theo Superpowers: spec → plan → TDD; theo tác giả, AI tham gia mọi khâu.",
          "Có test thật để chấm, và lịch sử bắt đầu sau mốc dữ liệu huấn luyện của các mô hình được thử."],
         size=18, bullet=True, space=14)
    rect(s, 8.3, 2.4, 4.43, 3.85, fill=LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    bignum(s, 8.65, 2.6, 3.9, N["Commits"], f"commit, từ {N['FirstDate']} đến {N['LastDate']}")
    bignum(s, 8.65, 4.45, 3.9, N["SpecPlanFiles"], "file spec và plan trong lịch sử git")


def s07_git():
    s = content(METHOD, "Kết quả phân tích lịch sử git (RQ1, RQ2)",
                "Đa số commit tính năng có plan đi trước, nhưng vẫn bị sửa lại nhiều như commit không có plan.",
                50,
                f"Lịch sử git cho hai ý. Thứ nhất, nếp spec, plan rất rõ: {N['FeatWithPlanPct']} phần trăm commit "
                f"tính năng có plan đi trước nêu đúng file. Quy tắc nối đúng {N['LinkCorrect']} trên "
                f"{N['LinkChecked']} lần kiểm tay và hay nối thừa, nên đây là cận trên. Thứ hai, commit có plan và "
                f"không có plan bị sửa lại gần như bằng nhau: {say('ReworkWithPlanMean')} và "
                f"{say('ReworkWithoutPlanMean')} commit sửa trong mười bốn ngày. Đây chỉ là quan sát; muốn biết nhân "
                f"quả phải làm thí nghiệm.",
                footer="Muốn biết spec có làm mã tốt hơn không thì phải làm thí nghiệm có đối chứng: phần tiếp theo.")
    rect(s, X0, 2.4, 5.9, 2.35, fill=LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    bignum(s, X0 + 0.35, 2.55, 5.3, f"{N['FeatWithPlanPct']}%",
           f"commit tính năng có plan đi trước ({N['FeatWithPlan']}/{N['CommitsFeat']}); quy tắc nối đúng "
           f"{N['LinkCorrect']}/{N['LinkChecked']} khi kiểm tay, hay nối thừa nên là cận trên")
    rect(s, X0 + 6.23, 2.4, 5.9, 2.35, fill=LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    bignum(s, X0 + 6.58, 2.55, 5.3, f"{N['ReworkWithPlanMean']} ≈ {N['ReworkWithoutPlanMean']}",
           "commit sửa lại trong 14 ngày sau mỗi commit tính năng: có plan ≈ không có plan")
    text(s, X0, 5.05, X1 - X0, 1.6,
         ["Git không cho biết dòng nào do AI viết: “AI tham gia mọi khâu” dựa trên lời khai của tác giả.",
          "Hai nhóm commit khác nhau về thời điểm và loại việc, nên đây chỉ là quan sát, chưa phải nhân quả."],
         size=16, bullet=True)


def s08_prompts():
    s = content(METHOD, "Thiết kế thí nghiệm: hai cách làm",
                "Cùng đề bài, mô hình, công cụ và giới hạn thời gian; chỉ khác đoạn prompt đặt trước đề bài.", 45,
                "Thí nghiệm có hai nhánh, chỉ khác một đoạn prompt quy trình đặt trước đề bài. Vibe: một câu, hãy cài "
                "đặt thay đổi sau. Spec-driven: trong cùng một phiên, viết docs/design.md, viết docs/plan.md, làm từng "
                "phần theo kiểu viết test trước, rồi chạy cả bộ test. Mọi thứ khác giữ nguyên, và không có người hỏi "
                "lại hay duyệt spec, vì các lượt chạy tự động.",
                footer="Prompt viết lại từ các bước của Superpowers để chạy y hệt trên Claude Code và Codex; nguyên văn "
                       "ở phụ lục báo cáo.")
    panel(s, X0, 2.4, 5.85, 2.6, "Vibe coding",
          ["Một câu: “Implement the following change in this repository.”", "Sau đó là đề bài."], accent=VIBE,
          size=17, bullet=False)
    panel(s, X0 + 6.28, 2.4, 5.85, 2.6, "Spec-driven",
          ["Viết docs/design.md (spec) → docs/plan.md → làm từng phần, viết test trước → chạy cả bộ test "
           "backend trước khi dừng.", "Sau đó là đề bài (giống hệt nhánh vibe)."], accent=SPEC, size=17,
          bullet=False)
    text(s, X0, 5.3, X1 - X0, 1.3,
         ["Chạy không người: bỏ bước hỏi lại người dùng và bước người duyệt spec của Superpowers.",
          "Mọi lượt spec đều để lại cả hai file; không lượt vibe nào viết chúng: can thiệp được thực hiện đúng."],
         size=16, bullet=True)


def s09_tasks():
    s = content(METHOD, "Bộ nhiệm vụ",
                f"{N['TasksMain']} nhiệm vụ lấy từ commit thật của ViPharmind, chia ba tầng theo kích thước.", 55,
                f"Nhiệm vụ cắt từ commit thật của backend, ba cỡ: {N['Tasks']} nhiệm vụ nhỏ một commit, "
                f"{N['MediumTasks']} vừa, {N['FeatureTasks']} lớn cỡ một tính năng. Mỗi nhiệm vụ có mã nền là commit "
                f"cha, một đề bài năm đến mười câu, và hidden test là test mà commit gốc thêm vào. Để hidden test chấm "
                f"được, đề phải nêu tên hàm và chữ ký; nghĩa là đề chi tiết thực chất đã là một bản spec do người viết. "
                f"Điểm này sẽ quan trọng ở cuối bài.",
                footer="Ứng viên tầng nhỏ được lọc tự động (test hỏng ở mã nền, đạt ở commit gốc) rồi chọn ngẫu nhiên "
                       "theo lớp mã với hạt giống cố định.")
    cols = [("Nhỏ", N["Tasks"], "1 commit", f"{N['TaskSrcLinesMin']}–{N['TaskSrcLinesMax']} dòng"),
            ("Vừa", N["MediumTasks"], f"{N['MediumCommitsMin']}–{N['MediumCommitsMax']} commit",
             f"{N['MediumSrcLinesMin']}–{N['MediumSrcLinesMax']} dòng"),
            ("Lớn", N["FeatureTasks"], f"{N['FeatureCommitsMin']}–{N['FeatureCommitsMax']} commit",
             f"{N['FeatureSrcLinesMin']}–{N['FeatureSrcLinesMax']} dòng")]
    for i, (t, n_, a, b) in enumerate(cols):
        x = X0 + i * 4.1
        rect(s, x, 2.4, 3.85, 1.75, fill=LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
        text(s, x + 0.3, 2.5, 1.4, 1.0, n_, size=44, color=SPEC, bold=True)
        text(s, x + 1.55, 2.62, 2.2, 1.4, [(f"Tầng {t.lower()}", {"bold": True, "color": NAVY}), a, b], size=15,
             space=2)
    text(s, X0, 4.5, X1 - X0, 2.1,
         ["Đề bài năm đến mười câu: nêu việc cần làm và giao diện phải giữ, không nêu cách cài đặt.",
          "Để hidden test chấm được, đề phải nêu tên hàm và chữ ký: **đề chi tiết thực chất là một bản spec do "
          "người viết**."], size=17, bullet=True, space=10)


def s10_runs():
    s = content(METHOD, "Cohort và số lượt chạy",
                f"3 cohort × 2 cách làm × 3 lần lặp × {N['TasksMain']} nhiệm vụ = {N['ResRuns']} lượt hợp lệ.", 45,
                f"Ba cohort: Claude Code với Sonnet và với Opus để so mô hình, Codex để so hãng. Ba cohort, hai cách, "
                f"ba lần lặp, {N['TasksMain']} nhiệm vụ: {N['ResRuns']} lượt. Mỗi lượt có một thư mục HOME sạch, không "
                f"skill hay plugin riêng, mức suy luận medium, thứ tự chạy xáo ngẫu nhiên. Antigravity với Gemini hết "
                f"quota ở {N['ResAgyDone']} trên {N['ResRunsPerCohort']} lượt nên bị loại.",
                footer=f"Antigravity + Gemini 3.8 Flash hết quota ở {N['ResAgyDone']}/{N['ResRunsPerCohort']} lượt nên "
                       "bị loại; quyết định ghi trong nhật ký sai lệch của preregistration.")
    cos = [("claude-sonnet", ["Claude Code + Sonnet 5.5", "Phép thử chính; so mô hình"]),
           ("claude-opus", ["Claude Code + Opus 5.5", "So mô hình (RQ5)"]),
           ("codex-luna", ["Codex CLI + gpt-6-luna", "So công cụ và hãng (RQ4)"])]
    for i, (t, b) in enumerate(cos):
        panel(s, X0 + i * 4.1, 2.4, 3.85, 1.95, t, b, accent=SPEC, size=15, bullet=False)
    text(s, X0, 4.7, X1 - X0, 1.9,
         ["Mỗi lượt: HOME sạch (không skill, plugin, bộ nhớ), mức suy luận medium, thứ tự chạy xáo ngẫu nhiên.",
          "Giới hạn thời gian theo cỡ nhiệm vụ; không lượt nào hết giờ, thoát lỗi hay lỗi harness."],
         size=16, bullet=True)


def s11_grading():
    s = content(METHOD, "Cách chấm",
                "Một lượt đạt khi mọi hidden test đạt và không test cũ nào hỏng.", 45,
                "Một lượt đạt khi mọi hidden test đạt và không test cũ nào hỏng. Trước khi chấm, grader bỏ hai file "
                "spec, đưa mọi test cũ về bản gốc rồi mới chép hidden test vào, nên agent không thể đạt bằng cách sửa "
                "test. Ngoài tỉ lệ đạt, nhóm đo token, thời gian, lỗi static analysis, maintainability index và test "
                "mà agent tự viết.",
                footer=f"Kiểm tra mù {N['PassCheckRuns']} lượt đạt ngẫu nhiên: cả {N['PassCheckCorrect']} đều đúng "
                       "thật, không có trường hợp “đạt test nhưng sai”.")
    steps = [("Patch", "bản vá của agent"), ("Dọn", "bỏ design.md, plan.md"), ("Reset", "test cũ về bản gốc"),
             ("Chép", "thêm hidden test"), ("Chạy", "toàn bộ pytest")]
    bw = 2.05
    for i, (t, d) in enumerate(steps):
        x = X0 + i * (bw + 0.47)
        panel(s, x, 2.45, bw, 1.45, t, [d], accent=SPEC if i < 4 else OK, size=14, bullet=False)
        if i < 4:
            arrow(s, x + bw + 0.06, 3.02)
    text(s, X0, 4.3, X1 - X0, 2.3,
         ["Agent không thấy hidden test; sửa test cũ cũng vô ích vì test cũ bị đưa về bản gốc trước khi chấm.",
          "Chỉ số phụ: token, thời gian, lỗi static analysis (ruff, pyrefly), maintainability index, test do agent "
          "tự viết."], size=16, bullet=True)


def s12_prereg():
    s = content(METHOD, "Preregistration",
                "Giả thuyết, nhiệm vụ và mã phân tích được chốt bằng git tag trước khi mở kết quả.", 45,
                "Để tránh chọn kết quả sau khi đã thấy số liệu, mọi thứ được chốt bằng git tag trước khi mở kết quả: giả thuyết và kế hoạch "
                "phân tích, rồi nhiệm vụ tầng vừa và lớn, rồi mã phân tích. Trước mỗi tag, một agent AI riêng là "
                "Fable phản biện độc lập. Cây mã giao cho agent không có lịch sử git hay spec cũ, để không lộ lời "
                "giải. Kết quả được đọc theo quy tắc chốt trước: khoảng tin cậy nằm hẳn về một phía mới kết luận.",
                footer="Cách đọc chốt trước: KTC 95% nằm hẳn về phía giả thuyết → ủng hộ; nằm hẳn phía ngược lại → "
                       "trái; còn lại → chưa kết luận được.")
    steps = [("prereg-v1", "giả thuyết, kế hoạch phân tích, tầng nhỏ"), ("prereg-v1.1", "nhiệm vụ tầng vừa, lớn"),
             ("analysis", "mã phân tích, chạy được trên dữ liệu thử"), ("Mở kết quả", "thay đổi sau đó đều ghi lại")]
    bw = 2.75
    for i, (t, d) in enumerate(steps):
        x = X0 + i * (bw + 0.38)
        panel(s, x, 2.45, bw, 1.55, f"{i + 1} · {t}", [d], accent=SPEC if i < 3 else VIBE, size=14, bullet=False)
        if i < 3:
            arrow(s, x + bw + 0.03, 3.07, w=0.32)
    text(s, X0, 4.35, X1 - X0, 2.3,
         ["Trước mỗi tag, Fable 5.2 (một agent AI chạy riêng) phản biện độc lập.",
          "Tránh lộ lời giải: cây mã không có lịch sử git, spec hay plan cũ; ghi mọi đường dẫn tới repo gốc để "
          "phân tích độ nhạy."], size=16, bullet=True)


def s13_h1():
    s = content(FIND, "Kết quả H1: tỉ lệ đạt với đề chi tiết",
                "Phép thử chính (Sonnet, nhiệm vụ nhỏ) chưa kết luận được; dữ liệu không ủng hộ một lợi ích đáng kể của spec.", 55,
                f"(Chuyển người nếu chia ba phần: phần hai.) Đây là phép thử chính: Sonnet, nhiệm vụ nhỏ. Spec đạt "
                f"{N['ResHOneSpecPct']} phần trăm, vibe {N['ResHOneVibePct']}, hiệu số {say('ResHOneEstPp')} điểm phần "
                f"trăm, khoảng tin cậy từ {say('ResHOneLowPp')} đến {say('ResHOneHighPp')}. Khoảng chứa 0 nên H1 chưa "
                f"kết luận được. Nhưng cận trên bằng 0, nên dữ liệu không ủng hộ một lợi ích đáng kể; với "
                f"{N['Tasks']} nhiệm vụ thì chưa loại được một lợi ích nhỏ. Các phân tích độ nhạy cho cùng kết luận.",
                footer=f"Hiệu số theo nhiệm vụ, KTC 95% bootstrap lấy mẫu lại {N['Tasks']} nhiệm vụ. Ba lần lặp cho kết "
                       f"quả khác nhau ở {N['ResVarDisagree']}/{N['ResVarCells']} ô.")
    bar_chart(s, X0, 2.3, 5.4, 3.95, ["Sonnet, nhiệm vụ nhỏ"],
              [("Spec-driven", [fnum("ResHOneSpecPct")]), ("Vibe", [fnum("ResHOneVibePct")])], [SPEC, VIBE],
              vmax=100, fmt='0.0"%"', size=13, dec=1, suffix="%")
    rect(s, 6.45, 2.45, 6.28, 3.8, fill=LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    bignum(s, 6.8, 2.6, 5.7, f"{m(N['ResHOneEstPp'])} pp",
           f"spec − vibe, KTC 95% {ci('ResHOneLowPp', 'ResHOneHighPp')}", size=44, label_size=16)
    text(s, 6.8, 4.25, 5.7, 2.2,
         ["KTC chứa 0 → **chưa kết luận được**.", "Cận trên 0,0: không ủng hộ một lợi ích đáng kể.",
          f"Với {N['Tasks']} nhiệm vụ, chưa loại được một lợi ích nhỏ."], size=16, bullet=True)


def s14_cohorts(forest: Path):
    s = content(FIND, "Kết quả theo cohort (RQ4, RQ5)",
                "Với Claude, hiệu số spec − vibe âm hoặc bằng 0 ở gần như mọi tầng; chỉ Codex ở tầng lớn nghiêng về spec.", 55,
                f"Mỗi hàng là một cohort ở một tầng; chấm là hiệu số, vạch ngang là khoảng tin cậy, đường dọc là 0. "
                f"Với Claude, hiệu số âm hoặc bằng 0 ở gần như mọi tầng. Ô duy nhất nghiêng về spec là Codex tầng lớn, "
                f"{N['ResCodexLargeSpecPct']} so với {N['ResCodexLargeVibePct']} phần trăm, nhưng chỉ ba nhiệm vụ và "
                f"là một trong {N['ResSecondaryComparisons']} phép so phụ không hiệu chỉnh. Mô hình mạnh hơn hay yếu "
                f"hơn cũng không đổi gì: H4 chưa kết luận được.",
                footer=f"H4 (spec giúp Sonnet nhiều hơn Opus): hiệu của hai hiệu số {sg('ResHFourDiffOfDiffsPp')} pp "
                       f"{ci('ResHFourDiffOfDiffsLowPp', 'ResHFourDiffOfDiffsHighPp')}, chưa kết luận được.")
    picture(s, forest, X0, 2.3, w=7.2)
    text(s, 8.15, 2.45, 4.58, 4.2,
         [f"**Claude (Sonnet, Opus):** hiệu số ≤ 0 ở mọi tầng, trừ Sonnet tầng vừa ({sg('ResSonnetMediumDiffPp')} "
          f"pp, chỉ tham khảo).",
          f"**Codex tầng lớn:** {N['ResCodexLargeSpecPct']}% vs {N['ResCodexLargeVibePct']}%, nhưng chỉ "
          f"{N['FeatureTasks']} nhiệm vụ; KTC co về một điểm.",
          f"Một ô “ủng hộ” trong {N['ResSecondaryComparisons']} phép so phụ không hiệu chỉnh: cần đọc thận trọng."],
         size=15, bullet=True, space=10)


def s15_size(scatter: Path):
    s = content(FIND, "Kết quả theo kích thước nhiệm vụ (RQ6)",
                "Hiệu số không tăng rõ khi nhiệm vụ lớn hơn; H5 chưa kết luận được.", 45,
                f"Mỗi điểm là một nhiệm vụ: đậm là trung bình ba cohort, nhạt là từng cohort; trục ngang là số dòng "
                f"của patch gốc. Hiệu số gộp ở tầng lớn trừ tầng nhỏ là {say('ResHFiveEstPp')} điểm, khoảng từ "
                f"{say('ResHFiveLowPp')} đến {say('ResHFiveHighPp')}. Hệ số tương tác của mô hình hỗn hợp cũng chứa 0. "
                f"Phần lớn nhiệm vụ có hiệu số bằng 0, và các nhiệm vụ lệch nằm ở cả hai phía.",
                footer=f"Tầng vừa có {N['MediumTasks']} và tầng lớn có {N['FeatureTasks']} nhiệm vụ, nên các khoảng tin "
                       "cậy ở hai tầng này chỉ để tham khảo.")
    picture(s, scatter, X0, 2.3, w=7.0)
    text(s, 8.0, 2.45, 4.73, 4.2,
         [f"Tầng lớn − tầng nhỏ: **{sg('ResHFiveEstPp')} pp** {ci('ResHFiveLowPp', 'ResHFiveHighPp')}.",
          f"Hệ số tương tác (logit): {N['ResHFiveCoef']} {ci('ResHFiveCoefLow', 'ResHFiveCoefHigh')}.",
          "Phần lớn nhiệm vụ có hiệu số 0; nhiệm vụ lệch nằm ở cả hai phía và ở mọi cỡ."],
         size=16, bullet=True, space=10)


def s16_cost():
    s = content(FIND, "Chi phí (H2)",
                f"Spec tốn gấp {N['ResTokenRatioMin']}–{N['ResTokenRatioMax']} lần token và "
                f"{N['ResWallRatioMin']}–{N['ResWallRatioMax']} lần thời gian ở mọi cohort và tầng (H2 được ủng hộ).",
                45,
                f"Về chi phí, spec tốn gấp {N['ResTokenRatioMin']} đến {N['ResTokenRatioMax']} lần token và "
                f"{N['ResWallRatioMin']} đến {N['ResWallRatioMax']} lần thời gian, ở mọi ô. Quy đổi theo giá API, một "
                f"lượt đạt của Sonnet ở nhiệm vụ nhỏ tốn {usd('claude-sonnet', 'small', 'spec')} đô với spec, so với "
                f"{usd('claude-sonnet', 'small', 'vibe')} đô với vibe. Chỉ ở Codex tầng lớn spec mới rẻ hơn, vì vibe "
                f"gần như không đạt.",
                footer="Chi phí quy đổi theo bảng giá API công khai; mọi lượt chạy bằng gói thuê bao. Codex chỉ có cận "
                       "dưới và cận trên của giá.")
    rows = [("Sonnet", "claude-sonnet"), ("Opus", "claude-opus"), ("Codex", "codex-luna")]
    bar_chart(s, X0, 2.3, 6.6, 3.95, ["Sonnet, nhỏ", "Opus, nhỏ", "Sonnet, lớn", "Opus, lớn"],
              [("Spec-driven", [float(usd(c, t, "spec").replace(",", ".")) for c, t in
                                [("claude-sonnet", "small"), ("claude-opus", "small"), ("claude-sonnet", "large"),
                                 ("claude-opus", "large")]]),
               ("Vibe", [float(usd(c, t, "vibe").replace(",", ".")) for c, t in
                         [("claude-sonnet", "small"), ("claude-opus", "small"), ("claude-sonnet", "large"),
                          ("claude-opus", "large")]])],
              [SPEC, VIBE], vmax=9, fmt='0.00', size=12, dec=2)
    text(s, X0, 2.12, 6.6, 0.3, "USD quy đổi cho một lượt đạt (Claude)", size=12, color=GRAY, bold=True)
    rect(s, 7.6, 2.45, 5.13, 3.8, fill=LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    bignum(s, 7.95, 2.6, 4.5, f"×{N['ResTokenRatioMin']}–{N['ResTokenRatioMax']}",
           "token mỗi lượt, spec so với vibe, mọi cohort và tầng", size=40, label_size=15)
    text(s, 7.95, 4.35, 4.5, 2.1,
         [f"Thời gian ×{N['ResWallRatioMin']}–{N['ResWallRatioMax']}.",
          f"Codex tầng lớn: spec rẻ hơn cho một lượt đạt ({usd('codex-luna', 'large', 'spec')} vs "
          f"{usd('codex-luna', 'large', 'vibe')} USD) vì vibe gần như không đạt."], size=15, bullet=True)
    return rows


def s17_tests():
    s = content(FIND, "Test do agent viết và chất lượng mã (H3)",
                "Nhánh spec để lại test ở phần lớn số lượt; các chỉ số chất lượng mã cho kết quả lẫn lộn.", 50,
                f"Khác biệt rõ nhất giữa hai cách là test do agent tự viết: {N['ResSonnetSpecTestsAnyPct']} đến {N['ResCodexSpecTestsAnyPct']} "
                f"phần trăm lượt spec có test do agent tự viết, trong khi vibe của Codex không viết test nào và Sonnet "
                f"chỉ {N['ResSonnetVibeTestsAnyPct']} phần trăm. Đây là hệ quả trực tiếp của prompt, và hidden test "
                f"không thưởng phần này; nó có thể có giá trị ở lần sửa sau, nhưng nghiên cứu này không đo. Về chất "
                f"lượng mã, kết quả lẫn lộn.",
                footer="Giá trị của bộ test này ở những lần sửa sau chưa được đo; hidden test không thưởng cho nó.")
    cats = ["Sonnet", "Opus", "Codex"]
    bar_chart(s, X0, 2.3, 6.6, 3.95, cats,
              [("Spec-driven", [fnum("ResSonnetSpecTestsAnyPct"), fnum("ResOpusSpecTestsAnyPct"),
                                fnum("ResCodexSpecTestsAnyPct")]),
               ("Vibe", [fnum("ResSonnetVibeTestsAnyPct"), fnum("ResOpusVibeTestsAnyPct"),
                         fnum("ResCodexVibeTestsAnyPct")])],
              [SPEC, VIBE], vmax=100, fmt='0"%"', size=13, dec=0, suffix="%")
    text(s, X0, 2.12, 6.6, 0.3, "% lượt có test do agent tự viết (mọi tầng)", size=12, color=GRAY, bold=True)
    text(s, 7.6, 2.45, 5.13, 4.2,
         [f"Test của agent chạy qua {N['ResSonnetSpecCovPct']}–{N['ResOpusSpecCovPct']}% số dòng mới ở nhánh spec.",
          f"Lỗi static analysis: spec nhiều hơn ở {H3A_BAD} ô (trái với H3), ít hơn ở Codex tầng lớn.",
          f"Regression ở Codex tầng lớn: {N['ResCodexLargeRegSpecPct']}% (spec) vs {N['ResCodexLargeRegVibePct']}% "
          f"(vibe), chỉ {N['FeatureTasks']} nhiệm vụ.",
          "Maintainability index: spec không kém hơn ở hầu hết các ô."], size=15, bullet=True, space=9)


def s18_decode():
    s = content(FIND, "Phân tích ca f15",
                "Đề không nói hàm trả về gì; spec của agent chọn sai, và test của agent kiểm theo lựa chọn đó.", 55,
                f"Quay lại f15. Đề nêu tên hàm dọn dữ liệu nhưng không nói nó trả về gì. Spec của agent tự chốt: trả "
                f"về danh sách đối tượng. Bản gốc thì trả về danh sách mã. Plan và test của agent đều dựa trên quyết "
                f"định đó, nên test của chính nó đạt; hidden test thì trượt. Vibe cũng phải tự chọn, và cả ba lượt "
                f"chọn đúng danh sách mã; {N['ResCaseVibePassed']} lượt đạt hết hidden test. Agent làm đúng quy "
                f"trình, nhưng spec chỉ ghi lại một cách đoán, rồi test kiểm theo chính cách đoán đó. Ca này có phải "
                f"ngoại lệ không?",
                footer=f"Vibe cũng phải tự chọn và chọn đúng danh sách mã ở cả {N['ResCaseReps']} lượt; "
                       f"{N['ResCaseVibePassed']}/{N['ResCaseReps']} lượt đạt hết hidden test.")
    steps = [("Đề bài", "Nêu tên hàm dọn dữ liệu, không nói trả về gì", GRAY),
             ("Spec của agent", "Tự chốt: trả về danh sách đối tượng", SPEC),
             ("Test của agent", "Kiểm theo cùng giả định → đạt", OK),
             ("Hidden test", "Bản gốc trả về danh sách mã → trượt", BAD)]
    bw = 2.68
    for i, (t, d, c) in enumerate(steps):
        x = X0 + i * (bw + 0.47)
        panel(s, x, 2.45, bw, 1.75, t, [d], accent=c, size=15, bullet=False)
        if i < 3:
            arrow(s, x + bw + 0.06, 3.2)
    text(s, X0, 4.55, X1 - X0, 2.0,
         ["Bước spec **biến chỗ đề bỏ ngỏ thành một quyết định cố định**.",
          "Plan và test viết trước đều dựa trên quyết định đó, nên không bắt được lỗi.",
          "Spec ghi lại cách agent đoán, không ghi lại ý của người giao việc."], size=17, bullet=True, space=8)


def s19_causes():
    s = content(FIND, "Nguyên nhân thất bại",
                f"{N['LabOutside']}/{N['LabRuns']} lượt hỏng của Claude do đề không nêu chi tiết hoặc nối sai mã có sẵn, với tỉ lệ như "
                "nhau ở hai cách.", 50,
                f"Để xem f15 có phải ngoại lệ không, Lợi và Bảo gán nhãn độc lập {N['LabRuns']} lượt hỏng của Claude, đồng "
                f"ý {N['LabAgree']}, kappa {N['LabKappa']}. {N['LabOutside']} trên {N['LabRuns']} lượt hỏng vì đề không "
                f"nêu chi tiết hoặc nối sai mã có sẵn; chỉ {N['LabLoiLogicTotal']} lượt là lỗi logic. Tỉ lệ này như "
                f"nhau ở hai cách, {N['LabOutsideSpecPct']} và {N['LabOutsideVibePct']} phần trăm: quy trình spec không "
                f"làm giảm loại lỗi này.",
                footer=f"Hai người gán nhãn độc lập, mù cách làm; đồng ý {N['LabAgree']}/{N['LabRuns']}, kappa "
                       f"{N['LabKappa']}; tác giả dự án phân xử chỗ lệch.")
    data = CategoryChartData()
    cats = ["Đề không nêu chi tiết", "Nối sai mã có sẵn", "Làm hỏng chức năng cũ", "Khác (gồm lỗi logic)"]
    data.categories = cats
    data.add_series("Lượt hỏng", [fnum("LabDeBaiThieuTotal"), fnum("LabSaiApiCoSanTotal"),
                                   fnum("LabHongChucNangCuTotal"), fnum("LabOther") + fnum("LabLoiLogicTotal")])
    gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, I(X0), I(2.3), I(6.6), I(3.95), data)
    ch = gf.chart
    ch.font.name, ch.font.size, ch.font.color.rgb = FONT, P(13), INK
    ch.has_legend = False
    ch.has_title = False
    ch.value_axis.visible = False
    ch.value_axis.has_major_gridlines = False
    ch.category_axis.reverse_order = True
    ch.category_axis.format.line.color.rgb = LINE
    pl = ch.plots[0]
    pl.gap_width = 55
    pl.has_data_labels = True
    pl.data_labels.font.size, pl.data_labels.font.bold = P(14), True
    pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
    ser = pl.series[0]
    ser.format.fill.solid()
    ser.format.fill.fore_color.rgb = NAVY
    for idx in (0, 1):
        pt = ser.points[idx]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = BAD
    rect(s, 7.6, 2.45, 5.13, 3.8, fill=LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    bignum(s, 7.95, 2.6, 4.5, f"{N['LabOutsideSpecPct']}% / {N['LabOutsideVibePct']}%",
           "tỉ lệ lượt hỏng do đề thiếu hoặc mã có sẵn: spec / vibe", size=36, label_size=15)
    text(s, 7.95, 4.35, 4.5, 2.1,
         [f"Chỉ {N['LabLoiLogicTotal']} lượt là lỗi logic agent tự viết.",
          "Quy trình spec không làm giảm loại lỗi này: bước thiết kế không tự biết điều đề không nói."],
         size=15, bullet=True)


def s20_human_spec():
    s = content(FIND, "Thí nghiệm thăm dò E2: đề sơ sài",
                "Bỏ phần spec do người viết khỏi đề làm điểm giảm mạnh; spec do agent tự viết chỉ bù lại một phần "
                "nhỏ.", 60,
                f"Kết quả tiếp theo đến từ thí nghiệm thăm dò E2. Đề chi tiết của thí nghiệm chính thực chất là một bản spec do người viết: tên hàm, "
                f"chữ ký, quy tắc. Thí nghiệm thăm dò E2 bỏ phần đó, chỉ giữ một hai câu, rồi chấm bằng checklist hành "
                f"vi. Bỏ spec của người, điểm giảm {say('ETwoXScoreShiftSpec')} và {say('ETwoXScoreShiftVibe')} điểm. "
                f"Còn spec agent tự viết chỉ bù lại {say('ETwoPooledSmallPp')} điểm ở nhiệm vụ nhỏ, và gần như không gì "
                f"ở nhiệm vụ vừa, lớn. Như vậy giá trị của spec nằm ở thông tin người viết đưa vào. Lưu ý: E2 thêm sau "
                f"khi thấy kết quả chính, nên là thăm dò.",
                footer=f"E2 · thăm dò, thêm sau khi xem kết quả chính. Điểm checklist do LLM judge chấm khi không biết "
                       f"cách làm; khớp chấm tay của hai người (kappa {N['ETwoHumanLoiJudgeKappa']}, "
                       f"{N['ETwoHumanBaoJudgeKappa']}).")
    chip(s, X1 - 1.5, 0.42, "thăm dò", color=VIBE, w=1.5)
    panel(s, X0, 2.4, 5.85, 3.3, "Spec của người", None, accent=NAVY)
    text(s, X0 + 0.3, 3.0, 5.3, 1.0, f"−{N['ETwoXScoreShiftSpec']} / −{N['ETwoXScoreShiftVibe']} pp", size=40,
         color=BAD, bold=True)
    text(s, X0 + 0.3, 3.85, 5.3, 2.6,
         ["Đề chi tiết = spec do người viết. Bỏ tên, chữ ký, quy tắc khỏi đề: điểm checklist giảm (spec / vibe).",
          "Đây là chênh lệch lớn nhất trong nghiên cứu, ở cả hai cách làm."], size=16, bullet=True)
    panel(s, X0 + 6.28, 2.4, 5.85, 3.3, "Spec của agent", None, accent=SPEC)
    text(s, X0 + 6.58, 3.0, 5.3, 1.0, f"{sg('ETwoPooledSmallPp')} pp", size=40, color=SPEC, bold=True)
    text(s, X0 + 6.58, 3.85, 5.3, 2.6,
         [f"Đề sơ sài, agent tự viết spec: bù lại ở nhiệm vụ nhỏ, KTC {ci('ETwoPooledSmallLowPp', 'ETwoPooledSmallHighPp')}.",
          f"Nhiệm vụ vừa {sg('ETwoPooledMediumRefPp')}, lớn {sg('ETwoPooledLargeRefPp')} pp (chỉ tham khảo)."],
         size=16, bullet=True)
    text(s, X0, 5.95, X1 - X0, 0.7, [("Đề chi tiết là một bản spec do người viết; spec do agent tự viết chỉ ghi lại "
                                      "cách agent đoán.", {"bold": True, "color": NAVY})], size=17)


def s21_conclusion():
    s = content(CLOSE, "Kết luận",
                "Giá trị của spec nằm ở thông tin người đưa vào, không ở việc agent tự viết spec.", 60,
                f"(Chuyển người nếu chia ba phần: phần ba.) Tóm lại. Với đề chi tiết, phép thử chính không thấy spec "
                f"do agent tự viết làm đạt nhiều hơn, H1 chưa kết luận được, mà tốn gấp {N['ResTokenRatioMin']} đến "
                f"{N['ResTokenRatioMax']} lần token. Với đề sơ sài, phần thăm dò cho thấy bỏ spec của người làm điểm "
                f"giảm khoảng {say('ETwoXScoreShiftSpec')} điểm, còn spec của agent chỉ bù {say('ETwoPooledSmallPp')} ở "
                f"nhiệm vụ nhỏ. Nhóm em đề xuất: viết spec rõ, hoặc để agent hỏi lại mình. Hạn chế chính: một dự án, "
                f"quy trình chạy tự động không có người duyệt, và tầng lớn chỉ có ba nhiệm vụ. Vòng sau, nhóm em muốn "
                f"thêm bước hỏi lại và người duyệt spec, và nhiều nhiệm vụ cỡ tính năng hơn.",
                footer="Hạn chế: một dự án Python · spec-driven chạy tự động, không hỏi lại, không người duyệt · tầng "
                       f"vừa {N['MediumTasks']}, lớn {N['FeatureTasks']} nhiệm vụ; E2 thêm sau khi xem kết quả chính.")
    items = [("Đề chi tiết",
              f"(Phép thử chính) Spec do agent tự viết không cho thấy đạt nhiều hơn (H1 chưa kết luận được), mà tốn "
              f"×{N['ResTokenRatioMin']}–{N['ResTokenRatioMax']} token.", SPEC),
             ("Đề sơ sài",
              f"(Thăm dò) Bỏ spec của người: −{N['ETwoXScoreShiftSpec']} pp; spec của agent chỉ bù {sg('ETwoPooledSmallPp')} pp ở "
              f"nhiệm vụ nhỏ.", VIBE),
             ("Đề xuất",
              "Viết spec rõ, hoặc để agent hỏi lại người dùng. Hướng tiếp: thêm bước hỏi lại và người duyệt spec, "
              "thêm nhiệm vụ lớn.", OK)]
    for i, (t, d, c) in enumerate(items):
        panel(s, X0 + i * 4.1, 2.4, 3.85, 3.0, t, [d], accent=c, size=17, bullet=False)
    text(s, X0, 5.65, X1 - X0, 0.9, [("Giá trị của spec nằm ở thông tin người viết đưa vào; agent không tự suy ra được "
                                      "thông tin đó.", {"bold": True, "color": NAVY})], size=18)


def s22_thanks():
    s = dark("Cảm ơn", [], 10, "Phần trình bày của nhóm em đến đây là hết. Em cảm ơn thầy và các bạn; nhóm em xin nhận "
             "câu hỏi.", CLOSE, layout="CUSTOM_3")
    text(s, 1.3, 1.9, 11, 1.2, "Xin cảm ơn!", size=56, color=NAVY, bold=True, font=TITLE_FONT)
    rect(s, 1.3, 3.15, 2.2, 0.06, fill=VIBE)
    text(s, 1.3, 3.4, 11, 0.6, "Hỏi đáp", size=24, color=INK, bold=True)
    text(s, 1.3, 4.1, 10.5, 1.2,
         ["Giá trị của spec nằm ở thông tin do người viết đưa vào.",
          "Mã, dữ liệu, prompt và kết quả thô được nộp kèm báo cáo."], size=16, color=INK)


# ---------------------------------------------------------------- backup slides

def b_h4():
    s = content(BACKUP, "Dự phòng: Sonnet và Opus (H4), nhiệm vụ nhỏ",
                "Cả hai mô hình gần trần ở nhiệm vụ nhỏ; spec không giúp mô hình yếu hơn nhiều hơn.", 0,
                "Slide dự phòng cho câu hỏi về H4.",
                footer=f"Sonnet spec và Opus vibe: cùng ước lượng điểm ({N['ResHFourSonnetSpecOpusVibePp']} pp, KTC rộng), "
                       f"chi phí bằng {N['ResHFourCostRatioPct']}%.")
    bar_chart(s, X0, 2.3, 7.0, 3.95, ["Sonnet", "Opus"],
              [("Spec-driven", [fnum("ResSonnetSmallSpecPct"), fnum("ResOpusSmallSpecPct")]),
               ("Vibe", [fnum("ResSonnetSmallVibePct"), fnum("ResOpusSmallVibePct")])], [SPEC, VIBE], vmax=100,
              fmt='0"%"', size=13, dec=0, suffix="%")
    text(s, 8.0, 2.45, 4.73, 4.2,
         [f"Hiệu của hai hiệu số (Sonnet − Opus): {sg('ResHFourDiffOfDiffsPp')} pp "
          f"{ci('ResHFourDiffOfDiffsLowPp', 'ResHFourDiffOfDiffsHighPp')}.", "H4 chưa kết luận được ở cả ba tầng."],
         size=16, bullet=True)


def b_e1():
    s = content(BACKUP, "Dự phòng: E1, Claude Haiku với đề chi tiết",
                "Mô hình yếu hơn cũng không được quy trình spec nâng lên khi đề đã chi tiết (thăm dò).", 0,
                "Slide dự phòng cho câu hỏi về mô hình yếu hơn.",
                footer=f"E1 · thăm dò, thêm sau khi xem kết quả chính; {N['EOneRuns']} lượt hợp lệ.")
    bar_chart(s, X0, 2.3, 7.0, 3.95, ["Nhỏ", "Vừa", "Lớn"],
              [("Spec-driven", [fnum("EOneSmallSpecPct"), fnum("EOneMediumSpecPct"), fnum("EOneLargeSpecPct")]),
               ("Vibe", [fnum("EOneSmallVibePct"), fnum("EOneMediumVibePct"), fnum("EOneLargeVibePct")])],
              [SPEC, VIBE], vmax=100, fmt='0"%"', size=13, dec=0, suffix="%")
    text(s, 8.0, 2.45, 4.73, 4.2,
         [f"Nhỏ: {sg('EOneSmallDiffPp')} pp {ci('EOneSmallLowPp', 'EOneSmallHighPp')}.",
          f"Token mỗi lượt nhỏ: {N['EOneSmallSpecTokensM']} vs {N['EOneSmallVibeTokensM']} triệu (spec / vibe)."],
         size=16, bullet=True)


def b_judge():
    s = content(BACKUP, "Dự phòng: độ tin cậy của LLM judge (E2)",
                "Judge khớp tốt với chấm tay theo từng mục, khớp vừa với hidden test theo cả lượt.", 0,
                "Slide dự phòng cho câu hỏi về LLM judge.",
                footer=f"Mẫu chấm tay chỉ có sáu lượt Codex: quá ít để kiểm độ nghiêng của judge (cùng họ Claude).")
    for i, (v, lab) in enumerate([(N["ETwoJudgeKappa"], f"kappa judge – hidden test, {N['ETwoJudgeN']} lượt đề chi tiết"),
                                  (N["ETwoHumanLoiBaoKappa"], f"kappa người – người, {N['ETwoHumanUnits']} lượt đề sơ sài"),
                                  (f"{N['ETwoHumanLoiJudgeKappa']} / {N['ETwoHumanBaoJudgeKappa']}",
                                   "kappa judge – từng người chấm; máy khắt khe hơn")]):
        rect(s, X0 + i * 4.1, 2.4, 3.85, 2.6, fill=LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
        bignum(s, X0 + i * 4.1 + 0.3, 2.55, 3.3, v, lab, size=36, label_size=14)


def b_funnel():
    s = content(BACKUP, "Dự phòng: chọn nhiệm vụ tầng nhỏ",
                "Lọc tự động rồi chọn ngẫu nhiên theo lớp mã với hạt giống cố định.", 0,
                "Slide dự phòng cho câu hỏi về cách chọn đề.")
    steps = [(N["Candidates"], "commit feat chạm src và tests"), (N["AfterCritOne"], "qua tiêu chí 1"),
             (N["AfterCritFour"], "qua tiêu chí 4"), (N["AfterCritFive"], "qua tiêu chí 5"),
             (N["AfterCritTwo"], "qua tiêu chí 2: chạy test thật"), (N["Tasks"], "chọn theo lớp mã")]
    for i, (v, lab) in enumerate(steps):
        x = X0 + i * 2.05
        rect(s, x, 2.6, 1.85, 2.3, fill=LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
        text(s, x + 0.2, 2.75, 1.5, 0.8, v, size=34, color=SPEC, bold=True)
        text(s, x + 0.2, 3.6, 1.5, 1.2, lab, size=13)


def b_cost_table():
    s = content(BACKUP, "Dự phòng: chi phí cho một lượt đạt (USD)",
                "Với Claude, spec đắt hơn ở mọi ô; với Codex tầng lớn thì ngược lại.", 0,
                "Slide dự phòng cho câu hỏi về chi phí.")
    rows = [("Cohort", "Nhỏ: spec", "Nhỏ: vibe", "Lớn: spec", "Lớn: vibe")]
    for name, c in [("Sonnet", "claude-sonnet"), ("Opus", "claude-opus"), ("Codex", "codex-luna")]:
        rows.append((name, usd(c, "small", "spec"), usd(c, "small", "vibe"), usd(c, "large", "spec"),
                     usd(c, "large", "vibe")))
    tbl = s.shapes.add_table(len(rows), 5, I(X0), I(2.5), I(10), I(2.4)).table
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            cell = tbl.cell(i, j)
            cell.text = v
            for p in cell.text_frame.paragraphs:
                for r in p.runs:
                    r.font.name, r.font.size, r.font.bold = FONT, P(16), i == 0
                    r.font.color.rgb = WHITE if i == 0 else INK
            cell.fill.solid()
            cell.fill.fore_color.rgb = NAVY if i == 0 else (LIGHT if i % 2 else WHITE)


# ---------------------------------------------------------------- build

def main():
    forest = figure_png("pass_diff_by_cohort")
    scatter = figure_png("effect_vs_size")
    s01_title()
    s02_hook()
    s03_promise()
    s04_rq()
    s05_related()
    s06_project()
    s07_git()
    s08_prompts()
    s09_tasks()
    s10_runs()
    s11_grading()
    s12_prereg()
    s13_h1()
    s14_cohorts(forest)
    s15_size(scatter)
    s16_cost()
    s17_tests()
    s18_decode()
    s19_causes()
    s20_human_spec()
    s21_conclusion()
    s22_thanks()
    for b in (b_h4, b_e1, b_judge, b_funnel, b_cost_table):
        b()
    PRS.save(str(OUT))

    talk = sum(p["secs"] for p in PAGES)
    rows = []
    t = 0
    for i, p in enumerate(PAGES, 1):
        t += p["secs"]
        rows.append(f"| {i} | {p['title']} | {p['section']} | {p['secs'] or '–'} | "
                    f"{f'{t // 60}:{t % 60:02d}' if p['secs'] else '–'} |")
    (HERE / "rehearsal.md").write_text(
        "# Tập dượt\n\nSinh tự động bởi `make_deck.py`; sửa thời lượng ở đó rồi chạy lại `build.sh`.\n\n"
        f"Tổng thời gian nói: {talk // 60}:{talk % 60:02d} cho {sum(1 for p in PAGES if p['secs'])} slide chính; "
        "cộng chuyển slide khoảng 18–19 phút. Ghi chú (notes) mỗi slide bắt đầu bằng nhắc giờ trong ngoặc vuông, "
        "không đọc thành tiếng; chỗ chuyển người nếu chia ba phần ghi ở slide 1, 13 và 21.\n\n"
        "| Slide | Tiêu đề | Phần | Giây | Cộng dồn |\n| --- | --- | --- | --- | --- |\n" + "\n".join(rows) + "\n",
        encoding="utf-8")
    print(f"slides={len(PAGES)} talk={talk // 60}:{talk % 60:02d}")
    if talk > MAX_TALK:
        sys.exit(f"talk over {MAX_TALK // 60} minutes")


if __name__ == "__main__":
    main()
