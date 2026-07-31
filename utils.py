"""
utils.py
--------
Shared initialization for the Data Breaches Streamlit app:
- page config
- data loading + cleaning (cached)
- a sidebar filter panel reused by every page so filters stay in sync
  across the whole app (app.py and everything in pages/)

Only pandas is used for data work and plotly.express for charts.
"""

import re
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent / "data"

# Preferred sheet name when the source file is the raw multi-sheet workbook
# from Information is Beautiful. Falls back to the first sheet if missing.
PREFERRED_SHEET = "breaches"

# The dataset encodes "data sensitivity" as 1-5. This is the legend used by
# the source (Information is Beautiful - World's Biggest Data Breaches).
SENSITIVITY_LABELS = {
    1: "1 - Email / online info",
    2: "2 - SSN / personal details",
    3: "3 - Credit card info",
    4: "4 - Health & other personal records",
    5: "5 - Full details",
}

FILTER_KEYS = [
    "filter_year_range",
    "filter_sectors",
    "filter_methods",
    "filter_sensitivity",
    "filter_search",
]


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------

def init_page(page_title: str, icon: str = "🔐") -> None:
    """Set the page config. Must be the first Streamlit call in a page."""
    st.set_page_config(
        page_title=f"{page_title} · Data Breaches",
        page_icon=icon,
        layout="wide",
    )


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _find_data_file() -> Path | None:
    """Look for the first .csv / .xlsx / .xls file dropped in data/."""
    if not DATA_DIR.exists():
        return None
    candidates = (
        sorted(DATA_DIR.glob("*.csv"))
        + sorted(DATA_DIR.glob("*.xlsx"))
        + sorted(DATA_DIR.glob("*.xls"))
    )
    # ignore Excel lock files like ~$file.xlsx
    candidates = [p for p in candidates if not p.name.startswith("~$")]
    return candidates[0] if candidates else None


def _to_number(value) -> float:
    """Turn messy numeric strings ('2,400,00', '53;000') into floats."""
    if pd.isna(value):
        return float("nan")
    digits = re.sub(r"[^0-9.]", "", str(value))
    return float(digits) if digits else float("nan")


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )
    df = df.rename(
        columns={
            "1st_source_link": "first_source_link",
            "2nd_source_link": "second_source_link",
        }
    )
    # drop the unlabeled spacer columns Excel leaves behind
    df = df.loc[:, ~df.columns.str.startswith("unnamed")]
    return df


def _clean_breaches(raw: pd.DataFrame) -> pd.DataFrame:
    df = _clean_columns(raw)

    # The raw workbook has a legend row at the top with no real year/org ->
    # coercing year and dropping unparsable rows removes it cleanly.
    df["year"] = pd.to_numeric(df.get("year"), errors="coerce")
    df = df.dropna(subset=["organisation", "year"]).copy()
    df["year"] = df["year"].astype(int)

    df["records_lost"] = df.get("records_lost").apply(_to_number)

    for col in ["sector", "method", "organisation", "source_name"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df.loc[df[col].isin(["nan", "none", ""]), col] = pd.NA

    df["data_sensitivity"] = pd.to_numeric(df.get("data_sensitivity"), errors="coerce")
    df["sensitivity_label"] = (
        df["data_sensitivity"].map(SENSITIVITY_LABELS).fillna("Unknown")
    )

    df["date"] = pd.to_datetime(df.get("date"), errors="coerce")

    if "interesting_story" in df.columns:
        df["is_notable"] = (
            df["interesting_story"].astype(str).str.strip().str.lower().eq("y")
        )
    else:
        df["is_notable"] = False

    keep_cols = [
        "id",
        "organisation",
        "alternative_name",
        "records_lost",
        "year",
        "date",
        "sector",
        "method",
        "data_sensitivity",
        "sensitivity_label",
        "is_notable",
        "displayed_records",
        "story",
        "source_name",
        "first_source_link",
        "second_source_link",
    ]
    keep_cols = [c for c in keep_cols if c in df.columns]
    df = df[keep_cols].reset_index(drop=True)
    return df


@st.cache_data(show_spinner="Loading data breach dataset...")
def load_data() -> pd.DataFrame | None:
    """Load and clean the dataset from data/. Returns None if no file found."""
    path = _find_data_file()
    if path is None:
        return None

    if path.suffix.lower() == ".csv":
        raw = pd.read_csv(path)
    else:
        try:
            raw = pd.read_excel(path, sheet_name=PREFERRED_SHEET)
        except ValueError:
            raw = pd.read_excel(path, sheet_name=0)

    return _clean_breaches(raw)


# ---------------------------------------------------------------------------
# Shared sidebar filters
# ---------------------------------------------------------------------------

ALL_LABEL = "All Types"

def _init_filters(df: pd.DataFrame) -> None:
    """Initialise filter defaults once, then keep alive across page switches.

    Without the re-assignment, Streamlit clears widget keys that weren't
    rendered on the previous run (i.e. when you were on a different page).
    """
    min_year, max_year = int(df["year"].min()), int(df["year"].max()) - 1

    filter_defaults = {
        "filter_year_range": (min_year, max_year),
        "filter_sectors": [ALL_LABEL],
        "filter_methods": [ALL_LABEL],
        "filter_sensitivity": [ALL_LABEL],
    }

    for key, default in filter_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default               # initialise once
        else:
            st.session_state[key] = st.session_state[key]  # keep alive across pages


def render_sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Render the shared filter panel in the sidebar and return the filtered
    dataframe. Widgets use fixed keys, so selections persist in
    st.session_state as the user moves between app.py and pages/*.
    """
    st.sidebar.header("Filters")

    if df is None or df.empty:
        st.sidebar.info("No data loaded yet.")
        return df

    _init_filters(df)

    year_range = st.sidebar.slider(
        "Year",
        min_value=int(df["year"].min()),
        max_value=int(df["year"].max()) - 1,
        key="filter_year_range",
    )

    sector_options = [ALL_LABEL] + sorted(df["sector"].dropna().unique().tolist())
    selected_sectors = st.sidebar.multiselect(
        "Sector",
        options=sector_options,
        key="filter_sectors",
    )

    method_options = [ALL_LABEL] + sorted(df["method"].dropna().unique().tolist())
    selected_methods = st.sidebar.multiselect(
        "Breach method",
        options=method_options,
        key="filter_methods",
    )

    present_levels = sorted(df["data_sensitivity"].dropna().unique().tolist())
    sensitivity_options = [ALL_LABEL] + [SENSITIVITY_LABELS.get(int(v), "Unknown") for v in present_levels]
    selected_sensitivity = st.sidebar.multiselect(
        "Data sensitivity",
        options=sensitivity_options,
        key="filter_sensitivity",
    )

    st.sidebar.divider()
    if st.sidebar.button("Reset filters", width='stretch'):
        for key in FILTER_KEYS:
            st.session_state.pop(key, None)
        st.rerun()

    mask = df["year"].between(*st.session_state["filter_year_range"])
    if ALL_LABEL not in selected_sectors:
        mask &= df["sector"].isin(selected_sectors)
    if ALL_LABEL not in selected_methods:
        mask &= df["method"].isin(selected_methods)
    if ALL_LABEL not in selected_sensitivity:
        mask &= df["sensitivity_label"].isin(selected_sensitivity)
    filtered = df[mask].copy()

    st.sidebar.caption(f"Showing **{len(filtered):,}** of **{len(df):,}** breaches")
    return filtered


# ---------------------------------------------------------------------------
# Small display helpers
# ---------------------------------------------------------------------------

def format_number(n) -> str:
    """1234567 -> '1.2M', useful for compact KPIs and chart labels."""
    if n is None or pd.isna(n):
        return "—"
    n = float(n)
    for unit, threshold in (("B", 1_000_000_000), ("M", 1_000_000), ("K", 1_000)):
        if abs(n) >= threshold:
            return f"{n / threshold:.1f}{unit}"
    return f"{n:,.0f}"
