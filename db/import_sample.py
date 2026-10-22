import csv
import os
import sys
from pathlib import Path

from mysql.connector import Error

sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import connect_with_retry

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
BATCH_SIZE = 1000


def load_schema(cursor):
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("DROP TABLE IF EXISTS sets")
    cursor.execute("DROP TABLE IF EXISTS themes")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    statements = SCHEMA_PATH.read_text().split(";")
    for statement in statements:
        sql = statement.strip()
        if sql:
            cursor.execute(sql)


def empty_to_none(value):
    if value is None:
        return None
    value = value.strip()
    return value or None


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        yield from csv.DictReader(handle)


def import_themes(cursor):
    rows = []
    for row in read_csv(DATA_DIR / "themes.csv"):
        rows.append(
            (
                int(row["id"]),
                row["name"],
                int(row["parent_id"]) if empty_to_none(row["parent_id"]) else None,
            )
        )

    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    for start in range(0, len(rows), BATCH_SIZE):
        cursor.executemany(
            """
            INSERT INTO themes (id, name, parent_id)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                parent_id = VALUES(parent_id)
            """,
            rows[start : start + BATCH_SIZE],
        )
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    print(f"Imported {len(rows)} themes")


def import_sets(cursor):
    rows = []
    for row in read_csv(DATA_DIR / "sets.csv"):
        rows.append(
            (
                row["set_num"],
                row["name"],
                int(row["year"]),
                int(row["theme_id"]) if empty_to_none(row["theme_id"]) else None,
                int(row["num_parts"]) if empty_to_none(row.get("num_parts", "")) else None,
                empty_to_none(row.get("img_url", "")),
            )
        )

    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    for start in range(0, len(rows), BATCH_SIZE):
        cursor.executemany(
            """
            INSERT INTO sets (set_num, name, year, theme_id, num_parts, img_url)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                year = VALUES(year),
                theme_id = VALUES(theme_id),
                num_parts = VALUES(num_parts),
                img_url = VALUES(img_url)
            """,
            rows[start : start + BATCH_SIZE],
        )
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    print(f"Imported {len(rows)} sets")


def main():
    connection = None
    cursor = None
    try:
        connection = connect_with_retry()
        cursor = connection.cursor()
        load_schema(cursor)
        import_themes(cursor)
        import_sets(cursor)
        connection.commit()
        print("Sample Rebrickable data import complete.")
    except Error as exc:
        print(f"Database Error: {exc}")
        sys.exit(1)
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    main()
