import os
import geopandas as gpd
# import rasterio
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
    
    # src = rasterio.open(raster_path)

    # coord_list = [(x, y) for x, y in zip(gdf["geometry"].x, gdf["geometry"].y)]
    # gdf[variable_name] = [x[0].round(2) for x in src.sample(coord_list)]

    # return gdf[["SubjectID", variable_name]]


def extract_values(gdf, raster_folder, selected_rasters_list, raster_crs):
    rasters_in_folder = os.listdir(raster_folder)
    rasters_to_link = [f for f in rasters_in_folder if f.endswith(".tif") and f in selected_rasters_list]

    # Create geodataframe of extracted points
    for raster in rasters_to_link:
        extracted_values = sample_points(gdf, raster)
        gdf = gdf.merge(extracted_values, on="SubjectID")
    
    return gdf


if __name__ == "__main__":
    input_file = r"C:\Users\5298954\Documents\Github_Repos\IRISCC_demonstrator_1\streamlit_app\Resources\cardiovascularCohort.gpkg"
    raster_folder=r"C:\Users\5298954\Documents\Github_Repos\IRISCC_demonstrator_1\streamlit_app\Resources\exposure_datasets"
    raster_crs=3857

    exposure_selection = ["TEMP_AVG_20201201.tif"]

    gdf = extract_values(
        input_gdf=gpd.read_file(input_file),
        raster_folder=raster_folder,
        exposure_selection=exposure_selection,
        raster_crs=raster_crs
    )

    print(gdf)



# # This should work as before, but without the multiprocessing.
# # I need to do a datacamp on multiprocessing.