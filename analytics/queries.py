"""Reports. Each function returns rows, not strings, so the CLI can render them
and the tests can assert on the numbers directly."""
from __future__ import annotations

import sqlite3

REVENUE_SQL = """
WITH monthly AS (
    SELECT strftime('%Y-%m', created_at) AS month,
           SUM(amount_cents)             AS revenue_cents,
           COUNT(*)                      AS bookings
    FROM bookings
    WHERE status = 'confirmed'
    GROUP BY month
)
SELECT month,
       revenue_cents,
       bookings,
       LAG(revenue_cents) OVER (ORDER BY month) AS prev_revenue_cents,
       ROUND(100.0 * (revenue_cents - LAG(revenue_cents) OVER (ORDER BY month))
             / LAG(revenue_cents) OVER (ORDER BY month), 2) AS growth_pct
FROM monthly
ORDER BY month;
"""

TOP_ROUTES_SQL = """
SELECT t.origin || '-' || t.destination AS route,
       SUM(b.amount_cents)             AS revenue_cents,
       COUNT(*)                        AS bookings,
       CAST(AVG(b.amount_cents) AS INTEGER) AS avg_cents,
       DENSE_RANK() OVER (ORDER BY SUM(b.amount_cents) DESC) AS rank
FROM bookings b
JOIN trips t ON t.id = b.trip_id
WHERE b.status = 'confirmed'
GROUP BY route
ORDER BY revenue_cents DESC;
"""

COHORT_SQL = """
WITH first_seen AS (
    SELECT customer_id, MIN(strftime('%Y-%m', created_at)) AS cohort
    FROM bookings
    GROUP BY customer_id
),
activity AS (
    SELECT b.customer_id,
           f.cohort,
           strftime('%Y-%m', b.created_at) AS month
    FROM bookings b
    JOIN first_seen f ON f.customer_id = b.customer_id
    GROUP BY b.customer_id, f.cohort, month
),
offsets AS (
    SELECT cohort,
           (CAST(strftime('%Y', month || '-01') AS INTEGER)
            - CAST(strftime('%Y', cohort || '-01') AS INTEGER)) * 12
           + (CAST(strftime('%m', month || '-01') AS INTEGER)
              - CAST(strftime('%m', cohort || '-01') AS INTEGER)) AS month_offset,
           COUNT(DISTINCT customer_id) AS active_customers
    FROM activity
    GROUP BY cohort, month_offset
)
SELECT cohort, month_offset, active_customers
FROM offsets
ORDER BY cohort, month_offset;
"""

FUNNEL_SQL = """
WITH steps(event_type, step) AS (
    VALUES ('search', 1), ('view', 2), ('checkout', 3), ('purchase', 4)
),
counts AS (
    SELECT s.event_type, s.step, COUNT(e.id) AS sessions
    FROM steps s
    LEFT JOIN events e ON e.event_type = s.event_type
    GROUP BY s.event_type, s.step
)
SELECT event_type,
       step,
       sessions,
       ROUND(100.0 * sessions / FIRST_VALUE(sessions) OVER (ORDER BY step), 1) AS pct_of_top,
       ROUND(100.0 * sessions / LAG(sessions) OVER (ORDER BY step), 1) AS pct_of_previous
FROM counts
ORDER BY step;
"""


def _rows(conn: sqlite3.Connection, sql: str) -> list[dict]:
    return [dict(r) for r in conn.execute(sql).fetchall()]


def revenue_by_month(conn: sqlite3.Connection) -> list[dict]:
    return _rows(conn, REVENUE_SQL)


def top_routes(conn: sqlite3.Connection) -> list[dict]:
    return _rows(conn, TOP_ROUTES_SQL)


def cohort_retention(conn: sqlite3.Connection) -> list[dict]:
    return _rows(conn, COHORT_SQL)


def funnel(conn: sqlite3.Connection) -> list[dict]:
    return _rows(conn, FUNNEL_SQL)
