import mysql.connector
from mysql.connector import Error
import sys
import time

DB_CONFIG = {
    "host": "db",
    "user": "root",
    "password": "cs348pass",
    "database": "lego_sets",
}

MAX_RETRIES = 30
RETRY_DELAY_SECONDS = 2

connection = None
cursor = None


def connect_with_retry():
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            if conn.is_connected():
                print(f"Successfully connected to the database! (attempt {attempt})")
                return conn
        except Error as e:
            last_error = e
            print(f"Waiting for MySQL (attempt {attempt}/{MAX_RETRIES}): {e}")
            time.sleep(RETRY_DELAY_SECONDS)
    raise last_error or Error("Could not connect to the database")


try:
    connection = connect_with_retry()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT s.set_num, s.name AS set_name, s.year, t.name AS theme_name
        FROM sets s
        INNER JOIN themes t ON s.theme_id = t.id
        ORDER BY s.year DESC, s.set_num
        LIMIT 10
    """
    print(query)

    cursor.execute(query)
    results = cursor.fetchall()

    for row in results:
        print(f"[{row['set_num']}] {row['set_name']} ({row['year']}) - Theme: {row['theme_name']}")

except Error as e:
    print(f"Database Error: {e}")
    sys.exit(1)

finally:
    if cursor is not None:
        cursor.close()
    if connection is not None and connection.is_connected():
        connection.close()
        print("\nMySQL connection is closed.")
