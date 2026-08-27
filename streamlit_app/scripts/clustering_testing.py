import clusterpy as cp
import geopandas as gpd
import pysal as ps
from sklearn import cluster

data = gpd.read_file(
    r"C:\Users\5298954\Documents\Github_Repos\IRISCC_demonstrator_1\streamlit_app\Resources\france_cohort.gpkg"
)

kmeans5 = cluster.KMeans(n_clusters=5)

# clusters = kmeans5.fit(data["numero"])

weights = ps.queen
layer = cp.Layer()


# print(clusters)
