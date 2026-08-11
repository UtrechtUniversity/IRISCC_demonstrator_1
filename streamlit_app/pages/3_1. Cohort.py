import os
import tempfile
import zipfile
import streamlit as st
from streamlit.components.v1 import html
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from pathlib import Path
import pandas as pd
from shapely import wkt
from shapely.geometry import Point
from utils.iriscc_utils import apply_app_style

BASE_DIR = Path(__file__).resolve().parent.parent

st.set_page_config(page_title="1. Cohort", layout="wide")
apply_app_style()



st.markdown(
    """
    <style>
    .iriscc-hero {
        border-radius: 28px;
        padding: 2rem 2rem 1.6rem 2rem;
        background:
            linear-gradient(135deg, rgba(255, 255, 255, 0.94), rgba(233, 239, 246, 0.90)),
            radial-gradient(circle at top right, rgba(15, 118, 110, 0.12), transparent 30%),
            radial-gradient(circle at bottom left, rgba(18, 59, 93, 0.10), transparent 28%);
        border: 1px solid rgba(16, 24, 40, 0.10);
        box-shadow: 0 24px 48px rgba(15, 23, 42, 0.10);
        margin-bottom: 1.25rem;
    }

    .iriscc-hero h1 {
        margin: 0;
        font-size: clamp(2.8rem, 5vw, 4.8rem);
        line-height: 1.05;
        letter-spacing: -0.04em;
    }

    .iriscc-subtitle {
        margin-top: 0.9rem;
        font-size: 1.35rem;
        line-height: 1.8;
        color: #425466;
    }

    .iriscc-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 1rem;
        margin: 1.3rem 0 0.4rem 0;
    }

    .iriscc-card {
        border-radius: 20px;
        padding: 1.1rem 1.1rem 1.8rem 1.8rem;
        background: rgba(255, 255, 255, 0.90);
        border: 1px solid rgba(16, 24, 40, 0.08);
        box-shadow: 0 14px 30px rgba(15, 23, 42, 0.06);
        height: 100%;
    }

    .iriscc-card h3 {
        margin: 0 0 0.45rem 0;
        font-size: 1.38rem;
    }

    .iriscc-card p {
        margin: 0;
        color: #516173;
        line-height: 1.72;
        font-size: 1.22rem;
    }

    .iriscc-section-title {
        margin-top: 1.4rem;
        margin-bottom: 0.5rem;
        font-size: 1.45rem;
        letter-spacing: -0.02em;
    }

    .iriscc-body {
        color: #344054;
        line-height: 1.82;
        font-size: 1.26rem;
    }

    .stMarkdown p,
    .stMarkdown li {
        font-size: 1.22rem;
        line-height: 1.8;
    }

    .stCaption {
        font-size: 1.08rem;
    }

    h2, h3, h4, h5, h6 {
        line-height: 1.2;
    }

    h2 {
        font-size: 1.9rem;
    }

    h3 {
        font-size: 1.45rem;
    }

    h4 {
        font-size: 1.25rem;
    }

    @media (max-width: 900px) {
        .iriscc-grid {
            grid-template-columns: 1fr;
        }

        .iriscc-hero {
            padding: 1.4rem 1.1rem 1.2rem 1.1rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header logos and hero banner to match the Introduction styling
col1, col2 = st.columns([3, 1])
with col1:
    iriscc_logo_path = BASE_DIR / "Resources" / "iriscc_logo.png"
    st.image(iriscc_logo_path)

with col2:
    iras_logo_path = BASE_DIR / "Resources" / "iras_logo.png"
    st.image(iras_logo_path)

st.markdown(
    """
    <div class="iriscc-hero">
        <h2>Step 1 — Prepare cohort data</h2>
    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    '''
    Analysis begins with a cohort of individuals.
    
    They may be recruited for a particular study or selected from a dataset of population health data.
    Often, studies are designed to follow a cohort over time, to understand how their health changes in response to environmental exposures.
    Subjects report their health status through surveys, or their health is measured through medical tests and wearable biosensors. 
    
    Each subject in the cohort is defined with a unique Subject ID and some spatial information.
    Often this is their residential address, but it could also be a workplace, a bigger unit such as a postal code, or even a path that they travel through often.
    The spatial information is used to link the subject to exposures.

    In the demonstrator, we demonstrate the linking process using a synthetic dataset of 100 subjects called *cardiovascularCohort*.
    You can use this dataset or upload your own cohort data in GeoPackage format.

    Note that studies usually involve large cohorts. You can visit <a href="https://molgeniscatalogue.org/EHEN/collections">this catalogue</a> to explore some cohorts that can be used for epidemiological and exposome research)
    '''
    ,
    unsafe_allow_html=True
)

# Initialize session state for dataset and source selection
if "location_gdf" not in st.session_state:
    st.session_state["location_gdf"] = None

if "data_source" not in st.session_state:
    st.session_state["data_source"] = "sample"


def load_spatial_file(uploaded_file):
    suffix = Path(uploaded_file.name).suffix.lower()

    with tempfile.TemporaryDirectory() as tmpdir:

        temp_path = Path(tmpdir) / uploaded_file.name
        temp_path.write_bytes(uploaded_file.getbuffer())

        # ZIP containing shapefile
        if suffix == ".zip":
            extract_dir = Path(tmpdir) / "unzipped"

            with zipfile.ZipFile(temp_path, "r") as z:
                z.extractall(extract_dir)

            shp = list(extract_dir.rglob("*.shp"))
            if not shp:
                raise ValueError("No .shp found in ZIP")

            return gpd.read_file(shp[0])

        # Parquet / Feather: read with pandas and construct geometry if possible
        if suffix in (".parquet", ".feather"):
            if suffix == ".parquet":
                df = pd.read_parquet(temp_path)
            else:
                df = pd.read_feather(temp_path)

            # If geometry column WKT
            if "geometry" in df.columns:
                try:
                    geom = df["geometry"].apply(lambda x: wkt.loads(x) if isinstance(x, str) else x)
                    gdf = gpd.GeoDataFrame(df, geometry=geom, crs=4326)
                    return gdf
                except Exception:
                    pass

            # Fallback: lat/lon columns
            lat_cols = [c for c in df.columns if c.lower() in ("lat", "latitude")]
            lon_cols = [c for c in df.columns if c.lower() in ("lon", "lng", "longitude")]
            if lat_cols and lon_cols:
                lat = lat_cols[0]
                lon = lon_cols[0]
                geom = [Point(xy) for xy in zip(df[lon], df[lat])]
                gdf = gpd.GeoDataFrame(df, geometry=geom, crs=4326)
                return gdf

            raise ValueError("Parquet/Feather file did not contain recognizable geometry (WKT or lat/lon columns)")

        # Default: let geopandas try to read (gpkg, geojson, etc.)
        return gpd.read_file(temp_path)


def validate_gdf(gdf):

    if gdf is None:
        raise ValueError("No data loaded")

    if gdf.empty:
        raise ValueError("Dataset is empty.")

    # If there's a geometry column name but not proper geometry objects, try to convert WKT
    if "geometry" in gdf.columns and not isinstance(gdf.geometry.iloc[0], (Point,)):
        try:
            gdf["geometry"] = gdf["geometry"].apply(lambda x: wkt.loads(x) if isinstance(x, str) else x)
        except Exception:
            pass

    if "geometry" not in gdf.columns:
        raise ValueError("No geometry column found.")

    if gdf.geometry.isna().all():
        raise ValueError("All geometries are null.")

    # Normalize CRS
    try:
        if gdf.crs is None:
            # assume lat/lon if geometry bounds look like lat/lon
            gdf = gdf.set_crs(epsg=4326, allow_override=True)
        else:
            gdf = gdf.to_crs(epsg=4326)
    except Exception as e:
        raise ValueError(f"Failed to set/transform CRS: {e}")

    # explode multipoints so limit applies to real individuals
    geom_types = set(gdf.geometry.geom_type.unique())
    if "MultiPoint" in geom_types:
        try:
            gdf = gdf.explode(index_parts=False).reset_index(drop=True)
        except Exception:
            pass

    # Only allow point-like geometries
    geom_types = set(gdf.geometry.geom_type.unique())
    allowed = {"Point"}
    if geom_types - allowed:
        raise ValueError(f"Only Point geometries allowed. Found: {geom_types}")

    MAX = 5000
    if len(gdf) > MAX:
        raise ValueError(f"Max {MAX} participants allowed. You uploaded {len(gdf)}.")

    # Ensure SubjectID exists; if not, create one
    if "SubjectID" not in gdf.columns:
        gdf = gdf.reset_index(drop=True)
        gdf["SubjectID"] = gdf.index.astype(str)

    # Standardize column order to put SubjectID first
    cols = gdf.columns.tolist()
    if "SubjectID" in cols:
        cols.insert(0, cols.pop(cols.index("SubjectID")))
        gdf = gdf[cols]

    return gdf


# UI: choose data source (sample or upload) — makes choice explicit
st.markdown("**Choose data source**")
source = st.radio("Select dataset", ("Sample dataset", "Upload your own"), index=0, horizontal=True)
st.session_state["data_source"] = "sample" if source == "Sample dataset" else "upload"

# If the user switched the chosen data source, clear any shown map to avoid mixing sources
prev_choice = st.session_state.get("choice_prev")
if prev_choice is None:
    st.session_state["choice_prev"] = st.session_state["data_source"]
elif prev_choice != st.session_state["data_source"]:
    st.session_state["show_map"] = False
    st.session_state["choice_prev"] = st.session_state["data_source"]

uploaded_file = None
if st.session_state["data_source"] == "upload":
    st.markdown("Upload a GeoPackage, GeoJSON, Parquet/Feather, or ZIP (shapefile)")
    uploaded_file = st.file_uploader(
        "Upload cohort file",
        type=["gpkg", "geojson", "json", "parquet", "feather", "zip"]
    )
else:
    st.markdown("Using the bundled `cardiovascularCohort.gpkg` sample dataset.")

st.info("After choosing the data source, use the buttons below: 'Load cohort' to load and preview, and 'Visualize cohort on map' to view locations.")

# -----------------------------------------------------------------------------
# Bottom action buttons: Load cohort and Visualize
# -----------------------------------------------------------------------------
col_load, col_vis = st.columns([1, 1])

with col_load:
    if st.button("Load cohort"):
        if st.session_state.get("data_source") == "sample":
            path = BASE_DIR / "Resources" / "cardiovascularCohort.gpkg"
            if not path.exists():
                st.error("Sample dataset not found in Resources.")
            else:
                gdf = gpd.read_file(path)
                gdf = validate_gdf(gdf)
                st.session_state["location_gdf"] = gdf
                st.session_state["loaded_source"] = "sample"
                st.success(f"Loaded sample cohort ({len(gdf)} records)")
                st.dataframe(gdf, hide_index=True)
                try:
                    csv = gdf.drop(columns=["geometry"], errors='ignore').to_csv(index=False)
                    st.download_button("Download CSV", data=csv, file_name="cardiovascularCohort.csv", mime="text/csv")
                except Exception:
                    pass

        else:
            if uploaded_file is None:
                st.warning("Please upload a file first (choose 'Upload your own').")
            else:
                try:
                    gdf = load_spatial_file(uploaded_file)
                    gdf = validate_gdf(gdf)
                    st.session_state["location_gdf"] = gdf
                    st.success(f"Loaded uploaded cohort ({len(gdf)} records)")
                    st.dataframe(gdf, hide_index=True)
                    try:
                        csv = gdf.drop(columns=["geometry"], errors='ignore').to_csv(index=False)
                        st.download_button("Download CSV", data=csv, file_name="uploaded_cohort.csv", mime="text/csv")
                    except Exception:
                        pass

                except Exception as e:
                    st.error(f"Failed to load uploaded file: {e}")

with col_vis:
    if st.button("Visualize cohort on map"):
        # Only allow visualizing when a dataset has been loaded for the currently selected source
        if st.session_state.get("location_gdf") is None:
            st.warning("Load cohort data first (use 'Load cohort').")
        elif st.session_state.get("loaded_source") != st.session_state.get("data_source"):
            st.warning("The currently selected data source has not been loaded. Please load it first.")
        else:
            st.session_state["show_map"] = True

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
        # Only show preset city zoom buttons for the bundled sample dataset
        if st.session_state.get("data_source") == "sample":
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