from collections import namedtuple
import streamlit as st
from beacon_api import *
import geopandas as gpd
st.set_page_config(page_title="3. Link Locations to Exposure Data", layout="wide")

st.title("Step 3 — Link Locations to Exposure Data")

st.markdown("""
            Now that we have our cohort data and exposure datasets, we can link them together. 
            
            This involves matching the residential locations of our subjects to the corresponding air quality and weather data at those locations. 
            
            The process can be complex due to differences in spatial and temporal resolution between datasets, but it is crucial for analyzing how environmental exposures affect health outcomes.
            """)

st.write("This page will run a simplified linking process if Resources files are present.")

run = st.button("Run linking (simplified)")


code_expander = st.expander("Want to see the code used in the linking process?")
with code_expander:
    code_snippet = """
    def fetch_exposure(parameter, value_column, bounds):
        minx, miny, maxx, maxy = bounds

        tables = client.list_tables()

        return (
            tables[parameter]
            .query()
            .add_select_column("x")
            .add_select_column("y")
            .add_select_column(value_column)
            .add_range_filter("x", minx, maxx)
            .add_range_filter("y", miny, maxy)
            .to_geo_pandas_dataframe("x", "y", crs="EPSG:3035")
        )

    # ----------------------------
    # NEAREST JOIN
    # ----------------------------
    def link_nearest(location_gdf, exposure_gdf, value_col, max_dist):

        exposure_lookup = exposure_gdf[["geometry", value_col]].copy()

        joined = gpd.sjoin_nearest(
            location_gdf,
            exposure_lookup,
            how="left",
            distance_col="distance",
            max_distance=max_dist
        )

        return joined[value_col]

    # ----------------------------
    # PIPELINE
    # ----------------------------

    linked_location_gdf = locations_gdf.copy()

    # stable ID (optional)
    linked_location_gdf["linking_id"] = range(len(linked_location_gdf))

    selected_exposures = st.session_state["exposure_selection"]
    st.write("Selected:", selected_exposures)

    # compute once
    st.write(f"locations_gdf: {locations_gdf}")
    bounds = locations_gdf.total_bounds
    st.write(f"bounds: {bounds}")

    for name in selected_exposures:

        cfg = exposures_dict.get(name)

        if cfg is None:
            continue

        st.write(f"Processing {name} ...")

        try:
            exposure_gdf = fetch_exposure(
                cfg.parameter,
                cfg.value_column,
                bounds
            )

            st.write(f"Fetched {name}: {len(exposure_gdf)} rows")

            values = link_nearest(
                linked_location_gdf,
                exposure_gdf,
                cfg.value_column,
                cfg.resolution
            )

            linked_location_gdf[name] = values

            st.write(f"{name} done")

        except Exception as e:
            st.write(f"{name} failed: {str(e)}")

    linked_location_gdf
    """
    
    st.code(code_snippet, language="python")

if run:

    locations_gdf = st.session_state.get("location_gdf", {})

    client = Client("https://beacon-iriscc.maris.nl")

    # ----------------------------
    # CONFIG
    # ----------------------------

    exposure_tuple = namedtuple("Exposure", ["parameter", "value_column", "resolution"])

    exposures_dict = {
        "NO2": exposure_tuple("no2", "no2", 25),
        "PM10": exposure_tuple("pm10", "pm10", 25),
        "PM2.5": exposure_tuple("pm25", "pm25", 25),
        "O3": exposure_tuple("o3", "o3", 25),
        "Black Carbon": exposure_tuple("annual_mean_black_carbon", "bc", 1000),
        "Annual mean temperature": exposure_tuple("annual_mean_temperature", "temperature", 1000),
        "Monthly mean temperature": exposure_tuple("monthly_mean_temperature", "temperature", 1000),
        "Daily average temperature": exposure_tuple("daily_mean_temperature", "temperature", 1000),
        "Daily minimum temperature": exposure_tuple("daily_min_temperature", "temperature", 1000),
        "Daily maximum temperature": exposure_tuple("daily_max_temperature", "temperature", 1000)
    }

    # ----------------------------
    # BEACON FETCH
    # ----------------------------
    def fetch_exposure(parameter, value_column, bounds):
        minx, miny, maxx, maxy = bounds

        tables = client.list_tables()

        return (
            tables[parameter]
            .query()
            .add_select_column("x")
            .add_select_column("y")
            .add_select_column(value_column)
            .add_range_filter("x", minx, maxx)
            .add_range_filter("y", miny, maxy)
            .to_geo_pandas_dataframe("x", "y", crs="EPSG:3035")
        )

    # ----------------------------
    # NEAREST JOIN
    # ----------------------------
    def link_nearest(location_gdf, exposure_gdf, value_col, max_dist):

        exposure_lookup = exposure_gdf[["geometry", value_col]].copy()

        joined = gpd.sjoin_nearest(
            location_gdf,
            exposure_lookup,
            how="left",
            distance_col="distance",
            max_distance=max_dist
        )

        return joined[value_col]

    # ----------------------------
    # PIPELINE
    # ----------------------------

    linked_location_gdf = locations_gdf.copy()

    # stable ID (optional)
    linked_location_gdf["linking_id"] = range(len(linked_location_gdf))

    selected_exposures = st.session_state["exposure_selection"]
    st.write("Selected:", selected_exposures)

    # compute once
    st.write(f"locations_gdf: {locations_gdf}")
    bounds = locations_gdf.total_bounds
    st.write(f"bounds: {bounds}")

    for name in selected_exposures:

        cfg = exposures_dict.get(name)

        if cfg is None:
            continue

        st.write(f"Processing {name} ...")

        try:
            exposure_gdf = fetch_exposure(
                cfg.parameter,
                cfg.value_column,
                bounds
            )

            st.write(f"Fetched {name}: {len(exposure_gdf)} rows")

            values = link_nearest(
                linked_location_gdf,
                exposure_gdf,
                cfg.value_column,
                cfg.resolution
            )

            linked_location_gdf[name] = values

            st.write(f"{name} done")

        except Exception as e:
            st.write(f"{name} failed: {str(e)}")

    linked_location_gdf
