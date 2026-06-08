import streamlit as st
from ..utils.iriscc_utils import safe_read_geopackage

st.title("Step 3 — Link Locations to Exposure Data")

st.write("This page will run a simplified linking process if Resources files are present.")

run = st.button("Run linking (simplified)")

if run:
    st.info("Attempting to load Resources/netherlands_addresses.gpkg and example exposure files.")
    gdf, err = safe_read_geopackage("Resources/netherlands_addresses.gpkg")
    if err:
        st.warning(f"Could not load locations: {err}")
    else:
        st.success(f"Loaded {len(gdf)} locations — linking not implemented fully in this starter.")
        st.write("This starter app outlines where to run the gpd spatial join from the notebook.\n")
        st.write("See the notebook code for the exact pipeline; implement the same sjoin_nearest logic in production.")
