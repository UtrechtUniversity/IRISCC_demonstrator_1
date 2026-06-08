import os
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(page_title="IRISCC Demonstrator", layout="wide")

logo_path = BASE_DIR / "Resources" / "iriscc_logo.png"
st.image(logo_path)

st.title("Risk on Human Health in Urban Areas during Heatwaves Associated with Deteriorated Air Quality")
st.header("IRISCC Demonstrator 1: Exposure Linking Notebook ")

'''
Summer in Europe is increasingly marked by two overlapping risks: extreme heat and poor air quality (AQ). Together, these hazards can be detrimental to human health.

This notebook shows how to connect **climate data**, **air-quality measurements**, and **address-level health data** in a practical way. 

We will link individual health records to weather and air-quality data at the same location and time. That makes it possible to study how heatwaves and pollution interact in urban environments.
'''