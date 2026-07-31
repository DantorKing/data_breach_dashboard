"""
pages/01_page.py
-----------------
Question this page answers: which sectors have been hit hardest by data
breaches, and how has that shifted year over year?

Uses the shared sidebar filters from utils.py (year / sector / method /
sensitivity), plus a page-specific control to choose the ranking metric and
how many sectors to show.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

import utils

utils.init_page("Sector Analysis", icon="🏭")

st.title("🏭 Which sectors are hit hardest?")
st.caption(
    "Ranking sectors by breach impact, and tracking how the leaders have "
    "changed over time."
)

df = utils.load_data()
if df is None:
    st.error(
        "No dataset found in the `data/` folder. Drop a `.csv` or `.xlsx` "
        "file in there and rerun the app."
    )
    st.stop()

filtered = utils.render_sidebar_filters(df)

if filtered.empty:
    st.warning("No breaches match the current filters. Try widening them in the sidebar.")
    st.stop()

# --- Page-specific filter -------------------------------------------------
control_col1, control_col2 = st.columns([2, 1])
with control_col1:
    metric_choice = st.radio(
        "Rank sectors by",
        ["Total records lost", "Number of breaches"],
        horizontal=True,
        key="page1_metric",
    )
with control_col2:
    top_n = st.slider("Sectors to show", min_value=3, max_value=15, value=8, key="page1_top_n")

value_col = "records_lost" if metric_choice == "Total records lost" else "breaches"

# Some entries list more than one sector (e.g. "tech, health"). Splitting
# these out gives each sector proper credit instead of lumping combos
# together as their own category.
exploded = filtered.assign(sector=filtered["sector"].str.split(","))
exploded = exploded.explode("sector")
exploded["sector"] = exploded["sector"].str.strip()

sector_totals = (
    exploded.groupby("sector")
    .agg(records_lost=("records_lost", "sum"), breaches=("organisation", "count"))
    .reset_index()
)
sector_totals = sector_totals.sort_values(value_col, ascending=False).head(top_n)
top_sectors = sector_totals["sector"].tolist()

# --- Chart 1: ranking ------------------------------------------------------
st.subheader(f"Top {len(top_sectors)} sectors by {metric_choice.lower()}")
fig_bar = px.bar(
    sector_totals.sort_values(value_col),
    x=value_col,
    y="sector",
    orientation="h",
    color=value_col,
    color_continuous_scale="Reds",
    labels={"records_lost": "Records lost", "breaches": "Number of breaches", "sector": "Sector"},
)
fig_bar.update_layout(coloraxis_showscale=False, yaxis_title="")
st.plotly_chart(fig_bar, width='stretch')

# --- Chart 2: trend over time for the top sectors -------------------------
st.subheader("How these sectors evolved over time")
trend = (
    exploded[exploded["sector"].isin(top_sectors)]
    .groupby(["year", "sector"])
    .agg(records_lost=("records_lost", "sum"), breaches=("organisation", "count"))
    .reset_index()
)
fig_area = px.area(
    trend,
    x="year",
    y=value_col,
    color="sector",
    labels={"year": "Year", "records_lost": "Records lost", "breaches": "Number of breaches"},
)
fig_area.update_layout(xaxis=dict(dtick=1))
st.plotly_chart(fig_area, width='stretch')

# --- Supporting KPIs & table ----------------------------------------------
col1, col2, col3 = st.columns(3)
col1.metric("Breaches in view", f"{len(filtered):,}")
col2.metric("Records lost in view", utils.format_number(filtered["records_lost"].sum()))
col3.metric("Sectors in view", int(exploded["sector"].nunique()))

with st.expander("See underlying sector totals"):
    st.dataframe(
        sector_totals.rename(
            columns={"records_lost": "Records lost", "breaches": "Breaches", "sector": "Sector"}
        ),
        width='stretch',
        hide_index=True,
    )
