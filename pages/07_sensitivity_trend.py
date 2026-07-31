"""
pages/07_sensitivity_trend.py
-------------------------------
Question this page answers: is there a trend in data sensitivity level over
time — are breaches involving more sensitive data (health records, full
details) becoming more or less common?

Uses the shared sidebar filters from utils.py (year / sector / method /
sensitivity), plus a page-specific control to toggle between average
sensitivity and the share of high-severity breaches.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

import utils

utils.init_page("Sensitivity Trend", icon="🔥")

st.title("🔥 Are data breaches getting more sensitive?")
st.caption(
    "Tracking the average data-sensitivity level over time, and whether "
    "breaches exposing health records, full personal details, etc. are "
    "becoming more or less common."
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
view_choice = st.radio(
    "Measure",
    ["Average sensitivity (1-5)", "Share of high-sensitivity breaches (4-5)"],
    horizontal=True,
    key="page7_view",
)

# --- Aggregate per year -----------------------------------------------------
yearly = (
    filtered.groupby("year", as_index=False)
    .agg(
        total=("organisation", "count"),
        avg_sensitivity=("data_sensitivity", "mean"),
        med_sensitivity=("data_sensitivity", "median"),
    )
    .sort_values("year")
)
# Share of breaches with sensitivity >= 4
sens_counts = (
    filtered.assign(high_sens=filtered["data_sensitivity"].ge(4))
    .groupby("year", as_index=False)
    .agg(
        total=("organisation", "count"),
        high_sens=("high_sens", "sum"),
    )
)
sens_counts["share_high"] = sens_counts["high_sens"] / sens_counts["total"] * 100
yearly = yearly.merge(sens_counts[["year", "share_high"]], on="year")

# --- Chart 1: average sensitivity over time ---------------------------------
st.subheader("Year-by-year trend")

if view_choice == "Average sensitivity (1-5)":
    value_col = "avg_sensitivity"
    ylabel = "Average data sensitivity (1-5)"
    hover_fmt = ":.2f"
else:
    value_col = "share_high"
    ylabel = "% of breaches with sensitivity 4-5"
    hover_fmt = ".1f"

fig_line = px.line(
    yearly,
    x="year",
    y=value_col,
    markers=True,
    hover_data={"total": True},
    labels={"year": "Year", value_col: ylabel, "total": "Breaches that year"},
)
fig_line.update_layout(xaxis=dict(dtick=1))
st.plotly_chart(fig_line, width='stretch')

# Sliding-window average for smoother trend signal
yearly["smooth"] = yearly[value_col].rolling(3, min_periods=1, center=True).mean()
fig_smooth = px.line(
    yearly,
    x="year",
    y="smooth",
    markers=True,
    hover_data={value_col: hover_fmt, "total": True},
    labels={"year": "Year", "smooth": f"{ylabel} (3-year centred average)", "total": "Breaches"},
)
fig_smooth.update_layout(xaxis=dict(dtick=1))
st.plotly_chart(fig_smooth, width='stretch')
st.caption("3-year centred rolling average to smooth out year-to-year noise.")

# --- Chart 2: distribution of sensitivity levels over time ------------------
st.subheader("How the mix of sensitivity levels has shifted")
levelled = (
    filtered.groupby(["year", "sensitivity_label"], as_index=False)
    .size()
    .rename(columns={"size": "count"})
)
levelled["sensitivity_label"] = pd.Categorical(
    levelled["sensitivity_label"],
    categories=sorted(levelled["sensitivity_label"].unique()),
    ordered=True,
)
fig_area = px.area(
    levelled,
    x="year",
    y="count",
    color="sensitivity_label",
    category_orders={
        "sensitivity_label": [
            "1 - Email / online info",
            "2 - SSN / personal details",
            "3 - Credit card info",
            "4 - Health & other personal records",
            "5 - Full details",
        ]
    },
    labels={
        "year": "Year",
        "count": "Number of breaches",
        "sensitivity_label": "Data sensitivity",
    },
)
fig_area.update_layout(xaxis=dict(dtick=1))
st.plotly_chart(fig_area, width='stretch')

# --- Supporting KPIs & table -------------------------------------------------
corr_year = yearly["year"].corr(yearly[value_col])
col1, col2, col3 = st.columns(3)
col1.metric("Years covered", f"{int(yearly['year'].min())}–{int(yearly['year'].max())}")
col2.metric(
    "Overall avg. sensitivity",
    f"{filtered['data_sensitivity'].mean():.2f} / 5",
)
col3.metric(
    "Year-over-year trend",
    f"r = {corr_year:.2f} ({'rising' if corr_year > 0.1 else 'falling' if corr_year < -0.1 else 'flat'})",
)

with st.expander("See yearly breakdown"):
    display = yearly.rename(
        columns={
            "year": "Year",
            "total": "Total breaches",
            "avg_sensitivity": "Avg. sensitivity",
            "med_sensitivity": "Median sensitivity",
            "share_high": "% high (4-5)",
        }
    )
    display["% high (4-5)"] = display["% high (4-5)"].round(1)
    display["Avg. sensitivity"] = display["Avg. sensitivity"].round(2)
    st.dataframe(display, width='stretch', hide_index=True)
