import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from analytics.cli import main
from analytics.report import to_markdown
from analytics.schema import connect, seed


class ReportTests(unittest.TestCase):
    def test_markdown_sections(self):
        conn = connect(":memory:")
        seed(conn)
        md = to_markdown(conn)
        for section in ("Revenue by month", "Top routes", "Cohort retention", "Funnel"):
            self.assertIn(section, md)
        self.assertIn("CDG-MAD", md)
        self.assertIn("+36.54%", md)
        conn.close()


class CliTests(unittest.TestCase):
    def run_cli(self, argv):
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(argv)
        return code, out.getvalue()

    def test_demo_report(self):
        code, out = self.run_cli(["report"])
        self.assertEqual(code, 0)
        self.assertIn("Travel analytics", out)

    def test_json_report(self):
        code, out = self.run_cli(["report", "--json"])
        payload = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(len(payload["revenue_by_month"]), 3)
        self.assertEqual(payload["funnel"][-1]["sessions"], 2)

    def test_out_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "report.md"
            code, _ = self.run_cli(["report", "--out", str(dest)])
            self.assertEqual(code, 0)
            self.assertIn("Travel analytics", dest.read_text(encoding="utf-8"))
