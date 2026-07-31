"""
pages/03_source_severity.py
------------------------------
Question this page answers: which news/media sources report the most
breaches in the dataset, and does that correlate with breach severity?

Uses the shared sidebar filters from utils.py (year / sector / method /
sensitivity), plus page-specific controls to choose the ranking metric,
how many sources to show, and a noise-reduction threshold for the
correlation check.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

import utils

utils.init_page("Source Analysis", icon="📰")

st.title("📰 Which sources report the most breaches -- and does it track severity?")
st.caption(
    "Ranking the outlets that most often break data-breach stories, then "
    "checking whether the most prolific reporters tend to cover more, or "
    "less, severe incidents."
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
control_col1, control_col2, control_col3 = st.columns([2, 1, 2])
with control_col1:
    metric_choice = st.radio(
        "Rank sources by",
        ["Number of breaches reported", "Total records covered"],
        horizontal=True,
        key="page3_metric",
    )
with control_col2:
    top_n = st.slider("Sources to show", min_value=5, max_value=30, value=15, key="page3_top_n")
with control_col3:
    min_breaches = st.slider(
        "Min. breaches for severity check",
        min_value=1,
        max_value=10,
        value=2,
        key="page3_min_breaches",
        help=(
            "Sources cited only once or twice add noise to the severity "
            "comparison below; raise this to focus on more established outlets."
        ),
    )

value_col = "breaches" if metric_choice == "Number of breaches reported" else "records_lost"

# --- Cleaning: split multi-source citations, standardize known duplicates --
# A handful of rows credit more than one outlet (comma- or semicolon-
# separated, e.g. "USA Today; Reuters"), and the same outlet is often
# spelled several different ways in the raw data (typos, abbreviations,
# spacing). Left alone, that would split one outlet's count across several
# rows and understate how much it actually reports. The aliases below only
# cover variants common enough to affect the ranking; everything else is
# left as-is.
SOURCE_ALIASES = {
    "beeping computer": "Bleeping Computer",
    "bleepingcomputer": "Bleeping Computer",
    "techcrunch": "TechCrunch",
    "tech crunch": "TechCrunch",
    "zd net": "ZDNet",
    "zdnet": "ZDNet",
    "guardian": "The Guardian",
    "the guardian": "The Guardian",
    "have i been pwned": "Have I Been Pwned",
    "haveibeenpwned": "Have I Been Pwned",
    "bbc": "BBC News",
    "bbc news": "BBC News",
    "nbc": "NBC News",
    "nbc news": "NBC News",
    "abc": "ABC News",
    "abc news": "ABC News",
    "cnet": "CNET",
    "krebs on security": "Krebs on Security",
    "krebson security": "Krebs on Security",
    "krebsonsecurity": "Krebs on Security",
    "ars technica": "Ars Technica",
    "arsetechnia": "Ars Technica",
    "ny times": "The New York Times",
    "nytimes": "The New York Times",
    "new york times": "The New York Times",
    "nyt": "The New York Times",
    "wall st journal": "The Wall Street Journal",
    "wall street journal": "The Wall Street Journal",
    "wsj": "The Wall Street Journal",
    "pc world": "PC World",
    "pcworld": "PC World",
}

exploded = filtered.dropna(subset=["source_name"]).copy()
exploded["source_name"] = exploded["source_name"].str.split(r"[,;]", regex=True)
exploded = exploded.explode("source_name")
exploded["source_name"] = exploded["source_name"].str.strip()
exploded = exploded[exploded["source_name"] != ""]
exploded["source_name"] = (
    exploded["source_name"].str.lower().map(SOURCE_ALIASES).fillna(exploded["source_name"])
)
exploded["data_sensitivity"] = pd.to_numeric(exploded["data_sensitivity"], errors="coerce")

if exploded.empty:
    st.warning("No breaches with a listed source match the current filters.")
    st.stop()

source_stats = (
    exploded.groupby("source_name")
    .agg(
        breaches=("organisation", "count"),
        records_lost=("records_lost", "sum"),
        avg_severity=("data_sensitivity", "mean"),
    )
    .reset_index()
)

ranked = source_stats.sort_values(value_col, ascending=False).head(top_n)

# --- Chart 1: most active reporting sources ---------------------------------
st.subheader(f"Top {len(ranked)} sources by {metric_choice.lower()}")
fig_bar = px.bar(
    ranked.sort_values(value_col),
    x=value_col,
    y="source_name",
    orientation="h",
    color=value_col,
    color_continuous_scale="Purples",
    labels={
        "records_lost": "Records covered",
        "breaches": "Number of breaches",
        "source_name": "Source",
    },
)
fig_bar.update_layout(coloraxis_showscale=False, yaxis_title="")
st.plotly_chart(fig_bar, width='stretch')
st.caption(
    "Source names are lightly standardized (e.g. 'Beeping Computer' / "
    "'BleepingComputer' -> 'Bleeping Computer') to avoid splitting one "
    "outlet's count across spelling variants."
)

# --- Chart 2: does reporting volume track severity? -------------------------
st.subheader("Reporting volume vs. average severity")
qualifying = source_stats[source_stats["breaches"] >= min_breaches].dropna(subset=["avg_severity"])

if len(qualifying) < 3:
    st.info(
        "Not enough sources meet the minimum-breaches threshold to check this "
        "relationship. Try lowering it in the controls above."
    )
else:
    corr = qualifying["breaches"].corr(qualifying["avg_severity"])

    fig_scatter = px.scatter(
        qualifying,
        x="breaches",
        y="avg_severity",
        size="records_lost",
        color="avg_severity",
        color_continuous_scale="Reds",
        hover_name="source_name",
        labels={
            "breaches": "Breaches reported by this source",
            "avg_severity": "Average severity (1-5 data sensitivity scale)",
            "records_lost": "Records covered",
        },
    )
    fig_scatter.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig_scatter, width='stretch')

    abs_r = abs(corr) if pd.notna(corr) else 0
    if abs_r < 0.1:
        strength = "negligible"
    elif abs_r < 0.3:
        strength = "weak"
    elif abs_r < 0.5:
        strength = "moderate"
    else:
        strength = "strong"
    direction = "positive" if corr > 0 else "negative" if corr < 0 else "no"

    st.caption(
        f"Across the {len(qualifying)} sources with at least {min_breaches} tracked "
        f"breach(es), the correlation between reporting volume and average severity "
        f"is **r = {corr:.2f}** -- a **{strength} {direction}** relationship. "
        "Severity uses the dataset's own 1-5 data-sensitivity scale, where higher "
        "means more sensitive data was exposed (5 = full personal details, "
        "1 = just an email address)."
    )

# --- Supporting KPIs & table -------------------------------------------------
col1, col2, col3 = st.columns(3)
col1.metric("Sources in view", int(exploded["source_name"].nunique()))
col2.metric("Breaches in view", f"{len(filtered):,}")
overall_avg_severity = exploded["data_sensitivity"].mean()
col3.metric(
    "Avg. severity across all breaches",
    f"{overall_avg_severity:.2f} / 5" if pd.notna(overall_avg_severity) else "N/A",
)

with st.expander("See underlying source totals"):
    st.dataframe(
        source_stats.rename(
            columns={
                "source_name": "Source",
                "breaches": "Breaches",
                "records_lost": "Records covered",
                "avg_severity": "Avg. severity (1-5)",
            }
        ).sort_values("Breaches", ascending=False),
        width='stretch',
        hide_index=True,
    )
