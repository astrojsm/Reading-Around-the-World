import pandas as pd
import streamlit as st
import plotly.express as px
from streamlit_js_eval import streamlit_js_eval

from _version import __version__
from lib_web import field_label, add_book, replace_book, remove_book
from lib_web import load_books_from_csv, build_country_csv_df
from lib_web import render_progress_circles, add_small_country_markers
from lib_web import country_map, continent_labels, continent_colors, continents_kr
from lib_web import normalize_text, optional_suffix

from lib_img import prepare_share_image, reset_share_state
from lib_pdf import prepare_share_pdf, reset_pdf_state

current_books = st.session_state.get("books", [])
visited_country_count = len({book.get("country_iso") for book in current_books if book.get("country_iso")})
has_crown = visited_country_count >= 200
crown_suffix = " 👑" if has_crown else ""

st.set_page_config(
    page_title="Reading Around the World Challenge",
    layout="wide"
)

st.markdown(
    """
    <style>
        /* Layout */
        .main .block-container {
            max-width: 1180px;
            padding-top: 2.1rem;
            padding-bottom: 2rem;
        }

        /* Hero */
        .hero-card {
            border: 1.5px solid rgba(30, 41, 59, 0.2);
            border-radius: 18px;
            padding: 1.6rem 1.8rem;
            margin-bottom: 1.1rem;
        }

        .hero-title {
            margin: 0 0 0.6rem;
            color: #11223a;
            font-size: clamp(1.8rem, 1.4rem + 2vw, 3rem);
            line-height: 1.18;
            font-weight: 800;
        }

        .hero-description {
            margin-top: 0.82rem;
            margin-bottom: 0;
            color: #25364c;
            font-size: 1.03rem;
            line-height: 1.72;
            max-width: 840px;
        }

        /* Hero progress chip */
        .hero-chip {
            display: inline-block;
            margin-top: 0.95rem;
            padding: 0.32rem 0.8rem;
            border-radius: 999px;
            font-size: 0.86rem;
            font-weight: 700;
            color: #1e3a5f;
            background: rgba(153, 206, 255, 0.24);
            border: 1px solid rgba(73, 132, 184, 0.3);
        }

        /* Form fields: base */
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stTextInput"] div[data-baseweb="input"],
        [data-testid="stTextInput"] div[data-baseweb="input"] > div,
        [data-testid="stTextInput"] div[data-baseweb="base-input"] {
            border-radius: 12px;
            border-color: rgba(32, 51, 82, 0.5) !important;
            border-width: 1.5px !important;
            background-color: rgba(255, 255, 255, 0.9);
        }

        /* Form fields: focus */
        [data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
        [data-testid="stTextInput"] div[data-baseweb="input"]:focus-within > div,
        [data-testid="stTextInput"] div[data-baseweb="base-input"]:focus-within,
        [data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within > div {
            border-color: #4984b8 !important;
            border-width: 2px !important;
            box-shadow: none !important;
        }

        /* Buttons */
        .stButton > button,
        .stDownloadButton > button {
            border-radius: 12px;
            border: 1px solid rgba(27, 44, 68, 0.22);
            color: #16253c;
            font-weight: 700;
            transition: border-color 0.16s ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            border-color: rgba(36, 66, 104, 0.34);
        }

        /* Checkbox spacing */
        [data-testid="stCheckbox"] {
            margin-top: 0 !important;
            margin-bottom: -0.4rem !important;
        }

        [data-testid="stCheckbox"] > label {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }

        /* File uploader */
        [data-testid="stFileUploader"] {
            border-radius: 14px;
            border: 1px dashed rgba(34, 62, 94, 0.28);
            background: rgba(255, 255, 255, 0.65);
            padding: 0.25rem 0.5rem;
        }

        /* Responsive */
        @media (max-width: 735px) {
            .hero-card {
                padding: 1.2rem 1.1rem;
            }
        }

    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <section class="hero-card">
        <h1 class="hero-title">Reading Around the World Challenge</h1>
        <p class="hero-description">
            전 세계 각 나라 출신 작가의 책을 최소 한 권씩 읽는 것을 목표로 하는 독서 챌린지입니다.<br>
            다양한 문화와 시선을 경험하며 나만의 세계 지도를 완성해보세요.<br>
            200개 국가와 지역의 작품을 읽으면 챌린지를 달성할 수 있습니다.
        </p>
        <span class="hero-chip">현재 방문 국가(지역): {visited_country_count} / 200 {crown_suffix}</span>
    </section>
    """,
    unsafe_allow_html=True,
)

# Initialize session state
SESSION_DEFAULTS = {
    "books": [],
    "replace": None,
    "form_feedback": None,
    "upload_feedback": None,
    "uploader_key": 0,
    "share_ready": False,
    "share_img_bytes": None,
    "share_pdf_ready": False,
    "share_pdf_bytes": None,
    "basic_only_countries": True,
    "screen_width": None,
}
for key, default_value in SESSION_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

raw_width = streamlit_js_eval(
    js_expressions="""
    (() => {
        if (!window.__readingWorldWidthListenerRegistered) {
            window.__readingWorldWidthListenerRegistered = true;

            let resizeTimer = null;
            const publishWidth = () => sendDataToPython({
                value: window.innerWidth,
                dataType: \"json\",
            });

            window.addEventListener(\"resize\", () => {
                window.clearTimeout(resizeTimer);
                resizeTimer = window.setTimeout(publishWidth, 120);
            });

            document.addEventListener(\"visibilitychange\", () => {
                if (!document.hidden) {
                    publishWidth();
                }
            });
        }

        return window.innerWidth;
    })()
    """,
    key="get_width",
)
if isinstance(raw_width, (int, float)):
    st.session_state.screen_width = int(raw_width)
elif isinstance(raw_width, str) and raw_width.isdigit():
    st.session_state.screen_width = int(raw_width)

# Book input form; add new books to the list
# st.subheader("새로 추가하기")
title_col1, title_col2 = st.columns(2)
with title_col1:
    field_label("제목", required=True)
    title = st.text_input("제목", key="title_input", label_visibility="collapsed")
with title_col2:
    field_label("제목(원어)")
    st.text_input("제목(원어)", key="title_original_input", label_visibility="collapsed")

author_col1, author_col2 = st.columns(2)
with author_col1:
    field_label("저자", required=True)
    author = st.text_input("저자", key="author_input", label_visibility="collapsed")
with author_col2:
    field_label("저자(원어)")
    st.text_input("저자(원어)", key="author_original_input", label_visibility="collapsed")

is_small_screen = isinstance(st.session_state.get("screen_width"), int) and st.session_state.screen_width <= 735

selected_continent = None
input_col1, input_col2, input_col3 = st.columns(3)
with input_col1:
    field_label("국가", required=True)
    if is_small_screen:
        st.checkbox(
            "기본 목록만 보기",
            key="basic_only_countries",
            help="체크를 해제하면 기본 200개 이외의 국가/지역을 선택할 수 있어요."
        )
    selected_continent = st.selectbox(
        "국가",
        options=continents_kr,
        key="selected_continent",
        index=None,
        placeholder="대륙 선택",
        label_visibility="collapsed"
    )

with input_col2:
    if not is_small_screen:
        st.checkbox(
            "기본 목록만 보기",
            key="basic_only_countries",
            help="체크를 해제하면 기본 200개 이외의 국가/지역을 선택할 수 있어요."
        )

selected_continent_code = None
if selected_continent is not None:
    selected_continent_code = {
        v: k for k, v in continent_labels.items()
    }[selected_continent]

registered_isos = {book["country_iso"] for book in st.session_state.books}

def format_country_option(country_name):
    info = country_map.get(country_name, {})
    country_iso = info.get("iso")
    if country_iso in registered_isos:
        return f"{country_name} (V)"
    return country_name

show_basic_only_countries = st.session_state.get("basic_only_countries", True)

filtered_countries = [
    name for name, info in country_map.items()
    if info["continent"] == selected_continent_code
    and (not show_basic_only_countries or not info.get("additional", False))
]

if st.session_state.get("selected_country") not in filtered_countries:
    st.session_state.selected_country = None

with input_col2:
    country_kr = st.selectbox(
        "국가",
        options=filtered_countries,
        format_func=format_country_option,
        key="selected_country",
        index=None,
        placeholder="국가 선택",
        label_visibility="collapsed",
        disabled=(selected_continent_code is None)
    )

with input_col3:
    field_label("출판연도")
    st.text_input("출판연도", key="publication_year_input", label_visibility="collapsed")

add_col1, add_col2, add_col3 = st.columns([1, 1, 8])

with add_col1:
    st.button("추가", on_click=add_book, width="stretch")

with add_col2:
    st.button("제거", on_click=remove_book, width="stretch")

if st.session_state.form_feedback is not None:
    level, message = st.session_state.form_feedback
    if level == "warning":
        st.warning(message)
    elif level == "success":
        st.success(message)
    st.session_state.form_feedback = None

# If there's already a book for the country, ask if user wants to replace it
if st.session_state.replace is not None:
    candidate = st.session_state.replace
    existing_book = st.session_state.books[candidate["index"]]
    new_book = candidate["new_book"]

    st.warning(
        f"{new_book['country_kr']}에는 이미 "
        f"{existing_book['title']}이(가) 등록되어 있어요."
    )

    rep_col1, rep_col2, rep_col3 = st.columns([1, 1, 8])

    with rep_col1:
        st.button("교체하기", on_click=replace_book, width="stretch")

    with rep_col2:
        if st.button("취소", width="stretch"):
            st.session_state.replace = None
            st.rerun()

# Upload button
uploaded_csv = st.file_uploader(
    "데이터 불러오기",
    type=["csv"],
    key=f"uploaded_csv_{st.session_state.uploader_key}"
)

if uploaded_csv is not None and st.button("불러오기"):
    with st.spinner("파일을 불러오는 중입니다..."):
        level, message = load_books_from_csv(uploaded_csv)

    st.session_state.upload_feedback = (level, message)
    st.session_state.uploader_key += 1
    st.rerun()

if st.session_state.upload_feedback is not None:
    level, message = st.session_state.upload_feedback
    if level == "error":
        st.error(message)
    elif level == "warning":
        st.warning(message)
    else:
        st.success(message)
    st.session_state.upload_feedback = None

# Display books and country counts
if st.session_state.books:
    books_df = pd.DataFrame(st.session_state.books)

    screen_width = st.session_state.get("screen_width")
    render_progress_circles(screen_width=screen_width)
    map_height = int(screen_width * 0.35) if isinstance(screen_width, int) else 500

    country_status = books_df[[
        "country_kr",
        "country_iso",
        "author",
        "author_original",
        "title",
        "title_original",
        "publication_year",
    ]].copy()
    for col in ["author", "author_original", "title", "title_original", "publication_year"]:
        country_status[col] = country_status[col].apply(normalize_text)

    country_status["author_original_suffix"] = country_status["author_original"].apply(optional_suffix)
    country_status["title_original_suffix"] = country_status["title_original"].apply(optional_suffix)
    country_status["publication_year_suffix"] = country_status["publication_year"].apply(optional_suffix)
    country_status["continent_code"] = country_status["country_kr"].map(
        lambda country: country_map[country]["continent"]
    )

    WORLD_ROTATION_LON = 13
    # Absolute longitude ranges for each split map panel (before offset)
    # MOBILE_SPLIT_LON_OFFSET: uniform longitude offset added to every range
    MOBILE_SPLIT_LON_OFFSET = 27
    MOBILE_SPLIT_LON_RANGES = [
        (-180, -60),
        (-60, 60),
        (60, 180),
    ]

    def normalize_lon(lon):
        return ((float(lon) + 180.0) % 360.0) - 180.0

    def build_map_figure(height, lon_range=None, rotation_lon=WORLD_ROTATION_LON):
        map_fig = px.choropleth(
            country_status,
            locations="country_iso",
            locationmode="ISO-3",
            color="continent_code",
            hover_name="country_kr",
            color_discrete_map={k: v for k, v in continent_colors.items() if k != "TT"},
            custom_data=[
                "country_kr",
                "author",
                "author_original_suffix",
                "title",
                "title_original_suffix",
                "publication_year_suffix",
            ]
        )

        map_fig.update_traces(
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "%{customdata[1]}%{customdata[2]}<br>"
                "『%{customdata[3]}%{customdata[4]}』%{customdata[5]}<br>"
                "<extra></extra>"
            ),
            selector=dict(type="choropleth")
        )

        geo_config = dict(
            resolution=110,
            showcoastlines=True,
            showcountries=False,
            lataxis=dict(range=[-55, 90]),
            projection=dict(type="equirectangular", rotation=dict(lon=rotation_lon)),
        )
        if lon_range is not None:
            geo_config["lonaxis"] = dict(range=list(lon_range))

        map_fig.update_layout(
            height=height,
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False,
            coloraxis_showscale=False,
            dragmode=False,
            geo=geo_config,
            hoverdistance=1,
            hovermode="closest",
            hoverlabel=dict(
                bgcolor="rgba(255,255,255,0.95)",
                bordercolor="rgba(0,0,0,0.1)",
                font_size=13,
            )
        )

        add_small_country_markers(map_fig, books_df)
        return map_fig

    # Keep a full-world figure for share image export.
    fig = build_map_figure(map_height)

    if isinstance(screen_width, int) and screen_width <= 735:
        split_map_height = int(screen_width * 1.2) # Taller height for mobile split view
        for lon_range in MOBILE_SPLIT_LON_RANGES:
            if not isinstance(lon_range, (list, tuple)) or len(lon_range) != 2:
                continue
            try:
                start_lon, end_lon = float(lon_range[0]), float(lon_range[1])
            except (TypeError, ValueError):
                continue

            if not (0 < end_lon - start_lon <= 360):
                continue

            start_lon += MOBILE_SPLIT_LON_OFFSET
            end_lon += MOBILE_SPLIT_LON_OFFSET

            segment_fig = build_map_figure(
                split_map_height,
                lon_range=(start_lon, end_lon),
                rotation_lon=normalize_lon((start_lon + end_lon) / 2.0),
            )
            st.plotly_chart(
                segment_fig,
                width="stretch",
                config={
                    "scrollZoom": False,
                    "doubleClick": False,
                    "displayModeBar": False,
                },
            )
    else:
        st.plotly_chart(
            fig,
            width="stretch",
            config={
                "scrollZoom": False,
                "doubleClick": False,
                "displayModeBar": False,
            },
        )
else:
    st.info("아직 추가된 책이 없습니다.")

# Download and delete buttons
if st.session_state.books:
    action_col1, action_col2, action_col3, action_col4 = st.columns(4)

    with action_col1:
        if not st.session_state.share_ready:
            st.button(
                "이미지로 공유하기",
                on_click=prepare_share_image,
                args=(fig,),
                width="stretch",
            )
        else:
            st.download_button(
                label="이미지 다운로드 (PNG)",
                data=st.session_state.share_img_bytes,
                file_name="reading_world_progress.png",
                mime="image/png",
                on_click=reset_share_state,
                width="stretch",
            )

    with action_col2:
        if not st.session_state.share_pdf_ready:
            st.button(
                "리스트로 공유하기", 
                on_click=prepare_share_pdf, 
                width="stretch"
            )
        else:
            st.download_button(
                label="리스트 다운로드 (PDF)",
                data=st.session_state.share_pdf_bytes,
                file_name="reading_world_progress.pdf",
                mime="application/pdf",
                on_click=reset_pdf_state,
                width="stretch",
            )

    with action_col3:
        csv_df = build_country_csv_df()
        csv_bytes = csv_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="데이터 저장하기",
            data=csv_bytes,
            file_name="reading_around_the_world.csv",
            mime="text/csv",
            width="stretch",
        )

    with action_col4:
        if st.button("데이터 삭제하기", width="stretch"):
            st.session_state.books = []
            st.rerun()

st.markdown(f"""
<div style="text-align: right; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid rgba(0,0,0,0.1);">
    <small>v{__version__} | © 2026 jsmoon.astro</small>
</div>
""", unsafe_allow_html=True)