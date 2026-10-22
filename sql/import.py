import sys
import time
from pathlib import Path

import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "db",
    "user": "root",
    "password": "cs348pass",
    "database": "lego_sets",
    "allow_local_infile": True,
    "charset": "utf8mb4",
}

SQL_PATH = Path(__file__).resolve().parent / "init.sql"
MAX_RETRIES = 30
RETRY_DELAY_SECONDS = 2

TABLES = [
    "themes",
    "colors",
    "part_categories",
    "parts",
    "elements",
    "sets",
    "minifigs",
    "inventories",
    "inventory_parts",
    "inventory_sets",
    "inventory_minifigs",
    "part_relationships",
    "part_mappings",
    "set_mappings",
    "color_mappings",
]

FIELD_OPTIONS = """
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
ESCAPED BY '"'
LINES TERMINATED BY '\\r\\n'
IGNORE 1 LINES
"""

BOOLEAN_EXPR = "LOWER({name}) IN ('true', 't', '1')"


def load_statement(table, column_clause=""):
    return f"""
LOAD DATA LOCAL INFILE '/data/{table}.csv'
INTO TABLE {table}
{FIELD_OPTIONS}
{column_clause}
"""


def boolean_column(name):
    return BOOLEAN_EXPR.format(name=name)


LOADS = [
    (
        "themes",
        load_statement(
            "themes",
            """
            (id, name, @parent_id)
            SET parent_id = NULLIF(@parent_id, '')
            """,
        ),
    ),
    (
        "colors",
        load_statement(
            "colors",
            f"""
            (id, name, rgb, @is_trans, num_parts, num_sets, @y1, @y2)
            SET
                is_trans = {boolean_column("@is_trans")},
                y1 = NULLIF(@y1, ''),
                y2 = NULLIF(@y2, '')
            """,
        ),
    ),
    ("part_categories", load_statement("part_categories")),
    ("parts", load_statement("parts")),
    (
        "elements",
        load_statement(
            "elements",
            """
            (element_id, part_num, color_id, @design_id)
            SET design_id = NULLIF(@design_id, '')
            """,
        ),
    ),
    ("sets", load_statement("sets")),
    ("minifigs", load_statement("minifigs")),
    ("inventories", load_statement("inventories")),
    (
        "inventory_parts",
        load_statement(
            "inventory_parts",
            f"""
            (inventory_id, part_num, color_id, quantity, @is_spare, @img_url)
            SET
                is_spare = {boolean_column("@is_spare")},
                img_url = NULLIF(@img_url, '')
            """,
        ),
    ),
    ("inventory_sets", load_statement("inventory_sets")),
    ("inventory_minifigs", load_statement("inventory_minifigs")),
    ("part_relationships", load_statement("part_relationships")),
    (
        "part_mappings",
        load_statement(
            "part_mappings",
            f"""
            (part_num, ext_system, ext_id, @is_export_id, @is_import_id)
            SET
                is_export_id = {boolean_column("@is_export_id")},
                is_import_id = {boolean_column("@is_import_id")}
            """,
        ),
    ),
    ("set_mappings", load_statement("set_mappings")),
    (
        "color_mappings",
        load_statement(
            "color_mappings",
            f"""
            (id, ext_system, ext_id, ext_descr, @is_export_id, @is_import_id)
            SET
                is_export_id = {boolean_column("@is_export_id")},
                is_import_id = {boolean_column("@is_import_id")}
            """,
        ),
    ),
]


def connect_with_retry():
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            if conn.is_connected():
                print(f"Import connected to the database (attempt {attempt})")
                conn.autocommit = True
                return conn
        except Error as e:
            last_error = e
            print(f"Waiting for MySQL (attempt {attempt}/{MAX_RETRIES}): {e}")
            time.sleep(RETRY_DELAY_SECONDS)
    raise last_error or Error("Could not connect to the database")


def statement_list(sql_text):
    statements = []
    for chunk in sql_text.split(";"):
        statement = chunk.strip()
        if statement:
            statements.append(statement)
    return statements


def catalog_loaded(cursor):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = DATABASE() AND table_name = 'themes'
        """
    )
    if cursor.fetchone()[0] == 0:
        return False
    cursor.execute("SELECT COUNT(*) FROM themes")
    return cursor.fetchone()[0] > 0


def execute_statements(cursor, statements):
    for statement in statements:
        cursor.execute(statement)


def reset_tables(cursor):
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    for table in TABLES:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")


def load_catalog(cursor):
    # themes.csv lists some child themes before their parent row.
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    try:
        for table, statement in LOADS:
            print(f"Loading {table}...")
            cursor.execute(statement)
            print(f"Loaded {table}: {cursor.rowcount} rows")
    finally:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")


def main():
    create_statements = statement_list(SQL_PATH.read_text(encoding="utf-8"))

    connection = None
    cursor = None
    try:
        connection = connect_with_retry()
        cursor = connection.cursor()
        if catalog_loaded(cursor):
            print("Catalog already loaded; skipping import.")
            return

        reset_tables(cursor)
        execute_statements(cursor, create_statements)
        load_catalog(cursor)
    except Error as e:
        print(f"Database Error: {e}")
        sys.exit(1)
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    main()
