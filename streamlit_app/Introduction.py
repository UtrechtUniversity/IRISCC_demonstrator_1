import streamlit as st
from pathlib import Path
from utils.iriscc_utils import apply_app_style

BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(page_title="IRISCC Demonstrator", layout="wide")
apply_app_style()

st.markdown(
    """
    <style>
    .iriscc-hero {
        border-radius: 28px;
        padding: 2rem 2rem 1.6rem 2rem;
        background:
            linear-gradient(135deg, rgba(255, 255, 255, 0.94), rgba(233, 239, 246, 0.90)),
            radial-gradient(circle at top right, rgba(15, 118, 110, 0.12), transparent 30%),
            radial-gradient(circle at bottom left, rgba(18, 59, 93, 0.10), transparent 28%);
        border: 1px solid rgba(16, 24, 40, 0.10);
        box-shadow: 0 24px 48px rgba(15, 23, 42, 0.10);
        margin-bottom: 1.25rem;
    }

    .iriscc-hero h1 {
        margin: 0;
        font-size: clamp(2.8rem, 5vw, 4.8rem);
        line-height: 1.05;
        letter-spacing: -0.04em;
    }

    .iriscc-subtitle {
        margin-top: 0.9rem;
        font-size: 1.35rem;
        line-height: 1.8;
        color: #425466;
    }

    .iriscc-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 1rem;
        margin: 1.3rem 0 0.4rem 0;
    }

    .iriscc-card {
        border-radius: 20px;
        padding: 1.1rem 1.1rem 1rem 1.1rem;
        background: rgba(255, 255, 255, 0.90);
        border: 1px solid rgba(16, 24, 40, 0.08);
        box-shadow: 0 14px 30px rgba(15, 23, 42, 0.06);
        height: 100%;
    }

    .iriscc-card h3 {
        margin: 0 0 0.45rem 0;
        font-size: 1.38rem;
    }

    .iriscc-card p {
        margin: 0;
        color: #516173;
        line-height: 1.72;
        font-size: 1.22rem;
    }

    .iriscc-section-title {
        margin-top: 1.4rem;
        margin-bottom: 0.5rem;
        font-size: 1.45rem;
        letter-spacing: -0.02em;
    }

    .iriscc-body {
        color: #344054;
        line-height: 1.82;
        font-size: 1.26rem;
    }

    .stMarkdown p,
    .stMarkdown li {
        font-size: 1.22rem;
        line-height: 1.8;
    }

    .stCaption {
        font-size: 1.08rem;
    }

    h2, h3, h4, h5, h6 {
        line-height: 1.2;
    }

    h2 {
        font-size: 1.9rem;
    }

    h3 {
        font-size: 1.45rem;
    }

    h4 {
        font-size: 1.25rem;
    }

    @media (max-width: 900px) {
        .iriscc-grid {
            grid-template-columns: 1fr;
        }

        .iriscc-hero {
            padding: 1.4rem 1.1rem 1.2rem 1.1rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns([3, 1])
with col1:
    iriscc_logo_path = BASE_DIR / "Resources" / "iriscc_logo.png"
    st.image(iriscc_logo_path)

with col2:
    iras_logo_path = BASE_DIR / "Resources" / "iras_logo.png"
    st.image(iras_logo_path)


st.markdown(
    """
    <div class="iriscc-hero">
        <h1>Risk on Human Health in Urban Areas during Heatwaves Associated with Deteriorated Air Quality</h1>
        <div class="iriscc-subtitle">
            Summer in Europe is increasingly marked by two overlapping threats: extreme heat and poor air quality.
            This demonstrator shows how spatial data can be combined with health information to understand where
            people may be exposed to higher environmental risk.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='iriscc-section-title'><strong>What this demonstrator does</strong></div>", unsafe_allow_html=True)
st.markdown(
    """
    <div class="iriscc-body">
        It brings together climate data, air-quality measurements, and individual-level or community-level health data. The core idea is to link exposures to residential locations so that analysis happens at the same place and time as the underlying risk.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="iriscc-grid">
        <div class="iriscc-card">
            <h3>Define the cohort</h3>
            <p>Select or prepare the population and location data that will be used for the linkage step.</p>
        </div>
        <div class="iriscc-card">
            <h3>Attach exposures</h3>
            <p>Match weather and air-quality data to each address or point in space at the relevant time.</p>
        </div>
        <div class="iriscc-card">
            <h3>Explore the results</h3>
            <p>Inspect the linked dataset and use the analysis pages to understand patterns and risk.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
