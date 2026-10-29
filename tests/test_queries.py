import unittest

from analytics.queries import cohort_retention, funnel, revenue_by_month, top_routes
from analytics.schema import connect, create_schema, seed


class SeededQueryTests(unittest.TestCase):
    def setUp(self):
        self.conn = connect(":memory:")
        seed(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_revenue_by_month(self):
        rows = revenue_by_month(self.conn)
        self.assertEqual([r["month"] for r in rows], ["2026-08", "2026-09", "2026-10"])
        self.assertEqual([r["revenue_cents"] for r in rows], [24000, 26000, 35500])
        self.assertEqual([r["bookings"] for r in rows], [2, 2, 2])

    def test_cancelled_bookings_are_excluded(self):
        # b4 (20000, cancelled) never shows up in any month total
        self.assertNotIn(20000, [r["revenue_cents"] for r in revenue_by_month(self.conn)])

    def test_growth_is_null_for_first_month_then_computed(self):
        rows = revenue_by_month(self.conn)
        self.assertIsNone(rows[0]["growth_pct"])
        self.assertAlmostEqual(rows[1]["growth_pct"], 8.33, places=2)
        self.assertAlmostEqual(rows[2]["growth_pct"], 36.54, places=2)

    def test_top_routes_ordering_and_rank(self):
        rows = top_routes(self.conn)
        self.assertEqual([r["route"] for r in rows], ["CDG-MAD", "CDG-LIS", "LYS-BCN"])
        self.assertEqual([r["rank"] for r in rows], [1, 2, 3])
        self.assertEqual(rows[0]["revenue_cents"], 35000)
        self.assertEqual(rows[0]["bookings"], 3)
        self.assertEqual(rows[0]["avg_cents"], 11666)   # 35000 / 3, truncated

    def test_cohorts(self):
        rows = cohort_retention(self.conn)
        by_cohort = {}
        for row in rows:
            by_cohort.setdefault(row["cohort"], {})[row["month_offset"]] = row["active_customers"]
        self.assertEqual(by_cohort["2026-08"], {0: 2, 1: 1, 2: 2})
        # c3 and c4 booked once each, in September: no M1 activity yet
        self.assertEqual(by_cohort["2026-09"], {0: 2})

    def test_funnel(self):
        rows = funnel(self.conn)
        self.assertEqual([r["event_type"] for r in rows],
                         ["search", "view", "checkout", "purchase"])
        self.assertEqual([r["sessions"] for r in rows], [4, 4, 3, 2])
        self.assertAlmostEqual(rows[-1]["pct_of_top"], 50.0)
        self.assertAlmostEqual(rows[-1]["pct_of_previous"], 66.7)
        self.assertIsNone(rows[0]["pct_of_previous"])

    def test_queries_are_read_only(self):
        before = self.conn.total_changes
        revenue_by_month(self.conn)
        top_routes(self.conn)
        cohort_retention(self.conn)
        funnel(self.conn)
        self.assertEqual(self.conn.total_changes, before)


class EmptyDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.conn = connect(":memory:")
        create_schema(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_empty_reports_do_not_crash(self):
        self.assertEqual(revenue_by_month(self.conn), [])
        self.assertEqual(top_routes(self.conn), [])
        self.assertEqual(cohort_retention(self.conn), [])
        self.assertEqual([r["sessions"] for r in funnel(self.conn)], [0, 0, 0, 0])
