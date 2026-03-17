import streamlit as st
from data.loader import load_all_jobs, get_kw_title_options, get_jobs_per_region
from components.charts import make_jobs_bar

st.set_page_config(
    page_title="Job Postings by Region",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Job Postings by Region")

df = load_all_jobs()

# Sidebar — filtr kw_title
kw_options = get_kw_title_options(df)
selected_kw = st.sidebar.selectbox("Job Role (kw_title)", kw_options)

# Filtrovaný počet
if selected_kw == "All":
    total = len(df)
else:
    total = len(df[df["kw_title"] == selected_kw])

st.caption(f"Showing **{total:,}** job postings")

jobs_df = get_jobs_per_region(df, kw_title_filter=selected_kw)

fig = make_jobs_bar(
    jobs_df,
    title=f"Job Postings by Region — {selected_kw}",
)
st.plotly_chart(fig, use_container_width=True)
