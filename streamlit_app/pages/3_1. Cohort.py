import os

import streamlit as st
from streamlit.components.v1 import html
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from pathlib import Path
from utils.iriscc_utils import apply_app_style

BASE_DIR = Path(__file__).resolve().parent.parent

st.set_page_config(page_title="1. Cohort", layout="wide")
apply_app_style()

st.title("Step 1 — Cohort data")

st.markdown(
    '''
    Analysis begins with a cohort of individuals, who may be recurited for a particular study, found in an existing cohort, or selected from a dataset of population health data. Each subject in the cohort is defined with a unique Subject ID and some spatial information. Often this is their residential address, but it could also be a workplace, school, or a bigger unit such as a postal code. The spatial information is used to link the subject to environmental exposures and other data.

    In the demonstrator, we use a synthetic dataset of 20 subjects called *cardiovascularCohort*. 
    Each subject has a fictional cardiovascular score that represents their normalized risk level for developing Cardiovascular diseases (CVDs) based on health and genetic factors measured in 2023. In practice, this could be any health data you're interested in, such as medical records or measurements.
    To explore the role of the exposome in CVDs, we will link the cohort to environmental exposures.

    The subjects live in five European cities: Amsterdam, Athens, Barcelona, Paris, and Zurich. We've already used a geocoding service to convert their street addresses into geographic coordinates (latitude and longitude). All of the data has been entered into a CSV file.
    
    Start by pressing the button to load in the sample cohort data as a table.
    '''
)


if st.button("Load sample cohort data"):
    path = BASE_DIR / "Resources" / "cardiovascularCohort.gpkg"
    location_gdf = gpd.read_file(path)

    # Reorder columns
    cols = location_gdf.columns.tolist()
    if 'SubjectID' in cols:
        cols.insert(0, cols.pop(cols.index('SubjectID')))
        location_gdf = location_gdf[cols]

    st.session_state["location_gdf"] = location_gdf
    st.dataframe(location_gdf, hide_index=True)

'''
Now press the button to visualize the address locations on a map.
'''

if st.button("Visualize sample cohort data"):
    if "location_gdf" in st.session_state:
        # Display the GeoDataFrame as a map
        st.session_state["show_map"] = True
    
    else:
        st.warning("Load the sample cohort data first.")

# -----------------------------------------------------------------------------
# Session state initialization
# -----------------------------------------------------------------------------
if "show_map" not in st.session_state:
    st.session_state["show_map"] = False

if "show_all_locations" not in st.session_state:
    st.session_state["show_all_locations"] = True

if "map_center" not in st.session_state:
    st.session_state["map_center"] = [52.3676, 4.9041]  # Amsterdam

if "map_zoom" not in st.session_state:
    st.session_state["map_zoom"] = 11

# -----------------------------------------------------------------------------
# Map section
# -----------------------------------------------------------------------------
if st.session_state["show_map"]:

    location_gdf = st.session_state["location_gdf"]

    # Ensure coordinates are in lat/lon
    if location_gdf.crs != "EPSG:4326":
        location_gdf = location_gdf.to_crs(4326)

    col_map, col_controls = st.columns([4, 1])

    # -------------------------------------------------------------------------
    # Controls
    # -------------------------------------------------------------------------
    with col_controls:

        st.subheader("Zoom to")

        if st.button("All subjects"):
            st.session_state["show_all_locations"] = True
            st.rerun()

        city_locations = {
            "Amsterdam": ([52.3676, 4.9041], 11),
            "Paris": ([48.8566, 2.3522], 11),
            "Barcelona": ([41.3851, 2.1734], 11),
            "Zurich": ([47.3769, 8.5417], 11),
            "Athens": ([37.9838, 23.7275], 11),
        }

        for city, (coords, zoom) in city_locations.items():
            if st.button(city):
                st.session_state["show_all_locations"] = False
                st.session_state["map_center"] = coords
                st.session_state["map_zoom"] = zoom
                st.rerun()

    # -------------------------------------------------------------------------
    # Map
    # -------------------------------------------------------------------------
    with col_map:

        if st.session_state["show_all_locations"]:

            m = folium.Map(
                tiles="CartoDB positron"
            )

            bounds = [
                [
                    location_gdf.geometry.y.min(),
                    location_gdf.geometry.x.min()
                ],
                [
                    location_gdf.geometry.y.max(),
                    location_gdf.geometry.x.max()
                ]
            ]

            m.fit_bounds(bounds, padding=(30, 30))

        else:

            m = folium.Map(
                location=st.session_state["map_center"],
                zoom_start=st.session_state["map_zoom"],
                tiles="CartoDB positron"
            )

        # ---------------------------------------------------------------------
        # Add points
        # ---------------------------------------------------------------------
        for _, row in location_gdf.iterrows():

            if row.geometry is None:
                continue

            folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=4,
                fill=True,
                fill_opacity=0.8,
                popup=str(row.get("Cardiovascular_Score", ""))
            ).add_to(m)

        st_folium(
            m,
            width="100%",
            height=700,
            returned_objects=[]
        )
# uploaded = st.file_uploader("Upload a GeoPackage (.gpkg) or select Resources/netherlands_addresses.gpkg", type=["gpkg"])

# use_sample = st.checkbox("Use Resources/netherlands_addresses.gpkg if available", value=True)

# path = None
# if uploaded is not None:
#     path = uploaded
# elif use_sample:
#     path = "Resources/netherlands_addresses.gpkg"

# if path:
#     gdf, err = safe_read_geopackage(path)
#     if err:
#         st.warning(f"Could not read geopackage: {err}")
#     elif gdf is None or gdf.empty:
#         st.info("No data found in provided file.")
#     else:
#         st.success(f"Loaded {len(gdf)} subjects")
#         st.dataframe(gdf.head(20))
#         html_table = dataframe_to_html(gdf)
#         html(html_table, height=300)
