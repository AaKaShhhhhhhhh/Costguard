# Team C — UI, CI/CD & Archestra Integration Guide

This document outlines Team C responsibilities: Streamlit dashboard, GitHub Actions, docker-compose improvements, and Archestra.AI workflow deployment scripts.

Summary
- Owner: Team C
- Scope: implement `ui/` Streamlit app, CI workflows under `.github/workflows`, add Dockerfiles and improve `docker-compose.yml` for dev, and provide Archestra.AI deployment scripts.

Primary tasks

1. **Streamlit UI** (`ui/`):
   - Create a multi-page Streamlit dashboard under `ui/pages/`:
     - Overview: budgets, monthly spend, top services
     - LLM usage: model distribution, token counts, cost per model
     - Anomalies: list with approve/reject buttons (calls backend endpoints)
     - Actions: pending optimization actions and status
   - Reusable components in `ui/components/` and helpers in `ui/utils/`.

2. **GitHub Actions (CI)**:
   - Create `.github/workflows/test.yml` that runs `pytest`, `ruff`, and `mypy`.
   - Create `deploy.yml` that builds Docker images and (optionally) pushes to registry.

Example `test.yml` job steps:

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with: python-version: '3.10'
      - name: Install deps
        run: |
          pip install -e .
          pip install pytest ruff mypy
      - name: Lint
        run: ruff check .
      - name: Test
        run: pytest -q
```

3. **Docker & docker-compose (Team C owns all Docker work)**:
  - Create Dockerfiles for `backend`, `mcp-servers/*` services (LLM tracker, AWS/GCP/Azure adapters), and the Streamlit UI.
  - Build and publish images in CI (or provide local `docker-compose` builds for developers).
  - Add service entries for `backend`, `llm-tracker-server`, and each MCP server in `docker-compose.yml` and maintain the compose dev setup.
  - Provide a `Makefile` target (already present) to `docker-up` and `docker-down`.

  Notes for Dockerfiles:
  - Use multi-stage builds where helpful to keep images small.
  - Install only runtime dependencies in final image and avoid embedding secrets.
  - Respect `PYTHONUNBUFFERED=1` and use a non-root user where possible.

4. **Archestra.AI integration**:
   - Create `scripts/deploy_archestra.sh` to register workflows and deploy agent code if Archestra provides an API/CLI.
   - Provide sample Archestra workflow manifests in `workflows/` (already present) and document how to upload them.

5. **End-to-end demo script**:
   - Create `scripts/demo.sh` to start services, seed demo data, start agent runner in demo mode, and open Streamlit.


Deliverables

- `ui/` Streamlit app with at least two pages (Overview, Anomalies).
- `.github/workflows/test.yml` and `deploy.yml` for CI.
- Dockerfiles for `backend` and MCP servers plus updated `docker-compose.yml` usable for local development.
- `scripts/deploy_archestra.sh` template and instructions.


Coordination notes

- UI will call backend endpoints (owned by Team A). Agree on endpoint paths and JSON shapes early.
- CI changes that affect deps must be coordinated with Team B if provider SDKs are added.
