import pandas as pd
import plotly.express as px
import streamlit as st

import utils

utils.init_page("Home", icon="🏠")

st.title("🌐 World's Biggest Data Breaches")
st.caption(
    "Dataset: Information is Beautiful - World's Biggest Data Breaches & Hacks"
)

df = utils.load_data()

if df is None:
    st.error(
        "No dataset found in the `data/` folder. Drop a `.csv` or `.xlsx` "
        "file in there and rerun the app."
    )
    st.stop()

filtered = utils.render_sidebar_filters(df)

st.markdown(
    """
Use the sidebar to filter by **year**, **sector**, **breach method**, and
**data sensitivity**. Your selections carry over to every page — open
**Sector Analysis** in the sidebar navigation for a deeper look.
"""
)

# --- KPI row -----------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Breaches", f"{len(filtered):,}")
col2.metric("Records lost", utils.format_number(filtered["records_lost"].sum()))
col3.metric("Sectors affected", int(filtered["sector"].nunique()))
if len(filtered):
    col4.metric("Years covered", f"{filtered['year'].min()}–{filtered['year'].max()}")
else:
    col4.metric("Years covered", "—")

st.divider()

# --- Overview chart ------------------------------------------------------
st.subheader("Breaches over time")

if filtered.empty:
    st.warning("No breaches match the current filters. Try widening them in the sidebar.")
else:
    yearly = (
        filtered.groupby("year", as_index=False)
        .agg(breaches=("organisation", "count"), records_lost=("records_lost", "sum"))
        .sort_values("year")
    )
    fig = px.bar(
        yearly,
        x="year",
        y="breaches",
        hover_data={"records_lost": ":,.0f"},
        labels={"year": "Year", "breaches": "Number of breaches"},
        title="Number of reported breaches per year",
    )
    fig.update_layout(xaxis=dict(dtick=1), bargap=0.15)
    st.plotly_chart(fig, width='stretch')

with st.expander("Preview filtered data"):
    st.dataframe(
        filtered.drop(columns=["story"], errors="ignore"),
        width='stretch',
    )
