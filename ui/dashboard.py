import os
import httpx
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
API_KEY = os.environ.get("API_KEY", "default_secret_key")

st.set_page_config(page_title="CostGuard Dashboard", layout="wide", page_icon="🛡")

# --- Custom CSS ---
st.markdown("""
<style>
    /* Dark theme overrides */
    .stApp { background-color: #0e1117; }
    .metric-card {
        background: linear-gradient(135deg, #1e2530 0%, #1a1f2e 100%);
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.5rem 0;
    }
    .metric-value { font-size: 2rem; font-weight: 700; color: #e2e8f0; }
    .metric-label { font-size: 0.85rem; color: #a0aec0; text-transform: uppercase; letter-spacing: 0.05em; }
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #e2e8f0;
        margin: 1.5rem 0 0.8rem 0;
        padding-bottom: 0.3rem;
        border-bottom: 2px solid #4a6cf7;
        display: inline-block;
    }
    div[data-testid="stSidebar"] { background: linear-gradient(180deg, #111827 0%, #0e1117 100%); }
    .stPlotlyChart { border-radius: 12px; overflow: hidden; }
    
    /* Chat Bubble Styles */
    .chat-container { display: flex; flex-direction: column; gap: 8px; padding: 10px; }
    .chat-msg {
        background: #2d3748;
        color: #e2e8f0;
        padding: 8px 12px;
        border-radius: 12px 12px 12px 0;
        max-width: 80%;
        align-self: flex-start;
        font-size: 0.9rem;
        border: 1px solid #4a5568;
    }
    .agent-msg {
        background: #2b4c7e;
        color: #fff;
        border-radius: 12px 12px 0 12px;
        align-self: flex-end;
        border: 1px solid #4a6cf7;
    }
    .system-msg {
        color: #718096;
        font-size: 0.75rem;
        text-align: center;
        margin: 4px 0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.markdown("# CostGuard")
st.sidebar.markdown("---")
page = st.sidebar.selectbox("Navigate", ["Overview", "LLM Usage", "Anomalies", "Actions", "Agent Control"])

HEADERS = {"Content-Type": "application/json", "X-API-Key": API_KEY}
TIMEOUT = 45.0
client = httpx.Client(timeout=TIMEOUT)

# Color palette
COLORS = ["#4a6cf7", "#f97316", "#10b981", "#ef4444", "#8b5cf6", "#06b6d4", "#f59e0b", "#ec4899"]
SEVERITY_COLORS = {"low": "#10b981", "medium": "#f59e0b", "high": "#f97316", "critical": "#ef4444"}
STATUS_COLORS = {"pending": "#f59e0b", "approved": "#4a6cf7", "denied": "#ef4444", "executed": "#10b981", "failed": "#6b7280"}

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#a0aec0", family="Inter, sans-serif"),
    margin=dict(l=40, r=20, t=40, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)


def safe_get(path: str, params: dict | None = None) -> dict | None:
    try:
        resp = client.get(f"{BACKEND_URL}{path}", params=params, headers=HEADERS)
        if resp.status_code == 200:
            return resp.json()
        st.sidebar.error(f"Backend returned {resp.status_code} for {path}")
        return None
    except Exception as e:
        st.sidebar.error(f"Error fetching {path}: {e}")
        return None


def safe_post(path: str, json_data: dict | None = None) -> dict | None:
    try:
        resp = client.post(f"{BACKEND_URL}{path}", json=json_data, headers=HEADERS)
        if resp.status_code in [200, 201]:
            return resp.json()
        st.error(f"Action failed: {resp.status_code} - {resp.text}")
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# OVERVIEW PAGE
# ═══════════════════════════════════════════════════════════════
if page == "Overview":
    st.title("Cost Overview")

    summary = safe_get("/api/v1/summary")
    anomaly_stats = safe_get("/api/v1/stats/anomalies")
    action_stats = safe_get("/api/v1/stats/actions")

    # --- KPI Cards ---
    c1, c2, c3, c4 = st.columns(4)
    if summary:
        c1.metric("Monthly Spend", f"${summary.get('current_month_cost', 0):,.2f}", delta=summary.get('delta_percent'))
    else:
        c1.metric("Monthly Spend", "$--")

    if anomaly_stats:
        total_anomalies = sum(s["count"] for s in anomaly_stats.get("severity_breakdown", []))
        c2.metric("Active Anomalies", total_anomalies)
    else:
        c2.metric("Active Anomalies", "--")

    # Calculate Tomorrow's Cost for Demo Verification
    try:
        tomorrow_date = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
        tomorrow_cost = 0.0
        if summary and summary.get("daily_costs"):
            for day in summary["daily_costs"]:
                if day.get("date") == tomorrow_date:
                    tomorrow_cost = day.get("cost", 0.0)
        
        # If tomorrow has data (optimized), show it
        if tomorrow_cost > 0:
             c3.metric("Projected Cost (Tomorrow)", f"${tomorrow_cost:,.2f}", delta="-99%", delta_color="normal")
        elif action_stats:
             c3.metric("Potential Savings", f"${action_stats.get('total_potential_savings', 0):,.2f}")
        else:
             c3.metric("Potential Savings", "$--")
    except:
         c3.metric("Potential Savings", "$--")

    if action_stats:
        c4.metric("Realized Savings", f"${action_stats.get('realized_savings', 0):,.2f}")
    else:
        c4.metric("Realized Savings", "$--")

    # --- Charts Row 1: Cost Trend + Provider Breakdown ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Daily Cost Trend (Last 30 Days)")
        if summary and summary.get("daily_costs"):
            df = pd.DataFrame(summary["daily_costs"])
            if not df.empty:
                # Ensure date sorting
                df["date"] = pd.to_datetime(df["date"])
                df = df.sort_values("date")
                
                fig = px.area(df, x="date", y="cost", line_shape="spline",
                              color_discrete_sequence=["#8b5cf6"])
                fig.update_layout(xaxis_title=None, yaxis_title="Cost ($)", margin=dict(l=0, r=0, t=0, b=0), height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No cost data available for the last 30 days.")
        else:
            st.info("Loading cost data...")

    with col2:
        st.subheader("Provider Breakdown")
        if summary and summary.get("provider_breakdown"):
            df = pd.DataFrame(summary["provider_breakdown"])
            if not df.empty:
                fig = px.pie(df, values="cost", names="provider", hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Vivid)
                fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=300, showlegend=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No provider data available.")
        else:
            st.info("Loading breakdown configuration...")

    st.markdown("---")

    # --- Charts Row 2: Anomaly Stats ---
    if anomaly_stats and anomaly_stats.get("severity_breakdown"):
        st.subheader("Anomalies by Severity")
        df_sev = pd.DataFrame(anomaly_stats["severity_breakdown"])
        if not df_sev.empty:
            fig = px.bar(df_sev, x="severity", y="count", color="severity", 
                         color_discrete_map=SEVERITY_COLORS, text="count")
            fig.update_layout(height=300, xaxis_title="Severity", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown('<div class="section-header">Archestra.AI Integration</div>', unsafe_allow_html=True)
    
    # Allow manual override
    # Note: st.text_input key must be unique per page/section to avoid duplicate ID errors
    default_url_ov = os.environ.get('ARCHESTRA_API_URL', 'http://localhost:9000')
    archestra_url_ov = st.text_input("Archestra API URL", value=default_url_ov, key="arch_url_overview", help="Enter the URL where Archestra is running")
    
    is_online_ov = False
    final_url_ov = archestra_url_ov
    error_detail_ov = ""
    
    try:
        r = httpx.get(archestra_url_ov, timeout=1.0)
        if r.status_code in [200, 401, 403, 404]:
            is_online_ov = True
    except Exception as e:
        error_detail_ov = str(e)

    if not is_online_ov and "localhost" in archestra_url_ov and archestra_url_ov == default_url_ov:
        fallback = archestra_url_ov.replace("localhost", "host.docker.internal")
        try:
            r = httpx.get(fallback, timeout=1.0)
            if r.status_code in [200, 401, 403, 404]:
                is_online_ov = True
                final_url_ov = fallback
        except:
            pass

    status_color = "🟢" if is_online_ov else "🔴"
    status_text = "Online" if is_online_ov else "Offline"
    
    c1, c2 = st.columns([1, 2])
    c1.markdown(f"**Status:** {status_color} {status_text}")
    
    if is_online_ov:
        st.success(f"Connected to Archestra at {final_url_ov}")
    else:
        st.error(f"Could not reach Archestra. Error: {error_detail_ov}")

    st.markdown("---")

    # --- Charts Row 1: Cost Trend + Provider Breakdown ---
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown('<div class="section-header">Daily Cost Trend (30 Days)</div>', unsafe_allow_html=True)
        if summary and summary.get("daily_costs"):
            df = pd.DataFrame(summary["daily_costs"])
            fig = px.area(df, x="date", y="cost",
                          color_discrete_sequence=["#4a6cf7"],
                          labels={"cost": "Cost ($)", "date": "Date"})
            fig.update_layout(**PLOT_LAYOUT, height=320,
                              xaxis=dict(showgrid=False),
                              yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"))
            fig.update_traces(fill="tozeroy", fillcolor="rgba(74,108,247,0.15)", line=dict(width=2.5))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No daily cost data available. Click **Re-Seed Database** to populate.")

    with col_right:
        st.markdown('<div class="section-header">Spend by Provider</div>', unsafe_allow_html=True)
        if summary and summary.get("provider_breakdown"):
            df = pd.DataFrame(summary["provider_breakdown"])
            fig = px.pie(df, names="provider", values="cost",
                         color_discrete_sequence=COLORS, hole=0.55)
            fig.update_layout(**PLOT_LAYOUT, height=320, showlegend=True,
                              legend=dict(orientation="h", yanchor="bottom", y=-0.2))
            fig.update_traces(textposition="inside", textinfo="percent+label",
                              marker=dict(line=dict(color="#0e1117", width=2)))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No provider data.")

    # --- Charts Row 2: Top Services + Action Status ---
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="section-header">Top Services</div>', unsafe_allow_html=True)
        if summary and summary.get("top_services"):
            df = pd.DataFrame(summary["top_services"])
            fig = px.bar(df, x="Cost", y="Service", orientation="h",
                         color_discrete_sequence=["#4a6cf7"],
                         text="Cost")
            fig.update_layout(**PLOT_LAYOUT, height=280,
                              xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                              yaxis=dict(showgrid=False))
            fig.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No service data.")

    with col_b:
        st.markdown('<div class="section-header">Action Status Breakdown</div>', unsafe_allow_html=True)
        if action_stats and action_stats.get("status_breakdown"):
            df = pd.DataFrame(action_stats["status_breakdown"])
            colors = [STATUS_COLORS.get(s, "#6b7280") for s in df["status"]]
            fig = px.bar(df, x="status", y="count", color="status",
                         color_discrete_map=STATUS_COLORS,
                         text="count")
            fig.update_layout(**PLOT_LAYOUT, height=280, showlegend=False,
                              xaxis=dict(showgrid=False),
                              yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"))
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No action data.")


# ═══════════════════════════════════════════════════════════════
# LLM USAGE PAGE
# ═══════════════════════════════════════════════════════════════
elif page == "LLM Usage":
    st.title("LLM Usage Analytics")

    data = safe_get("/api/v1/llm/usage", {"limit": "500"})

    if data and isinstance(data, list) and len(data) > 0:
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["date"] = df["timestamp"].dt.date

        # KPI row
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Spend", f"${df['cost'].sum():,.2f}")
        c2.metric("Total Requests", f"{len(df):,}")
        c3.metric("Avg Latency", f"{df['latency_ms'].mean():,.0f} ms" if 'latency_ms' in df else "--")
        c4.metric("Models Used", f"{df['model'].nunique()}")

        st.markdown("---")

        # Charts
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="section-header">Daily LLM Spend</div>', unsafe_allow_html=True)
            daily = df.groupby("date")["cost"].sum().reset_index()
            fig = px.area(daily, x="date", y="cost",
                          color_discrete_sequence=["#8b5cf6"],
                          labels={"cost": "Cost ($)", "date": "Date"})
            fig.update_layout(**PLOT_LAYOUT, height=300,
                              xaxis=dict(showgrid=False),
                              yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"))
            fig.update_traces(fill="tozeroy", fillcolor="rgba(139,92,246,0.15)", line=dict(width=2.5))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown('<div class="section-header">Cost by Model</div>', unsafe_allow_html=True)
            model_costs = df.groupby("model")["cost"].sum().reset_index().sort_values("cost", ascending=True)
            fig = px.bar(model_costs, x="cost", y="model", orientation="h",
                         color_discrete_sequence=["#06b6d4"],
                         text="cost")
            fig.update_layout(**PLOT_LAYOUT, height=300,
                              xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                              yaxis=dict(showgrid=False))
            fig.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

        # Provider usage pie + quality scatter
        col3, col4 = st.columns(2)

        with col3:
            st.markdown('<div class="section-header">Provider Distribution</div>', unsafe_allow_html=True)
            prov = df.groupby("provider")["cost"].sum().reset_index()
            fig = px.pie(prov, names="provider", values="cost",
                         color_discrete_sequence=COLORS, hole=0.5)
            fig.update_layout(**PLOT_LAYOUT, height=300)
            fig.update_traces(textposition="inside", textinfo="percent+label",
                              marker=dict(line=dict(color="#0e1117", width=2)))
            st.plotly_chart(fig, use_container_width=True)

        with col4:
            st.markdown('<div class="section-header">Cost vs Quality</div>', unsafe_allow_html=True)
            if "quality_score" in df.columns:
                fig = px.scatter(df.dropna(subset=["quality_score"]),
                                 x="cost", y="quality_score", color="provider",
                                 size="output_tokens",
                                 color_discrete_sequence=COLORS,
                                 labels={"cost": "Cost ($)", "quality_score": "Quality"})
                fig.update_layout(**PLOT_LAYOUT, height=300,
                                  xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                                  yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No quality data.")

        # Data table
        st.markdown('<div class="section-header">Recent Requests</div>', unsafe_allow_html=True)
        st.dataframe(df.head(50).drop(columns=["date"], errors="ignore"),
                      use_container_width=True, height=300)
    else:
        st.info("No LLM usage data. Click **Re-Seed Database** in the sidebar to populate.")


# ═══════════════════════════════════════════════════════════════
# ANOMALIES PAGE
# ═══════════════════════════════════════════════════════════════
elif page == "Anomalies":
    st.title("Cost Anomalies")

    data = safe_get("/api/v1/anomalies")
    stats = safe_get("/api/v1/stats/anomalies")

    if stats:
        # KPI row
        sev = {s["severity"]: s["count"] for s in stats.get("severity_breakdown", [])}
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Anomalies", sum(sev.values()))
        c2.metric("🔴 Critical/High", sev.get("critical", 0) + sev.get("high", 0))
        c3.metric("🟡 Medium", sev.get("medium", 0))
        c4.metric("🟢 Low", sev.get("low", 0))

        st.markdown("---")

        # Charts row
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="section-header">Severity Distribution</div>', unsafe_allow_html=True)
            if stats.get("severity_breakdown"):
                df_sev = pd.DataFrame(stats["severity_breakdown"])
                colors = [SEVERITY_COLORS.get(s, "#6b7280") for s in df_sev["severity"]]
                fig = go.Figure(go.Bar(
                    x=df_sev["severity"], y=df_sev["count"],
                    marker_color=colors, text=df_sev["count"],
                    textposition="outside"
                ))
                fig.update_layout(**PLOT_LAYOUT, height=280, title=None,
                                  xaxis=dict(showgrid=False),
                                  yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"))
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown('<div class="section-header">Anomalies by Provider</div>', unsafe_allow_html=True)
            if stats.get("provider_breakdown"):
                df_prov = pd.DataFrame(stats["provider_breakdown"])
                fig = px.pie(df_prov, names="provider", values="count",
                             color_discrete_sequence=COLORS, hole=0.5)
                fig.update_layout(**PLOT_LAYOUT, height=280)
                fig.update_traces(textposition="inside", textinfo="percent+label",
                                  marker=dict(line=dict(color="#0e1117", width=2)))
                st.plotly_chart(fig, use_container_width=True)

        # Anomaly timeline
        if stats.get("timeline"):
            st.markdown('<div class="section-header">Anomaly Timeline</div>', unsafe_allow_html=True)
            df_tl = pd.DataFrame(stats["timeline"])
            fig = px.scatter(df_tl, x="date", y="count", size="avg_deviation",
                             color_discrete_sequence=["#ef4444"],
                             labels={"count": "Anomalies", "date": "Date", "avg_deviation": "Avg Deviation %"})
            fig.update_layout(**PLOT_LAYOUT, height=250,
                              xaxis=dict(showgrid=False),
                              yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"))
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Anomaly list
    if data is not None:
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            st.info("No anomalies found. Run an **Agent Scan** to detect anomalies.")

        for a in items:
            sev_color = SEVERITY_COLORS.get(a.get("severity", ""), "#6b7280")
            with st.container():
                cols = st.columns([1, 1, 4, 2])
                cols[0].markdown(f'<span style="background:{sev_color};color:white;padding:2px 10px;border-radius:4px;font-weight:600;font-size:0.85rem">{a.get("severity", "UNKNOWN").upper()}</span>', unsafe_allow_html=True)
                cols[1].write(f'**{a.get("provider", "")}**')
                cols[2].write(f'{a.get("description")} ({a.get("service")})')
                cols[3].write(f'${a.get("current_cost", 0):,.2f} / ${a.get("expected_cost", 0):,.2f}')
                st.divider()
    else:
        st.info("No anomalies found (or backend not reachable).")


# ═══════════════════════════════════════════════════════════════
# ACTIONS PAGE
# ═══════════════════════════════════════════════════════════════
elif page == "Actions":
    st.title("Optimization Actions")

    data = safe_get("/api/v1/actions")
    stats = safe_get("/api/v1/stats/actions")

    if stats:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Potential Savings", f"${stats.get('total_potential_savings', 0):,.2f}")
        c2.metric("Realized Savings", f"${stats.get('realized_savings', 0):,.2f}")
        breakdown = {s["status"]: s["count"] for s in stats.get("status_breakdown", [])}
        c3.metric("Pending Actions", breakdown.get("pending", 0))

        # Action status pie chart
        if stats.get("status_breakdown"):
            st.markdown('<div class="section-header">Action Status Distribution</div>', unsafe_allow_html=True)
            df_stat = pd.DataFrame(stats["status_breakdown"])
            fig = px.pie(df_stat, names="status", values="count",
                         color="status", color_discrete_map=STATUS_COLORS, hole=0.5)
            fig.update_layout(**PLOT_LAYOUT, height=260)
            fig.update_traces(textposition="inside", textinfo="percent+label",
                              marker=dict(line=dict(color="#0e1117", width=2)))
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    if data:
        items = data if isinstance(data, list) else data.get("items", [])
        for action in items:
            status_color = STATUS_COLORS.get(action.get("status", ""), "#6b7280")
            with st.expander(f"🔧 {action.get('description', 'Action')} — **{action.get('status', 'unknown').upper()}**"):
                c1, c2, c3 = st.columns(3)
                c1.write(f"**Type:** {action.get('action_type', '--')}")
                c2.write(f"**Est. Savings:** ${action.get('estimated_savings', 0):,.2f}")
                c3.write(f"**Risk:** {action.get('risk_level', '--')}")

                if action.get("status") == "pending":
                    bc1, bc2, bc3 = st.columns(3)
                    if bc1.button("✅ Approve", key=f"approve_{action['id']}"):
                        res = safe_post(f"/api/v1/actions/{action['id']}/approve")
                        if res:
                            st.success(f"Action approved!")
                            st.rerun()
                    if bc2.button("❌ Reject", key=f"reject_{action['id']}"):
                        res = safe_post(f"/api/v1/actions/{action['id']}/deny")
                        if res:
                            st.warning(f"Action rejected.")
                            st.rerun()
                    if bc3.button("⚡ Execute Now", key=f"exec_{action['id']}"):
                        res = safe_post(f"/api/v1/agents/execute/{action['id']}")
                        if res:
                            st.success(res.get("message", "Executed!"))
                            st.rerun()
                elif action.get("status") == "approved":
                    if st.button("⚡ Execute Now", key=f"exec_{action['id']}"):
                        res = safe_post(f"/api/v1/agents/execute/{action['id']}")
                        if res:
                            st.success(res.get("message", "Executed!"))
                            st.rerun()
    else:
        st.write("No actions or backend unreachable.")


# ═══════════════════════════════════════════════════════════════
# AGENT CONTROL PAGE
# ═══════════════════════════════════════════════════════════════
elif page == "Agent Control":
    st.title("Agent Control Panel")
    st.markdown("Trigger AI agents to scan for anomalies and execute optimizations.")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">Detective Agent</div>', unsafe_allow_html=True)
        st.markdown("Scans LLM usage data for cost anomalies by comparing today's spend against a 7-day rolling average.")
        
        # Simulate spike — unified demo button
        if st.button("Simulate Cost Spike", use_container_width=True, type="primary"):
            with st.spinner("Injecting spike data and scanning..."):
                res = safe_post("/api/v1/agents/simulate-spike")
                if res:
                    scan = res.get("scan_result", {})
                    st.success(
                        f"Spike injected! **${res.get('spike_total_cost', 0):.2f}** in fake costs added.\n\n"
                        f"🔍 Scan found **{scan.get('anomalies_found', 0)}** anomalies, created **{scan.get('actions_created', 0)}** actions."
                    )
                    if scan.get("details"):
                        for d in scan["details"]:
                            sev_color = SEVERITY_COLORS.get(d.get("severity", ""), "#6b7280")
                            st.markdown(f'<span style="background:{sev_color};color:white;padding:2px 8px;border-radius:4px;font-size:0.8rem">{d["severity"].upper()}</span> {d["description"]}', unsafe_allow_html=True)
                    st.info("Navigate to **Overview**, **Anomalies**, or **Actions** to see the updated charts!")
        
        st.markdown("")
        
        # Regular scan button
        if st.button("Run Anomaly Scan", use_container_width=True):
            with st.spinner("Scanning for anomalies..."):
                res = safe_post("/api/v1/agents/scan")
                if res:
                    st.success(f"Scan complete! Found **{res.get('anomalies_found', 0)}** anomalies, created **{res.get('actions_created', 0)}** actions.")
                    if res.get("details"):
                        for d in res["details"]:
                            sev_color = SEVERITY_COLORS.get(d.get("severity", ""), "#6b7280")
                            st.markdown(f'<span style="background:{sev_color};color:white;padding:2px 8px;border-radius:4px;font-size:0.8rem">{d["severity"].upper()}</span> {d["description"]}', unsafe_allow_html=True)
                    else:
                        st.info("No new anomalies detected — costs are within normal range.")

    with col2:
        st.markdown('<div class="section-header">Executor Agent</div>', unsafe_allow_html=True)
        st.markdown("Execute approved optimization actions to reduce cloud spend.")

        # Show pending/approved actions for quick execution
        actions = safe_get("/api/v1/actions")
        if actions:
            actionable = [a for a in actions if a.get("status") in ("pending", "approved")]
            if actionable:
                for a in actionable[:5]:
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"• {a.get('description', '--')} (${a.get('estimated_savings', 0):.2f})")
                    if c2.button("Execute", key=f"ctrl_exec_{a['id']}"):
                        res = safe_post(f"/api/v1/agents/execute/{a['id']}")
                        if res:
                            st.success(res.get("message", "Done!"))
                            st.rerun()
            else:
                st.info("No actionable items. Run a scan first.")
        else:
            st.info("Could not load actions.")

    st.markdown("---")
    st.markdown("---")
    st.markdown('<div class="section-header">Archestra.AI Integration</div>', unsafe_allow_html=True)
    
    # Allow manual override for debugging
    default_url = os.environ.get('ARCHESTRA_API_URL', 'http://localhost:9000')
    archestra_url = st.text_input("Archestra API URL", value=default_url, help="Enter the URL where Archestra is running (e.g., http://host.docker.internal:9000)")
    
    # Auto-fallback logic only if user hasn't changed the default
    is_online = False
    final_url = archestra_url
    error_detail = ""
    
    # 1. Try configured/entered URL
    try:
        r = httpx.get(archestra_url, timeout=1.0)
        if r.status_code in [200, 401, 403, 404]:
            is_online = True
    except Exception as e:
        error_detail = str(e)

    # 2. If failed and URL is simply 'localhost', try host.docker.internal as a courtesy fallback
    if not is_online and "localhost" in archestra_url and archestra_url == default_url:
        fallback_url = archestra_url.replace("localhost", "host.docker.internal")
        try:
            r = httpx.get(fallback_url, timeout=1.0)
            if r.status_code in [200, 401, 403, 404]:
                is_online = True
                final_url = fallback_url
        except:
            pass

    status_color = "🟢" if is_online else "🔴"
    status_text = "Online" if is_online else "Offline"
    
    c1, c2 = st.columns([1, 2])
    c1.markdown(f"**Status:** {status_color} {status_text}")
    
    if is_online:
        st.success(f"Connected to Archestra at {final_url}")
    else:
        st.error(f"Could not reach Archestra. Error: {error_detail or 'Connection failed'}")
        st.info("Tip: If running in Docker on Windows/Mac, try using http://host.docker.internal:9000")

    st.markdown("### Interaction Logs")
    with st.expander("Live Archestra Communication", expanded=True):
        logs = safe_get("/api/v1/archestra/logs")
        if logs:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for entry in reversed(logs):
                # We show Bridge events as system notes, and Agent replies as bubbles
                msg_type = entry.get("type", "")
                status = entry.get("status", "")
                details = entry.get("details", "")
                ts = entry.get("timestamp", "")

                if msg_type == "Agent":
                    st.markdown(f'<div class="chat-msg agent-msg"><b>🤖 Agent:</b><br>{details}<br><small style="color:#cbd5e0">{ts}</small></div>', unsafe_allow_html=True)
                elif msg_type == "Bridge" and status == "Sending":
                     # This is effectively our message
                     st.markdown(f'<div class="chat-msg"><b>🛡 CostGuard:</b><br>{details}<br><small style="color:#a0aec0">{ts}</small></div>', unsafe_allow_html=True)
                else:
                    # Generic status update
                    st.markdown(f'<div class="system-msg">{status}: {details[:50]}... ({ts})</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No interaction logs yet. Trigger an action to see activity.")


# ═══════════════════════════════════════════════════════════════
# SIDEBAR FOOTER
# ═══════════════════════════════════════════════════════════════
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Re-Seed Database"):
    res = safe_post("/api/v1/debug/seed")
    if res:
        st.sidebar.success(res.get("message"))

st.sidebar.caption("CostGuard v2.0 — Teams A, B & C")
