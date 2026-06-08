import streamlit as st
from ..utils.iriscc_utils import fig_to_base64
from ..helpers import sample_plot
import matplotlib.pyplot as plt

st.title("Step 4 — Analysis")

st.write("Quick visualization examples. Use linked dataset from Step 3 in real analyses.")

if st.button("Show sample plot"):
    fig = sample_plot()
    st.pyplot(fig)

st.write("You can add analysis widgets here to model health outcomes against exposures.")
