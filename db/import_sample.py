import csv
import os
import sys
from pathlib import Path

from mysql.connector import Error

sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import connect_with_retry

DATA_DIR = Path(os.getenv("DATA_DIR", "data/subset"))
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
BATCH_SIZE = 1000
BOOLEAN_COLUMNS = {
    "is_export_id",
    "is_import_id",
    "is_spare",
    "is_trans",
}

TABLES = {
    "themes": ("id", "name", "parent_id"),
    "sets": ("set_num", "name", "year", "theme_id", "num_parts", "img_url"),
    "colors": ("id", "name", "rgb", "is_trans", "num_parts", "num_sets", "y1", "y2"),
    "part_categories": ("id", "name"),
    "parts": ("part_num", "name", "part_cat_id", "part_material"),
    "minifigs": ("fig_num", "name", "num_parts", "img_url"),
    "color_mappings": (
        "id",
        "ext_system",
        "ext_id",
        "ext_descr",
        "is_export_id",
        "is_import_id",
    ),
    "elements": ("element_id", "part_num", "color_id", "design_id"),
    "inventories": ("id", "version", "set_num"),
    "inventory_minifigs": ("inventory_id", "fig_num", "quantity"),
    "inventory_parts": (
        "inventory_id",
        "part_num",
        "color_id",
        "quantity",
        "is_spare",
        "img_url",
    ),
    "inventory_sets": ("inventory_id", "set_num", "quantity"),
    "part_mappings": (
        "part_num",
        "ext_system",
        "ext_id",
        "is_export_id",
        "is_import_id",
    ),
    "part_relationships": ("rel_type", "child_part_num", "parent_part_num"),
    "set_mappings": ("set_num", "ext_system", "ext_id"),
}


def ensure_schema(cursor):
    for statement in SCHEMA_PATH.read_text(encoding="utf-8").split(";"):
        sql = statement.strip()
        if sql:
            cursor.execute(sql)


def normalize_value(value, column):
    if value is None or not value.strip():
        return None
    if column in BOOLEAN_COLUMNS:
        normalized = value.strip().lower()
        if normalized in {"true", "1"}:
            return 1
        if normalized in {"false", "0"}:
            return 0
        raise ValueError(f"Invalid boolean value {value!r} for column {column}")
    return value


def validate_csv_files():
    for table, columns in TABLES.items():
        path = DATA_DIR / f"{table}.csv"
        if not path.is_file():
            raise FileNotFoundError(f"Sample data file not found: {path}")

        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames == ["version https://git-lfs.github.com/spec/v1"]:
                raise ValueError(
                    f"{path} is a Git LFS pointer, not CSV data. "
                    "Check that DATA_DIR points to the sample CSVs in data/subset."
                )
            if reader.fieldnames != list(columns):
                raise ValueError(
                    f"Unexpected columns in {path}: {reader.fieldnames}; "
                    f"expected {list(columns)}"
                )


def import_table(cursor, connection, table, columns):
    column_sql = ", ".join(f"`{column}`" for column in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    updates = ", ".join(
        f"`{column}` = VALUES(`{column}`)" for column in columns
    )
    insert_sql = (
        f"INSERT INTO `{table}` ({column_sql}) VALUES ({placeholders}) "
        f"ON DUPLICATE KEY UPDATE {updates}"
    )

    rows = []
    row_count = 0
    with (DATA_DIR / f"{table}.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                tuple(normalize_value(row[column], column) for column in columns)
            )
            if len(rows) >= BATCH_SIZE:
                cursor.executemany(insert_sql, rows)
                row_count += len(rows)
                rows.clear()

        if rows:
            cursor.executemany(insert_sql, rows)
            row_count += len(rows)

    connection.commit()
    print(f"Imported {row_count} rows into {table}")


def main():
    connection = None
    cursor = None
    try:
        validate_csv_files()
        connection = connect_with_retry()
        cursor = connection.cursor()
        ensure_schema(cursor)

        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        try:
            for table, columns in TABLES.items():
                import_table(cursor, connection, table, columns)
        finally:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        print("Sample Rebrickable data import complete.")
    except (Error, OSError, ValueError) as exc:
        print(f"Database/import error: {exc}")
        sys.exit(1)
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    main()
