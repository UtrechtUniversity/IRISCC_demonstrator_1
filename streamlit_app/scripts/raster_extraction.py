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

    print(raster_folder)
    print(os.exists(raster_folder))
    raster_files = [f for f in os.listdir(raster_folder) if f.endswith(".tif") and f in raster_list]

    # Read cohort data
    gdf = prepare_input_data(input_file, raster_crs)

    # Create geodataframe of extracted points
    for raster in raster_files:
        extracted_values = sample_points(gdf, raster)
        gdf.merge(extracted_values, on="SubjectID")
    
    return gdf


if __name__ == "__main__":
    input_file = r"C:\Users\5298954\Documents\Github_Repos\IRISCC_demonstrator_1\streamlit_app\Resources\cardiovascularCohort.gpkg"
    raster_folder=r"C:\Users\5298954\Documents\Github_Repos\IRISCC_demonstrator_1\streamlit_app\Resources\exposure_datasets"
    raster_crs=3857

    exposure_selection = ["TEMP_AVG_20201201.tif"]

    gdf = extract_values(
        input_file=input_file,
        raster_folder=raster_folder,
        exposure_selection=exposure_selection,
        raster_crs=raster_crs
    )

    print(gdf)



# # This should work as before, but without the multiprocessing.
# # I need to do a datacamp on multiprocessing.