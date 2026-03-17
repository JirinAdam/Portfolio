import streamlit as st
from data.loader import load_all_jobs, get_kw_title_options, get_salary_per_level
from components.charts import make_salary_bar

st.set_page_config(
    page_title="Salary by Seniority Level",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
