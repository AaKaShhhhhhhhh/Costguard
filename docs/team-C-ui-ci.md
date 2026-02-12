# Team C — UI, CI/CD & Dockerization (Simplified)

Purpose
- Build the Streamlit dashboard, create Dockerfiles and `docker-compose` for local dev, and add CI workflows to run tests and build images. Team C owns all Docker work and CI pipelines.

See the detailed Docker workflow in [CHECKLIST_DOCKER.md](CHECKLIST_DOCKER.md).

Deliverables (short)
- `ui/` Streamlit app with pages: Overview, LLM Usage, Anomalies, Actions
- Dockerfiles for `backend`, `mcp-servers/*` (as documented by Team B), and `ui`
- `docker-compose.yml` updated for local development
- GitHub Actions: `test.yml` (lint & tests) and `build.yml` (build/push images)
- `scripts/deploy_archestra.sh` template to deploy workflows to Archestra.AI

Docker checklist (practical)
- Use `python:3.10-slim` base and install only runtime deps.
- Respect env vars from Team B/A; do not bake secrets into images.
- Entrypoints:
  - Backend: `uvicorn backend.api.main:app --host 0.0.0.0 --port 8000`
  - LLM tracker: `uvicorn mcp_servers.llm_tracker_server.main:app --port 8001`
  - UI: `streamlit run ui/dashboard.py --server.port 8501`
- Use multi-stage builds and non-root user where possible.

CI basics
- `test.yml`: checkout, setup python, install deps, run `ruff`, `mypy`, `pytest`.
- `build.yml`: build Docker images and push to registry on tags or on `main` merges.

Streamlit UI guidance (what to show)
- Overview: monthly spend, budget, top services (charts)
- LLM Usage: model distribution, token counts, costs per model
- Anomalies: list with severity and a button that opens approval modal (calls backend)
- Actions: pending optimization actions and status

Coordination
- Confirm API endpoints and JSON shapes with Team A before wiring UI actions.
- Use Team B READMEs for env var names and runtime hints when building images.
