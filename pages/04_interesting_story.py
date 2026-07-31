"""
pages/04_interesting_story.py
-------------------------------
Question this page answers: what's the year-by-year count of breaches flagged
as an "interesting story," and does that align with the biggest or most
sensitive breaches?

Uses the shared sidebar filters from utils.py (year / sector / method /
sensitivity), plus a page-specific control to toggle between absolute counts
and percentages.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

import utils

utils.init_page("Interesting Stories", icon="📖")

st.title("📖 Do 'interesting story' breaches track the biggest incidents?")
st.caption(
    "Breaches flagged as an 'interesting story' -- year by year counts, "
    "and whether those years also saw the largest or most sensitive breaches."
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
control_col1, control_col2 = st.columns([2, 1])
with control_col1:
    view_choice = st.radio(
        "Show interesting stories as",
        ["Count per year", "% of yearly breaches"],
        horizontal=True,
        key="page4_view",
    )
# with control_col2:
#     top_n = st.slider("Top N years to highlight", min_value=3, max_value=15, value=5, key="page4_top_n")

# --- Aggregate per year -----------------------------------------------------
yearly = (
    filtered.groupby("year", as_index=False)
    .agg(
        total_breaches=("organisation", "count"),
        interesting=("is_notable", "sum"),
        records_lost=("records_lost", "sum"),
        avg_sensitivity=("data_sensitivity", "mean"),
    )
    .sort_values("year")
)
yearly["pct_interesting"] = (yearly["interesting"] / yearly["total_breaches"] * 100).fillna(0)

value_col = "interesting" if view_choice == "Count per year" else "pct_interesting"
ylabel = (
    "Interesting story breaches"
    if view_choice == "Count per year"
    else "% of breaches that are interesting stories"
)

# --- Chart 1: interesting stories over time ---------------------------------
st.subheader("Interesting story breaches year by year")
fig_bar = px.bar(
    yearly,
    x="year",
    y=value_col,
    hover_data={
        "total_breaches": True,
        "interesting": True,
        "records_lost": ":,.0f",
        "avg_sensitivity": ":.2f",
    },
    labels={"year": "Year", value_col: ylabel},
)
fig_bar.update_layout(xaxis=dict(dtick=1), bargap=0.15)
st.plotly_chart(fig_bar, width='stretch')

# --- Chart 2: interesting count vs. record scale ----------------------------
st.subheader("Do interesting stories coincide with the biggest breaches?")
corr_records = yearly["interesting"].corr(yearly["records_lost"])
fig_scatter = px.scatter(
    yearly,
    x="interesting",
    y="records_lost",
    size="total_breaches",
    hover_name="year",
    trendline="ols",
    labels={
        "interesting": "Interesting story breaches",
        "records_lost": "Total records lost",
        "total_breaches": "Total breaches that year",
    },
)
st.plotly_chart(fig_scatter, width='stretch')

abs_r = abs(corr_records) if pd.notna(corr_records) else 0
if abs_r < 0.1:
    strength = "negligible"
elif abs_r < 0.3:
    strength = "weak"
elif abs_r < 0.5:
    strength = "moderate"
else:
    strength = "strong"
direction = "positive" if corr_records > 0 else "negative" if corr_records < 0 else "no"
st.caption(
    f"Correlation: **r = {corr_records:.2f}** -- a **{strength} {direction}** "
    "relationship between how many interesting stories ran in a year and "
    "how many records were lost that year."
)

# --- Chart 3: interesting count vs. sensitivity ----------------------------
st.subheader("Do interesting stories track the most sensitive breaches?")
corr_sens = yearly["interesting"].corr(yearly["avg_sensitivity"])
fig_scatter2 = px.scatter(
    yearly,
    x="interesting",
    y="avg_sensitivity",
    size="total_breaches",
    hover_name="year",
    trendline="ols",
    labels={
        "interesting": "Interesting story breaches",
        "avg_sensitivity": "Average data sensitivity (1-5)",
        "total_breaches": "Total breaches that year",
    },
)
st.plotly_chart(fig_scatter2, width='stretch')

abs_r2 = abs(corr_sens) if pd.notna(corr_sens) else 0
if abs_r2 < 0.1:
    strength2 = "negligible"
elif abs_r2 < 0.3:
    strength2 = "weak"
elif abs_r2 < 0.5:
    strength2 = "moderate"
else:
    strength2 = "strong"
direction2 = "positive" if corr_sens > 0 else "negative" if corr_sens < 0 else "no"
st.caption(
    f"Correlation: **r = {corr_sens:.2f}** -- a **{strength2} {direction2}** "
    "relationship between interesting-story count and data sensitivity. "
    "Sensitivity uses the dataset's own 1-5 scale (5 = full personal details, "
    "1 = email address only)."
)

# --- Supporting KPIs & table -------------------------------------------------
interesting_only = filtered[filtered["is_notable"]]
col1, col2, col3 = st.columns(3)
col1.metric("Interesting stories in view", f"{int(yearly['interesting'].sum()):,}")
col2.metric("Total breaches in view", f"{int(yearly['total_breaches'].sum()):,}")
avg_sens_interesting = interesting_only["data_sensitivity"].mean()
col3.metric(
    "Avg. sensitivity of interesting stories",
    f"{avg_sens_interesting:.2f} / 5" if pd.notna(avg_sens_interesting) else "N/A",
)

with st.expander("See yearly breakdown"):
    display = yearly.rename(
        columns={
            "year": "Year",
            "total_breaches": "Total breaches",
            "interesting": "Interesting stories",
            "pct_interesting": "% interesting",
            "records_lost": "Records lost",
            "avg_sensitivity": "Avg. sensitivity",
        }
    )
    display["% interesting"] = display["% interesting"].round(1)
    st.dataframe(display, width='stretch', hide_index=True)
