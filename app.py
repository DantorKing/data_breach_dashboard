import streamlit as st

# Page config + CSS — applied ONCE here; app.py runs on every page switch
st.set_page_config(page_title="Data Breaches", page_icon="💽",
                   layout="wide", initial_sidebar_state="expanded")



# ─────────────────────────────────────────────────────────────────────────────
# Register your new page below
# ─────────────────────────────────────────────────────────────────────────────
pg = st.navigation([
    st.Page("pages/001_introduction.py",
            title="Introduction",   icon="📘"),
    st.Page("pages/00_breaches.py",
            title="Data Breaches",   icon="🌐"),
    st.Page("pages/01_sector.py",
            title="Sector Analysis",   icon="🏭"),
    st.Page("pages/02_method_sector_association.py",
            title="Method x Sector", icon="🔓"),
    st.Page("pages/03_source.py",
            title="Source Analysis", icon="📰"),
    st.Page("pages/04_interesting_story.py",
            title="Interesting Stories", icon="📖"),
    st.Page("pages/05_repeat_offenders.py",
            title="Repeat Offenders", icon="🔁"),
    st.Page("pages/06_largest_breaches.py",
            title="Largest Breaches", icon="📊"),
    st.Page("pages/07_sensitivity_trend.py",
            title="Sensitivity Trend", icon="🔥"),
    st.Page("pages/08_country.py",
            title="Country Analysis", icon="🌍"),

])
pg.run()
