import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

st.title("Step 2 — Air quality and weather data")

st.markdown("""
            Fine-resolution data has been modeled for many major exposome factors,
            including air pollution and weather [1].

            Open data platforms facilitate access to these datasets for research into the health impacts of environmental exposures.
            One place to find modeled air pollution data for all of Europe is the Exposome Maps
            Platform (https://exposome.uu.nl/). 
            
            For this demonstrator, we will consider the following datasets from the Exposome Maps Platform.
            Select the ones you want to work with in the next steps. You can select as many as you like.
            
            Notice that the datasets have different spatial and temporal resolutions. This will affect how you can link them to your cohort data and the types of analyses you can perform.
            """)


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
    "PM10": "Annual avg (2020) — 25m resolution",
    "PM2.5": "Annual avg (2020) — 25m resolution",
    "O3": "Annual avg (2020) — 25m resolution",
    "NO2": "Annual avg (2020) — 25m resolution",
    "Black Carbon": "Annual avg (2010) — 100m resolution",
}

weather_options = {
    "Annual mean temperature": "2020 — 1km resolution",
    "Monthly mean temperature (Dec 2020)": "1km resolution",
    "Daily mean temperature (31 Dec 2020)": "1km resolution",
    "Daily minimum temperature (31 Dec 2020)": "1km resolution",
    "Daily maximum temperature (31 Dec 2020)": "1km resolution",
}

# -----------------------------------------------------------------------------
# Helper function for toggle behavior
# -----------------------------------------------------------------------------
def toggle_selection(name, state_key):
    if name in st.session_state[state_key]:
        st.session_state[state_key].remove(name)
    else:
        st.session_state[state_key].append(name)

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

        with st.container():

            col_text, col_btn = st.columns([5, 1])

            with col_text:
                st.markdown(
                    f"""
                    <div style="
                        border: 1px solid {'#4CAF50' if selected else '#ddd'};
                        border-radius: 10px;
                        padding: 10px;
                        background-color: {'#f0fff4' if selected else 'white'};
                    ">
                        <strong>{name}</strong><br>
                        <span style="color: gray; font-size: 0.85em;">
                            {desc}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_btn:
                if st.button(
                    "✓" if selected else "+",
                    key=f"exp_{name}",
                    use_container_width=True,
                ):
                    toggle_selection(name, "exposure_selection")
                    st.rerun()

# =============================================================================
# Weather cards
# =============================================================================
with col2:
    st.subheader("Weather")

    for name, desc in weather_options.items():

        selected = name in st.session_state["weather_selection"]

        with st.container():

            col_text, col_btn = st.columns([5, 1])

            with col_text:
                st.markdown(
                    f"""
                    <div style="
                        border: 1px solid {'#2196F3' if selected else '#ddd'};
                        border-radius: 10px;
                        padding: 10px;
                        background-color: {'#f0f8ff' if selected else 'white'};
                    ">
                        <strong>{name}</strong><br>
                        <span style="color: gray; font-size: 0.85em;">
                            {desc}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_btn:
                if st.button(
                    "✓" if selected else "+",
                    key=f"wea_{name}",
                    use_container_width=True,
                ):
                    toggle_selection(name, "weather_selection")
                    st.rerun()

# -----------------------------------------------------------------------------
# Summary section
# -----------------------------------------------------------------------------
st.markdown("---")

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Selected exposures")
    if st.session_state["exposure_selection"]:
        for d in st.session_state["exposure_selection"]:
            st.write("•", d)
    else:
        st.info("None selected")

with col_b:
    st.subheader("Selected weather datasets")
    if st.session_state["weather_selection"]:
        for d in st.session_state["weather_selection"]:
            st.write("•", d)
    else:
        st.info("None selected")