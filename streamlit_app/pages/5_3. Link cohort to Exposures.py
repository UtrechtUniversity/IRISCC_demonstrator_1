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
            Therefore, two points that are within this pixel will be assigned the same value, even though in reality they're far away.
            """)


run = st.button("Run linking procedure")


code_expander = st.expander("Want to see the code used in the linking process?")


if run:
    input_file = "streamlit_app/Resources/cardiovascularCohort.gpkg"
    raster_folder = "streamlit_app/Resources/exposure_datasets"
    rasters_list = st.session_state.get("exposure_selection") + st.session_state.get("weather_selection")
    raster_crs = 3857
    linked_df = extract_values(input_file, raster_folder, rasters_list, raster_crs)
    st.dataframe(linked_df, hide_index=True)

    # exposure_to_filename = {
    #     "Annual PM10": "TEMP_AVG_20201201.tif"
    # }

    # What do I want ot happen? I want to go back to being the awesome productive and hardworking developer that I once was. Use those practices. Be less tired and lazy.
    # Okay, what do I need to do now? I need to create the linking process first, and make sure it works.
    # Then I need to select the variables.
    # Then I need to download them for each country, and do the merging. 
    # First, making sure that the linking process works well is the most critical and brain thing.




# if run:

#     locations_gdf = st.session_state.get("location_gdf", {})

#     client = Client("https://beacon-iriscc.maris.nl")

#     # ----------------------------
#     # CONFIG
#     # ----------------------------

#     exposure_tuple = namedtuple("Exposure", ["parameter", "value_column", "resolution"])

#     exposures_dict = {
#         "NO2": exposure_tuple("no2", "no2", 25),
#         "PM10": exposure_tuple("pm10", "pm10", 25),
#         "PM2.5": exposure_tuple("pm25", "pm25", 25),
#         "O3": exposure_tuple("o3", "o3", 25),
#         "Black Carbon": exposure_tuple("annual_mean_black_carbon", "bc", 1000),
#         "Annual mean temperature": exposure_tuple("annual_mean_temperature", "temperature", 1000),
#         "Monthly mean temperature": exposure_tuple("monthly_mean_temperature", "temperature", 1000),
#         "Daily average temperature": exposure_tuple("daily_mean_temperature", "temperature", 1000),
#         "Daily minimum temperature": exposure_tuple("daily_min_temperature", "temperature", 1000),
#         "Daily maximum temperature": exposure_tuple("daily_max_temperature", "temperature", 1000)
#     }

#     # ----------------------------
#     # BEACON FETCH
#     # ----------------------------
#     def fetch_exposure(parameter, value_column, bounds):
#         minx, miny, maxx, maxy = bounds

#         tables = client.list_tables()

#         return (
#             tables[parameter]
#             .query()
#             .add_select_column("x")
#             .add_select_column("y")
#             .add_select_column(value_column)
#             .add_range_filter("x", minx, maxx)
#             .add_range_filter("y", miny, maxy)
#             .to_geo_pandas_dataframe("x", "y", crs="EPSG:3035")
#         )

#     # ----------------------------
#     # NEAREST JOIN
#     # ----------------------------
#     def link_nearest(location_gdf, exposure_gdf, value_col, max_dist):

#         exposure_lookup = exposure_gdf[["geometry", value_col]].copy()

#         joined = gpd.sjoin_nearest(
#             location_gdf,
#             exposure_lookup,
#             how="left",
#             distance_col="distance",
#             max_distance=max_dist
#         )

#         return joined[value_col]

#     # ----------------------------
#     # PIPELINE
#     # ----------------------------

#     linked_location_gdf = locations_gdf.copy()

#     # stable ID (optional)
#     linked_location_gdf["linking_id"] = range(len(linked_location_gdf))

#     selected_exposures = st.session_state["exposure_selection"]
#     st.write("Selected:", selected_exposures)

#     # compute once
#     st.write(f"locations_gdf: {locations_gdf}")
#     bounds = locations_gdf.total_bounds
#     st.write(f"bounds: {bounds}")

#     for name in selected_exposures:

#         cfg = exposures_dict.get(name)

#         if cfg is None:
#             continue

#         st.write(f"Processing {name} ...")

#         try:
#             exposure_gdf = fetch_exposure(
#                 cfg.parameter,
#                 cfg.value_column,
#                 bounds
#             )

#             st.write(f"Fetched {name}: {len(exposure_gdf)} rows")

#             values = link_nearest(
#                 linked_location_gdf,
#                 exposure_gdf,
#                 cfg.value_column,
#                 cfg.resolution
#             )

#             linked_location_gdf[name] = values

#             st.write(f"{name} done")

#         except Exception as e:
#             st.write(f"{name} failed: {str(e)}")

#     linked_location_gdf
