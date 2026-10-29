# sqlite-analytics-report

Reporting built on SQL, not Python loops: CTEs, window functions (`LAG`,
`FIRST_VALUE`, `DENSE_RANK`), cohort analysis and a funnel — over SQLite, with
a deterministic seed so every number in the tests is hand-checkable.

Zero dependencies (stdlib only), Python 3.9+.

## Reports

```bash
python -m analytics report          # markdown
python -m analytics report --json   # rows, for a dashboard or tests
python -m analytics report --db prod.sqlite
```

| Report | Technique |
|---|---|
| Revenue by month + MoM growth | `LAG()` window, NULL-safe first row |
| Top routes | `SUM`, `DENSE_RANK() OVER (ORDER BY SUM(...))` |
| Cohort retention (M0/M1/M2) | two CTEs + month arithmetic between `strftime` values |
| Funnel | `VALUES` step table, `LEFT JOIN`, `FIRST_VALUE`/`LAG` |

## Design notes

- **Cancelled bookings never count.** Every revenue query filters
  `status = 'confirmed'`; there is a test that asserts the cancelled 200 EUR
  row cannot leak into a total.
- **The first month's growth is NULL, not 0.** Zero would read as "flat" and
  quietly drag an average down.
- Funnel uses `LEFT JOIN` so a step with zero sessions still appears — a
  missing row is indistinguishable from a step that nobody reached.
- Queries are read-only and covered by a test on `total_changes`.

## Tests

15 tests: exact revenue/growth/rank/cohort/funnel values, exclusion of
cancelled rows, empty-database behaviour, and the CLI's markdown + JSON output.
