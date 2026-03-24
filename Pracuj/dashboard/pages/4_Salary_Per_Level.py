import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from data.loader import load_all_jobs, get_kw_title_options, get_salary_per_level
from components.charts import make_salary_bar

st.set_page_config(
    page_title="Salary by Seniority Level",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300..700&display=swap" rel="stylesheet">'
    "<style>* {font-family: 'Space Grotesk', sans-serif !important;} [data-testid='stSidebarNavLink'] span { font-size: 130% !important; } h1 { font-size: 36px !important; } h3 { font-size: 60px !important; } [data-testid='stSidebarNav']::before { content: 'Pracuj.PL Data Jobs'; display: block; font-size: 45px; font-weight: 700; padding: 5px 0px 20px; }</style>",
    unsafe_allow_html=True,
)

st.markdown("### Pracuj.PL Data Jobs")
st.title("Salary by Seniority Level")

df = load_all_jobs()

# Sidebar — filtr kw_title
kw_options = get_kw_title_options(df)
selected_kw = st.sidebar.selectbox("Job Role (kw_title)", kw_options)

# Toggle Median / Mean / Oba
view = st.radio("Display", ["Median", "Mean", "Both"], index=2, horizontal=True)

salary_df = get_salary_per_level(df, kw_title_filter=selected_kw)

show_median = view in ("Median", "Both")
show_mean = view in ("Mean", "Both")

fig = make_salary_bar(
    salary_df,
    x_col="level",
    title=f"Monthly Max Salary by Seniority Level (PLN) — {selected_kw}",
    show_median=show_median,
    show_mean=show_mean,
)
st.plotly_chart(fig, use_container_width=True)

st.caption(f"Based on **{salary_df['count'].sum():,}** job postings with salary data")
