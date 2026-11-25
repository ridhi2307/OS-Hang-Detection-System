
import sqlite3
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "database",
    "os_monitor.db"
)


def get_database_connection():

    return sqlite3.connect(DATABASE_PATH)


def get_process_statistics():

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            COUNT(*),
            ROUND(AVG(cpu_percent), 2),
            ROUND(AVG(memory_mb), 2)
        FROM process_records
    """)

    result = cursor.fetchone()

    connection.close()

    return {
        "total_records": result[0] or 0,
        "average_cpu": result[1] or 0,
        "average_memory": result[2] or 0
    }


def get_hang_statistics():

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM hang_records
        WHERE status = 'NOT RESPONDING'
    """)

    result = cursor.fetchone()[0]

    connection.close()

    return result


def get_memory_statistics():

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            ROUND(AVG(usage_percent), 2),
            MAX(usage_percent)
        FROM memory_records
    """)

    result = cursor.fetchone()

    connection.close()

    return {
        "average_usage": result[0] or 0,
        "maximum_usage": result[1] or 0
    }


def get_deadlock_statistics():

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM deadlock_records
        WHERE deadlock_detected = 1
    """)

    result = cursor.fetchone()

    connection.close()

    return result[0]



def get_recovery_statistics():

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM recovery_records
        WHERE UPPER(result) LIKE '%SUCCESS%'
    """)

    successful_recoveries = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM recovery_records
    """)

    total_recoveries = cursor.fetchone()[0]

    connection.close()

    return {
        "total_attempts": total_recoveries,
        "successful_recoveries": successful_recoveries
    }

def generate_system_report():

    process_stats = get_process_statistics()
    hang_count = get_hang_statistics()
    memory_stats = get_memory_statistics()
    deadlock_count = get_deadlock_statistics()
    recovery_stats = get_recovery_statistics()

    print("\n" + "=" * 65)
    print("             SYSTEM ANALYTICS AND HEALTH REPORT")
    print("=" * 65)

    print("\nPROCESS STATISTICS")

    print("Total Process Records:", process_stats["total_records"])
    print("Average CPU Usage:", process_stats["average_cpu"], "%")
    print("Average Process Memory:", process_stats["average_memory"], "MB")

    print("\nAPPLICATION HANG STATISTICS")

    print("Detected Application Hangs:", hang_count)

    print("\nMEMORY STATISTICS")

    print("Average RAM Usage:", memory_stats["average_usage"], "%")
    print("Maximum RAM Usage:", memory_stats["maximum_usage"], "%")

    print("\nDEADLOCK STATISTICS")

    print("Detected Deadlocks:", deadlock_count)

    print("\nRECOVERY STATISTICS")

    print("Total Recovery Attempts:", recovery_stats["total_attempts"])
    print("Successful Recoveries:", recovery_stats["successful_recoveries"])

    print("\n" + "=" * 65)
    print("             END OF SYSTEM REPORT")
    print("=" * 65)


if __name__ == "__main__":

    generate_system_report()
