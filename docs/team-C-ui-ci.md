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



# Docker Workflow Checklist (Team C)

This checklist contains the Docker workflow and in-container tasks for local development, CI, and production. Use it as the single source of truth for building, running, and debugging container images for the CostGuard AI project.

## 1. Build & tag images
- Local dev: build images with descriptive tags:

```bash
docker build -t costguard/backend:local -f docker/backend/Dockerfile .
docker build -t costguard/llm-tracker:local -f mcp-servers/llm-tracker-server/Dockerfile .
docker build -t costguard/ui:local -f ui/Dockerfile .
```

- CI: tag images as `registry/org/costguard/<service>:${{ github.sha }}` and push to your container registry.

## 2. docker-compose for local development
- Compose orchestrates services (Postgres, Prometheus, Grafana, backend, tracker, UI).
- Keep secrets out of `docker-compose.yml`; pass env via `.env` or `docker-compose.override.yml` (ignored by git).

Example compose snippet for the backend service:

```yaml
services:
  backend:
    image: costguard/backend:local
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - ENVIRONMENT=development
    depends_on: [postgres]
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 3. In-container startup tasks
- **DB migrations**: On startup, the backend container should run `alembic upgrade head` (or a controlled migration job) before starting the app. For local dev you can run migrations from the host instead.
- **Seeding**: Optionally seed the DB with demo data in a CI/dev-only path.
- **Health checks**: Expose a `/health` endpoint for readiness and liveness checks used by compose or k8s.
- **Logging**: stdout/stderr should stream structured logs (Loguru config present). Do not write secrets to logs.

## 4. CI pipeline steps around Docker
- **Build**: Build images for each service with stable tags.
- **Test**: Run unit tests in the CI environment (preferably in a `test` image or via a matrix job). Avoid depending on external cloud services by mocking.
- **Push**: Push images to a registry when the build is from `main` or `release` tags.
- **Deploy**: Optional step to deploy images to staging/production (or call Archestra.AI deploy scripts).

## 5. Secrets & configuration
- For local dev use `.env` and `docker-compose` env interpolation.
- For CI and production use GitHub Secrets, Docker secrets, or a secrets manager (AWS Secrets Manager, GCP Secret Manager).

## 6. Resource hints & production readiness
- Add resource limits in compose/k8s manifests (e.g., `mem_limit: "512m"`).
- Use multi-stage builds to reduce image size and attack surface.

## 7. Debugging & logs
- To debug: `docker-compose up --build` then `docker logs -f <service>` or `docker-compose exec backend /bin/bash`.
- Provide a `make logs` target to tail service logs locally.

## 8. Pre-build questions for Team B/A
- Exact env var names and example values (Team B/A should provide READMEs).
- Ports the service listens on and any additional system requirements (e.g., Google Cloud SDK or system libraries).
- Any one-off setup commands (DB migrations, seeding) that must run in container startup.
