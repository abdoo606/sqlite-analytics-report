from __future__ import annotations

from .queries import cohort_retention, funnel, revenue_by_month, top_routes


def _eur(cents: int | None) -> str:
    return "—" if cents is None else f"{cents / 100:,.2f}"


def to_markdown(conn) -> str:
    lines = ["# Travel analytics", ""]

    lines += ["## Revenue by month", "",
              "| Month | Revenue | Bookings | MoM growth |", "|---|---:|---:|---:|"]
    for row in revenue_by_month(conn):
        growth = "—" if row["growth_pct"] is None else f"{row['growth_pct']:+.2f}%"
        lines.append(f"| {row['month']} | €{_eur(row['revenue_cents'])} | "
                     f"{row['bookings']} | {growth} |")

    lines += ["", "## Top routes", "",
              "| # | Route | Revenue | Bookings | Avg ticket |", "|---:|---|---:|---:|---:|"]
    for row in top_routes(conn):
        lines.append(f"| {row['rank']} | {row['route']} | €{_eur(row['revenue_cents'])} | "
                     f"{row['bookings']} | €{_eur(row['avg_cents'])} |")

    lines += ["", "## Cohort retention (distinct customers by months since first booking)", "",
              "| Cohort | M0 | M1 | M2 |", "|---|---:|---:|---:|"]
    rows = cohort_retention(conn)
    cohorts: dict[str, dict[int, int]] = {}
    for row in rows:
        cohorts.setdefault(row["cohort"], {})[row["month_offset"]] = row["active_customers"]
    for cohort, offsets in cohorts.items():
        cells = [str(offsets.get(i, 0)) for i in range(3)]
        lines.append(f"| {cohort} | " + " | ".join(cells) + " |")

    lines += ["", "## Funnel", "",
              "| Step | Sessions | % of search | % of previous |", "|---:|---:|---:|---:|"]
    for row in funnel(conn):
        prev = "—" if row["pct_of_previous"] is None else f"{row['pct_of_previous']:.1f}%"
        lines.append(f"| {row['step']}. {row['event_type']} | {row['sessions']} | "
                     f"{row['pct_of_top']:.1f}% | {prev} |")
    return "\n".join(lines) + "\n"
