# LLM Tracker Server

Lightweight FastAPI app to collect LLM usage metrics. Start with:

```bash
uvicorn mcp_servers.llm_tracker_server.main:app --reload
```

Replace the in-memory store with a persistent database in production.
