import streamlit as st
from html import escape
from datetime import date, timedelta
from pathlib import Path
import base64
import mimetypes
import os

from utils.iriscc_utils import apply_app_style

BASE_DIR = Path(__file__).resolve().parents[1]

st.set_page_config(page_title="2. Exposures", layout="wide")
apply_app_style()

st.markdown(
    """
    <div class="iriscc-page-header">
        <h2 class="iriscc-page-title">Step 2 — Select air quality and weather data</h2>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='iriscc-section-title'><strong>Exposure variables</strong></div>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="iriscc-body">
        This demonstrator focuses on two main types of exposure variables: air quality and weather data.
        <br><br>
        In the field of exposomics, exposure variables are environmental factors that individuals or populations are exposed to, which can have an impact on their health.
        These variables can be physical (e.g., temperature, noise), chemical (e.g., air pollutants, pesticides), related to the build environment (e.g. greenspaces, walkability), and more.
        <br><br>
        Exposure can be estimated in various ways. It can be measured directly, for example by using sensors in houses, giving surveys, or giving wearable devices to cohort members. Or it can be estimated based on models,
        useful when some exposures are impossible to measure comprehensively.
        Models use data from measurement stations and other data sources, such as satellite imagery, to estimate exposure levels across different locations and times. There are many data catalogues on the internet where you can find datasets of modeled exposure variables. In this demonstrator, we'll use datasets created in the <a href=\"https://expanseproject.eu/">Expanse Project</a>.
        All of the datasets created in this project are available in a <a href=\"https://exposome.uu.nl/">data catalogue</a> so other researchers can access them for their own studies. 
        <br><br>
        Studies show that combining pollutants can help reduce double-counting in health impact assessments and support more useful burden estimates for policy-makers [<a href=\"https://www.sciencedirect.com/science/article/pii/S0160412026002965?via%3Dihub">3</a>].
        Use the selection cards below to select the exposure variables you want to link to your cohort. You can select multiple pollutants.
        <br><br>
        Watch out! Different variables are available at differnet temporal and spatial resolutions, which will affect your subsequent analysis.
        <br><br>
     </div>
    """,
    unsafe_allow_html=True,
)



        # <div class="exposure-step">Step 2 of 4</div>
        #     <div class="exposure-intro-text">You can select multiple pollutants. Combining pollutants can help reduce double-counting in health impact assessments and support more useful burden estimates for policy-makers [<a href=\"https://www.sciencedirect.com/science/article/pii/S0160412026002965?via%3Dihub/\">3</a>].</div>
        # </div>

# st.markdown(
#     """
#     <div class="selection-guide">
#         <span>Select a variable</span>
#         <span>Set its timeframe</span>
#         <span>Review your selections below</span>
#     </div>
#     """,
#     unsafe_allow_html=True,
# )

# -----------------------------------------------------------------------------
# Session state
# -----------------------------------------------------------------------------
if "pollutant_selection" not in st.session_state:
    st.session_state["pollutant_selection"] = {}

if "weather_selection" not in st.session_state:
    st.session_state["weather_selection"] = {}


def default_selection_record(name):
    return {
        "variable": name,
        "timeframe_type": "single_day",
        "single_day": "",
        "start_date": "",
        "end_date": "",
        "single_year": "",
        "start_year": "",
        "end_year": "",
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
    if timeframe_type == "single_year":
        single_year = record.get("single_year", "").strip()
        if single_year:
            return f"{single_year}"
        return "Single year: not set"

    if timeframe_type == "year_range":
        start_year = record.get("start_year", "").strip()
        end_year = record.get("end_year", "").strip()
        if start_year and end_year:
            return f"{start_year} to {end_year}"
        if start_year:
            return f"{start_year}"
        if end_year:
            return f"{end_year}"
        return "Year range: not set"

    if timeframe_type == "single_day":
        single_day = record.get("single_day", "")
        if single_day:
            return f"{single_day}"
        return "Single day: not set"

    start_date = record.get("start_date", "").strip()
    end_date = record.get("end_date", "").strip()
    if start_date and end_date:
        return f"{start_date} to {end_date}"
    if start_date:
        return f"{start_date}"
    if end_date:
        return f"{end_date}"
    return "Day range: not set"


def get_temporal_mode(name):
    metadata = variable_metadata.get(name, {})
    mode = str(metadata.get("temporal_mode", "daily")).strip().lower()
    return "yearly" if mode == "yearly" else "daily"


def parse_metadata_date(value):
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def parse_metadata_year(value):
    value = str(value).strip()
    return int(value) if len(value) == 4 and value.isdigit() else None


def metadata_time_bounds(metadata, temporal_mode):
    start_time = metadata.get("start_time", "")
    end_time = metadata.get("end_time", "")
    if temporal_mode == "yearly":
        return parse_metadata_year(start_time), parse_metadata_year(end_time)
    return parse_metadata_date(start_time), parse_metadata_date(end_time)


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


def thumbnail_data_uri(relative_path):
    if not relative_path:
        return ""

    thumbnail_path = BASE_DIR / relative_path
    if not thumbnail_path.is_file():
        return ""

    mime_type = mimetypes.guess_type(thumbnail_path.name)[0] or "application/octet-stream"
    encoded_image = base64.b64encode(thumbnail_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded_image}"


def variable_selection_to_raster_list(variable_selection_dict):
    raster_list = []
    for variable, record in variable_selection_dict.items():
        if record.get("timeframe_type") == "single_day":
            date_name = record.get("single_day", "").replace("-", "_")
            raster_list.append(f"{variable_metadata[variable]['raster_prefix']}_{date_name}")
        elif record.get("timeframe_type") == "day_range":
            start_date = parse_metadata_date(record.get("start_date"))
            end_date = parse_metadata_date(record.get("end_date"))
            if start_date and end_date and start_date <= end_date:
                current_date = start_date
                while current_date <= end_date:
                    date_name = current_date.isoformat().replace("-", "_")
                    raster_list.append(f"{variable_metadata[variable]['raster_prefix']}_{date_name}")
                    current_date += timedelta(days=1)
        elif record.get("timeframe_type") == "single_year":
            year_name = str(record.get("single_year", "")).replace("-", "_")
            raster_list.append(f"{variable_metadata[variable]['raster_prefix']}_{year_name}")
        elif record.get("timeframe_type") == "year_range":
            start_year = parse_metadata_year(record.get("start_year"))
            end_year = parse_metadata_year(record.get("end_year"))
            if start_year and end_year and start_year <= end_year:
                for year in range(start_year, end_year + 1):
                    year_name = str(year).replace("-", "_")
                    raster_list.append(f"{variable_metadata[variable]['raster_prefix']}_{year_name}")
    return raster_list

# -----------------------------------------------------------------------------
# Dataset definitions
# -----------------------------------------------------------------------------
pollutant_options = {
    "Annual PM10": "PM10",
    "Annual PM2.5": "PM2_5",
    "Annual O3": "O3",
    "Annual NO2": "NO2",
}

weather_options = {
    "Annual mean temperature": "TMP_AVG_YEARLY",
    "Daily mean temperature": "TMP_AVG_DAILY",
    "Daily maximum temperature": "TMP_MAX_DAILY",
}

variable_metadata = {
    "Annual PM10": {
        "spatial_resolution": "25x25m",
        "temporal_mode": "yearly",
        "start_time": "2019",
        "end_time": "2023",
        "unit": "μg/m³",
        "description": "Inhalable particles with diameters 10 micrometers and smaller",
        "thumbnail": "Resources/thumbnails/pm10.png",
        "raster_prefix": "PM10"
    },
    "Annual PM2.5": {
        "spatial_resolution": "25x25m",
        "temporal_mode": "yearly",
        "start_time": "2019",
        "end_time": "2023",
        "unit": "μg/m³",
        "description": "Inhalable particles with diameters 2.5 micrometers and smaller",
        "thumbnail": "Resources/thumbnails/pm25.png",
        "raster_prefix": "PM2_5"
    },
    "Annual O3": {
        "spatial_resolution": "25x25m",
        "temporal_mode": "yearly",
        "start_time": "2019",
        "end_time": "2023",
        "unit": "μg/m³",
        "description": "Ground-level ozone, the result of reactions of man-made volatile organic compounds and nitrogen oxides",
        "thumbnail": "Resources/thumbnails/o3.png",
        "raster_prefix": "O3"
    },
    "Annual NO2": {
        "spatial_resolution": "25x25m",
        "temporal_mode": "yearly",
        "start_time": "2019",
        "end_time": "2023",
        "unit": "μg/m³",
        "description": "Nitrogen dioxide that gets in the air from the burning of fuel, primarily from vehicles and power plants",
        "thumbnail": "Resources/thumbnails/no2.png",
        "raster_prefix": "NO2"
    },
    "Annual mean temperature": {
        "spatial_resolution": "1x1km",
        "temporal_mode": "yearly",
        "start_time": "2020",
        "end_time": "2024",
        "unit": "°C",
        "description": "Modeled yearly average tempeature",
        "thumbnail": "Resources/thumbnails/yearly_avg_temp.png",
        "raster_prefix": "TMP_AVG"
    },
    "Daily mean temperature": {
        "spatial_resolution": "1x1km",
        "temporal_mode": "daily",
        "start_time": "2020-01-01",
        "end_time": "2024-12-31",
        "unit": "°C",
        "description": "Modeled daily average temperature",
        "thumbnail": "Resources/thumbnails/daily_average_temperature.png",
        "raster_prefix": "TMP_AVG"
    },
    "Daily maximum temperature": {
        "spatial_resolution": "1x1km",
        "temporal_mode": "daily",
        "start_time": "2020-01-01",
        "end_time": "2024-12-31",
        "unit": "°C",
        "description": "Modeled daily maximum temperature",
        "thumbnail": "Resources/thumbnails/daily_maximum_temperature.png",
        "raster_prefix": "TMP_MAX"
    },
}


def render_variable_card(name, desc, state_key, selected):
    metadata = variable_metadata.get(name, {})
    thumbnail_uri = thumbnail_data_uri(metadata.get("thumbnail", ""))
    thumbnail_html = (
        f'<img src="{escape(thumbnail_uri, quote=True)}" alt="{escape(name, quote=True)} thumbnail" style="width:100%; height:100%; object-fit:cover; display:block;" />'
        if thumbnail_uri
        else '<div style="padding:0.8rem; text-align:center; color:#5f6b7a; font-size:0.84rem; line-height:1.35;">Thumbnail<br>placeholder</div>'
    )

    metadata_grid = []
    for label, value in [
        ("Spatial resolution", metadata.get("spatial_resolution", "TBD")),
        ("Available window", f"{metadata.get('start_time', 'TBD')} to {metadata.get('end_time', 'TBD')}"),
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
                <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; margin-bottom:0.8rem;">
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

        select_button_label = "Remove variable" if selected else "Select variable"
        if st.button(select_button_label, key=f"{state_key}_{slugify(name)}_toggle", use_container_width=True):
            toggle_selection(state_key, name)
            st.rerun()

        if selected:
            record = ensure_selection_record(state_key, name)
            temporal_mode = get_temporal_mode(name)
            start_time, end_time = metadata_time_bounds(metadata, temporal_mode)

            if temporal_mode == "yearly":
                valid_timeframe = (
                    start_time is not None
                    and end_time is not None
                    and start_time <= end_time
                )
                timeframe_type = st.radio(
                    "Timeframe type",
                    ["Single year", "Year range"],
                    index=0 if record.get("timeframe_type") != "year_range" else 1,
                    horizontal=True,
                    key=f"{state_key}_{slugify(name)}_timeframe",
                )
                record["timeframe_type"] = "single_year" if timeframe_type == "Single year" else "year_range"

                if not valid_timeframe:
                    st.warning("Set valid start_time and end_time years in this variable's metadata.")
                else:
                    available_years = [str(year) for year in range(start_time, end_time + 1)]

                    if record["timeframe_type"] == "single_year":
                        selected_year = record.get("single_year", "")
                        if selected_year not in available_years:
                            selected_year = available_years[0]
                        record["single_year"] = st.selectbox(
                            "Year",
                            available_years,
                            index=available_years.index(selected_year),
                            key=f"{state_key}_{slugify(name)}_single_year",
                        )
                        record["start_year"] = ""
                        record["end_year"] = ""
                    else:
                        selected_start = record.get("start_year", "")
                        if selected_start not in available_years:
                            selected_start = available_years[0]
                        start_year = st.selectbox(
                            "Start year",
                            available_years,
                            index=available_years.index(selected_start),
                            key=f"{state_key}_{slugify(name)}_start_year",
                        )
                        end_year_options = [
                            year for year in available_years if int(year) >= int(start_year)
                        ]
                        selected_end = record.get("end_year", "")
                        if selected_end not in end_year_options:
                            selected_end = end_year_options[-1]
                        end_year = st.selectbox(
                            "End year",
                            end_year_options,
                            index=end_year_options.index(selected_end),
                            key=f"{state_key}_{slugify(name)}_end_year",
                        )
                        record["start_year"] = start_year
                        record["end_year"] = end_year
                        record["single_year"] = ""

                record["single_day"] = ""
                record["start_date"] = ""
                record["end_date"] = ""
            else:
                valid_timeframe = (
                    start_time is not None
                    and end_time is not None
                    and start_time <= end_time
                )
                timeframe_type = st.radio(
                    "Timeframe type",
                    ["Single day", "Day range"],
                    index=0 if record.get("timeframe_type") not in ("time_range", "day_range") else 1,
                    horizontal=True,
                    key=f"{state_key}_{slugify(name)}_timeframe",
                )
                record["timeframe_type"] = "single_day" if timeframe_type == "Single day" else "day_range"

                if not valid_timeframe:
                    st.warning("Set valid start_time and end_time dates (YYYY-MM-DD) in this variable's metadata.")
                elif record["timeframe_type"] == "single_day":
                    selected_day = parse_metadata_date(record.get("single_day")) or start_time
                    selected_day = min(max(selected_day, start_time), end_time)
                    selected_day = st.date_input(
                        "Day",
                        value=selected_day,
                        min_value=start_time,
                        max_value=end_time,
                        key=f"{state_key}_{slugify(name)}_single_day",
                        format="YYYY-MM-DD",
                    )
                    record["single_day"] = selected_day.isoformat()
                    record["start_date"] = ""
                    record["end_date"] = ""
                else:
                    selected_start = parse_metadata_date(record.get("start_date")) or start_time
                    selected_end = parse_metadata_date(record.get("end_date")) or end_time
                    selected_start = min(max(selected_start, start_time), end_time)
                    selected_end = min(max(selected_end, start_time), end_time)
                    if selected_end < selected_start:
                        selected_end = selected_start
                    selected_range = st.date_input(
                        "Day range",
                        value=(selected_start, selected_end),
                        min_value=start_time,
                        max_value=end_time,
                        key=f"{state_key}_{slugify(name)}_day_range",
                        format="YYYY-MM-DD",
                    )
                    if isinstance(selected_range, (tuple, list)) and len(selected_range) == 2:
                        record["start_date"] = selected_range[0].isoformat()
                        record["end_date"] = selected_range[1].isoformat()
                    record["single_day"] = ""


                record["single_year"] = ""
                record["start_year"] = ""
                record["end_year"] = ""

            st.caption(f"Selection saved: {format_timeframe_summary(record)}")

# -----------------------------------------------------------------------------
# UI layout
# -----------------------------------------------------------------------------
air_quality_col, weather_col = st.columns(2, gap="large")

with air_quality_col:
    st.subheader("Air quality datasets")
    for name, desc in pollutant_options.items():
        render_variable_card(name, desc, "pollutant_selection", name in st.session_state["pollutant_selection"])

with weather_col:
    st.subheader("Weather datasets")
    for name, desc in weather_options.items():
        render_variable_card(name, desc, "weather_selection", name in st.session_state["weather_selection"])

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
st.markdown("---")

st.subheader("Your selections")
st.markdown('<div class="variable-section-note">These choices are stored for the next step of the workflow.</div>', unsafe_allow_html=True)

summary_col_a, summary_col_b = st.columns(2)

with summary_col_a:
    with st.container(border=True):
        st.markdown("**Air quality**")
        if st.session_state["pollutant_selection"]:
            for name, record in st.session_state["pollutant_selection"].items():
                st.write(f"{name}  \n_{format_timeframe_summary(record)}_")
        else:
            st.caption("No pollutants selected yet")

with summary_col_b:
    with st.container(border=True):
        st.markdown("**Weather**")
        if st.session_state["weather_selection"]:
            for name, record in st.session_state["weather_selection"].items():
                st.write(f"{name}  \n_{format_timeframe_summary(record)}_")
        else:
            st.caption("No weather variables selected yet")


raster_list = variable_selection_to_raster_list(st.session_state["weather_selection"]) + variable_selection_to_raster_list(st.session_state["pollutant_selection"])
if len(raster_list) > 10:
    st.warning(f"""You have selected more than 10 variables or times.
               This may take a long time to process in the next step.
               Reduce the number of variables or narrow
               the timeframes before continuing.""")
else:
    st.session_state["raster_list"] = raster_list
