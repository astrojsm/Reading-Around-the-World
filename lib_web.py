import json
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# List of countries for the dropdown
with open("assets/country_iso.json", "r", encoding="utf-8") as f:
    country_map = json.load(f)

continent_labels = {
    "AF": "아프리카",
    "AS": "아시아",
    "OC": "오세아니아",
    "EU": "유럽",
    "AM": "아메리카",
}

continent_colors = {
    "TT": "#FFFFFF",
    "AF": "#60BD68",
    "AS": "#D96B6B",
    "OC": "#5DA5DA",
    "EU": "#9B6BB3",
    "AM": "#E6C84F",
}

# Coordinates based on https://latitude.to/
small_country_points = {
    "GMB": {"lat": 13.3441, "lon": -16.6522},   # 감비아
    "REU": {"lat": -21.1307, "lon": 55.5265},   # 레위니옹
    "MUS": {"lat": -20.2067, "lon": 57.6755},   # 모리셔스
    "STP": {"lat": 0.1997, "lon": 6.6106},      # 상투메프린시페
    "SYC": {"lat": -4.6839, "lon": 55.4495},    # 세이셸
    "CPV": {"lat": 15.1201, "lon": -23.6052},   # 카보베르데
    "COM": {"lat": -11.6520, "lon": 43.3726},   # 코모로

    "TLS": {"lat": -8.7947, "lon": 126.1369},   # 동티모르
    "LBN": {"lat": 33.8736, "lon": 35.8637},    # 레바논
    "MAC": {"lat": 22.1634, "lon": 113.5629},   # 마카오 
    "MDV": {"lat": 1.9772, "lon": 73.5361},     # 몰디브
    "BHR": {"lat": 25.9434, "lon": 50.6015},    # 바레인
    "BRN": {"lat": 4.5242, "lon": 114.7196},    # 브루나이
    "SGP": {"lat": 1.3147, "lon": 103.8454},    # 싱가포르
    "XTB": {"lat": 29.8556, "lon": 90.8750},    # 티베트
    "PSE": {"lat": 31.9474, "lon": 35.2272},    # 팔레스타인
    "HKG": {"lat": 22.2759, "lon": 114.1921},   # 홍콩

    "GUM": {"lat": 13.4502, "lon": 144.7875},   # 괌
    "NRU": {"lat": -0.5284, "lon": 166.9342},   # 나우루
    "NCL": {"lat": -21.2107, "lon": 165.8517},  # 누벨칼레도니
    "NIU": {"lat": -19.0543, "lon": -169.8621}, # 니우에
    "MHL": {"lat": 7.0897, "lon": 171.3803},    # 마셜제도
    "FSM": {"lat": 6.8875, "lon": 158.2151},    # 미크로네시아연방
    "VUT": {"lat": -15.4493, "lon": 167.5954},  # 바누아투
    "WSM": {"lat": -13.7583, "lon": -172.1048}, # 사모아
    "SLB": {"lat": -9.2263, "lon": 159.1874},   # 솔로몬제도
    "COK": {"lat": -21.2358, "lon": -159.7778}, # 쿡제도
    "KIR": {"lat": 1.3278, "lon": 172.9770},    # 키리바시
    "TON": {"lat": -21.2418, "lon": -175.1285}, # 통가
    "TUV": {"lat": -8.5245, "lon": 179.1966},   # 투발루
    "PLW": {"lat": 7.3674, "lon": 134.5388},    # 팔라우
    "PYF": {"lat": -17.6874, "lon": -149.3729}, # 프랑스령폴리네시아
    "FJI": {"lat": -17.4625, "lon": 179.2583},  # 피지

    "LUX": {"lat": 49.8153, "lon": 6.1333},     # 룩셈부르크
    "LIE": {"lat": 47.1594, "lon": 9.5536},     # 리히텐슈타인
    "MCO": {"lat": 43.7383, "lon": 7.42445},    # 모나코
    "MLT": {"lat": 35.9440, "lon": 14.3795},    # 몰타
    "VAT": {"lat": 41.9039, "lon": 12.4521},    # 바티칸시국
    "SMR": {"lat": 43.9429, "lon": 12.4601},    # 산마리노
    "AND": {"lat": 42.5423, "lon": 1.5977},     # 안도라
    "XKX": {"lat": 42.5833, "lon": 21.0001},    # 코소보
    "FRO": {"lat": 61.8925, "lon": -6.9730},    # 페로제도

    "GLP": {"lat": 15.9985, "lon": -61.7255},   # 과들루프
    "GRD": {"lat": 12.1100, "lon": -61.6935},   # 그레나다
    "DMA": {"lat": 15.3017, "lon": -61.3881},   # 도미니카연방
    "MTQ": {"lat": 14.6337, "lon": -61.0198},   # 마르티니크
    "BRB": {"lat": 13.1901, "lon": -59.5356},   # 바베이도스
    "BHS": {"lat": 25.0582, "lon": -77.3431},   # 바하마
    "LCA": {"lat": 13.9095, "lon": -60.9764},   # 세인트루시아
    "VCT": {"lat": 13.0113, "lon": -61.2353},   # 세인트빈센트그레나딘
    "KNA": {"lat": 17.3457, "lon": -62.8368},   # 세인트키츠네비스
    "ABW": {"lat": 12.5176, "lon": -69.9649},   # 아루바
    "ATG": {"lat": 17.3628, "lon": -61.7872},   # 앤티가바부다
    "JAM": {"lat": 18.1155, "lon": -77.2760},   # 자메이카
    "CUW": {"lat": 12.2135, "lon": -68.9496},   # 퀴라소
    "TTO": {"lat": 10.4437, "lon": -61.4191},   # 트리니다드토바고
    "PRI": {"lat": 18.1987, "lon": -66.3527},   # 푸에르토리코
}

CARIBBEAN_STACK_ORDER = [
    "LCA",  # 세인트루시아
    "VCT",  # 세인트빈센트그레나딘
    "GRD",  # 그레나다
    "MTQ",  # 마르티니크
    "DMA",  # 도미니카연방
    "GLP",  # 과들루프
    "KNA",  # 세인트키츠네비스
    "ATG",  # 앤티가바부다
]

SMALL_MARKER_HOVER_TEMPLATE = (
    "<b>%{customdata[0]}</b><br>"
    "%{customdata[1]}%{customdata[2]}<br>"
    "『%{customdata[3]}%{customdata[4]}』%{customdata[5]}<br>"
    "<extra></extra>"
)

continents_code = [
    code for code in continent_labels.keys()
    if any(info["continent"] == code for info in country_map.values())
]
continents_kr = [continent_labels[c] for c in continents_code]

def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()

def optional_suffix(value):
    text = normalize_text(value)
    return f" ({text})" if text else ""

def field_label(text, required=False):
    required_mark = " <span style='color:#d32f2f'>*</span>" if required else ""
    st.markdown(
        (
            "<div style='font-size:1rem; line-height:1.35; min-height:1.7rem; "
            "margin-bottom:0.35rem;'>"
            f"{text}{required_mark}"
            "</div>"
        ),
        unsafe_allow_html=True
    )

def add_book():
    title = normalize_text(st.session_state.title_input)
    title_original = normalize_text(st.session_state.title_original_input)
    author = normalize_text(st.session_state.author_input)
    author_original = normalize_text(st.session_state.author_original_input)
    publication_year = normalize_text(st.session_state.publication_year_input)

    country_kr = st.session_state.get("selected_country", "")

    missing_fields = []
    if not title:
        missing_fields.append("제목")
    if not author:
        missing_fields.append("저자")
    if not country_kr:
        missing_fields.append("국가")

    if missing_fields:
        st.session_state.form_feedback = (
            "warning",
            f"필수 항목을 입력해주세요: {', '.join(missing_fields)}"
        )
        return

    country_iso = country_map[country_kr]["iso"]

    existing_index = None
    for i, book in enumerate(st.session_state.books):
        if book["country_iso"] == country_iso:
            existing_index = i
            break

    new_book = {
        "title": title,
        "title_original": title_original,
        "author": author,
        "author_original": author_original,
        "publication_year": publication_year,
        "country_kr": country_kr,
        "country_iso": country_iso
    }

    if existing_index is None:
        st.session_state.books.append(new_book)
        st.session_state.form_feedback = (
            "success",
            f"{title}이(가) {country_kr}에 추가되었습니다."
        )
        st.session_state.title_input = ""
        st.session_state.title_original_input = ""
        st.session_state.author_input = ""
        st.session_state.author_original_input = ""
        st.session_state.publication_year_input = ""
        st.session_state.selected_continent = None
        st.session_state.selected_country = None
    else:
        st.session_state.replace = {
            "index": existing_index,
            "new_book": new_book
        }

def replace_book():
    candidate = st.session_state.replace
    if candidate is None:
        return

    new_book = candidate["new_book"]
    st.session_state.books[candidate["index"]] = new_book
    st.session_state.replace = None
    st.session_state.title_input = ""
    st.session_state.title_original_input = ""
    st.session_state.author_input = ""
    st.session_state.author_original_input = ""
    st.session_state.publication_year_input = ""
    st.session_state.selected_continent = None
    st.session_state.selected_country = None
    st.session_state.form_feedback = (
        "success",
        f"{new_book['title']}이(가) {new_book['country_kr']}에 추가되었습니다."
    )

def remove_book():
    country_kr = st.session_state.get("selected_country", "")

    if not country_kr:
        st.session_state.form_feedback = (
            "warning",
            f"필수 항목을 입력해주세요: {', '.join(["국가"])}"
        )
        return

    country_iso = country_map[country_kr]["iso"]
    
    existing_index = None
    for i, book in enumerate(st.session_state.books):
        if book["country_iso"] == country_iso:
            existing_index = i
            break

    if existing_index is not None:
        st.session_state.books.pop(existing_index)
        st.session_state.form_feedback = (
            "success",
            f"{country_kr}의 책이 제거되었습니다."
        )
    else:
        st.session_state.form_feedback = (
            "warning",
            f"{country_kr}에는 등록된 책이 없습니다."
        )

    st.session_state.selected_continent = None
    st.session_state.selected_country = None

def build_country_csv_df():
    books_by_iso = {
        book["country_iso"]: book
        for book in st.session_state.books
    }

    rows = []
    for country_kr, info in country_map.items():
        iso = info["iso"]
        book = books_by_iso.get(iso)

        if book is None:
            rows.append({
                "국가": country_kr,
                "저자 (한국어)": "",
                "저자 (원어)": "",
                "제목 (한국어)": "",
                "제목 (원어)": "",
                "출판연도": "",
            })
        else:
            rows.append({
                "국가": country_kr,
                "저자 (한국어)": book.get("author", ""),
                "저자 (원어)": book.get("author_original", ""),
                "제목 (한국어)": book.get("title", ""),
                "제목 (원어)": book.get("title_original", ""),
                "출판연도": book.get("publication_year", ""),
            })

    return pd.DataFrame(rows)

def load_books_from_csv(uploaded_file):
    df = pd.read_csv(uploaded_file, dtype=str, keep_default_na=False)

    required_columns = [
        "국가",
        "저자 (한국어)",
        "저자 (원어)",
        "제목 (한국어)",
        "제목 (원어)",
        "출판연도",
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return ("error", f"데이터 형식이 맞지 않습니다: {', '.join(missing_columns)}")

    loaded_books = []
    unsupported_countries = []

    for _, row in df.iterrows():
        country_kr = normalize_text(row["국가"])

        if not country_kr:
            continue

        if country_kr not in country_map:
            unsupported_countries.append(country_kr)
            continue

        author = normalize_text(row["저자 (한국어)"])
        author_original = normalize_text(row["저자 (원어)"])
        title = normalize_text(row["제목 (한국어)"])
        title_original = normalize_text(row["제목 (원어)"])
        publication_year = normalize_text(row["출판연도"])

        # if there is no data for the country
        if not any([author, author_original, title, title_original, publication_year]):
            continue

        loaded_books.append({
            "title": title,
            "title_original": title_original,
            "author": author,
            "author_original": author_original,
            "publication_year": publication_year,
            "country_kr": country_kr,
            "country_iso": country_map[country_kr]["iso"],
        })

    st.session_state.books = loaded_books
    if unsupported_countries:
        unique_unsupported = sorted(set(unsupported_countries))
        return (
            "warning",
            (
                f"{len(loaded_books)}개 국가의 데이터를 불러왔습니다. "
                f"지원하지 않는 국가는 제외되었습니다: {', '.join(unique_unsupported)}"
            ),
        )

    return ("success", f"{len(loaded_books)}개 국가의 데이터를 불러왔습니다.")

def ratio_to_rgba(hex_color, ratio):
    ratio = max(0.0, min(1.0, float(ratio)))
    alpha = 0.1 + 0.9 * ratio

    hex_color = hex_color.lstrip("#")
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    return f"rgba({r}, {g}, {b}, {alpha})"

def build_progress_summary():
    registered_isos = {book["country_iso"] for book in st.session_state.books}

    continent_totals = {code: 0 for code in continent_labels.keys()}
    continent_done = {code: 0 for code in continent_labels.keys()}

    country_isos = {info["iso"] for info in country_map.values()}
    registered_known_isos = registered_isos & country_isos

    for _, info in country_map.items():
        code = info["continent"]
        if not info.get("additional", False):
            continent_totals[code] += 1
        if info["iso"] in registered_known_isos:
            continent_done[code] += 1

    total_done = len(registered_known_isos)
    total_all = sum(1 for info in country_map.values() if not info.get("additional", False))

    items = [
        {"code": "TT", "label": "전체", "done": total_done, "total": total_all},
        {"code": "AF", "label": "아프리카", "done": continent_done["AF"], "total": continent_totals["AF"]},
        {"code": "AS", "label": "아시아", "done": continent_done["AS"], "total": continent_totals["AS"]},
        {"code": "OC", "label": "오세아니아", "done": continent_done["OC"], "total": continent_totals["OC"]},
        {"code": "EU", "label": "유럽", "done": continent_done["EU"], "total": continent_totals["EU"]},
        {"code": "AM", "label": "아메리카", "done": continent_done["AM"], "total": continent_totals["AM"]},
    ]

    for item in items:
        item["ratio"] = item["done"] / item["total"] if item["total"] else 0.0

    return items

def render_progress_circles():
    items = build_progress_summary()

    cards_html = "".join(
        f"""
        <div style="text-align:center;">
            <div style="
                position:relative;
                width:96px; height:96px;
                margin:0 auto 6px auto;
                border:3px solid black;
                border-radius:50%;
                background:#efefef;
                overflow:hidden;
            ">
                <div style="
                    position:absolute;
                    left:0; bottom:0;
                    width:100%; height:{(item["ratio"]*100 if item["done"]>0 else 0)}%;
                    background:{ratio_to_rgba(continent_colors[item["code"]], item["ratio"])};
                "></div>
                <div style="
                    position:absolute;
                    inset:0;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    font-weight:700;
                    font-size:17px;
                ">
                    {item["done"]}/{item["total"]}
                </div>
            </div>
            <div style="font-size:14px; font-weight:600;">
                {item["label"]}
            </div>
        </div>
        """
        for item in items
    )

    html = f"""
    <div style="
        display:flex;
        justify-content:center;
        gap:50px;
        flex-wrap:wrap;
        margin-bottom:0px;
    ">
        {cards_html}
    </div>
    """

    st.html(html)

def build_small_marker_customdata(row):
    return [
        row["country_kr"],
        row["author"],
        optional_suffix(row["author_original"]),
        row["title"],
        optional_suffix(row["title_original"]),
        optional_suffix(row["publication_year"]),
    ]

def add_small_country_markers(fig, books_df):
    # Larger value means marker is drawn later (on top) within the same trace.
    draw_order = {
        iso: len(CARIBBEAN_STACK_ORDER) - idx
        for idx, iso in enumerate(CARIBBEAN_STACK_ORDER)
    }

    point_rows = []
    for _, row in books_df.iterrows():
        iso = row["country_iso"]
        if iso in small_country_points:
            continent_code = country_map.get(row["country_kr"], {}).get("continent")
            point_rows.append({
                "country_iso": iso,
                "country_kr": row["country_kr"],
                "title": normalize_text(row.get("title", "")),
                "title_original": normalize_text(row.get("title_original", "")),
                "author": normalize_text(row.get("author", "")),
                "author_original": normalize_text(row.get("author_original", "")),
                "publication_year": normalize_text(row.get("publication_year", "")),
                "continent_code": continent_code,
                "lat": small_country_points[iso]["lat"],
                "lon": small_country_points[iso]["lon"],
                "draw_order": draw_order.get(iso, 0),
            })

    if point_rows:
        point_df = pd.DataFrame(point_rows)

        for continent_code, group in point_df.groupby("continent_code", dropna=False):
            group = group.sort_values("draw_order", ascending=True, kind="mergesort")
            marker_color = continent_colors.get(continent_code, "gold")
            customdata = group.apply(
                build_small_marker_customdata,
                axis=1
            ).tolist()
            fig.add_trace(
                go.Scattergeo(
                    lon=group["lon"],
                    lat=group["lat"],
                    mode="markers",
                    marker=dict(
                        size=4,
                        color=marker_color,
                        line=dict(width=1, color="black")
                    ),
                    customdata=customdata,
                    hovertemplate=SMALL_MARKER_HOVER_TEMPLATE,
                    showlegend=False
                )
            )