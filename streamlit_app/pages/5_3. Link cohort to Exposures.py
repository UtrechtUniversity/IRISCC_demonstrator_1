from collections import namedtuple
import streamlit as st
from beacon_api import *
import geopandas as gpd
from utils.iriscc_utils import apply_app_style
from scripts.raster_extraction import extract_values

st.set_page_config(page_title="3. Link Locations to Exposure Data", layout="wide")
apply_app_style()

st.title("Step 3 — Link cohort to exposures")

st.markdown("""
            Now we can programmatically link the addresses in the cohort dataset to the exposure datasets.

            As seen in the previous pages, locations are represented as points, and exposure datasets are represented as surfaces. In terms of data models, these are examples of a vector and a raster dataset, respectively.
            When a point is placed on a surface, we can extract the value at that point. 
            
            The process can be complex due to differences in spatial and temporal resolution between datasets. If a raster dataset has a spatial resolution of 100 meters, it means that each pixel represents 100 meters on the ground.
            Therefore, two points that are within this pixel will be assigned the same value, even though in reality they're up to 100 meters apart.

            Press the button to run the linking procedure. The result is a table, similar to the table we saw when introducting the cohort, but with a set of new columns: one column for the value of each exposure we selected earlier.
            """)


run = st.button("Run linking procedure")

if run:
    input_file = "streamlit_app/Resources/cardiovascularCohort.gpkg"
    raster_folder = "streamlit_app/Resources/exposure_datasets"
    rasters_list = st.session_state.get("exposure_selection") + st.session_state.get("weather_selection")
    raster_crs = 3857
    linked_df = extract_values(input_file, raster_folder, rasters_list, raster_crs)
    st.session_state["linked_df"] = linked_df
    st.dataframe(linked_df, hide_index=True)



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
