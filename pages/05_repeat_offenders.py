"""
pages/05_repeat_offenders.py
-------------------------------
Question this page answers: which organisations appear more than once in the
dataset, and how do their cumulative records lost compare?

Uses the shared sidebar filters from utils.py (year / sector / method /
sensitivity), plus a page-specific control to choose how many offenders to
display and to drill into a single organisation's breach timeline.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

import utils

utils.init_page("Repeat Offenders", icon="🔁")

st.title("🔁 Which organisations get breached again and again?")
st.caption(
    "Organisations that show up more than once in the dataset, ranked by "
    "cumulative records lost across all their incidents."
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

# --- Aggregate per organisation ---------------------------------------------
org_stats = (
    filtered.groupby("organisation")
    .agg(
        breaches=("organisation", "count"),
        total_records=("records_lost", "sum"),
        avg_records=("records_lost", "mean"),
        avg_sensitivity=("data_sensitivity", "mean"),
        first_year=("year", "min"),
        last_year=("year", "max"),
    )
    .reset_index()
    .sort_values("breaches", ascending=False)
)
org_stats["span"] = org_stats["last_year"] - org_stats["first_year"] + 1

repeat = org_stats[org_stats["breaches"] > 1].copy()
repeat = repeat.sort_values("total_records", ascending=False)

if repeat.empty:
    st.info("No repeat offenders match the current filters. Try widening them in the sidebar.")
    st.stop()

n_repeat = len(repeat)

# --- Page-specific controls -------------------------------------------------
control_col1, control_col2 = st.columns([2, 1])
with control_col1:
    labels = {5: "5", 10: "10", 15: "15", 20: "20", n_repeat: f"All ({n_repeat})"}
    choices = [5, 10, 15, 20, n_repeat]
    valid = [c for c in choices if c <= n_repeat]
    chosen = st.selectbox(
        "Offenders to show",
        options=valid,
        index=max(len(valid) - 1, 0),
        format_func=lambda x: labels[x],
        key="page5_top_n",
    )
    top_n = chosen
    if len(valid) == 1 and valid[0] < choices[0]:
        st.info("Only one repeat offender matches. Widen the sidebar filters to see more options.")
with control_col2:
    metric_choice = st.radio(
        "Rank by",
        ["Cumulative records lost", "Number of breaches"],
        horizontal=True,
        key="page5_metric",
    )

value_col = "total_records" if metric_choice == "Cumulative records lost" else "breaches"
ylabel = "Cumulative records lost" if metric_choice == "Cumulative records lost" else "Number of breaches"

ranked = repeat.head(top_n)

# --- Chart 1: cumulative records per repeat offender ------------------------
st.subheader(f"Top {len(ranked)} repeat offenders by {metric_choice.lower()}")
fig_bar = px.bar(
    ranked.sort_values(value_col),
    x=value_col,
    y="organisation",
    orientation="h",
    color=value_col,
    color_continuous_scale="Oranges",
    hover_data={
        "breaches": True,
        "total_records": ":,.0f",
        "avg_sensitivity": ":.2f",
        "span": True,
    },
    labels={
        "total_records": "Cumulative records lost",
        "breaches": "Number of breaches",
        "organisation": "Organisation",
        "avg_sensitivity": "Avg. sensitivity",
        "span": "Years between first and last breach",
    },
)
fig_bar.update_layout(coloraxis_showscale=False, yaxis_title="")
st.plotly_chart(fig_bar, width='stretch')

# --- Chart 2: breach count vs. cumulative records ---------------------------
st.subheader("More breaches, more records?")
fig_scatter = px.scatter(
    repeat,
    x="breaches",
    y="total_records",
    size="avg_sensitivity",
    hover_name="organisation",
    trendline="ols",
    labels={
        "breaches": "Number of breaches",
        "total_records": "Cumulative records lost",
        "avg_sensitivity": "Avg. sensitivity (1-5)",
    },
)
st.plotly_chart(fig_scatter, width='stretch')

corr_val = repeat["breaches"].corr(repeat["total_records"]).round(3)
st.caption(
    f"Correlation between breach count and cumulative records lost: **r = {corr_val}**."
)

# --- Chart 3: drill into a single organisation ------------------------------
st.subheader("Breach timeline for one organisation")
org_options = sorted(repeat["organisation"].tolist())
selected_org = st.selectbox("Organisation", org_options, key="page5_org")

org_breaches = filtered[filtered["organisation"] == selected_org].sort_values("year")

fig_timeline = px.bar(
    org_breaches,
    x="year",
    y="records_lost",
    color="records_lost",
    color_continuous_scale="Oranges",
    hover_data={
        "records_lost": ":,.0f",
        "method": True,
        "sector": True,
        "data_sensitivity": True,
    },
    labels={
        "year": "Year",
        "records_lost": "Records lost",
        "method": "Breach method",
        "sector": "Sector",
        "data_sensitivity": "Data sensitivity (1-5)",
    },
    title=f"{selected_org} — each bar is one breach",
)
fig_timeline.update_layout(xaxis=dict(dtick=1), coloraxis_showscale=False)
st.plotly_chart(fig_timeline, width='stretch')

# --- Supporting KPIs & table -------------------------------------------------
col1, col2, col3 = st.columns(3)
col1.metric("Repeat offenders in view", f"{len(repeat)}")
col2.metric("Total breaches by repeat offenders", f"{int(repeat['breaches'].sum()):,}")
col3.metric(
    "Cumulative records lost",
    utils.format_number(repeat["total_records"].sum()),
)

with st.expander("See all repeat offenders"):
    display = repeat.rename(
        columns={
            "organisation": "Organisation",
            "breaches": "Breaches",
            "total_records": "Cumulative records lost",
            "avg_records": "Avg. records per breach",
            "avg_sensitivity": "Avg. sensitivity",
            "first_year": "First breach",
            "last_year": "Last breach",
            "span": "Years active",
        }
    )
    display = display.sort_values("Cumulative records lost", ascending=False)
    st.dataframe(display, width='stretch', hide_index=True)
