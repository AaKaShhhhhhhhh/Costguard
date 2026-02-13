# AWS Cost Server

Provides helpers to query AWS Cost Explorer for cost metrics.

Usage:

```py
from aws_cost_server.server import fetch_costs

costs = await fetch_costs('2026-01-01', '2026-02-01')
```

Make sure AWS credentials are set in environment variables or `shared/config.py`.
