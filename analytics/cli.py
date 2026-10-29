from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from . import queries
from .report import to_markdown
from .schema import connect, seed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="analytics", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("report", help="render all reports")
    p.add_argument("--db", default=None, help="sqlite file; omit for the demo dataset")
    p.add_argument("--json", action="store_true")
    p.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        if args.db and Path(args.db).exists():
            conn = connect(args.db)
        else:
            conn = connect(":memory:")
            seed(conn)
    except (sqlite3.Error, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        payload = {
            "revenue_by_month": queries.revenue_by_month(conn),
            "top_routes": queries.top_routes(conn),
            "cohorts": queries.cohort_retention(conn),
            "funnel": queries.funnel(conn),
        }
        text = json.dumps(payload, indent=2) + "\n"
    else:
        text = to_markdown(conn)

    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
