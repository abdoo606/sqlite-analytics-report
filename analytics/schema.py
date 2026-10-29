"""Schema + deterministic seed data.

The seed is small on purpose: every report below has hand-checkable numbers,
which is how the queries are tested.
"""
from __future__ import annotations

import sqlite3

SCHEMA = """
CREATE TABLE customers (
    id      TEXT PRIMARY KEY,
    name    TEXT NOT NULL,
    country TEXT NOT NULL
);
CREATE TABLE trips (
    id          TEXT PRIMARY KEY,
    origin      TEXT NOT NULL,
    destination TEXT NOT NULL,
    depart_date TEXT NOT NULL
);
CREATE TABLE bookings (
    id           TEXT PRIMARY KEY,
    customer_id  TEXT NOT NULL REFERENCES customers(id),
    trip_id      TEXT NOT NULL REFERENCES trips(id),
    amount_cents INTEGER NOT NULL,
    status       TEXT NOT NULL,          -- confirmed | cancelled
    created_at   TEXT NOT NULL           -- YYYY-MM-DD
);
CREATE TABLE events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL,
    event_type  TEXT NOT NULL,           -- search | view | checkout | purchase
    occurred_at TEXT NOT NULL
);
"""

CUSTOMERS = [
    ("c1", "Amina", "SY"), ("c2", "Bilal", "MA"), ("c3", "Chloé", "FR"),
    ("c4", "Dan", "DE"), ("c5", "Elif", "TR"),
]
TRIPS = [
    ("t1", "CDG", "MAD", "2026-09-01"),
    ("t2", "CDG", "LIS", "2026-09-20"),
    ("t3", "LYS", "BCN", "2026-10-05"),
]
# month totals: 2026-08 = 24000, 2026-09 = 26000, 2026-10 = 35500
BOOKINGS = [
    ("b1", "c1", "t1", 12000, "confirmed", "2026-08-05"),
    ("b2", "c2", "t1", 12000, "confirmed", "2026-08-20"),
    ("b3", "c1", "t2", 15000, "confirmed", "2026-09-02"),
    ("b4", "c3", "t3", 20000, "cancelled", "2026-09-15"),
    ("b5", "c4", "t1", 11000, "confirmed", "2026-09-28"),
    ("b6", "c2", "t2", 14500, "confirmed", "2026-10-04"),
    ("b7", "c1", "t3", 21000, "confirmed", "2026-10-19"),
]
EVENTS = [
    ("s1", "search", "2026-10-01"), ("s1", "view", "2026-10-01"),
    ("s1", "checkout", "2026-10-02"), ("s1", "purchase", "2026-10-02"),
    ("s2", "search", "2026-10-03"), ("s2", "view", "2026-10-03"),
    ("s3", "search", "2026-10-04"), ("s3", "view", "2026-10-04"),
    ("s3", "checkout", "2026-10-05"),
    ("s4", "search", "2026-10-06"), ("s4", "view", "2026-10-06"),
    ("s4", "checkout", "2026-10-07"), ("s4", "purchase", "2026-10-07"),
]


def connect(path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def seed(conn: sqlite3.Connection) -> None:
    create_schema(conn)
    conn.executemany("INSERT INTO customers VALUES (?, ?, ?)", CUSTOMERS)
    conn.executemany("INSERT INTO trips VALUES (?, ?, ?, ?)", TRIPS)
    conn.executemany("INSERT INTO bookings VALUES (?, ?, ?, ?, ?, ?)", BOOKINGS)
    conn.executemany("INSERT INTO events (session_id, event_type, occurred_at) VALUES (?, ?, ?)",
                     EVENTS)
    conn.commit()
