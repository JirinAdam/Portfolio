import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from data.loader import load_all_jobs, get_kw_title_options, get_skills_counts
from components.charts import make_skills_bar

st.set_page_config(
    page_title="Pracuj.PL Data Jobs",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300..700&display=swap" rel="stylesheet">'
    "<style>"
    "* {font-family: 'Space Grotesk', sans-serif !important;}"
    "[data-testid='stSidebarNavLink'] span { font-size: 130% !important; }"
    "h1 { font-size: 36px !important; }"
    "</style>",
    unsafe_allow_html=True,
)

st.title("Top Skills in Data Jobs")

df = load_all_jobs()

# Sidebar — filtr kw_title
kw_options = get_kw_title_options(df)
selected_kw = st.sidebar.selectbox("Job Role (kw_title)", kw_options)

# Filtrovaný počet záznamů
if selected_kw == "All":
    filtered_df = df
else:
    filtered_df = df[df["kw_title"] == selected_kw]

st.caption(f"Analyzing **{len(filtered_df):,}** job postings")

# Skills data
skills = get_skills_counts(df, kw_title_filter=selected_kw)

# Bar chart — Top 20
fig = make_skills_bar(skills, top_n=20, title=f"Top 20 Skills — {selected_kw}")
st.plotly_chart(fig, use_container_width=True)

# Expander — kompletní tabulka
with st.expander("Show full skills table"):
    skills_df = skills.reset_index()
    skills_df.columns = ["Skill", "Count"]
    skills_df.index = range(1, len(skills_df) + 1)
    st.dataframe(skills_df, use_container_width=True)
