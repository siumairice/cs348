"""Load the full Rebrickable dataset from data/*.csv into MySQL.

Every CSV in data/ maps to one table in db/schema.sql. The import is skipped
when the tables already hold data, so restarting Compose is fast. Set
FORCE_IMPORT=1 to drop the catalogue tables and load them again.
"""

import csv
import os
import re
import sys
import time
from pathlib import Path

from mysql.connector import Error

sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import connect_with_retry

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
BATCH_SIZE = 5000
FORCE_IMPORT = os.getenv("FORCE_IMPORT", "").lower() in ("1", "true", "yes")


def text(value):
    value = value.strip()
    return value or None


def integer(value):
    value = value.strip()
    return int(value) if value else None


def boolean(value):
    return value.strip().lower() in ("true", "t", "1")


# (table, csv file, [(column, csv field, converter)]), parent tables first.
TABLES = [
    ("themes", "themes.csv", [
        ("id", "id", integer),
        ("name", "name", str),
        ("parent_id", "parent_id", integer),
    ]),
    ("sets", "sets.csv", [
        ("set_num", "set_num", str),
        ("name", "name", str),
        ("year", "year", integer),
        ("theme_id", "theme_id", integer),
        ("num_parts", "num_parts", integer),
        ("img_url", "img_url", text),
    ]),
    ("colors", "colors.csv", [
        ("id", "id", integer),
        ("name", "name", str),
        ("rgb", "rgb", str),
        ("is_trans", "is_trans", boolean),
        ("num_parts", "num_parts", integer),
        ("num_sets", "num_sets", integer),
        ("y1", "y1", integer),
        ("y2", "y2", integer),
    ]),
    ("part_categories", "part_categories.csv", [
        ("id", "id", integer),
        ("name", "name", str),
    ]),
    ("parts", "parts.csv", [
        ("part_num", "part_num", str),
        ("name", "name", str),
        ("part_cat_id", "part_cat_id", integer),
        ("part_material", "part_material", text),
    ]),
    ("part_relationships", "part_relationships.csv", [
        ("rel_type", "rel_type", str),
        ("child_part_num", "child_part_num", str),
        ("parent_part_num", "parent_part_num", str),
    ]),
    ("elements", "elements.csv", [
        ("element_id", "element_id", str),
        ("part_num", "part_num", str),
        ("color_id", "color_id", integer),
        ("design_id", "design_id", text),
    ]),
    ("minifigs", "minifigs.csv", [
        ("fig_num", "fig_num", str),
        ("name", "name", str),
        ("num_parts", "num_parts", integer),
        ("img_url", "img_url", text),
    ]),
    ("inventories", "inventories.csv", [
        ("id", "id", integer),
        ("version", "version", integer),
        ("set_num", "set_num", str),
    ]),
    ("inventory_parts", "inventory_parts.csv", [
        ("inventory_id", "inventory_id", integer),
        ("part_num", "part_num", str),
        ("color_id", "color_id", integer),
        ("quantity", "quantity", integer),
        ("is_spare", "is_spare", boolean),
        ("img_url", "img_url", text),
    ]),
    ("inventory_sets", "inventory_sets.csv", [
        ("inventory_id", "inventory_id", integer),
        ("set_num", "set_num", str),
        ("quantity", "quantity", integer),
    ]),
    ("inventory_minifigs", "inventory_minifigs.csv", [
        ("inventory_id", "inventory_id", integer),
        ("fig_num", "fig_num", str),
        ("quantity", "quantity", integer),
    ]),
    ("color_mappings", "color_mappings.csv", [
        ("color_id", "id", integer),
        ("ext_system", "ext_system", str),
        ("ext_id", "ext_id", str),
        ("ext_descr", "ext_descr", text),
        ("is_export_id", "is_export_id", boolean),
        ("is_import_id", "is_import_id", boolean),
    ]),
    ("part_mappings", "part_mappings.csv", [
        ("part_num", "part_num", str),
        ("ext_system", "ext_system", str),
        ("ext_id", "ext_id", str),
        ("is_export_id", "is_export_id", boolean),
        ("is_import_id", "is_import_id", boolean),
    ]),
    ("set_mappings", "set_mappings.csv", [
        ("set_num", "set_num", str),
        ("ext_system", "ext_system", str),
        ("ext_id", "ext_id", str),
    ]),
]


def check_data_files():
    missing = [name for _, name, _ in TABLES if not (DATA_DIR / name).is_file()]
    if missing:
        raise SystemExit(f"Missing data files in {DATA_DIR}: {', '.join(missing)}")
    # inventory_parts.csv is stored with Git LFS. Without `git lfs pull` the
    # checkout holds a small pointer file instead of the CSV.
    with (DATA_DIR / "inventory_parts.csv").open(encoding="utf-8") as handle:
        if handle.readline().startswith("version https://git-lfs"):
            raise SystemExit(
                "data/inventory_parts.csv is a Git LFS pointer. Run `git lfs pull` first."
            )


def already_loaded(cursor):
    for table, _, _ in TABLES:
        cursor.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_name = %s",
            (table,),
        )
        if cursor.fetchone()[0] == 0:
            return False
        cursor.execute(f"SELECT EXISTS (SELECT 1 FROM {table})")
        if not cursor.fetchone()[0]:
            return False
    return True


def load_schema(cursor):
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    for table, _, _ in reversed(TABLES):
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    schema = re.sub(r"--[^\n]*", "", SCHEMA_PATH.read_text())
    for statement in schema.split(";"):
        sql = statement.strip()
        if sql:
            cursor.execute(sql)


def read_rows(path, columns):
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            yield tuple(convert(row[field]) for _, field, convert in columns)


def import_table(cursor, table, filename, columns):
    names = ", ".join(column for column, _, _ in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    sql = f"INSERT INTO {table} ({names}) VALUES ({placeholders})"

    started = time.monotonic()
    count = 0
    batch = []
    for row in read_rows(DATA_DIR / filename, columns):
        batch.append(row)
        if len(batch) >= BATCH_SIZE:
            cursor.executemany(sql, batch)
            count += len(batch)
            batch.clear()
    if batch:
        cursor.executemany(sql, batch)
        count += len(batch)
    print(f"Imported {count:>9,} rows into {table} ({time.monotonic() - started:.1f}s)")


def main():
    check_data_files()
    connection = None
    cursor = None
    try:
        connection = connect_with_retry()
        cursor = connection.cursor()

        if not FORCE_IMPORT and already_loaded(cursor):
            print("Rebrickable data already loaded. Set FORCE_IMPORT=1 to reload.")
            return

        load_schema(cursor)
        for table, filename, columns in TABLES:
            # A theme can list a parent that appears later in themes.csv.
            self_referencing = table == "themes"
            if self_referencing:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            import_table(cursor, table, filename, columns)
            if self_referencing:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        connection.commit()
        print("Rebrickable data import complete.")
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
