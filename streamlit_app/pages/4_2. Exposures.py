import streamlit as st
from pathlib import Path
import pandas as pd
from html import escape
from utils.iriscc_utils import apply_app_style
st.set_page_config(page_title="2. Exposures", layout="wide")

apply_app_style()

BASE_DIR = Path(__file__).resolve().parent

st.title("Step 2 — Air quality and weather data")

st.markdown("""
            Fine-resolution data has been modeled for many major exposome factors, including air pollution and weather [1].
            Open data platforms facilitate access to these datasets for research into the health impacts of environmental exposures.
            One place to find modeled data for all of Europe is the [Exposome Maps Platform](https://exposome.uu.nl/). Other sources
            may include national or regional environmental agencies, or research consortia. It is also possible to create your own exposure datasets from raw measurements.
            
            In this demonstrator, we will consider the following datasets from the Exposome Maps Platform related to **air quality** and **weather**. 
            Notice that the datasets have different spatial and temporal resolutions, which affects how they can be linked
            to the cohort and what types of analysis can be performed later.

            Explore the datasets below and select the ones that you want to work with in the next steps. You can select as many as you want.
            """)

st.markdown(
    """
    <div style="
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.35rem 0.8rem;
        border-radius: 999px;
        background: rgba(15, 118, 110, 0.10);
        color: #0f766e;
        font-weight: 700;
        font-size: 0.82rem;
        margin-bottom: 1rem;
    ">
        <span>Derived from the Exposome Maps platform inventory</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Session state
# -----------------------------------------------------------------------------
if "exposure_selection" not in st.session_state:
    st.session_state["exposure_selection"] = []

if "weather_selection" not in st.session_state:
    st.session_state["weather_selection"] = []

# -----------------------------------------------------------------------------
# Dataset definitions
# -----------------------------------------------------------------------------
exposure_options = {
    "Annual PM10": "Annual avg (2020) — 25m resolution",
    "Annual PM2.5": "Annual avg (2020) — 25m resolution",
    "Annual O3": "Annual avg (2020) — 25m resolution",
    "Annual NO2": "Annual avg (2020) — 25m resolution",
    "Annual Black Carbon": "Annual avg (2010) — 100m resolution",
}

weather_options = {
    "Annual mean temperature": "2020 — 1km resolution",
    "Monthly mean temperature (Dec 2020)": "1km resolution",
    "Daily mean temperature (31 Dec 2020)": "1km resolution",
    "Daily minimum temperature (31 Dec 2020)": "1km resolution",
    "Daily maximum temperature (31 Dec 2020)": "1km resolution",
}

EXPOSOME_INVENTORY_URL = (
    "https://raw.githubusercontent.com/UtrechtUniversity/Exposome-Map-Documents/"
    "main/Exposome_maps_inventory/Exposome%20maps%20inventory.csv"
)

DATASET_CANDIDATES = {
    "Annual PM10": "Annual PM10 25m",
    "Annual PM2.5": "Annual PM2.5 25m",
    "Annual O3": "Annual O3 25m",
    "Annual NO2": "Annual NO2 25m",
    "Annual Black Carbon": "Black carbon along road networks Amsterdam",
    "Annual mean temperature": "Yearly average temperature",
    "Monthly mean temperature (Dec 2020)": "Monthly average temperature",
    "Daily mean temperature (31 Dec 2020)": "Daily average temperature",
    "Daily minimum temperature (31 Dec 2020)": "Daily minimum temperature",
    "Daily maximum temperature (31 Dec 2020)": "Daily maximum temperature",
}

PREFERRED_METADATA_COLUMNS = [
    "Title",
    "Subtitle",
    "Description",
    "Category",
    "Theme",
    "Parameter",
    "Spatial resolution",
    "Temporal resolution",
    "Units",
    "Coverage",
    "thumbnail",
]

# -----------------------------------------------------------------------------
# Helper function for toggle behavior
# -----------------------------------------------------------------------------
def toggle_selection(name, state_key):
    if name in st.session_state[state_key]:
        st.session_state[state_key].remove(name)
    else:
        st.session_state[state_key].append(name)


@st.cache_data(show_spinner=False)
def load_inventory():
    try:
        return pd.read_csv(EXPOSOME_INVENTORY_URL)
    except Exception:
        return pd.DataFrame()


def normalize_text(value):
    return " ".join(str(value).lower().replace(".", " ").replace("-", " ").split())


def find_inventory_row(dataset_name, inventory):
    if inventory.empty or "Title" not in inventory.columns:
        return None

    exact_title = DATASET_CANDIDATES.get(dataset_name)
    if not exact_title:
        return None

    titles = inventory["Title"].fillna("").astype(str)

    exact_matches = inventory[titles.str.strip().str.casefold() == exact_title.strip().casefold()]
    if len(exact_matches) >= 1:
        return exact_matches.iloc[0]

    return None


def get_metadata_value(row, *possible_columns):
    if row is None:
        return ""

    for column_name in possible_columns:
        if column_name in row and pd.notna(row[column_name]):
            value = str(row[column_name]).strip()
            if value:
                return value
    return ""


def build_metadata_cards(dataset_name):
    inventory = load_inventory()
    row = find_inventory_row(dataset_name, inventory)

    title_value = get_metadata_value(row, "Title") or dataset_name
    description_value = get_metadata_value(row, "Description", "Subtitle", "Summary")
    category_value = get_metadata_value(row, "Category", "Theme", "Parameter group")
    spatial_value = get_metadata_value(row, "Spatial resolution", "Resolution", "Grid resolution")
    temporal_value = get_metadata_value(row, "Temporal resolution", "Time resolution", "Temporal coverage")
    unit_value = get_metadata_value(row, "Units", "Unit")
    coverage_value = get_metadata_value(row, "Coverage", "Area", "Geographic coverage")
    thumbnail_value = get_metadata_value(row, "thumbnail", "Thumbnail", "thumbnail_url")

    return {
        "title": title_value,
        "description": description_value,
        "category": category_value,
        "spatial": spatial_value,
        "temporal": temporal_value,
        "unit": unit_value,
        "coverage": coverage_value,
        "thumbnail": thumbnail_value,
    }


def render_dataset_card(name, desc, selected, key_prefix, state_key, group_label):
    metadata = build_metadata_cards(name)
    thumbnail_html = (
        f'<img src="{escape(metadata["thumbnail"], quote=True)}" style="width:100%; height:100%; object-fit:cover; display:block;" />'
        if metadata["thumbnail"]
        else '<div style="padding:0.8rem; text-align:center; color:#5f6b7a; font-size:0.84rem; line-height:1.35;">Thumbnail space<br>from inventory</div>'
    )

    metadata_grid = []
    for label, value in [
        ("Category", metadata["category"]),
        ("Spatial resolution", metadata["spatial"]),
        ("Temporal resolution", metadata["temporal"]),
        ("Units", metadata["unit"]),
        ("Coverage", metadata["coverage"]),
    ]:
        metadata_grid.append(
            f'<div><div style="font-size:0.74rem; text-transform:uppercase; letter-spacing:0.06em; color:#5f6b7a; font-weight:700;">{escape(label)}</div><div style="font-weight:600;">{escape(value)}</div></div>'
        )
    metadata_grid_html = "".join(metadata_grid)

    with st.container():
        st.markdown(
            f"""
            <div class="iriscc-card {'is-selected' if selected else ''}">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; margin-bottom:0.9rem;">
                    <div class="iriscc-card-badge">Exposome Maps</div>
                    <div style="font-size:0.78rem; font-weight:700; color:#5f6b7a; text-transform:uppercase; letter-spacing:0.08em;">{escape(group_label)}</div>
                </div>
                <div style="display:flex; gap:1rem; align-items:stretch; flex-wrap:wrap;">
                    <div style="flex: 0 0 160px; min-width: 160px;">
                        <div style="
                            width: 160px;
                            height: 120px;
                            border-radius: 16px;
                            border: 1px solid rgba(16, 24, 40, 0.10);
                            background: linear-gradient(135deg, rgba(18, 59, 93, 0.06), rgba(15, 118, 110, 0.10));
                            overflow: hidden;
                            display:flex;
                            align-items:center;
                            justify-content:center;
                        ">
                            {thumbnail_html}
                        </div>
                    </div>
                    <div style="flex: 1 1 320px; min-width: 280px;">
                        <div class="iriscc-card-title">{escape(metadata['title'])}</div>
                        <div class="iriscc-card-subtitle" style="margin-bottom:0.9rem;">{escape(metadata['description'] or desc)}</div>
                        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap:0.6rem;">{metadata_grid_html}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        btn_col, _ = st.columns([1, 8])
        with btn_col:
            if st.button(
                "✓" if selected else "+",
                key=f"{key_prefix}_{name}",
                use_container_width=True,
            ):
                toggle_selection(name, state_key)
                st.rerun()

# -----------------------------------------------------------------------------
# UI layout
# -----------------------------------------------------------------------------
col1, col2 = st.columns(2)

# =============================================================================
# Exposure cards
# =============================================================================
with col1:
    st.subheader("Air Quality")

    for name, desc in exposure_options.items():
        selected = name in st.session_state["exposure_selection"]
        render_dataset_card(name, desc, selected, "exp", "exposure_selection", "Air quality")

# =============================================================================
# Weather cards
# =============================================================================
with col2:
    st.subheader("Weather")

    for name, desc in weather_options.items():
        selected = name in st.session_state["weather_selection"]
        render_dataset_card(name, desc, selected, "wea", "weather_selection", "Weather")

# -----------------------------------------------------------------------------
# Summary section
# -----------------------------------------------------------------------------
st.markdown("---")

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Selected air quality datasets")
    if st.session_state["exposure_selection"]:
        for d in st.session_state["exposure_selection"]:
            st.write("•", d)
    else:
        st.warning("None selected")

with col_b:
    st.subheader("Selected weather datasets")
    if st.session_state["weather_selection"]:
        for d in st.session_state["weather_selection"]:
            st.write("•", d)
    else:
        st.warning("None selected")