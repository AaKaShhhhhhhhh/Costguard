# Archestra.AI Integration Guide — CostGuard

This document outlines the bidirectional integration between **CostGuard** (the Specialized Cost Agent) and **Archestra.AI** (the Multi-Agent Orchestrator). 

## Architecture Overview

CostGuard operates as an autonomous guardian that detects issues and proposes solutions. Archestra acts as the central hub that executes these solutions across your infrastructure.

```mermaid
sequence_flow
    participant Dashboard as User Dashboard
    participant Backend as CostGuard Backend
    participant DB as SQLite/PostgreSQL
    participant Archestra as Archestra.AI

    Backend->>DB: 1. Scan & Detect Anomaly
    Dashboard->>Backend: 2. Click "Approve"
    Backend->>DB: Update status to "approved"
    Backend->>Archestra: 3. Outbound: POST /webhooks/workflow/resume
    Note over Archestra: Orchestrator executes Model Switch / Scaling
    Archestra->>Backend: 4. Inbound: POST /api/v1/archestra/webhook
    Backend->>DB: Update status to "executed"
    Backend->>Dashboard: 5. Display green "Executed" status
```

## Outbound: CostGuard ⮕ Archestra
When an action is approved in CostGuard, it notifies Archestra to resume the optimization workflow.

- **Endpoint**: `${ARCHESTRA_API_URL}/api/v1/webhooks/workflow/resume`
- **Payload**:
  ```json
  {
    "event": "action_review",
    "action_id": "uuid-string",
    "status": "approved",
    "approver": "user_id"
  }
  ```

## Inbound: Archestra ⮕ CostGuard
Once Archestra has completed the physical infrastructure change (e.g. changing an LLM model or scaling a Lambda), it notifies CostGuard to finalize the record.

- **Endpoint**: `http://localhost:8000/api/v1/archestra/webhook`
- **Method**: `POST`
- **Payload**:
  ```json
  {
    "event": "execution_complete",
    "action_id": "uuid-string",
    "status": "executed"
  }
  ```

## How to Oversee Archestra Workflow
1. **CostGuard Logs**: Check the backend logs for `Notified Archestra for action XXX`.
2. **Archestra Dashboard**: Log in to your Archestra.AI account to see the Workflow Instance associated with the `action_id`.
3. **Status Sync**: Verified when the "Approved" button on your dashboard turns into an "Executed" badge.
