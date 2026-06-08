import io
import base64
import matplotlib.pyplot as plt
import pandas as pd

def dataframe_to_html(df, max_rows=10):
    table_html = df.to_html(max_rows=max_rows, index=False)
    table_html = table_html.replace(
        "<table",
        '<table style="display:block; overflow-y:auto; max-height:400px;"'
    )
    return table_html

def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()

def safe_read_geopackage(path):
    try:
        import geopandas as gpd
    except Exception:
        return None, 'geopandas not installed'

    try:
        gdf = gpd.read_file(path)
        return gdf, None
    except Exception as e:
        return None, str(e)
