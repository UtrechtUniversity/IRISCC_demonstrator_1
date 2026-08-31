import math
from time import perf_counter

import geopandas as gpd
import rasterio
import streamlit as st
from owslib.wcs import WebCoverageService

WCS_URL = "https://exposome.uu.nl/geoserver/wcs"
TARGET_CRS = "EPSG:3857"
DEFAULT_BUFFER = 100
@st.cache_data(show_spinner=False)
def _request_coverage_bytes(coverage_id, bbox, timestamp, pixel_size):
    """Fetch and cache one deterministic WCS request."""
    wcs = WebCoverageService(WCS_URL, version="1.0.0")
    coverage = wcs.getCoverage(
        identifier=coverage_id,
        bbox=bbox,
        crs=TARGET_CRS,
        format="GeoTIFF",
        time=[timestamp],
        resx=pixel_size,
        resy=pixel_size,
        timeout=60,
    )
    return coverage.read()


def _sample_coverage(data, points):
    with rasterio.MemoryFile(data) as memfile:
        with memfile.open() as dataset:
            if dataset.count != 1:
                raise ValueError(
                    f"Expected 1 band, got {dataset.count} — check timestamp input."
                )
            sampled_values = []
            coordinates = zip(points.geometry.x, points.geometry.y)
            for coordinate in coordinates:
                try:
                    value = next(dataset.sample([coordinate], masked=True))[0]
                    numeric_value = float(value)
                    if (
                        value is None
                        or getattr(value, "mask", False)
                        or not math.isfinite(numeric_value)
                    ):
                        sampled_values.append(None)
                    else:
                        sampled_values.append(round(numeric_value, 2))
                except (TypeError, ValueError, IndexError, StopIteration):
                    sampled_values.append(None)
            return sampled_values


def link_to_raster(
    selected_variable_dict, points_dataframe, wcs=None, progress_callback=None,
    return_failures=False,
):
    """Sample a raster in 4-pixel grid cells and preserve point ordering."""
    total_start = perf_counter()
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

    variable_name = str(selected_variable_dict["variable"]).strip()
    geoserver_name = str(selected_variable_dict["geoserver_name"]).strip()
    timestamp = str(selected_variable_dict["time"]).strip()
    try:
        pixel_size = float(selected_variable_dict["pixel_size"])
    except (TypeError, ValueError):
        raise ValueError("Raster pixel_size must be a positive number.")
    if not variable_name or not geoserver_name or not timestamp:
        raise ValueError("Raster variable, GeoServer name, and time must be non-empty.")
    if not math.isfinite(pixel_size) or pixel_size <= 0:
        raise ValueError("Raster pixel_size must be a positive number.")

    output_column = f"{variable_name}_{timestamp}"
    points_in_raster_crs = points_dataframe.to_crs(TARGET_CRS)
    minx, miny, maxx, maxy = points_in_raster_crs.total_bounds
    if not all(math.isfinite(value) for value in (minx, miny, maxx, maxy)):
        raise ValueError("Point coordinates must be finite.")

    cell_size = pixel_size * 10
    column_count = max(1, math.ceil((maxx - minx) / cell_size))
    row_count = max(1, math.ceil((maxy - miny) / cell_size))
    cell_x = ((points_in_raster_crs.geometry.x - minx) // cell_size).astype(int).clip(upper=column_count - 1)
    cell_y = ((points_in_raster_crs.geometry.y - miny) // cell_size).astype(int).clip(upper=row_count - 1)
    occupied_tiles = {}
    for position, tile_id in enumerate(zip(cell_x, cell_y)):
        occupied_tiles.setdefault(tile_id, []).append(position)
    failures = []
    sampled_values = [None] * len(points_dataframe)
    coverage_id = f"EXPANSE_map:{geoserver_name}"

    print("Number of occupied tiles to process:", len(occupied_tiles))
    for tile_number, point_positions in enumerate(occupied_tiles.values(), start=1):
        tile_points = points_in_raster_crs.iloc[point_positions]
        if tile_points.empty:
            continue
        tile_minx, tile_miny, tile_maxx, tile_maxy = tile_points.total_bounds
        bbox = (
            float(tile_minx - DEFAULT_BUFFER),
            float(tile_miny - DEFAULT_BUFFER),
            float(tile_maxx + DEFAULT_BUFFER),
            float(tile_maxy + DEFAULT_BUFFER),
        )
        progress_message = f"Processing tile {tile_number} of {len(occupied_tiles)} for {output_column}"
        print(progress_message)
        if progress_callback:
            progress_callback("progress", progress_message)
        try:
            if wcs is None:
                data = _request_coverage_bytes(
                    coverage_id, bbox, timestamp, pixel_size
                )
            else:
                coverage = wcs.getCoverage(
                    identifier=coverage_id,
                    bbox=bbox,
                    crs=TARGET_CRS,
                    format="GeoTIFF",
                    time=[timestamp],
                    resx=pixel_size,
                    resy=pixel_size,
                )
                data = coverage.read()
            tile_values = _sample_coverage(data, tile_points)
            for position, value in zip(point_positions, tile_values):
                sampled_values[position] = value
        except Exception as error:
            failure = {
                "variable": output_column,
                "tile": tile_number,
                "bbox": bbox,
                "error": str(error),
            }
            failures.append(failure)
            print(f"Failed {output_column} tile {tile_number}: {error}")

    linked_points = points_dataframe.copy()
    linked_points[output_column] = sampled_values
    print(f"Timing: total link_to_raster = {perf_counter() - total_start:.3f}s")
    if return_failures:
        return linked_points, failures
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
    if any(
        column == "_" or column.startswith("_") or column.endswith("_")
        for column in output_columns
    ):
        raise ValueError(
            "Each raster selection must have a non-empty variable name and timestamp."
        )
    if len(output_columns) != len(set(output_columns)):
        raise ValueError("Each variable and timestamp combination must be unique.")

    total_start = perf_counter()
    linked_gdf = points_dataframe.copy()
    failures = []
    for variable_dict in selected_variable_dict:
        variable_name = str(variable_dict["variable"]).strip()
        timestamp = str(variable_dict["time"]).strip()
        output_column = f"{variable_name}_{timestamp}"
        try:
            if progress_callback:
                progress_callback("started", output_column)
            print(f"Extracting values from raster: {variable_dict['geoserver_name']}")
            extracted_values, tile_failures = link_to_raster(
                variable_dict,
                linked_gdf,
                progress_callback=progress_callback,
                return_failures=True,
            )
            linked_gdf[output_column] = extracted_values[output_column]
            failures.extend(tile_failures)
            if progress_callback:
                progress_callback("completed", output_column)
        except Exception as error:
            print(f"Failed to link {output_column}: {error}")
            linked_gdf[output_column] = [None] * len(linked_gdf)
            failures.append({"variable": output_column, "error": str(error)})
            if progress_callback:
                progress_callback("failed", output_column)

    print(
        f"Timing: total create_linked_dataframe = {perf_counter() - total_start:.3f}s"
    )
    if return_failures:
        return linked_gdf, failures
    return linked_gdf


if __name__ == "__main__":
    input_file = r"C:\Users\5298954\Documents\Github_Repos\IRISCC_demonstrator_1\streamlit_app\Resources\cardiovascularCohort.gpkg"
    selected_variable_dict = [
        {
            "variable": "NO2B25_AAV",
            "geoserver_name": "NO2B25_AAV",
            "time": "2023",
            "pixel_size": 25,
        }
    ]

    points_dataframe = gpd.read_file(input_file)

    gdf = create_linked_dataframe(selected_variable_dict, points_dataframe)

    print(gdf)


# # This should work as before, but without the multiprocessing.
# # I need to do a datacamp on multiprocessing.
