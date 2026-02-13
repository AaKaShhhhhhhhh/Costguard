# Project Roadmap: CostGuard AI

This document outlines the remaining work required to bring CostGuard AI to a fully production-ready state, broken down by team responsibilities.

## 🟢 Completed (Phase 1)
- **Core Infrastructure**: Dockerized environment with Postgres database (Team C).
- **Backend API**: Functional endpoints for anomalies, usage, and actions (Team A).
- **Database**: Automated migrations and seeding logic implemented (Team A).
- **Security**: Basic API Key authentication connected to Swagger UI (Team A).
- **Dashboard**: "Anomalies" page connects to backend and displays data (Team C).

---

## 🟡 Remaining Work

### Team A: Backend & Core (High Priority)
1.  **Production Authentication**: 
    - Replace the single hardcoded `default_secret_key` with a robust user/service management system (e.g., OAuth2 or database-backed API keys).
2.  **Persistent Storage**:
    - Ensure the Postgres volume is properly backed up or managed for production deployment (currently relies on Docker volume).
3.  **Action Execution Logic**:
    - Implement the actual execution logic for "Optimization Actions" (e.g., calling AWS API to resize an instance when "Approved"). Currently, it only updates the database status.

### Team B: AI Agents & Providers (Critical Path)
1.  **MCP Server Integration**:
    - The server skeletons exist in `mcp-servers/`. The actual logic to query AWS Cost Explorer, GCP Billing, and Azure Cost Management APIs needs to be fully implemented and tested.
2.  **"Detective" Agent Implementation**:
    - Build the cron job or background worker that periodically polls the MCP servers and posts new anomalies to `POST /api/v1/anomalies`.
3.  **LLM Usage Tracking**:
    - Connect the `llm-tracker-server` to real LLM provider logs (OpenAI/Anthropic) to populate the `llm_usage` table.

### Team C: UI & DevOps (Enhancement)
1.  **Action Workflows**:
    - Build a dedicated "Settings" page to manage cloud provider credentials securely from the UI.
2.  **Visualizations**:
    - Add trend lines and historical charts to the "Overview" page (currently a placeholder).
3.  **Deployment**:
    - Create a Helm chart or Kubernetes manifest for scaling the backend and agents independently.

---

## 🔵 Simple Workflow (For New Developers)

1.  **Configure**: Copy `.env.example` to `.env`.
2.  **Start**: Run `docker-compose up --build`.
3.  **Use**: 
    - Open `http://localhost:8501` for the Dashboard.
    - Open `http://localhost:8000/docs` for the API.
    - (Optional) Click "Re-Seed Database" in the UI sidebar to restore test data.
