"""LLM Tracker MCP server package.

Exposes a small FastAPI app for receiving LLM usage events and querying
recent usage. In production this would be backed by a database; the stub
keeps an in-memory store for development and testing.
"""

__all__ = ["app"]
