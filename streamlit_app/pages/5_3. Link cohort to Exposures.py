import geopandas as gpd
import pandas as pd
import streamlit as st

from scripts.raster_extraction import create_linked_dataframe
from utils.iriscc_utils import apply_app_style, visualize_gdf_as_df

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

st.markdown(
    "<div class='iriscc-section-title'><strong>Linking process</strong></div>",
    unsafe_allow_html=True,
)

st.markdown(
    """
            <div class="iriscc-instruction">
            Now you can programmatically link the addresses in the cohort dataset to the exposure datasets.
			<br><br>
            Locations are represented as points, and exposure datasets are represented as surfaces. In terms of data models, these are examples of a vector and a raster dataset, respectively.
            When a point is placed on a surface, you can sample the value at that point. This is how you link the cohort to the exposure datasets.
			<br><br>
            It's important to consider differences in spatial resolution between datasets. If a raster dataset has a spatial resolution of 100 meters, it means that each pixel represents 100 meters on the ground.
            Therefore, two points that are within this pixel will be assigned the same value, even though in reality they're up to 100 meters apart.
            <br><br>
            Press the button to run the linking procedure. Be patient, as this may take a few minutes depending on the number of locations and exposure datasets.
            <br><br>
            </div>
            """,
    unsafe_allow_html=True,
)


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
        and all(
            str(selection.get(key, "")).strip()
            for key in ("variable", "geoserver_name", "time")
        )
        for selection in raster_list
    )
)

if not cohort_ready:
    st.warning(
        "Load a valid cohort dataset on the Cohort page before starting the linking procedure."
    )

if not exposures_ready:
    st.warning(
        "Select at least one pollutant or temperature exposure, with no more than 10 raster times, on the Exposures page before starting the linking procedure."
    )

if exposures_ready:
    st.markdown("**Selected exposure variables**")
    selected_exposures = "\n".join(
        f"- {selection['variable']} {selection['time']}" for selection in raster_list
    )
    st.markdown(selected_exposures)

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
    st.session_state.pop("linked_df", None)
    st.session_state.pop("linking_failures", None)
    try:
        with st.status(
            "Linking exposure variables...", expanded=True
        ) as linking_status:

            def update_linking_status(state, variable_name):
                if state == "started":
                    linking_status.write(f"Linking `{variable_name}`...")
                    linking_status.update(label=f"Linking `{variable_name}`...")
                elif state == "completed":
                    linking_status.write(f"Finished `{variable_name}`")
                else:
                    linking_status.write(f"Could not link `{variable_name}`")

            linked_df, linking_failures = create_linked_dataframe(
                selected_variable_dict=raster_list,
                points_dataframe=location_gdf,
                return_failures=True,
                progress_callback=update_linking_status,
            )
            linking_status.update(label="Exposure linking finished", state="complete")
        st.session_state["linked_df"] = linked_df
        st.session_state["linking_failures"] = linking_failures

    except Exception as e:
        st.error(f"Error occurred while linking cohort to exposures: {e}")

linked_df_for_download = get_data()
if linked_df_for_download is not None:
    linking_failures = st.session_state.get("linking_failures", [])
    if linking_failures:
        failed_variables = ", ".join(
            failure["variable"] for failure in linking_failures
        )
        st.warning(
            f"Could not link these exposure layers: {failed_variables}. "
            "Their columns were added with null values."
        )
    st.success("""The linking procedure ran successfully!
    Notice the resulting table. Each row represents a subject in the cohort,
    and each column contains the value of an exposure variable.""")
    st.dataframe(visualize_gdf_as_df(linked_df_for_download), hide_index=True)

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
        type="secondary",
        disabled=linked_df_for_download.empty,
    )


code_expander = st.expander("Want to see the code used in the linking process?")
with code_expander:
    st.write("""
    ```python
        def link_to_raster(selected_variable_dict, points_dataframe, wcs=None):
            total_start = perf_counter()

            validation_start = perf_counter()
            if not isinstance(selected_variable_dict, dict):
                raise TypeError("Each raster selection must be a dictionary.")

            required_keys = {"variable", "geoserver_name", "time", "pixel_size"}
            missing_keys = required_keys.difference(selected_variable_dict)
            if missing_keys:
                raise ValueError(f"Raster selection is missing: {sorted(missing_keys)}")
            if not isinstance(points_dataframe, gpd.GeoDataFrame):
                raise TypeError("points_dataframe must be a GeoDataFrame.")
            if points_dataframe.empty:
                raise ValueError("points_dataframe contains no points.")
            if points_dataframe.crs is None:
                raise ValueError("points_dataframe has no CRS defined.")
            if points_dataframe.geometry.isna().any() or not points_dataframe.geometry.geom_type.eq("Point").all():
                raise ValueError("points_dataframe must contain only non-null Point geometries.")
            print(f"Timing: validation = {perf_counter() - validation_start:.3f}s")

            variable_name = str(selected_variable_dict["variable"]).strip()
            geoserver_name = str(selected_variable_dict["geoserver_name"]).strip()
            timestamp = str(selected_variable_dict["time"]).strip()
            pixel_size = float(selected_variable_dict["pixel_size"])
            if not variable_name or not geoserver_name or not timestamp:
                raise ValueError("Raster variable, GeoServer name, and time must be non-empty.")

            reprojection_start = perf_counter()
            original_crs = points_dataframe.crs
            points_in_raster_crs = points_dataframe.to_crs(TARGET_CRS)
            print(f"Timing: CRS conversion = {perf_counter() - reprojection_start:.3f}s")

            coverage_id = f"EXPANSE_map:{geoserver_name}"

            bounds_start = perf_counter()
            minx, miny, maxx, maxy = points_in_raster_crs.total_bounds
            if not all(math.isfinite(value) for value in (minx, miny, maxx, maxy)):
                raise ValueError("Point coordinates must be finite.")
            bbox = (
                float(minx - DEFAULT_BUFFER),
                float(miny - DEFAULT_BUFFER),
                float(maxx + DEFAULT_BUFFER),
                float(maxy + DEFAULT_BUFFER),
            )
            print(f"Timing: bounds and request preparation = {perf_counter() - bounds_start:.3f}s")

            print(f"Coverage id: {coverage_id}", f"Here are the bounding box coordinates: {bbox}", f"Here is the timestamp: {timestamp}")

            request_start = perf_counter()
            try:
                coverage = wcs.getCoverage(
                    identifier=coverage_id,
                    bbox=bbox,
                    crs=TARGET_CRS,
                    format="GeoTIFF",
                    time=[timestamp],
                    resx=pixel_size,
                    resy=pixel_size,
                )
            except Exception as e:
                raise RuntimeError(f"Failed to retrieve coverage from GeoServer: {e}")
            print(f"Timing: getCoverage request setup/response = {perf_counter() - request_start:.3f}s")

            read_start = perf_counter()
            data = coverage.read()
            print(f"Timing: coverage.read() = {perf_counter() - read_start:.3f}s ({len(data) / 1024 / 1024:.2f} MiB)")
            # print(data[:300])

            raster_start = perf_counter()
            with rasterio.MemoryFile(data) as memfile:
                with memfile.open() as dataset:
                    if dataset.count != 1:
                        raise ValueError(f"Expected 1 band, got {dataset.count} — check timestamp input.")

                    coord_list = list(zip(points_in_raster_crs.geometry.x, points_in_raster_crs.geometry.y))
                    sampled_values = []
                    for sample in dataset.sample(coord_list, masked=True):
                        value = sample[0]
                        sampled_values.append(None if value is None or getattr(value, "mask", False) else round(float(value), 2))
            print(f"Timing: GeoTIFF open and point sampling = {perf_counter() - raster_start:.3f}s ({len(sampled_values)} points)")

            linked_points = points_dataframe.copy()
            linked_points[variable_name] = sampled_values
            assert linked_points.crs == original_crs
            print(f"Timing: total link_to_raster = {perf_counter() - total_start:.3f}s")
            return linked_points


        def create_linked_dataframe(selected_variable_dict, points_dataframe):
            if not isinstance(selected_variable_dict, list) or not selected_variable_dict:
                raise ValueError("selected_variable_dict must be a non-empty list.")

            if not all(isinstance(selection, dict) for selection in selected_variable_dict):
                raise TypeError("Each raster selection must be a dictionary.")

            variable_names = [str(selection.get("variable", "")).strip() for selection in selected_variable_dict]
            if not all(variable_names):
                raise ValueError("Each raster selection must have a non-empty variable name.")
            if len(variable_names) != len(set(variable_names)):
                raise ValueError("Each raster selection must have a unique variable name.")

            total_start = perf_counter()
            linked_gdf = points_dataframe.copy()
            wcs = WebCoverageService(WCS_URL, version="1.0.0")
            print(f"Timing: WCS client creation = {perf_counter() - total_start:.3f}s")
            for variable_dict in selected_variable_dict:
                print(f"Extracting values from raster: {variable_dict['geoserver_name']}")
                extracted_values = link_to_raster(variable_dict, linked_gdf, wcs=wcs)
                variable_name = str(variable_dict["variable"]).strip()
                linked_gdf[variable_name] = extracted_values[variable_name]

            print(f"Timing: total create_linked_dataframe = {perf_counter() - total_start:.3f}s")
            return linked_gdf

        linked_df, linking_failures = create_linked_dataframe(
        selected_variable_dict=raster_list,
        points_dataframe=location_gdf,
        return_failures=True,
        )
    """)
