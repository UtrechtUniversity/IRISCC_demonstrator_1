import io
import base64
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


def apply_app_style():
    st.markdown(
        """
        <style>
        :root {
            --iriscc-primary: #123b5d;
            --iriscc-accent: #f59e0b;
            --iriscc-accent-soft: rgba(245, 158, 11, 0.12);
            --iriscc-accent-strong: #d97706;
            --iriscc-surface: rgba(255, 255, 255, 0.84);
            --iriscc-surface-strong: rgba(255, 255, 255, 0.96);
            --iriscc-border: rgba(16, 24, 40, 0.10);
            --iriscc-text: #102133;
            --iriscc-muted: #5f6b7a;
            --iriscc-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(245, 158, 11, 0.12), transparent 28%),
                radial-gradient(circle at top right, rgba(18, 59, 93, 0.10), transparent 30%),
                linear-gradient(180deg, #f6f8fb 0%, #eef3f8 100%);
            color: var(--iriscc-text);
        }

        section.main > div {
            padding-top: 1.5rem;
            max-width: 1220px;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #10263c 0%, #123b5d 100%);
        }

        [data-testid="stSidebar"] * {
            color: #f6fbff;
        }

        [data-testid="stSidebar"] a {
            color: #d9efff;
        }

        [data-testid="stSidebarNav"] {
            padding-top: 0.5rem;
        }

        div[data-testid="stHeader"] {
            display: none;
        }

        div[data-testid="stTitle"] h1,
        .stTitle h1 {
            color: var(--iriscc-text);
            letter-spacing: -0.03em;
            font-weight: 800;
            line-height: 1.08;
        }

        div[data-testid="stHeader"] + div {
            padding-top: 0;
        }

        h2, h3, h4, h5, h6 {
            color: var(--iriscc-text);
            letter-spacing: -0.02em;
        }

        p, li, div, span, label {
            color: var(--iriscc-text);
        }

        .stMarkdown p {
            color: var(--iriscc-text);
            line-height: 1.65;
        }

        .stInfo, .stWarning, .stSuccess, .stError {
            border-radius: 16px;
            border: 1px solid var(--iriscc-border);
            box-shadow: var(--iriscc-shadow);
        }

        .stInfo {
            border-left: 4px solid var(--iriscc-accent);
            background: linear-gradient(180deg, rgba(255, 249, 240, 0.96), rgba(255, 255, 255, 0.98));
        }

        .stRadio > div,
        .stSelectbox > div,
        [data-baseweb="select"] > div,
        [data-testid="stRadio"] {
            accent-color: var(--iriscc-accent) !important;
        }

        div[role="radiogroup"] label,
        div[role="radiogroup"] span,
        div[role="radiogroup"] div {
            font-size: 1.08rem !important;
        }

        .stRadio [role="radio"] {
            border-color: var(--iriscc-accent) !important;
        }

        .stRadio input:checked + div,
        .stRadio input:checked + span {
            color: var(--iriscc-accent) !important;
        }

        [data-testid="stDataFrame"] {
            border-radius: 18px;
            box-shadow: var(--iriscc-shadow);
            overflow: hidden;
        }

        [data-testid="stExpander"] {
            border-radius: 18px;
            background: var(--iriscc-surface);
            border: 1px solid var(--iriscc-border);
            box-shadow: var(--iriscc-shadow);
        }

        [data-testid="stHorizontalBlock"] {
            gap: 1rem;
        }

        .stButton > button {
            border-radius: 999px;
            border: 1px solid rgba(16, 24, 40, 0.10);
            background: var(--iriscc-surface-strong);
            color: var(--iriscc-text);
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
            transition: transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            border-color: rgba(245, 158, 11, 0.55);
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.12);
        }

        .stButton > button:focus-visible {
            outline: 3px solid rgba(245, 158, 11, 0.22);
            outline-offset: 2px;
        }

        .iriscc-card {
            border-radius: 18px;
            border: 1px solid var(--iriscc-border);
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(247, 250, 252, 0.95));
            box-shadow: var(--iriscc-shadow);
            padding: 1rem 1rem 0.95rem 1rem;
            transition: transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease;
        }

        .iriscc-card.is-selected {
            border-color: rgba(18, 59, 93, 0.34);
            background: linear-gradient(180deg, rgba(230, 242, 252, 0.96), rgba(247, 250, 252, 0.98));
        }

        .iriscc-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 20px 42px rgba(15, 23, 42, 0.12);
        }

        .iriscc-card-title {
            font-size: 1rem;
            font-weight: 700;
            color: var(--iriscc-text);
            margin-bottom: 0.2rem;
        }

        .iriscc-card-subtitle {
            color: var(--iriscc-muted);
            font-size: 0.9rem;
            line-height: 1.45;
        }

        .iriscc-card-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            border-radius: 999px;
            padding: 0.22rem 0.65rem;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            background: rgba(15, 118, 110, 0.10);
            color: var(--iriscc-accent);
            margin-bottom: 0.7rem;
        }

        hr {
            border-color: rgba(16, 24, 40, 0.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

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
