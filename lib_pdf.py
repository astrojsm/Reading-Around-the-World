import io
import unicodedata
from html import escape
from pathlib import Path

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from lib_web import build_country_csv_df, continent_colors
from lib_web import continent_labels, country_map

try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    ARABIC_SHAPING_AVAILABLE = True
except Exception:
    ARABIC_SHAPING_AVAILABLE = False

def normalize(value):
    if value is None:
        return ""
    return str(value).strip()

def hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def blend_with_white(rgb, ratio=0.35):
    r, g, b = rgb
    return (
        int(r + (255 - r) * ratio),
        int(g + (255 - g) * ratio),
        int(b + (255 - b) * ratio),
    )

def has_book_data(row):
    for key in ["저자 (한국어)", "저자 (원어)", "제목 (한국어)", "제목 (원어)", "출판연도"]:
        if normalize(row.get(key, "")):
            return True
    return False

def register_font(font_name, font_path):
    try:
        if font_name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
        return True
    except Exception:
        return False

def first_existing_path(directory, candidates):
    for name in candidates:
        path = directory / name
        if path.exists():
            return path
    return None

def build_font_map():
    fonts_dir = Path(__file__).parent / "fonts"

    font_specs = {
        "base_regular": ["NotoSans-Regular.ttf", "NotoSans-Regular.otf"],
        "base_bold": ["NotoSans-Bold.ttf", "NotoSans-Bold.otf"],
        "kr_regular": ["NotoSansKR-Regular.ttf", "NotoSansKR-Regular.otf"],
        "kr_bold": ["NotoSansKR-Bold.ttf", "NotoSansKR-Bold.otf"],
        "cjk_regular": [
            "NotoSansSC-Regular.otf",
            "NotoSansSC-Regular.ttf",
            "NotoSansTC-Regular.otf",
            "NotoSansTC-Regular.ttf",
        ],
        "cjk_bold": [
            "NotoSansSC-Bold.otf",
            "NotoSansSC-Bold.ttf",
            "NotoSansTC-Bold.otf",
            "NotoSansTC-Bold.ttf",
        ],
        "arabic_regular": ["NotoSansArabic-Regular.ttf"],
        "arabic_bold": ["NotoSansArabic-Bold.ttf"],
    }

    aliases = {
        "base_regular": "RWBaseRegular",
        "base_bold": "RWBaseBold",
        "kr_regular": "RWKrRegular",
        "kr_bold": "RWKrBold",
        "cjk_regular": "RWCjkRegular",
        "cjk_bold": "RWCjkBold",
        "arabic_regular": "RWArabicRegular",
        "arabic_bold": "RWArabicBold",
    }

    registered = {}
    for key, files in font_specs.items():
        path = first_existing_path(fonts_dir, files)
        if path is None:
            continue
        alias = aliases[key]
        if register_font(alias, path):
            registered[key] = alias

    base_regular = registered.get("base_regular", "Helvetica")
    base_bold = registered.get("base_bold", "Helvetica-Bold")

    return {
        "base_regular": base_regular,
        "base_bold": base_bold,
        "kr_regular": registered.get("kr_regular", base_regular),
        "kr_bold": registered.get("kr_bold", base_bold),
        "cjk_regular": registered.get("cjk_regular", base_regular),
        "cjk_bold": registered.get("cjk_bold", base_bold),
        "arabic_regular": registered.get("arabic_regular", base_regular),
        "arabic_bold": registered.get("arabic_bold", base_bold),
    }

def script_key(ch):
    cp = ord(ch)
    if (0x0600 <= cp <= 0x06FF) or (0x0750 <= cp <= 0x077F) or (0x08A0 <= cp <= 0x08FF):
        return "arabic"
    if (0x1100 <= cp <= 0x11FF) or (0x3130 <= cp <= 0x318F) or (0xAC00 <= cp <= 0xD7AF):
        return "kr"
    if (
        (0x2E80 <= cp <= 0x2FDF)
        or (0x3000 <= cp <= 0x303F)
        or (0x3040 <= cp <= 0x30FF)
        or (0x31F0 <= cp <= 0x31FF)
        or (0x3400 <= cp <= 0x4DBF)
        or (0x4E00 <= cp <= 0x9FFF)
        or (0xF900 <= cp <= 0xFAFF)
    ):
        return "cjk"
    return "base"

def is_neutral_char(ch):
    return unicodedata.category(ch)[0] in {"P", "Z"}

def shape_arabic_text(text):
    if not ARABIC_SHAPING_AVAILABLE:
        return text
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text

def script_runs(text):
    text = normalize(text)
    if not text:
        return []

    runs = []
    current_key = None
    current_chars = []
    pending_neutral = []

    for ch in text:
        key = script_key(ch)

        if key == "base" and is_neutral_char(ch):
            pending_neutral.append(ch)
            continue

        if current_key is None:
            current_key = key
            current_chars.extend(pending_neutral)
            pending_neutral = []
            current_chars.append(ch)
            continue

        if key == current_key:
            current_chars.extend(pending_neutral)
            pending_neutral = []
            current_chars.append(ch)
        else:
            runs.append((current_key, "".join(current_chars)))
            current_key = key
            current_chars = pending_neutral + [ch]
            pending_neutral = []

    if current_key is None:
        return [("base", "".join(pending_neutral))]

    current_chars.extend(pending_neutral)
    runs.append((current_key, "".join(current_chars)))
    return runs

def paragraph_markup(text, fonts, bold=False):
    runs = script_runs(text)
    if not runs:
        return ""

    parts = []
    for key, chunk in runs:
        if key == "arabic":
            chunk = shape_arabic_text(chunk)
        escaped = escape(chunk)

        if key == "kr":
            font_name = fonts["kr_bold"] if bold else fonts["kr_regular"]
        elif key == "cjk":
            font_name = fonts["cjk_bold"] if bold else fonts["cjk_regular"]
        elif key == "arabic":
            font_name = fonts["arabic_bold"] if bold else fonts["arabic_regular"]
        else:
            font_name = fonts["base_bold"] if bold else fonts["base_regular"]

        parts.append(f"<font name='{font_name}'>{escaped}</font>")

    return "".join(parts)

def build_table_data(df, fonts, body_style, header_style, section_style):
    columns = [
        {"key": "국가", "label": "국가"},
        {"key": "저자 (한국어)", "label": "저자 (한국어)"},
        {"key": "저자 (원어)", "label": "저자 (원어)"},
        {"key": "제목 (한국어)", "label": "제목 (한국어)"},
        {"key": "제목 (원어)", "label": "제목 (원어)"},
        {"key": "출판연도", "label": "연도"},
    ]

    table_data = [
        [Paragraph(paragraph_markup(col["label"], fonts, bold=True), header_style) for col in columns]
    ]

    section_rows = []
    colored_rows = []

    continent_totals = {}
    continent_done = {}
    for country_kr, info in country_map.items():
        code = info["continent"]
        continent_totals[code] = continent_totals.get(code, 0) + 1

    for _, row in df.iterrows():
        country_kr = normalize(row.get("국가", ""))
        if country_kr and country_kr in country_map and has_book_data(row):
            code = country_map[country_kr]["continent"]
            continent_done[code] = continent_done.get(code, 0) + 1

    current_continent = None
    logical_rows = []
    for _, row in df.iterrows():
        country_kr = normalize(row.get("국가", ""))
        if not country_kr or country_kr not in country_map:
            continue

        continent_code = country_map[country_kr]["continent"]
        if current_continent != continent_code:
            logical_rows.append({"type": "section", "continent_code": continent_code})
            current_continent = continent_code

        logical_rows.append({
            "type": "data",
            "continent_code": continent_code,
            "row": row,
            "has_book": has_book_data(row),
        })

    row_idx = 1
    for item in logical_rows:
        if item["type"] == "section":
            code = item["continent_code"]
            label = continent_labels.get(code, code)
            text = f"{label} ({continent_done.get(code, 0)}/{continent_totals.get(code, 0)})"
            table_data.append([
                Paragraph(paragraph_markup(text, fonts, bold=True), section_style),
                "",
                "",
                "",
                "",
                "",
            ])
            section_rows.append(row_idx)
            row_idx += 1
            continue

        row = item["row"]
        row_cells = []
        for col in columns:
            row_cells.append(Paragraph(paragraph_markup(normalize(row.get(col["key"], "")), fonts, bold=False), body_style))
        table_data.append(row_cells)

        if item["has_book"]:
            rgb = hex_to_rgb(continent_colors.get(item["continent_code"], "#FFFFFF"))
            blended = blend_with_white(rgb, ratio=0.35)
            colored_rows.append((row_idx, blended))

        row_idx += 1

    return table_data, section_rows, colored_rows

def build_share_pdf():
    fonts = build_font_map()
    df = build_country_csv_df().fillna("")
    page_size = landscape(A4)
    pdf_title = "Reading Around the World Challenge"

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        leftMargin=24,
        rightMargin=24,
        topMargin=20,
        bottomMargin=22,
        title=pdf_title,
    )

    title_style = ParagraphStyle(
        "title",
        fontName=fonts["base_bold"],
        fontSize=17,
        leading=20,
        alignment=1,
        spaceBefore=0,
        spaceAfter=0,
    )
    header_style = ParagraphStyle(
        "header",
        fontName=fonts["base_bold"],
        fontSize=9.5,
        leading=11.5,
        alignment=1,
        textColor=colors.white,
    )
    body_style = ParagraphStyle(
        "body",
        fontName=fonts["base_regular"],
        fontSize=9.5,
        leading=11.5,
        alignment=1,
    )
    section_style = ParagraphStyle(
        "section",
        fontName=fonts["base_bold"],
        fontSize=9.5,
        leading=11.5,
        alignment=1,
    )

    table_data, section_rows, colored_rows = build_table_data(df, fonts, body_style, header_style, section_style)

    # Keep same tuned ratio (first/last narrower).
    col_weights = [1.35, 1.79, 1.79, 2.10, 2.10, 0.42]
    total_weight = sum(col_weights)
    usable_width = doc.width
    col_widths = [(w / total_weight) * usable_width for w in col_weights]

    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        ("GRID", (0, 0), (-1, -1), 0.8, colors.HexColor("#d2d2d2")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]

    for row_index in section_rows:
        style_cmds.append(("SPAN", (0, row_index), (-1, row_index)))
        style_cmds.append(("BACKGROUND", (0, row_index), (-1, row_index), colors.white))

    for row_index, rgb in colored_rows:
        style_cmds.append(("BACKGROUND", (0, row_index), (-1, row_index), colors.Color(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)))

    table.setStyle(TableStyle(style_cmds))

    story = [
        Paragraph(paragraph_markup(pdf_title, fonts, bold=True), title_style),
        Spacer(1, 10 * mm),
        table,
    ]

    def apply_pdf_metadata(canvas, _doc):
        canvas.setTitle(pdf_title)

    doc.build(story, onFirstPage=apply_pdf_metadata, onLaterPages=apply_pdf_metadata)
    buffer.seek(0)
    return buffer

def prepare_share_pdf():
    try:
        st.session_state.share_pdf_bytes = build_share_pdf().getvalue()
        st.session_state.share_pdf_ready = True
    except Exception as exc:
        st.session_state.share_pdf_ready = False
        st.session_state.share_pdf_bytes = None
        st.error(f"PDF 생성 실패: {exc}")

def reset_pdf_state():
    st.session_state.share_pdf_ready = False
    st.session_state.share_pdf_bytes = None
