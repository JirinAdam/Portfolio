import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from data.loader import (
    load_history_roles,
    load_history_industries,
    get_history_role_options,
    get_history_industry_options,
)
from components.charts import make_trend_line

st.set_page_config(
    page_title="Historical Trends",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300..700&display=swap" rel="stylesheet">'
    "<style>* {font-family: 'Space Grotesk', sans-serif !important;} [data-testid='stSidebarNavLink'] span { font-size: 130% !important; } h1 { font-size: 36px !important; } h3 { font-size: 60px !important; } [data-testid='stSidebarNav']::before { content: 'Pracuj.PL Data Jobs'; display: block; font-size: 45px; font-weight: 700; padding: 5px 0px 20px; }</style>",
    unsafe_allow_html=True,
)

st.title("Historical Trends")

# Sidebar — dataset toggle
dataset = st.sidebar.radio("Dataset", ["IT Roles", "All Industries"])

# Load the selected CSV
if dataset == "IT Roles":
    df = load_history_roles()
    category_col = "kw_title"
    get_options_fn = get_history_role_options
    label = "Role"
else:
    df = load_history_industries()
    category_col = "mapped_industry"
    get_options_fn = get_history_industry_options
    label = "Industry"

# Handle missing CSV
if df is None:
    st.warning(
        "No historical data available yet. "
        "Run `python snapshot_history.py` after a scrape to start tracking trends."
    )
    st.stop()

if df.empty:
    st.info("History file exists but contains no data points.")
    st.stop()

# Sidebar — category filter
options = get_options_fn(df)
selected = st.sidebar.multiselect(f"Filter {label}", options, default=["All"])

# Filter dataframe
if "All" not in selected and len(selected) > 0:
    filtered_df = df[df[category_col].isin(selected)]
else:
    filtered_df = df

# Summary
n_dates = filtered_df["date"].nunique()
n_categories = filtered_df[category_col].nunique()
st.caption(f"Showing **{n_dates}** snapshots across **{n_categories}** categories")

# Chart
fig = make_trend_line(
    filtered_df,
    category_col=category_col,
    title=f"Job Count Over Time — {dataset}",
)
st.plotly_chart(fig, use_container_width=True)

# Data table
with st.expander("Show data table"):
    pivot = filtered_df.pivot_table(
        index="date", columns=category_col, values="job_count", aggfunc="sum"
    )
    pivot = pivot.sort_index(ascending=False)
    st.dataframe(pivot, use_container_width=True)
