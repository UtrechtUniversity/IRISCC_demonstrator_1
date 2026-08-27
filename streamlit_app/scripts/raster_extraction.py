import math
import geopandas as gpd
import rasterio
from owslib.wcs import WebCoverageService
from time import perf_counter

WCS_URL = "https://exposome.uu.nl/geoserver/wcs"
TARGET_CRS = "EPSG:3035"
DEFAULT_BUFFER = 100
DEFAULT_RESOLUTION = 100

def link_to_raster(selected_variable_dict, points_dataframe, wcs=None):
    """Sample one WCS coverage at the locations in ``points_dataframe``."""
    total_start = perf_counter()

    validation_start = perf_counter()
    if not isinstance(selected_variable_dict, dict):
        raise TypeError("Each raster selection must be a dictionary.")

    required_keys = {"variable", "geoserver_name", "time"}
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
    if not variable_name or not geoserver_name or not timestamp:
        raise ValueError("Raster variable, GeoServer name, and time must be non-empty.")
    output_column = f"{variable_name}_{timestamp}"

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
            resx=DEFAULT_RESOLUTION,
            resy=DEFAULT_RESOLUTION,
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
            for coordinate in coord_list:
                try:
                    sample = next(dataset.sample([coordinate], masked=True))
                    value = sample[0]
                    numeric_value = float(value)
                    if value is None or getattr(value, "mask", False) or not math.isfinite(numeric_value):
                        sampled_values.append(None)
                    else:
                        sampled_values.append(round(numeric_value, 2))
                except (TypeError, ValueError, IndexError, StopIteration):
                    sampled_values.append(None)
    print(f"Timing: GeoTIFF open and point sampling = {perf_counter() - raster_start:.3f}s ({len(sampled_values)} points)")

    linked_points = points_dataframe.copy()
    linked_points[output_column] = sampled_values
    assert linked_points.crs == original_crs
    print(f"Timing: total link_to_raster = {perf_counter() - total_start:.3f}s")
    return linked_points


def create_linked_dataframe(
    selected_variable_dict,
    points_dataframe,
    return_failures=False,
    progress_callback=None,
):
    """Add one sampled exposure column for every selected raster/time.

    Failed layers are added as null columns and recorded in the optional
    failure report instead of stopping the remaining layers.
    """
    if not isinstance(selected_variable_dict, list) or not selected_variable_dict:
        raise ValueError("selected_variable_dict must be a non-empty list.")

    if not all(isinstance(selection, dict) for selection in selected_variable_dict):
        raise TypeError("Each raster selection must be a dictionary.")

    output_columns = [
        f"{str(selection.get('variable', '')).strip()}_{str(selection.get('time', '')).strip()}"
        for selection in selected_variable_dict
    ]
    if any(column == "_" or column.startswith("_") or column.endswith("_") for column in output_columns):
        raise ValueError("Each raster selection must have a non-empty variable name and timestamp.")
    if len(output_columns) != len(set(output_columns)):
        raise ValueError("Each variable and timestamp combination must be unique.")

    total_start = perf_counter()
    linked_gdf = points_dataframe.copy()
    failures = []
    wcs = WebCoverageService(WCS_URL, version="1.0.0")
    print(f"Timing: WCS client creation = {perf_counter() - total_start:.3f}s")
    for variable_dict in selected_variable_dict:
        variable_name = str(variable_dict["variable"]).strip()
        timestamp = str(variable_dict["time"]).strip()
        output_column = f"{variable_name}_{timestamp}"
        try:
            if progress_callback:
                progress_callback("started", output_column)
            print(f"Extracting values from raster: {variable_dict['geoserver_name']}")
            extracted_values = link_to_raster(variable_dict, linked_gdf, wcs=wcs)
            linked_gdf[output_column] = extracted_values[output_column]
            if progress_callback:
                progress_callback("completed", output_column)
        except Exception as error:
            print(f"Failed to link {output_column}: {error}")
            linked_gdf[output_column] = [None] * len(linked_gdf)
            failures.append({"variable": output_column, "error": str(error)})
            if progress_callback:
                progress_callback("failed", output_column)

    print(f"Timing: total create_linked_dataframe = {perf_counter() - total_start:.3f}s")
    if return_failures:
        return linked_gdf, failures
    return linked_gdf


if __name__ == "__main__":
    input_file = r"C:\Users\5298954\Documents\Github_Repos\IRISCC_demonstrator_1\streamlit_app\Resources\cardiovascularCohort.gpkg"
    selected_variable_dict = [
        {
            "variable": "NO2B25_AAV",
            "geoserver_name": "NO2B25_AAV",
            "time": "2023"
        }
    ]

    points_dataframe = gpd.read_file(input_file)

    gdf = create_linked_dataframe(selected_variable_dict, points_dataframe)

    print(gdf)



# # This should work as before, but without the multiprocessing.
# # I need to do a datacamp on multiprocessing.