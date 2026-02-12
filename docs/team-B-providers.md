# Team B — Provider Integrations & MCP Servers Guide

This document outlines work for Team B: implement GCP and Azure billing integrations, harden AWS implementation, and create Dockerfiles for MCP servers.

Summary
- Owner: Team B
- Scope: finish `mcp-servers/gcp-billing-server/` and `mcp-servers/azure-cost-server/`, add Dockerfiles and integration tests, and provide instructions for configuring credentials and least-privilege roles.

Primary tasks

1. **GCP Billing implementation** (`mcp-servers/gcp-billing-server`):
   - Query exported billing data in BigQuery (preferred) or use the Billing API.
   - Recommended approach: use BigQuery billing export table and run SQL to aggregate costs by date/service.
   - Add async functions that return `{ "total_cost": float, "breakdown": {...} }`.
   - Example BigQuery query (pseudocode):

```sql
SELECT
  DATE(usage_start_time) AS day,
  service.description AS service,
  SUM(cost) AS total
FROM `PROJECT.GCLOUD_BILLING_EXPORT_TABLE`
WHERE DATE(usage_start_time) BETWEEN @start AND @end
GROUP BY day, service
ORDER BY day
```

2. **Azure Cost implementation** (`mcp-servers/azure-cost-server`):
   - Use `azure-identity` and `azure-mgmt-costmanagement` or query exported cost data.
   - Provide an async wrapper similar to AWS that returns aggregated totals.

3. **Harden AWS cost server** (`mcp-servers/aws-cost-server`):
   - Add retries, timeouts, and exponential backoff when calling Cost Explorer.
   - Add pagination/aggregation safeguards.

Note: Containerization and Dockerfile responsibilities are handled by Team C (UI, CI/CD & Dockerization). Team B should document any runtime requirements and environment variables each MCP server needs; Team C will create Dockerfiles and CI build steps.

5. **Integration tests**:
   - Create lightweight tests that validate the server returns structured data when run with mocked cloud clients (use `pytest` + `respx` or monkeypatch).

Credentials & permissions (security)

- GCP: create a service account with only the required BigQuery read permissions (or Billing Viewer if using the Billing API). Store key file and point `GCP_CREDENTIALS_PATH` to it.
- Azure: create a service principal with `Cost Management Reader` role for subscription.
- AWS: use an IAM role with read-only access to Cost Explorer (`ce:GetCostAndUsage`). Avoid long-lived root keys.

Testing locally

1. Use emulator data or small exported CSVs for GCP/Azure billing during development.
2. For AWS, run the `aws-cost-server.server.fetch_costs` function in a test script with mock `boto3` responses.

Deliverables

- `mcp-servers/gcp-billing-server/server.py` with a working `fetch_billing(start,end)` implementation.
- `mcp-servers/azure-cost-server/server.py` with `fetch_azure_costs(start,end)`.
- Docs in each folder explaining environment variables and run commands. (Dockerfiles will be added by Team C)
- Integration tests demonstrating correctness with mocked cloud responses.

Coordination

- If new dependencies are required (e.g., `google-cloud-bigquery`, `azure-mgmt-costmanagement`), open a single PR updating `pyproject.toml` and inform Team A and Team C.
