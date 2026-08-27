import streamlit as st
import geopandas as gpd
import pandas as pd
from utils.iriscc_utils import apply_app_style, visualize_gdf_as_df
from scripts.raster_extraction import create_linked_dataframe

st.set_page_config(page_title="3. Link Locations to Exposure Data", layout="wide")
apply_app_style()

st.markdown(
    """
    <div class="iriscc-page-header">
        <h2 class="iriscc-page-title">Step 3 — Link cohort to exposures</h2>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='iriscc-section-title'><strong>Linking process</strong></div>", unsafe_allow_html=True)

st.markdown("""
            <div class="iriscc-instruction">
            Now you can programmatically link the addresses in the cohort dataset to the exposure datasets.
			<br><br>
            Locations are represented as points, and exposure datasets are represented as surfaces. In terms of data models, these are examples of a vector and a raster dataset, respectively.
            When a point is placed on a surface, you can sample the value at that point. This is how you link the cohort to the exposure datasets.
			<br><br>
            It's important to consider differences in spatial resolution between datasets. If a raster dataset has a spatial resolution of 100 meters, it means that each pixel represents 100 meters on the ground.
            Therefore, two points that are within this pixel will be assigned the same value, even though in reality they're up to 100 meters apart.
            <br><br>
            Press the button to run the linking procedure.
            <br><br>
            </div>
            """, unsafe_allow_html=True)


location_gdf = st.session_state.get("location_gdf")
raster_list = st.session_state.get("raster_list")

cohort_ready = (
    isinstance(location_gdf, gpd.GeoDataFrame)
    and not location_gdf.empty
    and "geometry" in location_gdf.columns
    and location_gdf.geometry.notna().any()
    and set(location_gdf.geometry.dropna().geom_type.unique()) <= {"Point"}
)
exposures_ready = (
    isinstance(raster_list, list)
    and 0 < len(raster_list) <= 10
    and all(
        isinstance(selection, dict)
        and all(str(selection.get(key, "")).strip() for key in ("variable", "geoserver_name", "time"))
        for selection in raster_list
    )
)

if not cohort_ready:
    st.warning("Load a valid cohort dataset on the Cohort page before starting the linking procedure.")

if not exposures_ready:
    st.warning("Select at least one pollutant or temperature exposure, with no more than 10 raster times, on the Exposures page before starting the linking procedure.")

run = st.button(
    "Run linking procedure",
    disabled=not (cohort_ready and exposures_ready),
)

def get_data():
    return st.session_state.get("linked_df")

@st.cache_data
def convert_for_download(_df):
    if _df is None:
        return b""
    # If geodataframe, drop geometry column and convert to pandas dataframe
    if isinstance(_df, gpd.GeoDataFrame):
        _df = _df.drop(columns="geometry").copy()
    return _df.to_csv(index=False).encode("utf-8")


if run:
    try:
        linked_df, linking_failures = create_linked_dataframe(
            selected_variable_dict=raster_list,
            points_dataframe=location_gdf,
            return_failures=True,
        )
        st.session_state["linked_df"] = linked_df
        if linking_failures:
            failed_variables = ", ".join(failure["variable"] for failure in linking_failures)
            st.warning(
                f"Could not link these exposure layers: {failed_variables}. "
                "Their columns were added with null values."
            )
        st.success("""The linking procedure ran successfully!
        Notice the resulting table. Each row represents a subject in the cohort,
        and each column contains the value of an exposure variable.""")
        st.dataframe(visualize_gdf_as_df(st.session_state["linked_df"]), hide_index=True)

    except Exception as e:
        st.error(f"Error occurred while linking cohort to exposures: {e}")

    linked_df_for_download = get_data()
    csv = convert_for_download(linked_df_for_download)



    print(f"Type: {type(csv)}, Length: {len(csv)}")

    file_name = st.session_state.get("uploaded_file_name")
    file_name = file_name.split(".")[0]
    file_name = f"{file_name}_linked.csv"

    print("file name", file_name)

    st.download_button(
        label="Download linked data as CSV",
        data=csv,
        file_name=file_name,
        mime="text/csv",
        key="download_button",
        on_click="ignore",
        icon=":material/download:",
        type= "secondary",
        disabled=linked_df_for_download is None or linked_df_for_download.empty,
    )

   
    # st.session_state["linked_df"] = linked_df
    # st.dataframe(linked_df, hide_index=True)
    #
    # st.session_state["linked_df"] = linked_df


    # exposure_to_filename = {
    #     "Annual PM10": "TEMP_AVG_20201201.tif"
    # }

    # What do I want ot happen? I want to go back to being the awesome productive and hardworking developer that I once was. Use those practices. Be less tired and lazy.
    # Okay, what do I need to do now? I need to create the linking process first, and make sure it works.
    # Then I need to select the variables.
    # Then I need to download them for each country, and do the merging. 


code_expander = st.expander("Want to see the code used in the linking process?")
with code_expander:
    """
        import os
        import geopandas as gpd
        import rasterio
        from pathlib import Path

        def prepare_input_data(input_file, raster_crs):
            gdf = gpd.read_file(input_file)

            gdf.to_crs(raster_crs, inplace=True)
            return gdf

        def sample_points(gdf, raster_name):
            raster_to_var_name = {
                "TEMP_AVG_20201201.tif": "avg_temp_20201201"
            }
            variable_name = raster_to_var_name.get(raster_name)

            raster_path = Path("streamlit_app", "Resources", "exposure_datasets", raster_name).resolve()
            
            src = rasterio.open(raster_path)

            coord_list = [(x, y) for x, y in zip(gdf["geometry"].x, gdf["geometry"].y)]
            gdf[variable_name] = [x[0].round(2) for x in src.sample(coord_list)]

            return gdf[["SubjectID", variable_name]]


        def extract_values(input_file, raster_folder, exposure_selection, raster_crs):
            # Selected environmental rasters to extract values from
            displayName_to_raster = {
                "Daily mean temperature (31 Dec 2020)": "TEMP_AVG_20201201.tif"
            }
            raster_list = [displayName_to_raster.get(e) for e in exposure_selection]
            raster_files = [f for f in os.listdir(raster_folder) if f.endswith(".tif") and f in raster_list]

            # Read cohort data
            gdf = prepare_input_data(input_file, raster_crs)

            # Create geodataframe of extracted points
            for raster in raster_files:
                extracted_values = sample_points(gdf, raster)
                gdf.merge(extracted_values, on="SubjectID")
            
            return gdf
    """
