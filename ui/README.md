# UI (Team C)

This folder contains the Streamlit dashboard for CostGuard.

Quick start (local):

```bash
# build image (optional)
docker build -t costguard/ui:local -f ui/Dockerfile ui/

# run with docker-compose override
BACKEND_URL=http://localhost:8000 docker compose -f docker/ui-compose.yml up --build

# or run locally without docker
python -m pip install streamlit httpx pandas plotly
streamlit run ui/dashboard.py
```

Notes
- The UI expects a backend API reachable at the `BACKEND_URL` env var. By default it points to `http://localhost:8000`.
- Do not modify `docker-compose.yml` in the repo root; use `docker/ui-compose.yml` to avoid conflicts with other teams.
- Before wiring UI actions to endpoints, confirm route shapes with Team A.
