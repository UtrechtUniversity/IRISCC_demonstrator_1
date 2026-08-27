import math
from time import perf_counter

import geopandas as gpd
import rasterio
from owslib.wcs import WebCoverageService

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
    if (
        points_dataframe.geometry.isna().any()
        or not points_dataframe.geometry.geom_type.eq("Point").all()
    ):
        raise ValueError(
            "points_dataframe must contain only non-null Point geometries."
        )
    print(f"Timing: validation = {perf_counter() - validation_start:.3f}s")

    variable_name = str(selected_variable_dict["variable"]).strip()
    geoserver_name = str(selected_variable_dict["geoserver_name"]).strip()
    timestamp = str(selected_variable_dict["time"]).strip()
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
    print(
        f"Timing: bounds and request preparation = {perf_counter() - bounds_start:.3f}s"
    )

    print(
        f"Coverage id: {coverage_id}",
        f"Here are the bounding box coordinates: {bbox}",
        f"Here is the timestamp: {timestamp}",
    )

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
    print(
        f"Timing: getCoverage request setup/response = {perf_counter() - request_start:.3f}s"
    )

    read_start = perf_counter()
    data = coverage.read()
    print(
        f"Timing: coverage.read() = {perf_counter() - read_start:.3f}s ({len(data) / 1024 / 1024:.2f} MiB)"
    )
    # print(data[:300])

    raster_start = perf_counter()
    with rasterio.MemoryFile(data) as memfile:
        with memfile.open() as dataset:
            if dataset.count != 1:
                raise ValueError(
                    f"Expected 1 band, got {dataset.count} — check timestamp input."
                )

            coord_list = list(
                zip(points_in_raster_crs.geometry.x, points_in_raster_crs.geometry.y)
            )
            sampled_values = []
            for sample in dataset.sample(coord_list, masked=True):
                value = sample[0]
                sampled_values.append(
                    None
                    if value is None or getattr(value, "mask", False)
                    else round(float(value), 2)
                )
    print(
        f"Timing: GeoTIFF open and point sampling = {perf_counter() - raster_start:.3f}s ({len(sampled_values)} points)"
    )

    linked_points = points_dataframe.copy()
    linked_points[variable_name] = sampled_values
    assert linked_points.crs == original_crs
    print(f"Timing: total link_to_raster = {perf_counter() - total_start:.3f}s")
    return linked_points


def create_linked_dataframe(selected_variable_dict, points_dataframe):
    """Add one sampled exposure column for every selected raster/time."""
    if not isinstance(selected_variable_dict, list) or not selected_variable_dict:
        raise ValueError("selected_variable_dict must be a non-empty list.")

    if not all(isinstance(selection, dict) for selection in selected_variable_dict):
        raise TypeError("Each raster selection must be a dictionary.")

    variable_names = [
        str(selection.get("variable", "")).strip()
        for selection in selected_variable_dict
    ]
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

    print(
        f"Timing: total create_linked_dataframe = {perf_counter() - total_start:.3f}s"
    )
    return linked_gdf


if __name__ == "__main__":
    selected_variable_dict = [
        {
            "variable": "Yearly average temperature",
            "geoserver_name": "TMP_AVG_YEARLY",
            "time": "2023",
        }
    ]

    points_dataframe = gpd.read_file(
        r"C:\Users\5298954\Documents\Github_Repos\IRISCC_demonstrator_1\streamlit_app\Resources\france_cohort.gpkg"
    )

    linked_df = create_linked_dataframe(selected_variable_dict, points_dataframe)
    print(linked_df.head())

    # # Extra printing for testing if needed
    # cov_info = wcs[coverage_id]
    # print(cov_info.timepositions)
    # print("Title:", cov_info.title)
    # print("Bounding box (WGS84):", bbox)
    # print("Supported CRSs:", cov_info.supportedCRS)
    # print("Supported formats:", cov_info.supportedFormats)
    # print(cov_info.timelimits)
    # raw = coverage.read()

    # Save tiff for testing
    # data = coverage.read()
    # print(data[:200])
    # raster_path = Path("streamlit_app", "Resources", "exposure_datasets", f"test_geoserver_5.tif").resolve()
    # with open(raster_path, 'wb') as f:
    #     f.write(coverage.read())
    # print(f"Raster {coverage_id} downloaded successfully.")


# def get_points_bounds(points):
#     points_3857 = points.to_crs("EPSG:3857")

#     x, y = points_3857.geometry.iloc[0].x, points_3857.geometry.iloc[0].y
#     print(x, y)
#     return x, y


#     # min_x, min_y, max_x, max_y = points_3857.total_bounds

#     # print(points_3857.crs)
#     # print(min_x, min_y, max_x, max_y)

#     # return min_x, min_y, max_x, max_y


# def query_geoserver_for_raster(raster_name):
#     points = gpd.read_file(r"C:\Users\5298954\Documents\Github_Repos\IRISCC_demonstrator_1\streamlit_app\Resources\NL_points_1_km.gpkg")

#     x, y = get_points_bounds(points)

#     wms = WebMapService("https://exposome.uu.nl/geoserver/wms", version="1.3.0")

#     bbox = (4.5, 52.0, 5.5, 52.5)
#     print(list(wms.contents))
#     response = wms.getmap(
#         layers=["EXPANSE_map:TEMP_MAX_MONTHLY"],
#         srs="EPSG:4326",
#         bbox=bbox,
#         size=(1024, 1024),       # pixel dimensions of output image
#         format="image/geotiff",  # GeoServer WMS often supports this directly
#         transparent=True
#     )

#     print(response.status_code)
#     print(response.headers.get("Content-Type"))
#     print(len(response.content))


# # # def query_geoserver_for_raster(raster_name):
# #     points = gpd.read_file(r"C:\Users\5298954\Documents\Github_Repos\IRISCC_demonstrator_1\streamlit_app\Resources\NL_points_1_km.gpkg")

# #     x, y = get_points_bounds(points)


# #     wcs = WebCoverageService("https://exposome.uu.nl/geoserver/wcs", version="1.0.0")

# #     overage_id = "workspace:layername"  # pick one from the list above

# #     cov_info = wcs["EXPANSE_map:P10B100_MAV"]

# #     print("Title:", cov_info.title)
# #     print("Bounding box (WGS84):", cov_info.boundingBoxWGS84)
# #     print("Supported CRSs:", cov_info.supportedCRS)
# #     print("Supported formats:", cov_info.supportedFormats)

# #     bbox = (4.5, 52.0, 5.5, 52.5)  # (minx, miny, maxx, maxy) — use values within boundingBoxWGS84

# #     coverage = wcs.getCoverage(
# #         identifier="EXPANSE_map:P10B100_MAV",
# #         bbox=bbox,
# #         crs="EPSG:4326",         # match one of cov_info.supportedCRS
# #         format="GeoTIFF",        # match one of cov_info.supportedFormats
# #         resx=100,               # resolution in x — adjust to your needs
# #         resy=100                # resolution in y
# #     )

# #     with open("coverage_output.tif", "wb") as f:
# #         f.write(coverage.read())

# #     print("Saved coverage_output.tif")

#     # geoserver_url = "https://exposome.uu.nl/geoserver/wcs"
#     # params = {
#     #     "service": "WCS",
#     #     "version": "2.0.1",
#     #     "request": "GetCoverage",
#     #     "coverageId": "EXPANSE_map__MVI_MD5",
#     #     "format": "image/tiff",
#     #     "subset": [
#     #         f"X({x - 500},{x + 500})",
#     #         f"Y({y - 500},{y + 500})",
#     #     ],
#     # }

#     # response = requests.get(geoserver_url, params=params)

#     # print(response.status_code)
#     # print(response.headers.get("Content-Type"))
#     # print(len(response.content))
#     # response = requests.get(geoserver_url, params=params)

#     # print(response.status_code)
#     # print(response.headers.get("Content-Type"))
#     # print(response.text)
#     # # with rasterio.MemoryFile(response.content) as memfile:
#     # #     with memfile.open() as src:
#     # #         values = list(src.sample(points))

#     # # with MemoryFile() as memfile:
#     # #     with memfile.open(driver='GTiff', count=3, ...) as dataset:
#     # #         dataset.write(data_array)

#     # if response.status_code == 200:
#     #     raster_path = Path("streamlit_app", "Resources", "exposure_datasets", raster_name).resolve()
#     #     with open(raster_path, 'wb') as f:
#     #         f.write(response.content)
#     #     print(f"Raster {raster_name} downloaded successfully.")
#     # else:
#     #     print(f"Failed to download raster {raster_name}. Status code: {response.status_code}")

# def sample_points(gdf, raster_name):
#     print(f"Sampling points from raster: {raster_name}")
#     raster_path = Path("streamlit_app", "Resources", "exposure_datasets", raster_name).resolve()
#     print(f"Raster path: {raster_path}")

#     # src = rasterio.open(raster_path)

#     # coord_list = [(x, y) for x, y in zip(gdf["geometry"].x, gdf["geometry"].y)]
#     # gdf[variable_name] = [x[0].round(2) for x in src.sample(coord_list)]

#     # return gdf[["SubjectID", variable_name]]


# def extract_values(gdf, raster_folder, selected_rasters_list, raster_crs):
#     rasters_in_folder = os.listdir(raster_folder)
#     rasters_to_link = [f for f in rasters_in_folder if f.endswith(".tif") and f in selected_rasters_list]

#     # Create geodataframe of extracted points
#     for raster in rasters_to_link:
#         print(f"Extracting values from raster: {raster}")
#         extracted_values = sample_points(gdf, raster)
#     #     gdf = gdf.merge(extracted_values, on="SubjectID")

#     # return gdf
