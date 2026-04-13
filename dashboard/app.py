import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import date

import subprocess

def refresh_data():
    """Re-export activities from PostgreSQL to CSV before loading."""
    try:
        subprocess.run(
            ["python", "scripts/export_activities.py"],
            capture_output=True
        )
    except Exception as e:
        st.warning(f"Could not refresh data: {e}")

API_BASE = "http://localhost:8000"
RACE_DATE = "2026-11-01"

st.set_page_config(
    page_title="Marathon Coach",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    /* Global */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .block-container {
        padding: 2rem 2rem 2rem 2rem;
        max-width: 900px;
    }

    /* Metric cards */
    .metric-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        border: 1px solid #e9ecef;
    }
    .metric-label {
        font-size: 12px;
        color: #6c757d;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #212529;
        line-height: 1.2;
    }
    .metric-sub {
        font-size: 12px;
        color: #adb5bd;
        margin-top: 4px;
    }

    /* Risk badge */
    .badge-low {
        background: #d1fae5;
        color: #065f46;
        padding: 4px 12px;
        border-radius: 99px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-high {
        background: #fee2e2;
        color: #991b1b;
        padding: 4px 12px;
        border-radius: 99px;
        font-size: 12px;
        font-weight: 600;
    }
            
    .stApp {
            animation: none !important;
            transition: none !important;
    }

    /* Plan day card */
    .day-card {
        background: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 0.9rem 1.2rem;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .day-name { font-weight: 600; font-size: 14px; color: #212529; }
    .day-detail { font-size: 13px; color: #6c757d; }

    /* Run type pills */
    .pill-easy   { background:#dbeafe; color:#1e40af; padding:2px 10px; border-radius:99px; font-size:11px; font-weight:600; }
    .pill-tempo  { background:#fef9c3; color:#854d0e; padding:2px 10px; border-radius:99px; font-size:11px; font-weight:600; }
    .pill-long   { background:#ede9fe; color:#5b21b6; padding:2px 10px; border-radius:99px; font-size:11px; font-weight:600; }
    .pill-rest   { background:#f3f4f6; color:#6b7280; padding:2px 10px; border-radius:99px; font-size:11px; font-weight:600; }

    /* Insight box */
    .insight-box {
        background: #eff6ff;
        border-left: 3px solid #3b82f6;
        border-radius: 0 8px 8px 0;
        padding: 0.8rem 1rem;
        font-size: 13px;
        color: #1e40af;
        margin-top: 8px;
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def fetch_fitness():
    try:
        r = requests.get(f"{API_BASE}/athlete/fitness", timeout=5)
        return r.json()
    except Exception as e:
        st.error(f"fetch_fitness error: {e}")
        return None

@st.cache_data(ttl=60)
def fetch_plan():
    try:
        r = requests.get(
            f"{API_BASE}/plan/weekly",
            params={"race_date": RACE_DATE},
            timeout=5
        )
        return r.json()
    except:
        return None

@st.cache_data(ttl=60)
def fetch_trends():
    try:
        r = requests.get(f"{API_BASE}/athlete/trends", timeout=5)
        return r.json()
    except:
        return None


def pill(run_type):
    t = run_type.lower()
    if "easy"  in t: return f'<span class="pill-easy">{run_type}</span>'
    if "tempo" in t: return f'<span class="pill-tempo">{run_type}</span>'
    if "long"  in t: return f'<span class="pill-long">{run_type}</span>'
    return f'<span class="pill-rest">{run_type}</span>'


# ── Header ──
st.markdown("## Marathon Coach")
st.markdown(
    f"<span style='color:#6c757d;font-size:14px'>NYC Marathon · "
    f"{(date(2026, 11, 1) - date.today()).days} days away</span>",
    unsafe_allow_html=True
)
st.markdown("---")

# ── Navigation ──
page = st.radio(
    "Navigationn",
    ["Dashboard", "This week", "Trends", "Connect Strava"],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)


# ══════════════════════════════
# PAGE 1 — DASHBOARD
# ══════════════════════════════
if page == "Dashboard":
    fitness = fetch_fitness()

    if not fitness:
        st.error("Could not connect to API. Make sure Docker is running.")
        st.stop()

    risk = fitness.get("overtraining_risk", "Low")
    risk_color = "green" if risk == "Low" else "red"

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Predicted finish",
            value=fitness.get("predicted_finish", "--"),
            help="Your predicted NYC Marathon finish time"
        )

    with col2:
        st.metric(
            label="Overtraining risk",
            value=risk,
            help=f"{fitness.get('risk_confidence', '--')}% confidence"
        )

    with col3:
        st.metric(
            label="Top factor",
            value=fitness.get("top_factor", "--"),
            help="Biggest driver of your prediction today"
        )

    st.markdown("---")

    insight = fitness.get("insight", "")
    if insight:
        st.info(f'"{insight}"')

    st.markdown("---")
    st.subheader("SHAP breakdown")
    st.caption("Negative = faster, Positive = slower")

    shap = fitness.get("shap_values", {})
    for feature, value in sorted(shap.items(), key=lambda x: abs(x[1]), reverse=True):
        direction = "faster" if value < 0 else "slower"
        st.write(f"**{feature}** — {value:+.1f} min ({direction})")


# ══════════════════════════════
# PAGE 2 — THIS WEEK
# ══════════════════════════════
elif page == "This week":
    plan = fetch_plan()

    if not plan:
        st.error("Could not connect to API. Make sure Docker is running.")
        st.stop()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Phase</div>
            <div class="metric-value" style="font-size:20px;text-transform:capitalize">
                {plan.get('phase','--')}
            </div>
            <div class="metric-sub">{plan.get('weeks_to_race','--')} weeks to race</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total this week</div>
            <div class="metric-value">{plan.get('total_km', '--')} km</div>
            <div class="metric-sub">Planned volume</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Predicted finish</div>
            <div class="metric-value">{plan.get('predicted_finish','--')}</div>
            <div class="metric-sub">Current estimate</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    for day in plan.get("schedule", []):
        run_type = day["type"]
        if run_type == "Rest":
            detail = "Rest or light cross-training"
            km_str = ""
        else:
            detail = day.get("pace", "")
            km_str = f"{day['km']} km · "

        st.markdown(f"""
        <div class="day-card">
            <div>
                <div class="day-name">{day['day']}</div>
                <div class="day-detail">{km_str}{detail}</div>
            </div>
            {pill(run_type)}
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════
# PAGE 3 — TRENDS
# ══════════════════════════════
elif page == "Trends":
    trends = fetch_trends()

    if not trends:
        st.error("Could not connect to API. Make sure Docker is running.")
        st.stop()

    rows = trends.get("trends", [])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Best pace (8w)</div>
            <div class="metric-value">{trends.get('best_pace','--')}</div>
            <div class="metric-sub">per km</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Avg weekly km</div>
            <div class="metric-value">{trends.get('avg_weekly_km','--')}</div>
            <div class="metric-sub">last 8 weeks</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Worst pace (8w)</div>
            <div class="metric-value">{trends.get('worst_pace','--')}</div>
            <div class="metric-sub">per km</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    if rows:
        dates  = [r["date"]   for r in rows]
        paces  = [r["pace_s"] for r in rows]
        labels = [r["pace"]   for r in rows]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=paces,
            mode="lines+markers",
            line=dict(color="#3b82f6", width=2.5),
            marker=dict(size=7, color="#3b82f6"),
            text=labels,
            hovertemplate="%{x}<br>Pace: %{text} /km<extra></extra>",
        ))
        fig.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=280,
            xaxis=dict(showgrid=False, title=""),
            yaxis=dict(
                showgrid=True,
                gridcolor="#f0f0f0",
                title="sec/km",
                autorange="reversed",
            ),
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(size=12),
        )
        st.plotly_chart(fig, use_container_width=False, width=800)
        st.caption("Lower is faster. Y-axis shows pace in seconds per km.")


# ══════════════════════════════
# PAGE 4 — CONNECT STRAVA
# ══════════════════════════════
elif page == "Connect Strava":
    st.markdown("### Connect your Strava account")
    st.markdown(
        "Authorize access to your Strava activities. "
        "This will import all your runs and keep them updated automatically."
    )
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    strava_url = f"{API_BASE}/auth/strava"
    st.markdown(f"""
    <a href="{strava_url}" target="_self">
        <button style="
            background:#fc4c02;
            color:white;
            border:none;
            padding:12px 28px;
            border-radius:8px;
            font-size:15px;
            font-weight:600;
            cursor:pointer;
            letter-spacing:0.02em;
        ">Connect with Strava</button>
    </a>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.markdown("**What we access:**")
    st.markdown("- Your public profile (name, city)")
    st.markdown("- Your activity list (runs only)")
    st.markdown("- Distance, pace, elevation per run")
    st.markdown("")
    st.markdown(
        "<span style='color:#adb5bd;font-size:12px'>"
        "We never access heart rate data, segments, or personal records. "
        "You can revoke access at any time from your Strava settings."
        "</span>",
        unsafe_allow_html=True
    )
