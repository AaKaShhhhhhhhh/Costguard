"""AWS Cost Explorer MCP server package.

This package exposes helpers to fetch cost data from AWS Cost Explorer.
It is intentionally lightweight and safe to import without credentials; the
actual calls to AWS are guarded and will raise informative errors if
configuration or dependencies are missing.
"""

__all__ = ["fetch_costs"]
