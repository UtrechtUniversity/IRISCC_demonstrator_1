import streamlit as st
from html import escape

from utils.iriscc_utils import apply_app_style

st.set_page_config(page_title="2. Exposures", layout="wide")
apply_app_style()

st.title("Step 2 — Select air quality and weather data")

st.markdown(
    """
    Choose the variables you want to work with and define the time period for each one.
    You can select as many air quality and weather items as needed, and each item can be linked
    to either a single day or a time range.
    """
)

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
        <span>Flexible variable selection</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Session state
# -----------------------------------------------------------------------------
if "exposure_selection" not in st.session_state:
    st.session_state["exposure_selection"] = {}

if "weather_selection" not in st.session_state:
    st.session_state["weather_selection"] = {}


def default_selection_record(name):
    return {
        "variable": name,
        "timeframe_type": "single_day",
        "single_day": "",
        "start_date": "",
        "end_date": "",
    }


def ensure_selection_record(state_key, name):
    store = st.session_state[state_key]
    if name not in store:
        store[name] = default_selection_record(name)
    return store[name]


def toggle_selection(state_key, name):
    store = st.session_state[state_key]
    if name in store:
        del store[name]
    else:
        store[name] = default_selection_record(name)


def format_timeframe_summary(record):
    if not record:
        return "No timeframe selected"

    timeframe_type = record.get("timeframe_type", "single_day")
    if timeframe_type == "single_day":
        single_day = record.get("single_day", "").strip()
        if single_day:
            return f"Single day: {single_day}"
        return "Single day: not set"

    start_date = record.get("start_date", "").strip()
    end_date = record.get("end_date", "").strip()
    if start_date and end_date:
        return f"Time range: {start_date} to {end_date}"
    if start_date:
        return f"Time range: from {start_date}"
    if end_date:
        return f"Time range: until {end_date}"
    return "Time range: not set"


def slugify(value):
    return (
        value.lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "_")
        .replace(".", "")
    )


# -----------------------------------------------------------------------------
# Dataset definitions
# -----------------------------------------------------------------------------
exposure_options = {
    "Annual PM10": "PM10",
    "Annual PM2.5": "PM2_5",
    "Annual O3": "O3",
    "Annual NO2": "NO2",
    "Annual Black Carbon": "BC",
}

weather_options = {
    "Annual mean temperature": "TMP_AVG_YEARLY",
    "Daily mean temperature (31 Dec 2020)": "TMP_AVG_DAILY",
    "Daily maximum temperature (31 Dec 2020)": "TMP_MAX_DAILY",
}

variable_metadata = {
    "Annual PM10": {
        "spatial_resolution": "TBD",
        "temporal_coverage": "TBD",
        "unit": "TBD",
        "description": "Fine-scale particulate matter estimate for annual exposure assessment.",
        "thumbnail": "",
    },
    "Annual PM2.5": {
        "spatial_resolution": "TBD",
        "temporal_coverage": "TBD",
        "unit": "TBD",
        "description": "Fine-scale particulate matter estimate for annual exposure assessment.",
        "thumbnail": "",
    },
    "Annual O3": {
        "spatial_resolution": "TBD",
        "temporal_coverage": "TBD",
        "unit": "TBD",
        "description": "Ground-level ozone model output intended for long-term comparison.",
        "thumbnail": "",
    },
    "Annual NO2": {
        "spatial_resolution": "TBD",
        "temporal_coverage": "TBD",
        "unit": "TBD",
        "description": "Nitrogen dioxide exposure indicator for annual health analyses.",
        "thumbnail": "",
    },
    "Annual Black Carbon": {
        "spatial_resolution": "TBD",
        "temporal_coverage": "TBD",
        "unit": "TBD",
        "description": "Black carbon metric designed for road-network or traffic-related analyses.",
        "thumbnail": "",
    },
    "Annual mean temperature": {
        "spatial_resolution": "TBD",
        "temporal_coverage": "TBD",
        "unit": "TBD",
        "description": "Long-term annual average thermal condition used for climate exposure comparisons.",
        "thumbnail": "",
    },
    "Monthly mean temperature (Dec 2020)": {
        "spatial_resolution": "TBD",
        "temporal_coverage": "TBD",
        "unit": "TBD",
        "description": "Monthly average temperature relevant to seasonal conditions and heat stress.",
        "thumbnail": "",
    },
    "Daily mean temperature (31 Dec 2020)": {
        "spatial_resolution": "TBD",
        "temporal_coverage": "TBD",
        "unit": "TBD",
        "description": "Daily average temperature for short-term weather and exposure analyses.",
        "thumbnail": "",
    },
    "Daily minimum temperature (31 Dec 2020)": {
        "spatial_resolution": "TBD",
        "temporal_coverage": "TBD",
        "unit": "TBD",
        "description": "Daily minimum temperature indicator for cold exposure evaluation.",
        "thumbnail": "",
    },
    "Daily maximum temperature (31 Dec 2020)": {
        "spatial_resolution": "TBD",
        "temporal_coverage": "TBD",
        "unit": "TBD",
        "description": "Daily maximum temperature indicator for hot-day and heat exposure analyses.",
        "thumbnail": "",
    },
}


def render_variable_card(name, desc, state_key, group_label, selected):
    metadata = variable_metadata.get(name, {})
    thumbnail_html = (
        f'<img src="{escape(metadata.get("thumbnail", ""), quote=True)}" style="width:100%; height:100%; object-fit:cover; display:block;" />'
        if metadata.get("thumbnail")
        else '<div style="padding:0.8rem; text-align:center; color:#5f6b7a; font-size:0.84rem; line-height:1.35;">Thumbnail<br>placeholder</div>'
    )

    metadata_grid = []
    for label, value in [
        ("Spatial resolution", metadata.get("spatial_resolution", "TBD")),
        ("Temporal coverage", metadata.get("temporal_coverage", "TBD")),
        ("Unit", metadata.get("unit", "TBD")),
    ]:
        metadata_grid.append(
            f'<div><div style="font-size:0.72rem; text-transform:uppercase; letter-spacing:0.06em; color:#5f6b7a; font-weight:700;">{escape(label)}</div><div style="font-weight:600;">{escape(str(value))}</div></div>'
        )
    metadata_grid_html = "".join(metadata_grid)

    with st.container():
        st.markdown(
            f"""
            <div class="iriscc-card {'is-selected' if selected else ''}">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; margin-bottom:0.9rem;">
                    <div class="iriscc-card-badge">Variable</div>
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
                        <div class="iriscc-card-title">{escape(name)}</div>
                        <div class="iriscc-card-subtitle" style="margin-bottom:0.9rem;">{escape(metadata.get("description", desc))}</div>
                        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap:0.6rem;">{metadata_grid_html}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        select_button_label = "Selected" if selected else "Select variable"
        if st.button(select_button_label, key=f"{state_key}_{slugify(name)}_toggle", use_container_width=True):
            toggle_selection(state_key, name)
            st.rerun()

        if selected:
            record = ensure_selection_record(state_key, name)
            timeframe_type = st.radio(
                "Timeframe type",
                ["Single day", "Time range"],
                index=0 if record["timeframe_type"] == "single_day" else 1,
                horizontal=True,
                key=f"{state_key}_{slugify(name)}_timeframe",
            )
            record["timeframe_type"] = "single_day" if timeframe_type == "Single day" else "time_range"

            if record["timeframe_type"] == "single_day":
                record["single_day"] = st.text_input(
                    "Date",
                    value=record.get("single_day", ""),
                    key=f"{state_key}_{slugify(name)}_single_day",
                    placeholder="YYYY-MM-DD",
                )
                record["start_date"] = ""
                record["end_date"] = ""
            else:
                record["start_date"] = st.text_input(
                    "Start date",
                    value=record.get("start_date", ""),
                    key=f"{state_key}_{slugify(name)}_start_date",
                    placeholder="YYYY-MM-DD",
                )
                record["end_date"] = st.text_input(
                    "End date",
                    value=record.get("end_date", ""),
                    key=f"{state_key}_{slugify(name)}_end_date",
                    placeholder="YYYY-MM-DD",
                )
                record["single_day"] = ""

            st.caption(f"Selection saved: {format_timeframe_summary(record)}")

# -----------------------------------------------------------------------------
# UI layout
# -----------------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Air Quality")
    for name, desc in exposure_options.items():
        render_variable_card(name, desc, "exposure_selection", "Air quality", name in st.session_state["exposure_selection"])

with col2:
    st.subheader("Weather")
    for name, desc in weather_options.items():
        render_variable_card(name, desc, "weather_selection", "Weather", name in st.session_state["weather_selection"])

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
st.markdown("---")

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Selected air quality datasets")
    if st.session_state["exposure_selection"]:
        for name, record in st.session_state["exposure_selection"].items():
            st.write(f"• {name} — {format_timeframe_summary(record)}")
    else:
        st.warning("None selected")

with col_b:
    st.subheader("Selected weather datasets")
    if st.session_state["weather_selection"]:
        for name, record in st.session_state["weather_selection"].items():
            st.write(f"• {name} — {format_timeframe_summary(record)}")
    else:
        st.warning("None selected")

st.caption("Session state is stored as a per-variable selection map with its own date or date-range inputs.")

