import os
import httpx
import streamlit as st
from datetime import datetime, timedelta

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="CostGuard Dashboard", layout="wide")

st.sidebar.title("CostGuard")
page = st.sidebar.selectbox("Page", ["Overview", "LLM Usage", "Anomalies", "Actions"])

HEADERS = {"Content-Type": "application/json"}
TIMEOUT = 5.0

client = httpx.Client(timeout=TIMEOUT)


def safe_get(path: str, params: dict | None = None) -> dict | None:
    try:
        resp = client.get(f"{BACKEND_URL}{path}", params=params, headers=HEADERS)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None


if page == "Overview":
    st.title("Overview")
    st.markdown("Monthly spend summary and top services")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("This month", "$12,345", delta="+3.2%")
        st.line_chart([100, 120, 90, 140, 160, 180])
    with col2:
        st.subheader("Top services")
        st.table(
            {
                "Service": ["EC2", "S3", "BigQuery", "ManagedDB"],
                "Cost": [5234.1, 2345.2, 1987.0, 987.0],
            }
        )

    st.info(
        "This view will fetch normalized cost-summary from the backend when available (env `BACKEND_URL`)."
    )

elif page == "LLM Usage":
    st.title("LLM Usage")
    rng = st.selectbox("Range", ["24h", "7d", "30d"], index=1)
    params = {"range": rng}
    data = safe_get("/api/v1/llm/usage", params)
    if data:
        st.write(data)
    else:
        st.warning("Backend not available or returned no data. Showing demo stats.")
        st.table({"Model": ["gpt-4o", "gpt-4o-mini"], "Tokens": [12345, 5432], "Cost": [12.3, 4.2]})

elif page == "Anomalies":
    st.title("Anomalies")
    data = safe_get("/api/v1/anomalies")
    if data:
        for a in data.get("items", [])[:20]:
            st.card(f"{a.get('id')} - {a.get('severity')}")
    else:
        st.info("No anomalies found (or backend not reachable).")

elif page == "Actions":
    st.title("Optimization Actions")
    data = safe_get("/api/v1/actions")
    if data:
        st.write(data)
    else:
        st.write("No pending actions or backend unreachable.")


st.sidebar.markdown("---")
st.sidebar.caption("UI built by Team C — local dev: `BACKEND_URL` env var")
