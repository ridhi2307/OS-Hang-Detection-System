
import sqlite3
import os


# Database file location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "database",
    "os_monitor.db"
)


def get_connection():

    os.makedirs(
        os.path.dirname(DATABASE_PATH),
        exist_ok=True
    )

    connection = sqlite3.connect(DATABASE_PATH)

    return connection


def create_tables():

    connection = get_connection()

    cursor = connection.cursor()

    # Table 1: Process Monitoring
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS process_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pid INTEGER,
            process_name TEXT,
            cpu_percent REAL,
            memory_mb REAL,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 2: Application Hang Detection
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hang_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pid INTEGER,
            process_name TEXT,
            window_title TEXT,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 3: Memory Monitoring
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_gb REAL,
            used_gb REAL,
            available_gb REAL,
            usage_percent REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 4: Deadlock Detection
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deadlock_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deadlock_detected INTEGER,
            description TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 5: Storage Monitoring
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS storage_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device TEXT,
            total_gb REAL,
            used_gb REAL,
            free_gb REAL,
            usage_percent REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 6: Recovery Actions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recovery_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pid INTEGER,
            action TEXT,
            result TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()

    connection.close()

    print("Database tables created successfully!")


if __name__ == "__main__":

    create_tables()

    print(f"Database location: {DATABASE_PATH}")
