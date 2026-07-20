import streamlit as st
import geopandas as gpd
import pandas as pd
import tempfile
import zipfile
from pathlib import Path
import folium
from streamlit_folium import st_folium
from utils.iriscc_utils import apply_app_style

BASE_DIR = Path(__file__).resolve().parent.parent

st.set_page_config(page_title="6. Try with Your Own Data", layout="wide")
apply_app_style()

st.title("Try your own cohort")

st.markdown("""
Now it's your turn! You can upload your own spatial dataset containing participant locations. Then we'll repeat the exposure linking process using your data.
Upload a spatial dataset containing participant locations.

Supported formats:

- GeoPackage (.gpkg)
- GeoJSON (.geojson, .json)
- Parquet (.parquet)
- Feather (.feather)
- Zipped Shapefile (.zip)            

If you don't have your own data, you can also select from two pre-made large cohorts. 
""")

st.warning("This is an unsecure demonstrator. When uploading read addresses, never upload real health data. Only use synthetic data or anonymized datasets, and make sure to comply with your local data protection regulations. Relate environemental exposures to health data only in a secure environment.")

# -----------------------------------------------------------------------------
# Session state
# -----------------------------------------------------------------------------
if "location_gdf" not in st.session_state:
    st.session_state["location_gdf"] = None

if "cohort_mode" not in st.session_state:
    st.session_state["cohort_mode"] = None


# -----------------------------------------------------------------------------
# Load helpers
# -----------------------------------------------------------------------------
def load_spatial_file(uploaded_file):
    suffix = Path(uploaded_file.name).suffix.lower()

    with tempfile.TemporaryDirectory() as tmpdir:

        temp_path = Path(tmpdir) / uploaded_file.name
        temp_path.write_bytes(uploaded_file.getbuffer())

        if suffix == ".zip":
            extract_dir = Path(tmpdir) / "unzipped"

            with zipfile.ZipFile(temp_path, "r") as z:
                z.extractall(extract_dir)

            shp = list(extract_dir.rglob("*.shp"))
            if not shp:
                raise ValueError("No .shp found in ZIP")

            return gpd.read_file(shp[0])

        return gpd.read_file(temp_path)


def validate_gdf(gdf):

    if gdf.empty:
        st.error("Dataset is empty.")
        st.stop()

    if "geometry" not in gdf.columns:
        st.error("No geometry column found.")
        st.stop()

    if gdf.geometry.isna().all():
        st.error("All geometries are null.")
        st.stop()

    geom_types = set(gdf.geometry.geom_type.unique())
    allowed = {"Point", "MultiPoint"}

    if geom_types - allowed:
        st.error(f"Only Point/MultiPoint allowed. Found: {geom_types}")
        st.stop()

    if gdf.crs is None:
        st.error("Missing CRS.")
        st.stop()

    gdf = gdf.to_crs(4326)

    # explode multipoints so limit applies to real individuals
    if "MultiPoint" in geom_types:
        gdf = gdf.explode(index_parts=False).reset_index(drop=True)

    MAX = 1000
    if len(gdf) > MAX:
        st.error(f"Max {MAX} participants allowed. You uploaded {len(gdf)}.")
        st.stop()

    return gdf


# -----------------------------------------------------------------------------
# Cohort selection mode
# -----------------------------------------------------------------------------
mode = st.radio(
    "Select cohort source",
    ["Upload my own data", "Belgium cohort", "Berlin cohort"],
    horizontal=True
)

st.session_state["cohort_mode"] = mode


# -----------------------------------------------------------------------------
# PRE-MADE COHORTS (replace with your real datasets)
# -----------------------------------------------------------------------------
@st.cache_data
def load_prebuilt_belgium():
    # placeholder example
    return gpd.read_file(BASE_DIR / "Resources" / "belgium_subjects.gpkg")

@st.cache_data
def load_prebuilt_berlin():
    return gpd.read_file(BASE_DIR / "Resources" / "berlin_subjects.gpkg")


gdf = None


# -----------------------------------------------------------------------------
# Upload option
# -----------------------------------------------------------------------------
if mode == "Upload my own data":

    uploaded_file = st.file_uploader(
        "Upload cohort file",
        type=["gpkg", "geojson", "json", "parquet", "feather", "zip"]
    )

    if uploaded_file:
        try:
            gdf = load_spatial_file(uploaded_file)
            gdf = validate_gdf(gdf)

        except Exception as e:
            st.error(str(e))


# -----------------------------------------------------------------------------
# Pre-made cohorts
# -----------------------------------------------------------------------------
elif mode == "Belgium cohort":
    gdf = validate_gdf(load_prebuilt_belgium())

elif mode == "Berlin cohort":
    gdf = validate_gdf(load_prebuilt_berlin())


# -----------------------------------------------------------------------------
# Store result
# -----------------------------------------------------------------------------
if gdf is not None:

    st.session_state["location_gdf"] = gdf

    st.success(f"Cohort loaded: {len(gdf)} participants")

    # -----------------------------------------------------------------------------
    # Preview map
    # -----------------------------------------------------------------------------
    st.subheader("Preview")

    m = folium.Map(tiles="CartoDB positron")

    bounds = [
        [gdf.geometry.y.min(), gdf.geometry.x.min()],
        [gdf.geometry.y.max(), gdf.geometry.x.max()]
    ]

    m.fit_bounds(bounds, padding=(30, 30))

    for geom in gdf.geometry:

        if geom.geom_type == "Point":
            folium.CircleMarker(
                location=[geom.y, geom.x],
                radius=3,
                fill=True,
                fill_opacity=0.7,
            ).add_to(m)

    st_folium(m, height=500, use_container_width=True)


# -----------------------------------------------------------------------------
# Placeholder for next step
# -----------------------------------------------------------------------------
if gdf is not None:

    st.markdown("---")
    if st.button("Continue to analysis"):
        st.info("Next analysis step will be added here.")