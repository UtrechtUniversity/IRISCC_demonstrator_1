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
        padding: 1.1rem 1.1rem 1.8rem 1.8rem;
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
        <h2>Risk on Human Health in Urban Areas during Heatwaves Associated with Deteriorated Air Quality</h2>
        <div class="iriscc-subtitle">
            Summer in Europe is increasingly marked by two overlapping threats to health: extreme heat and poor air quality.
            Research has shown that combined exposure to these environmental risk factors presents a greater risk to health than the sum of their individual risks [<a href="https://www.eea.europa.eu/en/newsroom/editorial/combined-effects-of-air-pollution-and-heat-exposure">1</a>].
            Worryingly, climate change is projected to not only increase the frequency and intensity of heatwaves, but to impact the emission of air pollutants during extreme events.
        </div>
        <div class="iriscc-subtitle">
            This demonstrator will show you how spatial datasets can be combined with health information to understand patterns of exposure to heat and air pollution,
            and how these exposures may be linked to health outcomes. This is a key workflow in Health Impact Assessments (HIA).
        </div>
        <div class="iriscc-subtitle">
            These insights can be used to guide urban design, build resilient healthcare systems,
            inform local public health interventions, and develop strategic public policy (at national and global levels) that incporates health considerations [<a href="https://sciencemediahub.eu/2026/07/15/a-scientists-opinion-interview-with-prof-dr-roel-vermeulen-on-extreme-weather-and-the-impact-on-our-health/">2</a>].
       </div>

    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='iriscc-section-title'><strong>What this demonstrator does</strong></div>", unsafe_allow_html=True)
st.markdown(
    """
    <div class="iriscc-body">
        It brings together climate data, air-quality measurements, and residential address data of study cohorts. The workflow will demonstrate how to link exposures to locations to derive scientific insights.
        <br><br> We'll do these steps:

    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div class="iriscc-grid">
        <div class="iriscc-card">
            <h3>Define the cohort and exposures</h3>
            <p>Based on our research question, define the study population, location data, and exposure variables of interest.</p>
        </div>
        <div class="iriscc-card">
            <h3>Attach exposures</h3>
            <p>Match weather and air-quality data to each address at the relevant time.</p>
        </div>
        <div class="iriscc-card">
            <h3>Explore the results</h3>
            <p>Analyze and visualize the linked dataset to understand patterns of risk.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.space("medium")

st.page_link("pages/3_1. Cohort.py", label="Start the demonstrator", icon="➡️", width="content")
