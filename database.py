import os
import time

import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "db"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "cs348pass"),
    "database": os.getenv("DB_NAME", "lego_sets"),
}

MAX_RETRIES = 30
RETRY_DELAY_SECONDS = 2


def connect_with_retry():
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            if connection.is_connected():
                print(f"Successfully connected to the database! (attempt {attempt})")
                return connection
            connection.close()
        except Error as exc:
            last_error = exc
            print(f"Waiting for MySQL (attempt {attempt}/{MAX_RETRIES}): {exc}")
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS)
    raise last_error or Error("Could not connect to MySQL")


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)
