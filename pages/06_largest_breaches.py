"""
pages/06_largest_breaches.py
-------------------------------
Question this page answers: which are the 20 largest breaches by records lost,
and how do they compare on a log scale?

Uses the shared sidebar filters from utils.py (year / sector / method /
sensitivity), plus a page-specific toggle between linear and log scale.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

import utils

utils.init_page("Largest Breaches", icon="📊")

st.title("📊 The 20 largest data breaches ever recorded")
st.caption(
    "Ranked by records lost, with the option to view on a log scale so "
    "smaller entries in the top 20 don't get visually crushed."
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

# --- Page-specific controls -------------------------------------------------
scale_choice = st.radio(
    "Y-axis scale",
    ["Log", "Linear"],
    horizontal=True,
    key="page6_scale",
    help="Log scale makes it easier to compare breaches that differ by orders of magnitude.",
)

# --- Top 20 -----------------------------------------------------------------
top20 = filtered.sort_values("records_lost", ascending=False).head(20).copy()
# Short label for display
top20["label"] = top20["organisation"] + " (" + top20["year"].astype(str) + ")"

# --- Chart: horizontal bar, sorted ascending so the largest is at the top ---
st.subheader("Top 20 breaches ranked by records lost")
fig_bar = px.bar(
    top20.sort_values("records_lost"),
    x="records_lost",
    y="label",
    orientation="h",
    color="records_lost",
    color_continuous_scale="Reds",
    log_x=(scale_choice == "Log"),
    hover_data={
        "records_lost": ":,.0f",
        "sector": True,
        "method": True,
        "data_sensitivity": True,
    },
    labels={
        "records_lost": "Records lost",
        "label": "",
        "sector": "Sector",
        "method": "Method",
        "data_sensitivity": "Data sensitivity",
    },
)
fig_bar.update_layout(coloraxis_showscale=False, yaxis_title="")
st.plotly_chart(fig_bar, width='stretch')

# --- Chart 2: rank vs. records_lost on both scales --------------------------
st.subheader("Drop-off across the top 20")
top20_sorted = top20.sort_values("records_lost", ascending=False).reset_index(drop=True)
top20_sorted["rank"] = top20_sorted.index + 1

fig_line = px.line(
    top20_sorted,
    x="rank",
    y="records_lost",
    markers=True,
    hover_name="organisation",
    hover_data={"records_lost": ":,.0f", "year": True},
    labels={"rank": "Rank", "records_lost": "Records lost"},
)
fig_line.update_layout(xaxis=dict(tickmode="linear", dtick=1))
if scale_choice == "Log":
    fig_line.update_yaxes(type="log")

st.plotly_chart(fig_line, width='stretch')

# --- Supporting KPIs & table -------------------------------------------------
col1, col2, col3 = st.columns(3)
col1.metric("Largest breach", utils.format_number(top20["records_lost"].max()))
col2.metric("Smallest in top 20", utils.format_number(top20["records_lost"].min()))
col3.metric(
    "Median records lost",
    utils.format_number(top20["records_lost"].median()),
)

with st.expander("See full top 20 table"):
    display = top20_sorted.rename(
        columns={
            "rank": "Rank",
            "organisation": "Organisation",
            "year": "Year",
            "records_lost": "Records lost",
            "sector": "Sector",
            "method": "Method",
            "data_sensitivity": "Sensitivity",
        }
    )[
        [
            "Rank",
            "Organisation",
            "Year",
            "Records lost",
            "Sector",
            "Method",
            "Sensitivity",
        ]
    ]
    st.dataframe(display, width='stretch', hide_index=True)
