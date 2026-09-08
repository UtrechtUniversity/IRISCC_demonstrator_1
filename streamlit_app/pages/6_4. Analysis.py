import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import folium
import branca.colormap as cm
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from utils.iriscc_utils import apply_app_style

st.set_page_config(page_title="4. Analysis", layout="wide")
apply_app_style()

st.markdown(
    """
    <div class="iriscc-page-header">
        <h2 class="iriscc-page-title">Step 4 — Analysis</h2>
    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    Your linked dataset can be used to explore the relationship between air pollution, heatwaves, and health outcomes. You can perform various analyses, such as descriptive statistics, visualizations, and statistical modeling, to gain insights into the data.
    This is done offline. You can go back to the last page to download the linked dataset and perform your own analysis using your preferred tools and methods.

    Here are a few examples of analyses you can perform on the linked dataset:
    """,
    unsafe_allow_html=True,
)

# st.markdown(
#     """Here is one kind of analysis you can do: you can create a scatter plot of the linked data to visualize the relationship between two variables. You can also perform statistical tests or build regression models to quantify the relationship between exposures and health outcomes.
#     You can also use machine learning algorithms to predict health outcomes based on exposures. The possibilities are endless, and you can customize the analysis based on your specific research questions and data.
#     """
#         unsafe_allow_html=True,
# )

# st.markdown(
#     "Explore the spatial distribution and frequency of the exposure values linked to your cohort.",
#     unsafe_allow_html=True,
# )

st.markdown(
    "<div class='iriscc-section-title'><strong>Visualizing the spatial distribution</strong></div>",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="iriscc-body">
        Start by visualizing the spatial distribution of the exposure values linked to your cohort. You can create a map that shows the locations of the cohort members and color-code them based on their exposure values. This will help you identify any spatial patterns or clusters in the data.
        To see the overall distribution of values, you can also create a histogram of the exposure values. This will give you an idea of the range and frequency of the values in your dataset. Go back to the exposures page to see the units of each exposure.
        <br><br>
      </div>
    """,
    unsafe_allow_html=True,
)

linked_df = st.session_state.get("linked_df")
raster_list = st.session_state.get("raster_list", [])

if not isinstance(linked_df, gpd.GeoDataFrame) or linked_df.empty:
    st.info("Run the linking procedure on the previous page to create data for analysis.")
    st.stop()

selected_columns = [
    f"{selection.get('variable', '').strip()}_{selection.get('time', '').strip()}"
    for selection in raster_list
    if isinstance(selection, dict)
]
exposure_columns = [
    column for column in dict.fromkeys(selected_columns) if column in linked_df.columns
]

if not exposure_columns:
    st.warning("No selected exposure columns are available in the linked data.")
    st.stop()

selected_variable = st.selectbox("Exposure variable",
                                 exposure_columns,
                                 label_visibility="collapsed",
                                 width=500,
                                 )
numeric_values = pd.to_numeric(linked_df[selected_variable], errors="coerce")
valid_values = numeric_values.dropna()

if valid_values.empty:
    st.warning(f"{selected_variable} does not contain any numeric values to plot.")
    st.stop()

if linked_df.crs is None:
    st.error("The linked points do not have a coordinate reference system.")
    st.stop()

minimum = float(valid_values.min())
maximum = float(valid_values.max())


def normalized_color(value):
    if maximum <= minimum:
        return 0.0
    return (float(value) - minimum) / (maximum - minimum)


map_column, histogram_column = st.columns([3, 2])
panel_height = 560

with map_column:
    map_gdf = linked_df.to_crs("EPSG:4326")
    colour_map = plt.get_cmap("plasma_r")

    bounds = map_gdf.total_bounds
    map_center = [float(map_gdf.geometry.y.mean()), float(map_gdf.geometry.x.mean())]
    folium_map = folium.Map(
        location=map_center,
        zoom_start=7,
        tiles='https://tile.openstreetmap.org/{z}/{x}/{y}.png',
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    )
    folium_map.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]], padding=(20, 20))

    legend_positions = [
        minimum,
        minimum + (maximum - minimum) * 0.25,
        minimum + (maximum - minimum) * 0.5,
        minimum + (maximum - minimum) * 0.75,
        maximum,
    ]
    exposure_legend = cm.LinearColormap(
        colors=[mcolors.to_hex(colour_map(normalized_color(position))) for position in legend_positions],
        vmin=minimum,
        vmax=maximum,
    )
    exposure_legend.add_to(folium_map)

    for _, row in map_gdf.iterrows():
        value = pd.to_numeric(pd.Series([row[selected_variable]]), errors="coerce").iloc[0]
        marker_colour = "#98a2b3" if pd.isna(value) else mcolors.to_hex(colour_map(normalized_color(value)))
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=5,
            color=marker_colour,
            fill=True,
            fill_color=marker_colour,
            fill_opacity=0.85,
            weight=1,
            tooltip=f"{selected_variable}: {value if pd.notna(value) else 'No data'}",
        ).add_to(folium_map)

    st_folium(folium_map, width="100%", height=panel_height, returned_objects=[])

with histogram_column:
    bin_count = st.slider("Number of bins", min_value=5, max_value=50, value=20)
    figure, axis = plt.subplots(figsize=(7, panel_height / 100), dpi=100)
    figure.patch.set_facecolor("#f8fafc")
    axis.set_facecolor("#f8fafc")
    axis.hist(
        valid_values,
        bins=bin_count,
        color="#f5b042",
        edgecolor="#ffffff",
        linewidth=1.0,
        alpha=0.9,
    )
    axis.set_xlabel(selected_variable, fontsize=10, fontweight="semibold")
    axis.set_ylabel("Number of points", fontsize=10, fontweight="semibold")
    axis.set_title(f"Distribution of {selected_variable}", fontsize=12, fontweight="bold", pad=8)
    axis.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    axis.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.35)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_color("#cbd5e1")
    axis.spines["bottom"].set_color("#cbd5e1")
    axis.tick_params(axis="both", labelsize=9, colors="#475569")
    figure.tight_layout()
    st.pyplot(figure, clear_figure=True)
    plt.close(figure)


# st.subheader("Compare exposure between urban and rural areas")
# st.write("""There are various ways to define urban, suburban, and rural areas on a European or country-specific basis.
#         In this demonstrator, we will use the Eurostat Degree of Urbanisation (DEGURBA) classification, which is based on population density and settlement patterns. The DEGURBA classification divides areas into three categories: urban, suburban, and rural. You can use this classification to compare the exposure values between these different types of areas.
# """)

st.markdown(
    "<div class='iriscc-section-title'><strong>Exposure to heatwaves</strong></div>",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="iriscc-body">
        There is no single universal definition of a heatwave: different countries and studies use different thresholds and rules
        [<a href="https://climate.copernicus.eu/heatwaves-brief-introduction">5</a>].
        <br><br>
        Heatwave indices are often defined by one or more of the following:
        <ul>
            <li>a fixed temperature threshold</li>
            <li>a threshold relative to local historical data</li>
            <li>the temperature measured at a single location</li>
            <li>how widespread the heat is across a region</li>
            <li>the duration and intensity of the event</li>
            <li>daily minimum, average, or maximum temperature</li>
        </ul>
        <br>
        This section demonstrates how to identify individuals exposed to heatwaves using a simple rule-based approach.
        The table below contains sample daily temperature values for a dummy cohort during June, July, and August 2024.
        You can choose the definition you want to apply and see how many subjects match it.
        <br><br>
    </div>
    """,
    unsafe_allow_html=True,
)

summer_dates = pd.date_range("2024-06-01", "2024-08-31", freq="D")

sample_heatwave_df = pd.DataFrame({
    "subject_id": [f"{i:03d}" for i in range(1, 101)]
})

rng = pd.Series(range(100)).sample(frac=1, random_state=42).reset_index(drop=True)

for day in summer_dates:
    day_label = day.strftime("%Y-%m-%d")
    min_col = f"min_{day_label}"
    avg_col = f"avg_{day_label}"
    max_col = f"max_{day_label}"

    seasonal_baseline = 22 + 8 * (1 - abs(day.dayofyear - 200) / 120)

    sample_heatwave_df[min_col] = 0.0
    sample_heatwave_df[avg_col] = 0.0
    sample_heatwave_df[max_col] = 0.0

    for idx in range(len(sample_heatwave_df)):
        heat_bias = 0.0
        if idx % 11 == 0 and day.month in [7, 8]:
            heat_bias += 8
        if idx % 19 == 0 and day.month == 8:
            heat_bias += 7
        if idx % 29 == 0:
            heat_bias += 6
        if day.month == 6 and idx % 13 == 0:
            heat_bias -= 2

        daily_variation = (rng.iloc[idx] % 7) * 0.9
        max_temp = seasonal_baseline + daily_variation + heat_bias
        avg_temp = max_temp - 4 + ((rng.iloc[idx] % 3) * 0.8)
        min_temp = max(12, avg_temp - 6 + ((rng.iloc[idx] % 4) * 0.6))

        sample_heatwave_df.at[idx, min_col] = round(min_temp, 1)
        sample_heatwave_df.at[idx, avg_col] = round(avg_temp, 1)
        sample_heatwave_df.at[idx, max_col] = round(max_temp, 1)

max_columns = [col for col in sample_heatwave_df.columns if col.startswith("max_")]
avg_columns = [col for col in sample_heatwave_df.columns if col.startswith("avg_")]
min_columns = [col for col in sample_heatwave_df.columns if col.startswith("min_")]


st.markdown(
    "<div class='iriscc-instruction'><strong>1. Linked daily cohort temperature data</strong></div>",
    unsafe_allow_html=True,
)
st.caption("This is the output table of the linking step. The table shows one row per subject and one column per daily temperature value for the summer period.")
st.dataframe(
    sample_heatwave_df,
    use_container_width=True,
    height=420,
    hide_index=True,
)

heatwave_definitions = {
    "3 or more consecutive days where the maximum temperature exceeds a threshold": "max_gt_threshold",
    "5 or more consecutive days where the daily maximum exceeds the daily average by more than 5°C": "max_over_avg_gt_5",
    "Tropical night: 3 or more consecutive days where the minimum temperature exceeds a threshold": "min_gt_threshold",
}

st.markdown(
    "<div class='iriscc-instruction'><strong>2. Choose a heatwave definition</strong></div>",
    unsafe_allow_html=True,
)
selected_heatwave_definition = st.selectbox(
    "Definition to apply",
    list(heatwave_definitions.keys()),
    label_visibility="collapsed",
    width=1000,
)

heatwave_definition_key = heatwave_definitions[selected_heatwave_definition]

if heatwave_definition_key in {"max_gt_threshold", "min_gt_threshold"}:
    heat_threshold = st.slider(
        "Threshold temperature (°C)",
        min_value=20.0,
        max_value=35.0,
        value=28.0,
        step=1.0,
        width=300,
    )
else:
    heat_threshold = None


def has_consecutive_run(series, minimum_days):
    run_length = 0
    for value in series:
        if value:
            run_length += 1
            if run_length >= minimum_days:
                return True
        else:
            run_length = 0
    return False


def meets_heatwave_definition(row):
    max_values = row[max_columns]
    avg_values = row[avg_columns]
    min_values = row[min_columns]

    if heatwave_definition_key == "max_gt_threshold":
        return has_consecutive_run((max_values > heat_threshold).to_numpy(), 3)
    if heatwave_definition_key == "max_over_avg_gt_5":
        return has_consecutive_run(((max_values - avg_values) > 5).to_numpy(), 5)
    if heatwave_definition_key == "min_gt_threshold":
        return has_consecutive_run((min_values > heat_threshold).to_numpy(), 3)
    return False

sample_heatwave_df["meets_definition"] = sample_heatwave_df.apply(meets_heatwave_definition, axis=1)

sample_heatwave_df["max_days_over_threshold"] = (sample_heatwave_df[max_columns] > heat_threshold).sum(axis=1) if heatwave_definition_key == "max_gt_threshold" else 0
sample_heatwave_df["max_over_avg_days"] = ((sample_heatwave_df[max_columns] - sample_heatwave_df[avg_columns]) > 5).sum(axis=1) if heatwave_definition_key == "max_over_avg_gt_5" else 0
sample_heatwave_df["min_days_over_threshold"] = (sample_heatwave_df[min_columns] > heat_threshold).sum(axis=1) if heatwave_definition_key == "min_gt_threshold" else 0

matching_ids = sample_heatwave_df.loc[sample_heatwave_df["meets_definition"], "subject_id"].tolist()

st.markdown(
    "<div class='iriscc-instruction'><strong>3. Results</strong></div>",
    unsafe_allow_html=True,
)
st.write(
    f"{len(matching_ids)} out of {len(sample_heatwave_df)} subjects meet the selected definition and threshold in 2024."
)

if matching_ids:
    st.write(f"Subject IDs: {', '.join(map(str, matching_ids))}")

