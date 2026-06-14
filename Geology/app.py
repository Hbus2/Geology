"""
app.py — Chattanooga Bedrock Geology dashboard.
Run:  streamlit run app.py
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import geo_utils as G
from photos import rock_info

st.set_page_config(page_title="Chattanooga Geology", page_icon="🪨", layout="wide")

TEXT, MUTED, CARD = "#1F2329", "#6B7280", "#FFFFFF"

# KPI tile accent colors + tiny inline icons (no emoji)
ICONS = {
    "points": ('#5A86C2', '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><path d="M12 21s-6-5.7-6-10a6 6 0 0 1 12 0c0 4.3-6 10-6 10z"/><circle cx="12" cy="11" r="2"/></svg>'),
    "formations": ('#C08552', '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><path d="M3 7l9-4 9 4-9 4-9-4z"/><path d="M3 12l9 4 9-4"/><path d="M3 17l9 4 9-4"/></svg>'),
    "rock_types": ('#5FB39A', '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><path d="M12 2l9 5v10l-9 5-9-5V7z"/></svg>'),
    "periods": ('#6E7CA8', '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>'),
}

CSS = f"""
<style>
.block-container {{ padding-top: 2rem; max-width: 1280px; }}
h1, h2, h3 {{ color: {TEXT}; font-weight: 700; }}
.sub {{ color: {MUTED}; font-size: 0.86rem; margin: 0 0 0.2rem 0; }}
.card-h {{ font-size: 1.02rem; font-weight: 700; color: {TEXT}; margin-bottom: 0.1rem; }}
/* KPI */
.kpi {{ display:flex; align-items:center; gap:0.7rem; }}
.kpi-sq {{ width:42px; height:42px; border-radius:11px; display:flex; align-items:center; justify-content:center; flex:none; }}
.kpi-num {{ font-size:1.55rem; font-weight:750; color:{TEXT}; line-height:1.05; }}
.kpi-lab {{ font-size:0.78rem; color:{MUTED}; }}
/* donut legend */
.lg {{ display:grid; grid-template-columns:1fr 1fr; gap:2px 14px; margin-top:6px; }}
.lg-i {{ display:flex; align-items:center; font-size:0.8rem; color:{TEXT}; }}
.lg-d {{ width:10px; height:10px; border-radius:3px; margin-right:7px; flex:none; }}
.lg-p {{ margin-left:auto; color:{MUTED}; }}
/* gallery */
.gimg {{ width:100%; height:150px; object-fit:cover; border-radius:11px; display:block; }}
.gph {{ width:100%; height:150px; border-radius:11px; display:flex; align-items:center; justify-content:center;
        background:#EEF1F4; color:{MUTED}; font-size:0.82rem; }}
.gname {{ font-weight:700; color:{TEXT}; margin-top:8px; }}
.gcount {{ font-size:0.74rem; color:{MUTED}; }}
.gblurb {{ font-size:0.8rem; color:#4B5563; margin-top:4px; line-height:1.35; }}
.glink {{ font-size:0.76rem; }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def get_df():
    return G.load_data()


def render_kpi(col, key, value, label):
    color, icon = ICONS[key]
    col.markdown(
        f'<div class="kpi"><div class="kpi-sq" style="background:{color}">{icon}</div>'
        f'<div><div class="kpi-num">{value}</div><div class="kpi-lab">{label}</div></div></div>',
        unsafe_allow_html=True,
    )


def render_donut(bd, colors):
    labels = bd["label"].tolist()
    vals = bd["count"].tolist()
    cols = [colors.get(l, "#9AA7A0") for l in labels]
    total = sum(vals)
    fig = go.Figure(go.Pie(
        labels=labels, values=vals, hole=0.58, sort=False, direction="clockwise",
        marker=dict(colors=cols, line=dict(color="#fff", width=2)),
        textinfo="none", hoverinfo="label+value+percent",
    ))
    fig.update_layout(
        showlegend=False, height=270, margin=dict(l=0, r=0, t=4, b=0),
        annotations=[dict(text=f"<b>{total}</b><br><span style='font-size:0.7em;color:{MUTED}'>points</span>",
                          x=0.5, y=0.5, showarrow=False, font=dict(size=20, color=TEXT))],
        paper_bgcolor="rgba(0,0,0,0)",
    )
    # custom legend
    items = ""
    for l, v in zip(labels, vals):
        pct = v / total * 100 if total else 0
        items += (f'<div class="lg-i"><span class="lg-d" style="background:{colors.get(l, "#9AA7A0")}"></span>'
                  f'{l}<span class="lg-p">{pct:.0f}%</span></div>')
    return fig, f'<div class="lg">{items}</div>'


def render_period_bar(bd):
    bd = bd.iloc[::-1]  # so oldest ends up on top in a horizontal bar
    colors = [G.PERIOD_COLORS.get(p, "#9AA7A0") for p in bd["age"]]
    fig = go.Figure(go.Bar(
        x=bd["count"], y=bd["age"], orientation="h",
        marker=dict(color=colors), text=bd["count"], textposition="outside",
        cliponaxis=False, hoverinfo="x+y",
    ))
    fig.update_layout(
        height=300, margin=dict(l=6, r=30, t=6, b=6), paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    return fig


def render_map(df, color_by):
    field = "age" if color_by == "Geologic period" else "rock_type"
    cmap = G.PERIOD_COLORS if color_by == "Geologic period" else G.LITH_COLORS
    if color_by == "Geologic period":
        order = G.period_breakdown(df)["age"].tolist()
    else:
        order = G.lithology_breakdown(df)["label"].tolist()
    fig = px.scatter_mapbox(
        df, lat="lat", lon="lon", color=field,
        color_discrete_map=cmap, category_orders={field: order},
        hover_name="unit_short", hover_data={"rock_type": True, "age": True, "lat": False, "lon": False, field: False},
        zoom=8.6, height=540,
    )
    fig.update_traces(marker=dict(size=11, opacity=0.85))
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_center={"lat": df["lat"].mean(), "lon": df["lon"].mean()},
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=0.01, xanchor="left", x=0.01,
                    bgcolor="rgba(255,255,255,0.8)", font=dict(size=11), title=""),
    )
    return fig


# ---------------------------------------------------------------- load
df = get_df()

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("### 🪨 Chattanooga Geology")
    st.markdown('<div class="sub">Bedrock data from Macrostrat</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("#### Filters")
    rock_opts = G.lithology_breakdown(df)["label"].tolist()
    period_opts = G.period_breakdown(df)["age"].tolist()
    sel_rocks = st.multiselect("Rock type", rock_opts)
    sel_periods = st.multiselect("Geologic period", period_opts)
    search = st.text_input("Search formations", placeholder="e.g. Knox, limestone, coal")
    st.caption("Empty filters show everything. Search looks in formation names, lithology, and descriptions.")

fdf = G.apply_filters(df, sel_rocks, sel_periods, search)

# ---------------------------------------------------------------- header
st.title("Chattanooga Bedrock Geology")
st.markdown(
    '<div class="sub">What rock lies beneath the Chattanooga area — formations, lithology, and geologic age, '
    'sampled across the Valley &amp; Ridge and Cumberland Plateau.</div>',
    unsafe_allow_html=True,
)
st.write("")

if fdf.empty:
    st.warning("No rock units match these filters. Try clearing one.")
    st.stop()

# ---------------------------------------------------------------- KPIs
k = G.kpis(fdf)
c1, c2, c3, c4 = st.columns(4)
for col, key, val, lab in [
    (c1, "points", k["points"], "Points sampled"),
    (c2, "formations", k["formations"], "Formations"),
    (c3, "rock_types", k["rock_types"], "Rock types"),
    (c4, "periods", k["periods"], "Geologic periods"),
]:
    with col:
        with st.container(border=True):
            render_kpi(col, key, val, lab)

st.write("")

# ---------------------------------------------------------------- map
with st.container(border=True):
    top = st.columns([3, 1])
    top[0].markdown('<div class="card-h">Where the rocks are</div>'
                    '<div class="sub">Each point is a sampled location, colored by your choice</div>',
                    unsafe_allow_html=True)
    color_by = top[1].selectbox("Color points by", ["Geologic period", "Rock type"], label_visibility="collapsed")
    st.plotly_chart(render_map(fdf, color_by), use_container_width=True)

st.write("")

# ---------------------------------------------------------------- charts row
left, right = st.columns(2)
with left:
    with st.container(border=True):
        st.markdown('<div class="card-h">Dominant rock type</div>'
                    '<div class="sub">By sampled point</div>', unsafe_allow_html=True)
        fig, legend = render_donut(G.lithology_breakdown(fdf), G.LITH_COLORS)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(legend, unsafe_allow_html=True)
with right:
    with st.container(border=True):
        st.markdown('<div class="card-h">Geologic timeline</div>'
                    '<div class="sub">Points by period — oldest at top</div>', unsafe_allow_html=True)
        st.plotly_chart(render_period_bar(G.period_breakdown(fdf)), use_container_width=True)

st.write("")

# ---------------------------------------------------------------- formations table
with st.container(border=True):
    st.markdown('<div class="card-h">Formations</div>'
                '<div class="sub">Geologic units found in the sampled area</div>', unsafe_allow_html=True)
    st.dataframe(G.formations_table(fdf), use_container_width=True, hide_index=True, height=360)

st.write("")

# ---------------------------------------------------------------- rock gallery
st.markdown('<div class="card-h">Rock types in this area</div>'
            '<div class="sub">Photos &amp; descriptions from Wikipedia</div>', unsafe_allow_html=True)
st.write("")

rocks = G.rock_types_present(fdf)
ncols = 4
rows = [rocks[i:i + ncols] for i in range(0, len(rocks), ncols)]
for row in rows:
    cols = st.columns(ncols)
    for col, (label, key, count) in zip(cols, row):
        with col:
            with st.container(border=True):
                info = rock_info(key, label)
                if info.get("image"):
                    col.markdown(f'<img class="gimg" src="{info["image"]}" alt="{label}">', unsafe_allow_html=True)
                else:
                    col.markdown(f'<div class="gph">{label}</div>', unsafe_allow_html=True)
                blurb = info.get("extract", "")
                if len(blurb) > 180:
                    blurb = blurb[:180].rstrip() + "…"
                link = f'<a class="glink" href="{info["url"]}" target="_blank">Learn more →</a>' if info.get("url") else ""
                col.markdown(
                    f'<div class="gname">{label}</div>'
                    f'<div class="gcount">{count} sampled point{"s" if count != 1 else ""}</div>'
                    f'<div class="gblurb">{blurb}</div>{link}',
                    unsafe_allow_html=True,
                )
