#!/usr/bin/env python3
"""Generate a short bird's-eye Turkish FD002 presentation."""

from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_THEME_COLOR
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE, PP_PLACEHOLDER
from pptx.enum.text import MSO_AUTO_SIZE, MSO_VERTICAL_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = PROJECT_ROOT / "kaynaklar" / "YAP101-proje-seminer-şablon.pptx"
OUTPUT_PATH = PROJECT_ROOT / "reports" / "fd002_short_presentation.pptx"
ANALYSIS_SUMMARY_PATH = PROJECT_ROOT / "reports" / "tables" / "fd002_analysis_summary.json"
METRICS_PATH = PROJECT_ROOT / "artifacts" / "fd002_attention_lstm_small" / "metrics.json"

SLIDE_DATE = "13 Nisan 2026"
FOOTER_TEXT = "C-MAPSS RUL Projesi | YAP101"

WHITE = RGBColor(255, 255, 255)
TEXT_DARK = RGBColor(40, 48, 56)
TEXT_MUTED = RGBColor(88, 99, 110)
CARD_LINE = RGBColor(215, 222, 228)
SOFT_BG = RGBColor(247, 249, 251)
ACCENT_TEAL = RGBColor(63, 191, 196)
ACCENT_GREEN = RGBColor(152, 205, 148)
ACCENT_BLUE = RGBColor(14, 64, 122)
ACCENT_SKY = RGBColor(98, 176, 220)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def remove_all_slides(prs: Presentation) -> None:
    for slide_id in list(prs.slides._sldIdLst):
        rel_id = slide_id.get(qn("r:id"))
        prs.part.drop_rel(rel_id)
        prs.slides._sldIdLst.remove(slide_id)


def set_slide_chrome(slide, slide_number: int) -> None:
    for placeholder in slide.placeholders:
        ph_type = placeholder.placeholder_format.type
        if ph_type == PP_PLACEHOLDER.DATE:
            placeholder.text = SLIDE_DATE
        elif ph_type == PP_PLACEHOLDER.FOOTER:
            placeholder.text = FOOTER_TEXT
        elif ph_type == PP_PLACEHOLDER.SLIDE_NUMBER:
            placeholder.text = str(slide_number)


def prepare_content_slide(slide, title_text: str, slide_number: int) -> None:
    title = slide.shapes.title
    title.text = title_text
    title.left = Inches(0.78)
    title.top = Inches(0.88)
    title.width = Inches(7.60)
    title.height = Inches(0.55)
    style_paragraph(title.text_frame.paragraphs[0], 25, bold=True, color=TEXT_DARK)
    set_slide_chrome(slide, slide_number)


def style_paragraph(paragraph, font_size: int, *, bold: bool = False, color: RGBColor = TEXT_DARK, align=PP_ALIGN.LEFT) -> None:
    if not paragraph.runs:
        paragraph.add_run()
    paragraph.alignment = align
    paragraph.line_spacing = 1.08
    paragraph.space_after = Pt(6)
    for run in paragraph.runs:
        run.font.size = Pt(font_size)
        run.font.bold = bold
        run.font.color.rgb = color


def fill_text_frame(shape, lines: list[str], *, font_size: int, title: str | None = None, title_size: int = 18, color: RGBColor = TEXT_DARK, align=PP_ALIGN.LEFT) -> None:
    text_frame = shape.text_frame
    text_frame.clear()
    text_frame.word_wrap = True
    text_frame.vertical_anchor = MSO_VERTICAL_ANCHOR.TOP
    text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE

    start_index = 0
    if title is not None:
        title_paragraph = text_frame.paragraphs[0]
        title_paragraph.text = title
        title_paragraph.space_after = Pt(8)
        style_paragraph(title_paragraph, title_size, bold=True, color=color, align=align)
        start_index = 1

    for index, line in enumerate(lines):
        paragraph = text_frame.paragraphs[0] if start_index == 0 and index == 0 else text_frame.add_paragraph()
        paragraph.text = line
        style_paragraph(paragraph, font_size, color=color, align=align)


def add_textbox(slide, left: float, top: float, width: float, height: float, lines: list[str], *, font_size: int, title: str | None = None, title_size: int = 18, color: RGBColor = TEXT_DARK, align=PP_ALIGN.LEFT):
    shape = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    fill_text_frame(shape, lines, font_size=font_size, title=title, title_size=title_size, color=color, align=align)
    return shape


def add_card(slide, left: float, top: float, width: float, height: float, *, theme_color: MSO_THEME_COLOR | None = None, fill_rgb: RGBColor | None = None, line_rgb: RGBColor = CARD_LINE):
    shape = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
        Inches(left),
        Inches(top),
        Inches(width),
        Inches(height),
    )
    shape.fill.solid()
    if theme_color is not None:
        shape.fill.fore_color.theme_color = theme_color
        shape.line.color.theme_color = theme_color
    else:
        shape.fill.fore_color.rgb = fill_rgb or WHITE
        shape.line.color.rgb = line_rgb
    shape.line.width = Pt(1.1)
    return shape


def add_labeled_card(slide, left: float, top: float, width: float, height: float, *, title: str, lines: list[str], theme_color: MSO_THEME_COLOR | None = None, fill_rgb: RGBColor | None = None, title_color: RGBColor = TEXT_DARK, body_color: RGBColor = TEXT_DARK, body_size: int = 17):
    shape = add_card(slide, left, top, width, height, theme_color=theme_color, fill_rgb=fill_rgb)
    fill_text_frame(
        shape,
        lines,
        font_size=body_size,
        title=title,
        title_size=19,
        color=body_color,
    )
    # Re-color title separately if needed
    if title_color != body_color:
        paragraph = shape.text_frame.paragraphs[0]
        for run in paragraph.runs:
            run.font.color.rgb = title_color
    return shape


def add_metric_card(slide, left: float, top: float, width: float, height: float, value: str, label: str, fill_rgb: RGBColor) -> None:
    shape = add_card(slide, left, top, width, height, fill_rgb=fill_rgb, line_rgb=fill_rgb)
    text_frame = shape.text_frame
    text_frame.clear()
    text_frame.word_wrap = True
    text_frame.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE

    paragraph1 = text_frame.paragraphs[0]
    paragraph1.text = value
    paragraph1.alignment = PP_ALIGN.CENTER
    paragraph1.space_after = Pt(4)
    style_paragraph(paragraph1, 25, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    paragraph2 = text_frame.add_paragraph()
    paragraph2.text = label
    paragraph2.alignment = PP_ALIGN.CENTER
    style_paragraph(paragraph2, 13, color=WHITE, align=PP_ALIGN.CENTER)


def add_step_card(slide, left: float, top: float, width: float, height: float, number: str, title: str, body: str, accent_rgb: RGBColor) -> None:
    shape = add_card(slide, left, top, width, height, fill_rgb=SOFT_BG)
    shape.line.color.rgb = accent_rgb
    shape.line.width = Pt(1.4)

    badge = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.OVAL,
        Inches(left + 0.18),
        Inches(top + 0.18),
        Inches(0.52),
        Inches(0.52),
    )
    badge.fill.solid()
    badge.fill.fore_color.rgb = accent_rgb
    badge.line.color.rgb = accent_rgb
    fill_text_frame(badge, [number], font_size=15, color=WHITE, align=PP_ALIGN.CENTER)
    badge.text_frame.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE

    add_textbox(
        slide,
        left + 0.82,
        top + 0.16,
        width - 1.00,
        height - 0.28,
        [body],
        font_size=15,
        title=title,
        title_size=17,
    )


def create_title_slide(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    title = slide.shapes.title
    subtitle = slide.placeholders[1]

    title.text = "C-MAPSS ile RUL Tahmini"
    style_paragraph(title.text_frame.paragraphs[0], 28, bold=True, color=TEXT_DARK, align=PP_ALIGN.LEFT)

    fill_text_frame(
        subtitle,
        [
            "Kuşbakışı kısa sunum",
            "Amaç, veri seti, çözüm adımları ve kısa sonuçlar",
            "Bu çalışmada C-MAPSS içinden FD002 alt kümesi kullanıldı",
            "YAP101 Veri Bilimine Giriş",
            SLIDE_DATE,
        ],
        font_size=18,
        color=TEXT_DARK,
    )


def create_objective_slide(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    prepare_content_slide(slide, "Projenin Amacı", 2)

    add_labeled_card(
        slide,
        0.70,
        1.80,
        4.15,
        3.20,
        title="Ne yapmaya çalışıyoruz?",
        lines=[
            "Amaç, bir motorun ne kadar ömrü kaldığını yani RUL değerini tahmin etmek.",
            "Böylece bakım kararı arızadan önce, daha doğru zamanda verilebilir.",
            "Bu projede bunu C-MAPSS verisi üzerinden kendi Attention-LSTM modelimizle yaptık.",
        ],
        fill_rgb=WHITE,
        body_size=17,
    )
    add_labeled_card(
        slide,
        5.00,
        1.80,
        3.25,
        3.20,
        title="Bu sunumda odak ne?",
        lines=[
            "Önce verinin yapısını ve değişkenlerin ne anlattığını netleştiriyoruz.",
            "Sonra çözüm akışını, yani rejim ayırma, sensör seçimi ve modeli kısa biçimde anlatıyoruz.",
            "Son slaytta da yalnızca başlıca hata sonuçlarını veriyoruz.",
        ],
        fill_rgb=WHITE,
        body_size=16,
    )

    add_metric_card(slide, 1.10, 5.18, 2.00, 0.90, "RUL", "tahmin hedefi", ACCENT_TEAL)
    add_metric_card(slide, 3.40, 5.18, 2.00, 0.90, "C-MAPSS", "kullanılan veri", ACCENT_GREEN)
    add_metric_card(slide, 5.70, 5.18, 1.70, 0.90, "FD002", "seçilen alt küme", ACCENT_BLUE)


def create_dataset_slide(prs: Presentation, summary: dict) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    prepare_content_slide(slide, "Veri Seti", 3)

    add_labeled_card(
        slide,
        0.70,
        1.80,
        4.00,
        3.15,
        title="Nasıl bir veri bu?",
        lines=[
            "Bu veri setinde her motoru zaman içinde adım adım izliyoruz.",
            "Bu yüzden veri, birden fazla giriş ve birden fazla ölçüm içeren bir zaman serisi gibi düşünülebilir.",
            "Her adımda çalışma koşulları ve sensör ölçümleri birlikte geliyor.",
        ],
        fill_rgb=WHITE,
        body_size=16,
    )
    add_labeled_card(
        slide,
        5.00,
        1.80,
        3.25,
        3.15,
        title="Her satırda ne var?",
        lines=[
            "unit_id: motor kimliği",
            "cycle: zaman / ömür ilerleyişi",
            "op1-op3: çalışma koşulu bilgisi",
            "s1-s21: sensör ölçümleri",
        ],
        fill_rgb=WHITE,
        body_size=16,
    )

    add_metric_card(slide, 0.90, 5.10, 1.55, 0.92, f"{summary['train_units']}", "train motor", ACCENT_TEAL)
    add_metric_card(slide, 2.75, 5.10, 1.55, 0.92, f"{summary['test_units']}", "test motor", ACCENT_GREEN)
    add_metric_card(slide, 4.60, 5.10, 1.55, 0.92, "3", "çalışma ayarı", ACCENT_BLUE)
    add_metric_card(slide, 6.45, 5.10, 1.10, 0.92, "21", "sensör", ACCENT_SKY)


def create_data_interpretation_slide(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    prepare_content_slide(slide, "Veriyi Nasıl Okuyoruz?", 4)

    add_labeled_card(
        slide,
        0.70,
        1.80,
        3.65,
        2.35,
        title="Çalışma koşulları neyi anlatıyor?",
        lines=[
            "op1: irtifa / çalışma seviyesi",
            "op2: Mach sayısı / hız rejimi",
            "op3: gaz kolu açısı",
        ],
        fill_rgb=WHITE,
        body_size=15,
    )
    add_labeled_card(
        slide,
        4.65,
        1.80,
        3.60,
        2.35,
        title="Neden ayırmamız gerekiyor?",
        lines=[
            "Bu alanlar motorun bozulmasını değil, o andaki çalışma ortamını anlatıyor.",
            "Yani aynı sensör, farklı koşullarda farklı seviyelerde görünebiliyor.",
        ],
        fill_rgb=WHITE,
        body_size=15,
    )
    add_labeled_card(
        slide,
        0.90,
        4.40,
        7.10,
        1.60,
        title="Bu projedeki temel yorum",
        lines=[
            "Bozulma bilgisini op1-op3 içinde değil, sensörlerin zaman içindeki değişiminde arıyoruz.",
            "Bu yüzden önce çalışma rejimini ayırıp sonra sensör seçimi ve modelleme aşamasına geçtik.",
        ],
        fill_rgb=SOFT_BG,
        body_size=16,
    )


def create_approach_slide(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    prepare_content_slide(slide, "Çözüm İçin Yaptığımız Adımlar", 5)

    add_step_card(
        slide,
        0.70,
        1.80,
        4.00,
        1.75,
        "1",
        "Problemi ayır",
        "Önce op1-op2-op3 ile K-Means kullanıp çalışma koşulu etkisini ayrı bir yapıda topladık.",
        ACCENT_TEAL,
    )
    add_step_card(
        slide,
        4.95,
        1.80,
        3.25,
        1.75,
        "2",
        "Sensörleri süz",
        "Sensörleri bozulma eğilimi, tutarlılık ve çalışma koşulundan etkilenme açısından puanladık. 21 sensörden 12'sini tuttuk, 7'sini eledik.",
        ACCENT_GREEN,
    )
    add_step_card(
        slide,
        0.70,
        3.85,
        4.00,
        1.75,
        "3",
        "Modeli kur",
        "Seçtiğimiz sensörler ve çalışma bilgisiyle Attention-LSTM modelimizi eğittik.",
        ACCENT_BLUE,
    )
    add_step_card(
        slide,
        4.95,
        3.85,
        3.25,
        1.75,
        "4",
        "Değerlendir",
        "Modeli validation ve test RMSE değerlerine bakarak değerlendirdik.",
        ACCENT_SKY,
    )


def add_rmse_table(slide, left: float, top: float, width: float, height: float, metrics: dict) -> None:
    rows, cols = 3, 2
    table = slide.shapes.add_table(rows, cols, Inches(left), Inches(top), Inches(width), Inches(height)).table
    table.columns[0].width = Inches(width * 0.67)
    table.columns[1].width = Inches(width * 0.33)

    entries = [
        ("Değerlendirme", "RMSE"),
        ("Validation", f"{metrics['validation_capped']['rmse']:.2f}"),
        ("Test", f"{metrics['test_capped']['rmse']:.2f}"),
    ]

    for row_index, row_values in enumerate(entries):
        for col_index, value in enumerate(row_values):
            cell = table.cell(row_index, col_index)
            cell.text = value
            cell.margin_left = Inches(0.10)
            cell.margin_right = Inches(0.10)
            cell.margin_top = Inches(0.05)
            cell.margin_bottom = Inches(0.05)
            cell.fill.solid()
            cell.fill.fore_color.rgb = ACCENT_BLUE if row_index == 0 else WHITE
            cell.text_frame.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE
            paragraph = cell.text_frame.paragraphs[0]
            style_paragraph(
                paragraph,
                16 if row_index == 0 else 15,
                bold=row_index == 0,
                color=WHITE if row_index == 0 else TEXT_DARK,
                align=PP_ALIGN.CENTER if col_index == 1 else PP_ALIGN.LEFT,
            )


def create_results_slide(prs: Presentation, summary: dict, metrics: dict) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    prepare_content_slide(slide, "Sonuçlar", 6)

    add_labeled_card(
        slide,
        0.80,
        1.70,
        7.30,
        0.95,
        title="Genel özet",
        lines=[
            f"Seçilen alt kümede {summary['final_k']} çalışma rejimi ayrıldı, {len(summary['working_set'])} sensör seçildi ve modelimizi bu daha sade giriş setiyle eğittik.",
        ],
        fill_rgb=SOFT_BG,
        body_size=16,
    )

    add_rmse_table(slide, 0.95, 2.85, 4.70, 1.85, metrics)

    add_labeled_card(
        slide,
        5.95,
        2.85,
        2.15,
        2.30,
        title="Kısa yorum",
        lines=[
            "Validation ve test sonuçları birbirine yakın.",
            "Bu da modelin yeni motorlarda da dengeli davrandığını gösteriyor.",
            "Seçtiğimiz ön işleme adımları sonuçlara olumlu yansımış görünüyor.",
        ],
        fill_rgb=WHITE,
        body_size=15,
    )
    add_metric_card(slide, 1.80, 5.45, 5.40, 0.72, "Ana mesaj", "Doğru ön işleme, bu problemde model kadar belirleyici.", ACCENT_TEAL)


def main() -> None:
    summary = load_json(ANALYSIS_SUMMARY_PATH)
    metrics = load_json(METRICS_PATH)

    prs = Presentation(str(TEMPLATE_PATH))
    remove_all_slides(prs)
    prs.core_properties.title = "C-MAPSS ile RUL Tahmini"
    prs.core_properties.subject = "Kuşbakışı kısa proje sunumu"
    prs.core_properties.author = "Codex"

    create_title_slide(prs)
    create_objective_slide(prs)
    create_dataset_slide(prs, summary)
    create_data_interpretation_slide(prs)
    create_approach_slide(prs)
    create_results_slide(prs, summary, metrics)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUTPUT_PATH))

    print(f"Generated {OUTPUT_PATH}")
    print(f"Slides: {len(prs.slides)}")


if __name__ == "__main__":
    main()
