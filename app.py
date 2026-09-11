import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta

st.set_page_config(
    page_title="Live Climate Impact Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

NASA_URL = "https://power.larc.nasa.gov/api/temporal/hourly/point"
AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
OWID_URL = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"

# Custom CSS for Modern UI, Typography, and Glassmorphism
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700&display=swap');

:root {
    --bg-dark: #080e14;
    --bg-card: rgba(13, 24, 33, 0.75);
    --border-subtle: rgba(77, 208, 225, 0.14);
    --border-hover: rgba(77, 208, 225, 0.35);
    --text-main: #f0f7f9;
    --text-muted: #8ba2b5;
    --accent-cyan: #00d2ff;
    --accent-mint: #2ee59d;
    --accent-amber: #ffb74d;
    --accent-coral: #ff708d;
}

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    background: 
        radial-gradient(circle at 10% 15%, rgba(0, 210, 255, 0.08), transparent 30%),
        radial-gradient(circle at 90% 20%, rgba(46, 229, 157, 0.07), transparent 28%),
        radial-gradient(circle at 50% 85%, rgba(13, 71, 161, 0.08), transparent 35%),
        #070d13;
    color: var(--text-main);
}

.stApp {
    background: transparent;
}

.block-container {
    padding-top: 1.5rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1400px;
}

/* Typography Overrides */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: var(--text-main) !important;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: rgba(8, 15, 22, 0.95);
    border-right: 1px solid var(--border-subtle);
    backdrop-filter: blur(12px);
}

[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stNumberInput label {
    font-size: 0.82rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
}

/* Glassmorphic Hero Banner */
.hero-card {
    background: linear-gradient(135deg, rgba(16, 33, 44, 0.8), rgba(9, 21, 29, 0.6));
    border: 1px solid var(--border-subtle);
    border-radius: 20px;
    padding: 1.4rem 1.75rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(16px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
}

.hero-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 0.35rem 0.85rem;
    background: rgba(0, 210, 255, 0.12);
    border: 1px solid rgba(0, 210, 255, 0.25);
    border-radius: 50px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--accent-cyan);
}

.hero-title {
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--text-main);
    margin-top: 0.75rem;
    line-height: 1.5;
}

/* Custom KPI Card Grid */
.kpi-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.kpi-card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 18px;
    padding: 1.1rem 1.25rem;
    backdrop-filter: blur(12px);
    transition: all 0.25s ease;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.18);
}

.kpi-card:hover {
    border-color: var(--border-hover);
    transform: translateY(-2px);
    box-shadow: 0 12px 28px rgba(0, 210, 255, 0.08);
}

.kpi-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.5rem;
}

.kpi-label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-muted);
}

.kpi-icon {
    font-size: 1.1rem;
}

.kpi-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.65rem;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.03em;
}

.kpi-sub {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 0.2rem;
}

/* Chart Card Containers */
div[data-testid="stPlotlyChart"] {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 20px;
    padding: 12px;
    backdrop-filter: blur(14px);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

/* Custom Alert & Expanders */
.stAlert {
    background: rgba(14, 28, 38, 0.8) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 14px !important;
}

.stExpander {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 16px !important;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_nasa_weather(lat, lon):
    end = date.today()
    start = end - timedelta(days=2)
    params = {
        "parameters": "T2M,RH2M,PRECTOTCORR,WS10M,ALLSKY_SFC_SW_DWN",
        "community": "RE", "longitude": lon, "latitude": lat,
        "start": start.strftime("%Y%m%d"), "end": end.strftime("%Y%m%d"),
        "format": "JSON", "time-standard": "UTC"
    }
    r = requests.get(NASA_URL, params=params, timeout=30)
    r.raise_for_status()
    payload = r.json()
    p = payload["properties"]["parameter"]
    df = pd.DataFrame(p)
    df.index = pd.to_datetime(df.index, format="%Y%m%d%H")
    df.index.name = "timestamp"
    df = df.rename(columns={
        "T2M": "temperature_c", "RH2M": "humidity_pct",
        "PRECTOTCORR": "precipitation_mm", "WS10M": "wind_ms",
        "ALLSKY_SFC_SW_DWN": "solar_wm2"
    }).replace(-999, np.nan)
    return df.reset_index().sort_values("timestamp")

@st.cache_data(ttl=900, show_spinner=False)
def fetch_air_quality(lat, lon):
    params = {
        "latitude": lat, "longitude": lon,
        "current": "pm2_5,carbon_dioxide,carbon_monoxide,nitrogen_dioxide,ozone",
        "hourly": "pm2_5,carbon_dioxide,nitrogen_dioxide,ozone",
        "timezone": "auto", "past_days": 1, "forecast_days": 1
    }
    r = requests.get(AQ_URL, params=params, timeout=30)
    r.raise_for_status()
    j = r.json()
    current = j.get("current", {})
    hourly = pd.DataFrame(j.get("hourly", {}))
    if not hourly.empty:
        hourly["time"] = pd.to_datetime(hourly["time"])
        hourly = hourly.replace(-999, np.nan)
    return current, hourly

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_emissions():
    df = pd.read_csv(OWID_URL)
    cols = ["country", "year", "co2", "co2_per_capita", "share_global_co2"]
    cols = [c for c in cols if c in df.columns]
    return df[cols]

def climate_score(temp, pm25, co2):
    score = 100
    if pd.notna(temp): score -= min(abs(temp - 20) * 1.2, 25)
    if pd.notna(pm25): score -= min(pm25 * 1.1, 40)
    if pd.notna(co2): score -= min(max(co2 - 400, 0) * 0.06, 25)
    return max(0, round(score, 1))

def style_chart(fig, height=350):
    fig.update_layout(
        template=None,
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=48, r=20, t=25, b=35),
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#8ba2b5", size=11),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f0f7f9", size=11),
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.06)",
            gridwidth=1,
            zeroline=False,
            automargin=True,
            tickfont=dict(color="#8ba2b5", size=10),
            linecolor="rgba(255, 255, 255, 0.12)",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.06)",
            gridwidth=1,
            zeroline=False,
            automargin=True,
            tickfont=dict(color="#8ba2b5", size=10),
            linecolor="rgba(255, 255, 255, 0.12)",
        ),
        hoverlabel=dict(
            bgcolor="#0c1a24",
            bordercolor="rgba(0,210,255,0.3)",
            font=dict(family="JetBrains Mono, monospace", color="#ffffff", size=12)
        )
    )
    return fig

# Sidebar setup
st.sidebar.title("🌍 Climate Control")
city = st.sidebar.selectbox("Quick location", ["Kolkata, India", "New York, USA", "London, UK", "Sydney, Australia", "Custom"])
defaults = {
    "Kolkata, India": (22.5726, 88.3639),
    "New York, USA": (40.7128, -74.0060),
    "London, UK": (51.5072, -0.1278),
    "Sydney, Australia": (-33.8688, 151.2093)
}
if city == "Custom":
    lat = st.sidebar.number_input("Latitude", value=22.5726, format="%.4f")
    lon = st.sidebar.number_input("Longitude", value=88.3639, format="%.4f")
    label = f"Custom ({lat:.2f}, {lon:.2f})"
else:
    lat, lon = defaults[city]
    label = city

country = st.sidebar.selectbox("Emissions country", ["India", "United States", "China", "United Kingdom", "Australia", "World"])
st.sidebar.caption("Live/API data refreshes automatically via Streamlit cache.")
if st.sidebar.button("🔄 Refresh live data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Header
st.title("🌍 Live Climate Impact Dashboard")

st.markdown(f"""
<div class="hero-card">
    <div class="hero-pill">● LIVE CLIMATE INTELLIGENCE</div>
    <div class="hero-title">
        Real-world climate signals for <strong>{label}</strong> — blending live meteorology, atmospheric composition, and emissions context.
    </div>
</div>
""", unsafe_allow_html=True)

# Data Fetching
try:
    with st.spinner("Connecting to live telemetry feeds..."):
        weather = fetch_nasa_weather(lat, lon)
        aq_current, aq_hourly = fetch_air_quality(lat, lon)
        emissions = fetch_emissions()
except Exception as e:
    st.error(f"API connection failed: {e}")
    st.stop()

latest = weather.dropna(subset=["temperature_c"]).iloc[-1] if not weather.empty else {}
temp = latest.get("temperature_c", np.nan)
humidity = latest.get("humidity_pct", np.nan)
pm25 = aq_current.get("pm2_5", np.nan)
atmos_co2 = aq_current.get("carbon_dioxide", np.nan)
score = climate_score(temp, pm25, atmos_co2)

country_df = emissions[emissions["country"] == country].dropna(subset=["co2"]).sort_values("year")
latest_em = country_df.iloc[-1] if not country_df.empty else None

# Custom Non-Truncating Modern KPI Cards
st.markdown(f"""
<div class="kpi-container">
    <div class="kpi-card">
        <div class="kpi-header">
            <span class="kpi-label">Temperature</span>
            <span class="kpi-icon">🌡️</span>
        </div>
        <div class="kpi-value">{f"{temp:.1f} °C" if pd.notna(temp) else "N/A"}</div>
        <div class="kpi-sub">NASA POWER 2m air temp</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-header">
            <span class="kpi-label">Relative Humidity</span>
            <span class="kpi-icon">💧</span>
        </div>
        <div class="kpi-value">{f"{humidity:.0f}%" if pd.notna(humidity) else "N/A"}</div>
        <div class="kpi-sub">Near-surface moisture</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-header">
            <span class="kpi-label">Particulate PM2.5</span>
            <span class="kpi-icon">🌫️</span>
        </div>
        <div class="kpi-value">{f"{pm25:.1f} <span style='font-size:1rem;color:var(--text-muted);'>µg/m³</span>" if pd.notna(pm25) else "N/A"}</div>
        <div class="kpi-sub">Open-Meteo Air Quality</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-header">
            <span class="kpi-label">Atmospheric CO₂</span>
            <span class="kpi-icon">🫧</span>
        </div>
        <div class="kpi-value">{f"{atmos_co2:.0f} <span style='font-size:1rem;color:var(--text-muted);'>ppm</span>" if pd.notna(atmos_co2) else "N/A"}</div>
        <div class="kpi-sub">Ambient concentration</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-header">
            <span class="kpi-label">Climate Score</span>
            <span class="kpi-icon">🌱</span>
        </div>
        <div class="kpi-value">{score}<span style='font-size:1.1rem;color:var(--accent-mint);'>/100</span></div>
        <div class="kpi-sub">Analytical composite index</div>
    </div>
</div>
""", unsafe_allow_html=True)

if latest_em is not None:
    st.info(f"📊 **Latest available annual CO₂ emissions for {country}:** `{latest_em['co2']:.2f} Mt CO₂` ({int(latest_em['year'])}). Annual emissions are reported retrospectively and separated from real-time streaming signals.")

st.write("")

# Row 1: Weather Telemetry
left, right = st.columns(2)
with left:
    st.markdown("### 📈 NASA Temperature Stream")
    fig = px.line(
        weather,
        x="timestamp",
        y="temperature_c",
        labels={"temperature_c": "Temperature (°C)", "timestamp": "UTC Time"},
    )
    fig.update_traces(line=dict(color="#00d2ff", width=2.8))
    fig = style_chart(fig, height=340)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.markdown("### 🌧️ Weather Drivers")
    plot = weather.melt(
        id_vars="timestamp",
        value_vars=["humidity_pct", "wind_ms", "precipitation_mm"],
        var_name="metric",
        value_name="value",
    )
    fig = px.line(
        plot, 
        x="timestamp", 
        y="value", 
        color="metric",
        labels={"value": "Magnitude", "timestamp": "UTC Time", "metric": "Signal"}
    )
    fig.update_traces(line=dict(width=2.4))
    fig.for_each_trace(lambda t: t.update(line=dict(color={
        "humidity_pct": "#00d2ff",
        "wind_ms": "#2ee59d",
        "precipitation_mm": "#ff708d",
    }.get(t.name, "#00d2ff"))))
    fig = style_chart(fig, height=340)
    st.plotly_chart(fig, use_container_width=True)

# Row 2: Atmospheric Signals
st.markdown("### 🌫️ Air-Quality & Atmospheric Trace Gases")
if not aq_hourly.empty:
    available = [c for c in ["pm2_5", "carbon_dioxide", "nitrogen_dioxide", "ozone"] if c in aq_hourly.columns]
    selected = st.multiselect("Select telemetry signals to display", available, default=available[:2])
    if selected:
        fig = px.line(
            aq_hourly, 
            x="time", 
            y=selected,
            labels={"value": "Concentration", "time": "Timestamp", "variable": "Pollutant"}
        )
        fig.update_traces(line=dict(width=2.4))
        fig = style_chart(fig, height=360)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No hourly air-quality data returned for this location.")

# Row 3: Historical Emissions
st.markdown(f"### 🏭 Long-term CO₂ Emissions — {country}")
if not country_df.empty:
    fig = px.area(
        country_df,
        x="year",
        y="co2",
        labels={"co2": "Million Tonnes CO₂", "year": "Year"},
    )
    fig.update_traces(
        line=dict(color="#00d2ff", width=2), 
        fillcolor="rgba(0, 210, 255, 0.18)"
    )
    fig = style_chart(fig, height=380)
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("🔎 View Cleaned Emissions History Table"):
        st.dataframe(country_df.tail(15), use_container_width=True)
else:
    st.warning("No emissions records found for this selection.")

with st.expander("📘 Analyst Methodology & Verification Notes"):
    st.markdown("""
- **Live Ingestion**: REST parameters queried live via `NASA POWER` and `Open-Meteo`.
- **Data Hygiene**: Replaced `-999` sentinels with `NaN`, ISO timestamp parsing, explicit timezone anchoring.
- **Metric Distinction**: Separates **atmospheric ambient concentration (ppm)** from **national annual emissions output (Mt CO₂)**.
""")

st.caption("Sources: NASA POWER API • Open-Meteo Air Quality API • Our World in Data CO₂ dataset.")