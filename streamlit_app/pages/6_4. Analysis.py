import streamlit as st
# from ..utils.iriscc_utils import fig_to_base64
# from ..helpers import sample_plot
import matplotlib.pyplot as plt
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

st.markdown("<div class='iriscc-instruction'>With our cohort information linked to exposure variables, you can now begin to visualize the exposure to air pollution and temperature in the uploaded cohort.</div>", unsafe_allow_html=True)
if "linked_df" in st.session_state:
    st.dataframe(st.session_state["linked_df"])


# if st.button("Show sample plot"):
#     fig = sample_plot()
#     st.pyplot(fig)

# st.write("You can add analysis widgets here to model health outcomes against exposures.")
