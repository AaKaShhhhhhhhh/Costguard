# Team B — Provider Integrations (Simplified)

Purpose
- Implement the cloud adapters that gather cost data from AWS, GCP, and Azure and return a consistent JSON summary. Document runtime requirements for Team C to containerize.

Deliverables (short)
- `mcp-servers/gcp-billing-server/server.py`: `fetch_billing(start,end)` → `{"total_cost": float, "breakdown": {...}}`
- `mcp-servers/azure-cost-server/server.py`: `fetch_azure_costs(start,end)` → same shape
- Hardened `mcp-servers/aws-cost-server/server.py` with retries, timeouts and pagination handling
- Unit/integration tests (mocked SDKs) and README updates listing required env vars

Credentials & quick steps

GCP (preferred path)
- Enable Billing export to BigQuery in Google Cloud Console and point Team B code at the exported dataset.
- Create a service account with BigQuery read access for that dataset and download the JSON key. Set `.env`: `GCP_CREDENTIALS_PATH=/path/key.json`, `GCP_PROJECT_ID=your-project`.

Azure
- Create a Service Principal (App Registration) and grant `Cost Management Reader` to the subscription. Set `.env`: `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`.

AWS
- Create an IAM user/role with `ce:GetCostAndUsage`. Set `.env`: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`.

Implementation notes
- Return the same output shape from each adapter so downstream code is simple.
- Keep calls safe: use timeouts, retries (exponential backoff), and parameterized queries for BigQuery.
- Document exact env var names, recommended ports, and any extra system requirements in each server's README for Team C.

Testing guidance
- Use small exported CSVs or a test BigQuery dataset for local testing.
- Mock cloud SDKs in CI tests to avoid external calls.

Coordination
- If adding SDK deps (e.g., `google-cloud-bigquery`), update `pyproject.toml` in a single PR and notify Teams A and C.
