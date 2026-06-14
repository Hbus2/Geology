"""
geo_utils.py — data layer for the Chattanooga geology dashboard.
Pure pandas; no Streamlit imports so it's easy to test.
"""

import re
import pandas as pd

DATA_PATH = "chattanooga_geology.csv"

# Approximate ages (millions of years ago) used only to order periods oldest -> youngest.
AGE_MA = {
    "Precambrian": 1000, "Paleozoic": 396, "Cambrian": 513, "Ordovician": 464,
    "Silurian": 431, "Devonian": 389, "Carboniferous": 332, "Mississippian": 341,
    "Serpukhovian": 327, "Pennsylvanian": 311, "Bashkirian": 318, "Morrowan": 319,
    "Atokan": 313, "Mesozoic": 200, "Cenozoic": 30,
}

# Display label + Wikipedia title for each parsed rock type.
LITH_DISPLAY = {
    "limestone": "Limestone", "sandstone": "Sandstone", "shale": "Shale",
    "dolostone": "Dolostone", "dolomite": "Dolostone", "chert": "Chert",
    "conglomerate": "Conglomerate", "mudstone": "Mudstone", "siltstone": "Siltstone",
    "coal": "Coal", "sedimentary": "Sedimentary (undiff.)",
    "sedimentary rocks": "Sedimentary (undiff.)",
}

# Stable colors per rock type (used on the map + charts).
LITH_COLORS = {
    "Limestone": "#5A86C2", "Sandstone": "#E0B567", "Shale": "#6E7CA8",
    "Dolostone": "#5FB39A", "Chert": "#B5638F", "Conglomerate": "#C08552",
    "Mudstone": "#8A8D91", "Siltstone": "#A8915F", "Coal": "#3B3B3B",
    "Sedimentary (undiff.)": "#9AA7A0",
}

# Colors per geologic period (curated, cohesive).
PERIOD_COLORS = {
    "Cambrian": "#8FAE6B", "Ordovician": "#3C9DA6", "Silurian": "#5FB6B0",
    "Devonian": "#C18E4B", "Carboniferous": "#5A86C2", "Mississippian": "#5A86C2",
    "Serpukhovian": "#7AA0D0", "Pennsylvanian": "#6E7CA8", "Morrowan": "#8A93B8",
    "Paleozoic": "#9AA7A0",
}


def parse_major_liths(s):
    """Return the list of 'Major' lithologies from Macrostrat's lith string."""
    s = str(s)
    m = re.search(r"Major:\{([^}]*)\}", s)
    core = m.group(1) if m else s
    core = core.replace("{", "").replace("}", "")
    return [t.strip().lower() for t in core.split(",") if t.strip()]


def primary_lith_display(s):
    """The dominant rock type at a point, as a clean display label."""
    terms = parse_major_liths(s)
    first = terms[0] if terms else ""
    return LITH_DISPLAY.get(first, first.title() if first else "Unknown")


def primary_lith_key(s):
    """Lowercase key for the dominant rock type (for Wikipedia lookup)."""
    terms = parse_major_liths(s)
    return terms[0] if terms else ""


def short_name(s, n=46):
    s = str(s)
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def age_rank(period):
    """Bigger = older. Unknown periods sort to the end (youngest)."""
    return AGE_MA.get(str(period), -1)


def load_data(path=DATA_PATH):
    df = pd.read_csv(path)
    df["rock_type"] = df["lithology"].apply(primary_lith_display)
    df["rock_key"] = df["lithology"].apply(primary_lith_key)
    df["unit_short"] = df["unit_name"].apply(short_name)
    df["age_rank"] = df["age"].apply(age_rank)
    return df


def apply_filters(df, rock_types=None, periods=None, search=""):
    out = df
    if rock_types:
        out = out[out["rock_type"].isin(rock_types)]
    if periods:
        out = out[out["age"].isin(periods)]
    if search:
        s = search.strip().lower()
        mask = (
            out["unit_name"].astype(str).str.lower().str.contains(s)
            | out["lithology"].astype(str).str.lower().str.contains(s)
            | out["description"].astype(str).str.lower().str.contains(s)
        )
        out = out[mask]
    return out.reset_index(drop=True)


def kpis(df):
    return {
        "points": len(df),
        "formations": df["unit_name"].nunique(),
        "rock_types": df["rock_type"].nunique(),
        "periods": df["age"].nunique(),
    }


def lithology_breakdown(df):
    bd = df["rock_type"].value_counts().rename_axis("label").reset_index(name="count")
    return bd


def period_breakdown(df):
    bd = df.groupby("age").size().reset_index(name="count")
    bd["rank"] = bd["age"].apply(age_rank)
    bd = bd.sort_values("rank", ascending=False).reset_index(drop=True)  # oldest first (largest Ma)
    return bd[["age", "count"]]


def formations_table(df):
    g = (
        df.groupby(["unit_name", "rock_type", "age"])
        .size()
        .reset_index(name="Points")
        .sort_values("Points", ascending=False)
    )
    g = g.rename(columns={"unit_name": "Formation", "rock_type": "Lithology", "age": "Age"})
    g["Formation"] = g["Formation"].apply(lambda s: short_name(s, 60))
    return g.reset_index(drop=True)


def rock_types_present(df):
    """List of (display_label, wiki_key) for each rock type present, by frequency."""
    seen = df.drop_duplicates("rock_type")
    counts = df["rock_type"].value_counts()
    rows = []
    for label in counts.index:
        key = seen.loc[seen["rock_type"] == label, "rock_key"].iloc[0]
        rows.append((label, key, int(counts[label])))
    return rows
