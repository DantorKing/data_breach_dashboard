"""
pages/02_method_sector_association.py
---------------------------------------
Question this page answers: which sectors are most associated with each
breach method (e.g., is "inside job" more common in finance vs. web)?

Uses the shared sidebar filters from utils.py (year / sector / method /
sensitivity), plus page-specific controls to choose the metric, how the
heatmap is normalized, and how many sectors to show.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

import utils

utils.init_page("Method x Sector", icon="🔓")

st.title("🔓 Which sectors are most associated with each breach method?")
st.caption(
    "Comparing how breach methods -- hacks, inside jobs, lost devices, and "
    "so on -- show up differently from one sector to the next."
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
control_col1, control_col2, control_col3 = st.columns([2, 2, 1])
with control_col1:
    metric_choice = st.radio(
        "Measure by",
        ["Number of breaches", "Total records lost"],
        horizontal=True,
        key="page2_metric",
    )
with control_col2:
    view_choice = st.radio(
        "Show as",
        ["Share within sector (%)", "Raw totals"],
        horizontal=True,
        key="page2_view",
        help=(
            "Share within sector controls for sectors simply having more "
            "breaches overall, so you can fairly compare how common a "
            "method is from one sector to another."
        ),
    )
with control_col3:
    top_n = st.slider("Sectors to show", min_value=3, max_value=20, value=10, key="page2_top_n")

value_col = "breaches" if metric_choice == "Number of breaches" else "records_lost"

# Some entries list more than one sector, or more than one method (e.g. a
# breach logged as "hacked, poor security"). Splitting both out gives each
# sector/method combination proper credit instead of lumping combos together
# as their own category.
exploded = filtered.dropna(subset=["sector", "method"]).copy()

exploded["sector"] = exploded["sector"].str.split(",")
exploded = exploded.explode("sector")
exploded["sector"] = exploded["sector"].str.strip()

exploded["method"] = exploded["method"].str.split(",")
exploded = exploded.explode("method")
exploded["method"] = exploded["method"].str.strip()

if exploded.empty:
    st.warning("No breaches with both a sector and a method match the current filters.")
    st.stop()

combo = (
    exploded.groupby(["sector", "method"])
    .agg(records_lost=("records_lost", "sum"), breaches=("organisation", "count"))
    .reset_index()
)

# Keep the heatmap readable by only showing the sectors with the most overall activity
sector_totals = combo.groupby("sector")[value_col].sum().sort_values(ascending=False)
top_sectors = sector_totals.head(top_n).index.tolist()
combo_top = combo[combo["sector"].isin(top_sectors)]

pivot = combo_top.pivot_table(index="sector", columns="method", values=value_col, fill_value=0)
pivot = pivot.reindex(top_sectors)  # keep sectors ranked by overall activity

if view_choice == "Share within sector (%)":
    display_pivot = pivot.div(pivot.sum(axis=1), axis=0) * 100
    color_label = "% of sector's breaches"
    text_fmt = ".0f"
    color_scale = "Blues"
else:
    display_pivot = pivot
    color_label = "Records lost" if value_col == "records_lost" else "Number of breaches"
    text_fmt = ",.0f" if value_col == "records_lost" else ".0f"
    color_scale = "Reds"

# --- Chart 1: sector x method heatmap ---------------------------------------
st.subheader("Breach method mix by sector")
fig_heat = px.imshow(
    display_pivot,
    labels=dict(x="Method", y="Sector", color=color_label),
    color_continuous_scale=color_scale,
    text_auto=text_fmt,
    aspect="auto",
)
fig_heat.update_layout(height=max(350, 40 * len(top_sectors)))
st.plotly_chart(fig_heat, width='stretch')
if view_choice == "Share within sector (%)":
    st.caption(
        "Each row sums to 100%. Compare a single column (method) across rows "
        "(sectors) to see where that method is over- or under-represented."
    )

# --- Chart 2: drill into a single method ------------------------------------
st.subheader("Zoom in on one method")
method_options = sorted(exploded["method"].unique().tolist())
selected_method = st.selectbox("Breach method", method_options, key="page2_method")

method_slice = combo[combo["method"] == selected_method].sort_values(value_col, ascending=False).head(top_n)

fig_bar = px.bar(
    method_slice.sort_values(value_col),
    x=value_col,
    y="sector",
    orientation="h",
    color=value_col,
    color_continuous_scale=color_scale,
    labels={"records_lost": "Records lost", "breaches": "Number of breaches", "sector": "Sector"},
)
fig_bar.update_layout(coloraxis_showscale=False, yaxis_title="")
st.plotly_chart(fig_bar, width='stretch')
st.caption(f"Sectors ranked by **{metric_choice.lower()}** attributed to **{selected_method}**.")

# --- Supporting KPIs & table -------------------------------------------------
method_shares = exploded["method"].value_counts(normalize=True)
top_method_overall = method_shares.idxmax()

col1, col2, col3 = st.columns(3)
col1.metric("Breaches in view", f"{len(filtered):,}")
col2.metric("Methods in view", int(exploded["method"].nunique()))
col3.metric("Sectors in view", int(exploded["sector"].nunique()))

st.caption(
    f"Across the current filters, **{top_method_overall}** is the most common "
    f"breach method overall, showing up in {method_shares.max() * 100:.0f}% of "
    "tracked breaches."
)

with st.expander("See underlying sector x method totals"):
    st.dataframe(
        combo.rename(
            columns={
                "records_lost": "Records lost",
                "breaches": "Breaches",
                "sector": "Sector",
                "method": "Method",
            }
        ).sort_values(["Sector", "Method"]),
        width='stretch',
        hide_index=True,
    )
