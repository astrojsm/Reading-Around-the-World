import io, os

import streamlit as st

from PIL import Image, ImageDraw, ImageFont

from lib_web import build_progress_summary, continent_colors

STAMP_BLUE = (25, 85, 165, 230)

def load_font(name, size):
    base_dir = os.path.dirname(__file__)
    candidates = [
        name,
        os.path.join(base_dir, "fonts", name),
        os.path.join("C:\\Windows\\Fonts", name),
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()

def ratio_to_rgba(hex_color, ratio):
    ratio = max(0.0, min(1.0, float(ratio)))
    alpha = 0.1 + 0.9 * ratio

    hex_color = hex_color.lstrip("#")
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    alpha = int(round(alpha * 255))
    return (r, g, b, alpha)

def make_progress_banner(items, width=1400, height=220):
    img = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    circle_d = 210
    border_w = 6
    gap = 50
    label_gap = 14

    total_width = len(items) * circle_d + (len(items) - 1) * gap
    start_x = (width - total_width) // 2
    circle_y = 24

    font_main = load_font("NotoSansKR-Bold.ttf", 32)

    for i, item in enumerate(items):
        x = start_x + i * (circle_d + gap)
        y = circle_y

        ratio = item["ratio"]
        fill_h = int(circle_d * ratio) if item["done"] > 0 else 0
        fill_color = ratio_to_rgba(continent_colors[item["code"]], ratio)

        # outline
        draw.ellipse(
            [x, y, x + circle_d, y + circle_d],
            fill=(240, 241, 242, 255),
            outline=None
        )

        # fill
        if fill_h > 0:
            fill_top = y + circle_d - fill_h
            circle_fill = Image.new("RGBA", (circle_d, circle_d), (0, 0, 0, 0))
            circle_draw = ImageDraw.Draw(circle_fill)
            circle_draw.ellipse([0, 0, circle_d, circle_d], fill=fill_color)
            fill_strip = circle_fill.crop((0, circle_d - fill_h, circle_d, circle_d))
            img.alpha_composite(fill_strip, (x, fill_top))

        # outline (redraw to be on top of fill)
        draw.ellipse(
            [x, y, x + circle_d, y + circle_d],
            outline="black",
            width=border_w
        )

        # number
        text = f'{item["done"]}/{item["total"]}'
        bbox = draw.textbbox((0, 0), text, font=font_main)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = x + (circle_d - tw) / 2
        ty = y + (circle_d - th) / 2 - 2
        draw.text((tx, ty), text, fill="black", font=font_main)

        # label
        label = item["label"]
        bbox = draw.textbbox((0, 0), label, font=font_main)
        lw = bbox[2] - bbox[0]
        lx = x + (circle_d - lw) / 2
        ly = y + circle_d + label_gap
        draw.text((lx, ly), label, fill="black", font=font_main)

    return img

def draw_completion_stamp(base_img, top_right_x, top_right_y):
    stamp_size = 280
    pad = 46
    canvas_size = stamp_size + (pad * 2)

    stamp_layer = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(stamp_layer)

    x0 = pad
    y0 = pad
    x1 = pad + stamp_size
    y1 = pad + stamp_size

    draw.rectangle([x0, y0, x1, y1], outline=STAMP_BLUE, width=3)
    draw.rectangle([x0 + 12, y0 + 12, x1 - 12, y1 - 12], outline=STAMP_BLUE, width=3)

    top_font = load_font("SourceSans3-Bold.ttf", 40)
    complete_font = load_font("SourceSans3-Bold.ttf", 52)

    top_text = "READING\nAROUND\nTHE WORLD"
    top_bbox = draw.multiline_textbbox((0, 0), top_text, font=top_font, spacing=6, align="center")
    top_w = top_bbox[2] - top_bbox[0]
    top_x = x0 + (stamp_size - top_w) / 2
    top_y = y0 + 28
    draw.multiline_text((top_x, top_y), top_text, font=top_font, fill=STAMP_BLUE, spacing=8, align="center")

    complete_text = "COMPLETE"
    complete_bbox = draw.textbbox((0, 0), complete_text, font=complete_font)
    complete_w = complete_bbox[2] - complete_bbox[0]
    complete_x = x0 + (stamp_size - complete_w) / 2
    complete_y = y1 - 92
    draw.text((complete_x, complete_y), complete_text, font=complete_font, fill=STAMP_BLUE)

    rotated = stamp_layer.rotate(11, resample=Image.Resampling.BICUBIC, expand=True)
    paste_x = int(top_right_x - rotated.width)
    paste_y = int(top_right_y)
    base_img.paste(rotated, (paste_x, paste_y), rotated)

def build_share_image(fig):
    final_width = 1600
    final_height = 1200
    side_pad = 20
    top_pad = 60
    title_area_h = 80
    title_banner_gap = 30
    bottom_pad = 60
    banner_height = 320
    banner_map_gap = 0

    content_width = final_width - (side_pad * 2)
    banner_y = top_pad + title_area_h + title_banner_gap
    map_y = banner_y + banner_height + banner_map_gap
    map_height = final_height - bottom_pad - map_y

    items = build_progress_summary()
    banner = make_progress_banner(items, width=content_width, height=banner_height)

    map_bytes = fig.to_image(format="png", width=content_width, height=map_height, scale=1)
    map_img = Image.open(io.BytesIO(map_bytes)).convert("RGBA")

    final_img = Image.new(
        "RGB",
        (final_width, final_height),
        "white"
    )

    draw = ImageDraw.Draw(final_img)
    title = "Reading Around the World Challenge"
    title_font = load_font("SourceSans3-Bold.ttf", 70)

    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    title_h = title_bbox[3] - title_bbox[1]
    title_x = side_pad + 34
    title_y = top_pad + (title_area_h - title_h) // 2
    draw.text((title_x, title_y), title, fill="black", font=title_font)

    map_x = (final_img.width - map_img.width) // 2
    final_img.paste(map_img, (map_x, map_y), map_img)

    banner_x = (final_img.width - banner.width) // 2
    final_img.paste(banner, (banner_x, banner_y), banner)

    total_done = next((item.get("done", 0) for item in items if item.get("code") == "TT"), 0)
    if total_done >= 200:
        draw_completion_stamp(
            final_img,
            top_right_x=final_width - side_pad + 6,
            top_right_y=top_pad - 92,
        )

    out = io.BytesIO()
    final_img.save(out, format="PNG")
    out.seek(0)
    return out

def prepare_share_image(fig):
    st.session_state.share_img_bytes = build_share_image(fig).getvalue()
    st.session_state.share_ready = True

def reset_share_state():
    st.session_state.share_ready = False
    st.session_state.share_img_bytes = None
