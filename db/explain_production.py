"""Query plans and timings for the feature queries on the production dataset.

Runs db/test-production.sql statement by statement on one connection. For each
query tagged with a `-- plan: <label>` comment it records the median time of
5 runs and its EXPLAIN ANALYZE plan. Untagged statements (setup, the remove
step, cleanup) run once as normal, so tagged queries see the same data as in
test-production.out.

    docker compose exec -T app python db/explain_production.py > db/test-production-plans.out
"""

import re
import statistics
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import connect_with_retry  # noqa: E402

SCRIPT = Path(__file__).resolve().parent / "test-production.sql"
RUNS = 5


def statements(text):
    for chunk in re.split(r";[ \t]*\n", text):
        label = re.search(r"^-- plan: (.+)$", chunk, re.M)
        sql = "\n".join(
            line for line in chunk.splitlines() if not line.lstrip().startswith("--")
        ).strip()
        if sql:
            yield (label.group(1).strip() if label else None), sql


def run(cursor, sql):
    cursor.execute(sql)
    return cursor.fetchall() if cursor.with_rows else []


def main():
    connection = connect_with_retry()
    cursor = connection.cursor()
    summary = []
    plans = []
    for label, sql in statements(SCRIPT.read_text(encoding="utf-8")):
        if label is None:
            run(cursor, sql)
            connection.commit()
            continue
        timings = []
        for _ in range(RUNS):
            started = time.perf_counter()
            rows = run(cursor, sql)
            timings.append((time.perf_counter() - started) * 1000)
        plan = run(cursor, "EXPLAIN ANALYZE " + sql)[0][0]
        median = statistics.median(timings)
        summary.append((label, median, len(rows)))
        plans.append((label, median, plan))
    connection.close()

    print(f"Median of {RUNS} runs per query, on the production dataset (MySQL {connection.get_server_info()}).")
    print()
    width = max(len(label) for label, _, _ in summary)
    print(f"{'Query'.ljust(width)}  {'Median':>9}  Rows")
    for label, median, rows in summary:
        print(f"{label.ljust(width)}  {median:7.1f} ms  {rows}")
    for label, median, plan in plans:
        print()
        print("=" * 80)
        print(f"{label} ({median:.1f} ms)")
        print("=" * 80)
        print(plan)


if __name__ == "__main__":
    main()
