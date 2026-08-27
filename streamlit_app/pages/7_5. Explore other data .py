import streamlit as st

# from beacon_api import *
from utils.iriscc_utils import apply_app_style

# client = Client("https://beacon-iriscc.maris.nl")

apply_app_style()

# '''
# This is where linking to ACTIS data is done
# '''
# def fetch_exposure():

#     tables = client.list_tables()

#     return (
#         tables['actris-nrt']
#         .query()
#         .add_select_column("x")
#         .add_select_column("y")
#         # .add_select_column(value_column)
#         # .add_range_filter("x", minx, maxx)
#         # .add_range_filter("y", miny, maxy)
#         .to_geo_pandas_dataframe("x", "y", crs="EPSG:3035")
#     )


# tables = client.list_tables()
# tables

# result = fetch_exposure()
