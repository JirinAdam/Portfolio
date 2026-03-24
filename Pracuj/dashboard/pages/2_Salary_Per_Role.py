import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from data.loader import load_all_jobs, get_salary_per_kw_title
from components.charts import make_salary_bar

st.set_page_config(
    page_title="Salary by Job Role",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300..700&display=swap" rel="stylesheet">'
    "<style>* {font-family: 'Space Grotesk', sans-serif !important;} [data-testid='stSidebarNavLink'] span { font-size: 130% !important; } h1 { font-size: 36px !important; } h3 { font-size: 60px !important; } [data-testid='stSidebarNav']::before { content: 'Pracuj.PL Data Jobs'; display: block; font-size: 45px; font-weight: 700; padding: 5px 0px 20px; }" "</style>",
    unsafe_allow_html=True,
)

st.markdown("### Pracuj.PL Data Jobs")
st.title("Salary by Job Role")

df = load_all_jobs()

# Toggle Median / Mean / Oba
view = st.radio("Display", ["Median", "Mean", "Both"], index=2, horizontal=True)

salary_df = get_salary_per_kw_title(df)

show_median = view in ("Median", "Both")
show_mean = view in ("Mean", "Both")

fig = make_salary_bar(
    salary_df,
    x_col="kw_title",
    title="Monthly Max Salary by Job Role (PLN)",
    show_median=show_median,
    show_mean=show_mean,
)
st.plotly_chart(fig, use_container_width=True)

# Počet záznamů se salary daty
salary_count = len(df[df["monthly_max_salary"].notna() & (df["monthly_max_salary"] > 0)])
st.caption(f"Based on **{salary_count:,}** job postings with salary data")
