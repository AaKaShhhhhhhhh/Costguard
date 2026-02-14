import os
import httpx
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
API_KEY = os.environ.get("API_KEY", "default_secret_key")
st.sidebar.write(f"DEBUG: Connecting to {BACKEND_URL}")

st.set_page_config(page_title="CostGuard Dashboard", layout="wide")

st.sidebar.title("CostGuard")
page = st.sidebar.selectbox("Page", ["Overview", "LLM Usage", "Anomalies", "Actions"])

HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}
TIMEOUT = 5.0

client = httpx.Client(timeout=TIMEOUT)


def safe_get(path: str, params: dict | None = None) -> dict | None:
    try:
        url = f"{BACKEND_URL}{path}"
        resp = client.get(url, params=params, headers=HEADERS)
        if resp.status_code == 200:
            return resp.json()
        
        detail = "No detail provided"
        try:
            detail = resp.json().get("detail", resp.text)
        except:
            detail = resp.text
            
        st.sidebar.error(f"Backend returned {resp.status_code} for {path}")
        st.sidebar.write(f"Error Detail: {detail}")
        return None
    except Exception as e:
        st.sidebar.error(f"Error fetching {path}: {e}")
        return None


def safe_post(path: str, json_data: dict | None = None) -> dict | None:
    try:
        resp = client.post(f"{BACKEND_URL}{path}", json=json_data, headers=HEADERS)
        if resp.status_code in [200, 201]:
            return resp.json()
        else:
            st.error(f"Action failed: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        st.error(f"Error sending data: {e}")
        return None


if page == "Overview":
    st.title("Overview")
    st.markdown("Monthly spend summary and top services")
    
    # Placeholder for summary endpoint, e.g., /api/v1/summary
    # efficient approach: reuse safe_get logic
    summary = safe_get("/api/v1/summary")

    col1, col2 = st.columns(2)
    with col1:
        if summary:
            st.metric("This month", f"${summary.get('current_month_cost', 0):,.2f}", delta=summary.get('delta_percent'))
            # chart_data = summary.get('daily_costs', [])
            # st.line_chart(chart_data)
        else:
            st.metric("This month", "$--", delta="--%")
            st.info("Backend summary not available.")

    with col2:
        st.subheader("Top services")
        if summary and 'top_services' in summary:
            st.table(summary['top_services'])
        else:
            st.info("No service data.")

elif page == "LLM Usage":
    st.title("LLM Usage")
    rng = st.selectbox("Range", ["24h", "7d", "30d"], index=1)
    params = {"range": rng}
    data = safe_get("/api/v1/llm/usage", params)
    
    if data and isinstance(data, list):
         df = pd.DataFrame(data)
         if not df.empty:
             st.dataframe(df)
             st.bar_chart(df, x='model', y='cost')
         else:
             st.info("No usage data returned.")
    elif data:
        st.write(data)
    else:
        st.warning("Backend not available or returned no data.")

elif page == "Anomalies":
    st.title("Anomalies")
    data = safe_get("/api/v1/anomalies")
    
    if data is not None:
        # Assuming data is a list of anomalies or dict with 'items'
        items = data if isinstance(data, list) else data.get("items", [])
        
        if not items:
            st.info("No anomalies found in the database.")
        
        for a in items:
            with st.container():
                cols = st.columns([1, 4, 2])
                cols[0].write(f"**{a.get('severity', 'UNKNOWN')}**")
                cols[1].write(f"{a.get('description')} ({a.get('service')})")
                
                # Check if action is required/available
                action_id = a.get('action_id') # Hypothetical link
                if action_id:
                    if cols[2].button(f"View Action {action_id}", key=f"btn_{a['id']}"):
                         st.session_state['page'] = 'Actions' # Naive navigation
                         st.experimental_rerun()
                else:
                    cols[2].write("No action linked")
                st.divider()

    else:
        st.info("No anomalies found (or backend not reachable).")

elif page == "Actions":
    st.title("Optimization Actions")
    data = safe_get("/api/v1/actions")
    
    if data:
        items = data if isinstance(data, list) else data.get("items", [])
        for action in items:
            with st.expander(f"{action.get('id')} - {action.get('status')}"):
                st.write(f"**Description:** {action.get('description')}")
                st.write(f"**Estimated Savings:** ${action.get('estimated_savings')}")
                
                if action.get('status') == 'pending':
                    c1, c2 = st.columns(2)
                    if c1.button("Approve", key=f"approve_{action['id']}"):
                        res = safe_post(f"/api/v1/actions/{action['id']}/approve")
                        if res:
                            st.success(f"Action {action['id']} approved!")
                            st.rerun()
                    
                    if c2.button("Reject", key=f"reject_{action['id']}"):
                        # Assuming reject endpoint exists or similar logic
                        res = safe_post(f"/api/v1/actions/{action['id']}/deny")
                        if res:
                            st.warning(f"Action {action['id']} rejected!")
                            st.rerun()
    else:
        st.write("No pending actions or backend unreachable.")


st.sidebar.markdown("---")
if st.sidebar.button("FIX: Re-Seed Database"):
    res = safe_post("/api/v1/debug/seed")
    if res:
        st.sidebar.success(res.get("message"))

st.sidebar.caption("UI built by Team C — local dev: `BACKEND_URL` env var")
