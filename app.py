import mysql.connector
from mysql.connector import Error
import time

print("Waiting 10 seconds for the database to boot...")
time.sleep(10)

connection = None
cursor = None

try:
    connection = mysql.connector.connect(
        host='db',
        user='root',
        password='cs348pass',
        database='lego_sets'
    )
    
    if connection.is_connected():
        print("Successfully connected to the database!")
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("DROP TABLE IF EXISTS users")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS themes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sets (
                set_num VARCHAR(50) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                year INT NOT NULL,
                theme_id INT,
                FOREIGN KEY (theme_id) REFERENCES themes(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("DELETE FROM sets")
        cursor.execute("DELETE FROM themes")
        
        cursor.execute("INSERT INTO themes (name) VALUES (%s)", ("Star Wars",))
        star_wars_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO themes (name) VALUES (%s)", ("Icons",))
        icons_id = cursor.lastrowid
        
        lego_sets_data = [
            ("75355-1", "X-Wing Starfighter", 2023, star_wars_id),
            ("75192-1", "Millennium Falcon", 2017, star_wars_id),
            ("10316-1", "The Lord of the Rings: Rivendell", 2023, icons_id)
        ]
        
        cursor.executemany(
            "INSERT INTO sets (set_num, name, year, theme_id) VALUES (%s, %s, %s, %s)",
            lego_sets_data
        )
        connection.commit()
        
        query = """
            SELECT s.set_num, s.name AS set_name, s.year, t.name AS theme_name
            FROM sets s
            INNER JOIN themes t ON s.theme_id = t.id
            ORDER BY s.year DESC
        """
        print(query)

        cursor.execute(query)
        results = cursor.fetchall()
        
        for row in results:
            print(f"[{row['set_num']}] {row['set_name']} ({row['year']}) - Theme: {row['theme_name']}")
            
except Error as e:
    print(f"Database Error: {e}")

finally:
    if cursor is not None:
        cursor.close()
    if connection is not None and connection.is_connected():
        connection.close()
        print("\nMySQL connection is closed.")
