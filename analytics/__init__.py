"""analytics: SQL-first reporting (CTEs, window functions) over SQLite."""
from .queries import cohort_retention, funnel, revenue_by_month, top_routes
from .schema import connect, seed

__all__ = ["cohort_retention", "funnel", "revenue_by_month", "top_routes", "connect", "seed"]
__version__ = "0.1.0"
