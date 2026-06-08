import streamlit as st
from beacon_api import *
client = Client("https://beacon-iriscc.maris.nl")

'''
This is where linking to ACTIS data is done
'''

st.set_page_config(page_title="5. Explore Other Datasets", layout="wide")


def fetch_exposure():

    tables = client.list_tables()

    return (
        tables['iagos-l2']
        .query()
        .add_select_column("x")
        .add_select_column("y")
        # .add_select_column(value_column)
        # .add_range_filter("x", minx, maxx)
        # .add_range_filter("y", miny, maxy)
        .to_geo_pandas_dataframe("x", "y", crs="EPSG:3035")
    )


# tables = client.list_tables()
# tables

# result = fetch_exposure()
# result.head()