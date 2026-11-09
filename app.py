from __future__ import annotations

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from data_loader import load_gtfs
from route_stats import build_route_stops, overview_table, routes_between
from scoring import add_convenience_score, recommendation_text

st.set_page_config(
    page_title="CommuteWise — Pune Transit",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Design system ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root { --ink:#17211f; --muted:#6b7772; --paper:#f5f7f3; --green:#b9f36b; --deep:#172a25; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background:var(--paper); color:var(--ink); }
.block-container { max-width:1440px; padding-top:1.5rem; padding-bottom:3rem; }
h1,h2,h3 { font-family:'Space Grotesk',sans-serif !important; letter-spacing:-.04em; color:var(--ink); }
[data-testid="stSidebar"] { background:#172a25; }
[data-testid="stSidebar"] * { color:#eef5e9 !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { padding:.45rem .3rem; }
.hero {
  background:linear-gradient(120deg,#172a25 0%,#25483b 100%);
  border-radius:24px; padding:30px 34px; color:#f5f8f1; margin-bottom:22px;
  position:relative; overflow:hidden;
}
.hero:after { content:""; position:absolute; width:260px; height:260px; right:-55px; top:-120px;
  border:1px solid rgba(185,243,107,.35); border-radius:50%; box-shadow:0 0 0 28px rgba(185,243,107,.04),0 0 0 58px rgba(185,243,107,.04); }
.hero h1 { color:#f5f8f1 !important; font-size:clamp(2.2rem,5vw,4rem); margin:8px 0 4px; }
.hero p { color:#c5d4ca; max-width:640px; margin:0; font-size:1rem; }
.eyebrow { color:#b9f36b; font-size:.72rem; font-weight:700; letter-spacing:.16em; text-transform:uppercase; }
.metric-card { background:white; border:1px solid #e6ebe4; border-radius:18px; padding:18px 20px; min-height:116px; }
.metric-label { color:#748078; font-size:.78rem; font-weight:600; text-transform:uppercase; letter-spacing:.08em; }
.metric-value { color:#172a25; font-family:'Space Grotesk'; font-size:2rem; font-weight:700; margin-top:6px; }
.metric-note { color:#7a857e; font-size:.78rem; margin-top:2px; }
.route-card { background:white; border:1px solid #e5ebe3; border-radius:18px; padding:18px 20px; margin:10px 0; }
.route-top { display:flex; justify-content:space-between; gap:12px; align-items:center; }
.score-pill { background:#e9f8d7; color:#31551b; border-radius:999px; padding:6px 11px; font-weight:700; font-size:.8rem; white-space:nowrap; }
.small-muted { color:#748078; font-size:.82rem; }
div.stButton > button { border-radius:999px; border:0; background:#b9f36b; color:#172a25; font-weight:700; padding:.65rem 1.1rem; }
div.stButton > button:hover { background:#a8e653; color:#172a25; }
[data-testid="stMetric"] { background:white; border:1px solid #e6ebe4; border-radius:16px; padding:14px 16px; }
[data-testid="stMetricLabel"] { color:#748078; }
[data-testid="stMetricValue"] { color:#172a25; font-family:'Space Grotesk'; }
hr { border-color:#e2e9df; }
footer { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner="Loading Pune transit data…")
def prepare_data():
    data = load_gtfs("data")
    route_stops = build_route_stops(data)
    overview = overview_table(data, route_stops)
    return data, route_stops, overview

def metric_card(label, value, note=""):
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
        unsafe_allow_html=True,
    )

def style_chart(fig, height=340):
    fig.update_layout(
        height=height, margin=dict(l=8,r=8,t=42,b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color="#43514a"),
        title_font=dict(family="Space Grotesk", size=18, color="#172a25"),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#e9eee7", zeroline=False),
        colorway=["#6a9f45","#172a25","#d4a84f","#7da9a0"],
        legend=dict(orientation="h", y=1.12),
    )
    return fig

def show_route_map(stops, title="Route shape"):
    if stops.empty:
        st.info("No stop coordinates are available for this route.")
        return
    clean = stops.dropna(subset=["stop_lat", "stop_lon"]).copy()
    if clean.empty:
        st.info("No valid coordinates are available for this route.")
        return
    clean = clean.sort_values("stop_sequence")
    fig = px.line_map(
        clean, lat="stop_lat", lon="stop_lon", hover_name="stop_name",
        hover_data={"stop_sequence": True, "stop_lat": False, "stop_lon": False},
        zoom=10, height=430,
    )
    fig.update_traces(line_color="#5d8c3b", line_width=4, marker={"size":7, "color":"#172a25"})
    fig.update_layout(
        map_style="open-street-map", margin=dict(l=0,r=0,t=8,b=0),
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🚌 CommuteWise")
    st.caption("PUNE • PMPML TRANSIT INTELLIGENCE")
    page = st.radio("WORKSPACE", ["Overview", "Plan a commute", "Route explorer", "About the score"], label_visibility="visible")
    st.divider()
    st.markdown("**DATA NOTE**")
    st.caption("Built from open PMPML GTFS data. Trip counts are dataset counts, not live arrival predictions.")
    st.caption("Travel distances are estimated from stop coordinates.")

try:
    data, route_stops, overview = prepare_data()
except Exception as exc:
    st.error("CommuteWise couldn't load its GTFS dataset.")
    st.markdown("Make sure `routes.txt`, `trips.txt`, `stops.txt` and `stop_times.txt` are inside the repository's `data/` folder.")
    with st.expander("Technical details"):
        st.exception(exc)
    st.stop()

if overview.empty or route_stops.empty:
    st.warning("The GTFS files loaded, but they did not produce any route records.")
    st.stop()

total_routes = int(overview["route_id"].nunique())
total_stops = int(data["stops"]["stop_id"].nunique())
total_trips = int(data["trips"]["trip_id"].nunique())
avg_stops = round(float(overview["n_stops"].mean()), 1)

# ---------- Overview ----------
if page == "Overview":
    st.markdown(
        '<div class="hero"><div class="eyebrow">Pune transit, decoded</div>'
        '<h1>Make every commute<br>count.</h1>'
        '<p>Compare bus routes with clarity. Find the option that balances fewer stops, shorter distance and more service.</p></div>',
        unsafe_allow_html=True,
    )
    a,b,c,d = st.columns(4)
    with a: metric_card("Routes mapped", f"{total_routes:,}", "Unique PMPML routes")
    with b: metric_card("Stops indexed", f"{total_stops:,}", "Unique stop locations")
    with c: metric_card("Trips in feed", f"{total_trips:,}", "GTFS trip records")
    with d: metric_card("Avg. route stops", f"{avg_stops}", "Representative route patterns")
    st.write("")
    left,right = st.columns([1.35,1])
    with left:
        top = overview.nlargest(10, "n_stops").sort_values("n_stops")
        fig = px.bar(top, x="n_stops", y="route_long_name", orientation="h",
                     title="Routes with the widest stop coverage", text="n_stops")
        fig.update_traces(marker_color="#6a9f45", textposition="outside", cliponaxis=False)
        st.plotly_chart(style_chart(fig, 420), use_container_width=True)
    with right:
        st.markdown("### Network snapshot")
        st.markdown('<div class="route-card">', unsafe_allow_html=True)
        st.metric("Longest representative route", f'{overview.iloc[0]["length_km"]:.1f} km')
        st.metric("Most stops on a route", f'{int(overview["n_stops"].max())}')
        st.metric("Routes with trip records", f'{int((overview["trips"] > 0).sum())}')
        st.markdown('</div>', unsafe_allow_html=True)
        st.caption("Route length uses the longest available trip pattern for each route. It is an estimate, not a road-distance measurement.")
    st.markdown("### Explore the network")
    st.write("Choose **Plan a commute** to compare routes between two stops, or open **Route explorer** to inspect a route's stop sequence and map.")

# ---------- Plan a commute ----------
elif page == "Plan a commute":
    st.markdown('<div class="eyebrow">ROUTE MATCHING</div>', unsafe_allow_html=True)
    st.title("Where are you headed?")
    st.write("Search by part of a PMPML stop name. We'll find routes that serve your origin and destination in that order.")
    stop_names = sorted(data["stops"]["stop_name"].dropna().astype(str).unique().tolist())
    default_from = next((x for x in stop_names if "swargate" in x.lower()), stop_names[0] if stop_names else "")
    default_to = next((x for x in stop_names if "katraj" in x.lower()), stop_names[-1] if stop_names else "")
    with st.form("journey_form"):
        x,y = st.columns(2)
        origin = x.selectbox("FROM · Boarding stop", stop_names, index=stop_names.index(default_from) if default_from in stop_names else 0)
        destination = y.selectbox("TO · Destination stop", stop_names, index=stop_names.index(default_to) if default_to in stop_names else 0)
        submitted = st.form_submit_button("Find my routes →", use_container_width=True)
    if submitted:
        found = routes_between(data, route_stops, origin, destination)
        if found.empty:
            st.warning("No one-seat route was found for this stop pair. Try nearby stops or shorter search terms.")
        else:
            scored = add_convenience_score(found)
            st.session_state["last_results"] = scored
            st.session_state["last_pair"] = (origin, destination)
    if "last_results" in st.session_state:
        scored = st.session_state["last_results"]
        pair = st.session_state.get("last_pair", ("your origin","your destination"))
        st.divider()
        st.markdown(f"### {len(scored)} route option(s) found")
        best = scored.iloc[0]
        st.success(
            f"Best overall: **{best['route_name']}** · {best['convenience_score']:.1f}/100. "
            f"{int(best['stops_between'])} stops between {best['board_at']} and {best['get_off_at']}."
        )
        k1,k2,k3 = st.columns(3)
        with k1: metric_card("Best score", f"{best['convenience_score']:.1f}/100", str(best["route_name"]))
        with k2: metric_card("Distance", f'{best["distance_km"]:.1f} km', "Estimated stop-to-stop distance")
        with k3: metric_card("Stops", f'{int(best["stops_between"])}', "Between selected stops")
        for _, row in scored.iterrows():
            st.markdown(
                f'<div class="route-card"><div class="route-top"><div><b>{row["route_name"]}</b>'
                f'<div class="small-muted">{row["board_at"]} → {row["get_off_at"]}</div></div>'
                f'<div class="score-pill">{row["convenience_score"]:.1f} / 100</div></div>'
                f'<hr><div class="small-muted">{int(row["stops_between"])} stops &nbsp;·&nbsp; '
                f'{row["distance_km"]:.1f} km &nbsp;·&nbsp; {int(row["trips"])} trips in feed</div></div>',
                unsafe_allow_html=True,
            )
        chart = px.bar(scored.sort_values("convenience_score"), x="convenience_score", y="route_name",
                       orientation="h", title="Convenience score comparison", text="convenience_score")
        chart.update_traces(marker_color="#6a9f45", texttemplate="%{text:.1f}", textposition="outside")
        st.plotly_chart(style_chart(chart, max(300, 55*len(scored))), use_container_width=True)
        st.caption("The convenience score is a project-defined comparison model, not an official PMPML rating. It does not include live traffic or real-time bus arrivals.")

# ---------- Route explorer ----------
elif page == "Route explorer":
    st.markdown('<div class="eyebrow">NETWORK EXPLORER</div>', unsafe_allow_html=True)
    st.title("Get to know a route.")
    options = overview.sort_values("route_long_name")
    labels = {f'{r.route_long_name} · {r.route_id}': r.route_id for r in options.itertuples()}
    selected = st.selectbox("Choose a route", list(labels.keys()))
    route_id = labels[selected]
    row = overview.loc[overview["route_id"] == route_id].iloc[0]
    direction_rows = route_stops.loc[route_stops["route_id"] == route_id]
    directions = sorted(direction_rows["direction_id"].dropna().unique().tolist())
    direction = st.selectbox("Direction pattern", directions) if directions else None
    selected_stops = direction_rows.loc[direction_rows["direction_id"] == direction].sort_values("stop_sequence") if direction is not None else pd.DataFrame()
    m1,m2,m3 = st.columns(3)
    with m1: metric_card("Stops", f'{len(selected_stops):,}', "Selected direction pattern")
    with m2: metric_card("Route length", f'{selected_stops["cum_km"].max():.1f} km' if not selected_stops.empty else "—", "Coordinate-based estimate")
    with m3: metric_card("Trips", f'{int(data["trips"].loc[data["trips"]["route_id"] == route_id].shape[0]):,}', "Across available directions")
    st.markdown("### Route map")
    show_route_map(selected_stops)
    st.markdown("### Stop sequence")
    if not selected_stops.empty:
        table = selected_stops[["stop_sequence","stop_name","cum_km"]].copy()
        table.columns = ["Sequence","Stop","Distance from start (km)"]
        table["Distance from start (km)"] = table["Distance from start (km)"].round(2)
        st.dataframe(table, use_container_width=True, hide_index=True, height=420)
    else:
        st.info("No stop sequence is available for this direction.")

# ---------- Scoring methodology ----------
else:
    st.markdown('<div class="eyebrow">TRANSPARENT BY DESIGN</div>', unsafe_allow_html=True)
    st.title("How the score works.")
    st.write("CommuteWise uses a simple weighted model to compare routes found between the same two stops.")
    components = pd.DataFrame({
        "Signal":["Fewer stops","Shorter distance","More trips"],
        "Weight":[40,30,30],
        "Why it matters":["Fewer intermediate stops can mean a simpler ride.","A shorter route distance can reduce time on the road.","More trips in the feed can indicate more service opportunities."]
    })
    fig = px.bar(components, x="Weight", y="Signal", orientation="h", text="Weight",
                 title="Convenience score weights (%)")
    fig.update_traces(marker_color="#6a9f45", texttemplate="%{text}%", textposition="outside")
    st.plotly_chart(style_chart(fig, 280), use_container_width=True)
    st.dataframe(components, use_container_width=True, hide_index=True)
    st.info("Scores are min–max normalized within the routes returned for one origin/destination pair. They are relative rankings, not predictions of journey time or official PMPML quality scores.")
    st.markdown("**Important limitations**")
    st.markdown("- GTFS trip counts are not live frequency or a guaranteed timetable.\n- Distance is calculated between stop coordinates, not along the road network.\n- The route pattern represents the longest trip available for each route and direction.\n- Transfers, fares, traffic, accessibility and real-time vehicle positions are not modelled.")
