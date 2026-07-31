"""
pages/09_introduction.py
------------------------
Landing / "about" page: introduces the dataset, its structure, and the
approach used across every visualization in this app.
"""

import streamlit as st

import utils

utils.init_page("Introduction", icon="📘")

st.title("📘 World's Biggest Data Breaches")
st.caption("An interactive dashboard built with Streamlit + Plotly")

# ---------------------------------------------------------------------------
# 1. About the dataset
# ---------------------------------------------------------------------------
st.header("The dataset")
st.markdown(
    """
    **Source:** *[Information is Beautiful — World's Biggest Data Breaches &
    Hacks](https://informationisbeautiful.net/visualizations/worlds-biggest-data-breaches-hacks/)*,
    a well-known curated dataset tracking major data breaches going back
    decades. The version bundled in `data/` is the latest release.

    Each row is **one breach**: an organisation, the year it happened, how many
    records were lost, which sector it belongs to, how it was breached, and how
    sensitive the exposed data was. It is a *journalistic collection*, not a
    government register — it documents big, publicly-reported incidents rather
    than every breach that has ever occurred.
    """
)

with st.expander("Column by column"):
    st.markdown(
        """
        | Column | Meaning |
        |---|---|
        | `organisation` | Name of the breached organisation |
        | `records_lost` | Records exposed (parsed to a number, see below) |
        | `year` / `date` | When the breach was reported / happened |
        | `sector` | 25 industry sectors, e.g. *healthcare*, *tech* |
        | `method` | How it happened, e.g. *hacked*, *poor security*, *inside job* |
        | `data_sensitivity` | Source's own 1–5 scale of how sensitive the leaked data is |
        | `interesting_story` | Flag for the breaches the source calls out as notable |
        | `story` | A plain-language narrative of what happened |
        | `source_name` + links | Where the information was verified from |
        """
    )

# ---------------------------------------------------------------------------
# 2. How the data is prepared
# ---------------------------------------------------------------------------
st.header("How the data is prepared")
st.markdown(
    """
    The raw workbook was built for humans to read, not machines. Before
    anything is charted (`utils.py`) we:

    - **Normalize columns** to consistent snake_case names and drop the
      leftover Excel legend/spacer rows.
    - **Parse messy record counts** — values like `2,400,00` or `53;000` are
      cleaned into real numbers so they can be summed and compared.
    - **Map the sensitivity scale** (1 → "email / online info" … 5 → "full
      details") into readable labels.
    - **Expose a shared filter panel** in the sidebar (year, sector, method,
      sensitivity). Your selections persist as you move between pages, so every
      chart always answers the same question against the same subset of data.
    """
)

# ---------------------------------------------------------------------------
# 3. The visualization approach
# ---------------------------------------------------------------------------
st.header("The visualization approach")
st.markdown(
    """
    This app doesn't try to show the whole dataset at once — each page is
    built around **one question** and picks the chart that answers it best:

    | Page | Question | Approach |
    |---|---|---|
    | Sector Analysis | Where do breaches cluster by industry? | Bar + treemap by sector |
    | Method x Sector | Do certain methods hit certain sectors? | Cross-tab heatmap |
    | Source Analysis | How reliable is the reporting? | Breakdown by source |
    | Interesting Stories | What is a "notable" breach? | Comparisons of flagged rows |
    | Repeat Offenders | Which organisations keep getting hit? | Multi-breach ranking |
    | Largest Breaches | Which single breaches were enormous? | Log-scale ranking |
    | Sensitivity Trend | Is leaked data getting more sensitive? | Time series by sensitivity |
    | Country Analysis | Which countries are most affected? | Choropleth + bar chart |

    Two conventions appear throughout:

    - **The sidebar filter is the lens.** Every chart on every page respects
      the same filters, so "healthcare in 2020+" or "only hacked breaches" is
      one click away.
    - **Honest about uncertainty.** Where the data is ambiguous — most notably
      *Country Analysis*, which **infers** a country from organisation names
      because the dataset has no location field — the page says so instead of
      pretending precision it doesn't have.
    """
)

# ---------------------------------------------------------------------------
# 4. Notes & limitations
# ---------------------------------------------------------------------------
st.header("Notes & limitations")
st.markdown(
    """
    - **Not exhaustive:** only major, publicly documented breaches appear here.
    - **"Records lost" is the source's estimate.** Figures differ wildly
      between incidents and should be read as orders of magnitude, not exact
      counts.
    - **Coverage varies by year** — the collection grows in detail over time,
      so early years are under-represented relative to recent ones.
    - **Inferred geography:** *Country Analysis* is derived from organisation
      names and is an approximation by design.
    - Global organisations (e.g. *Facebook*, *Amazon*) and rows that can't be
      tied to a single country are grouped under **"Global / Unknown"**.
    """
)

st.divider()
st.caption(
    "Use the sidebar filters to start exploring — your selections carry over "
    "to every page."
)
