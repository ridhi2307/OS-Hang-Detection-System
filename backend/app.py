from flask import Flask, jsonify, render_template, request
from backend.process_monitor import get_running_processes
from backend.hang_detector import get_application_windows
from backend.memory_analyzer import (
    get_memory_information,
    get_top_memory_processes
)
from backend.storage_monitor import get_storage_information
from backend.database import create_tables, get_connection
from backend.recovery_manager import recover_test_application


app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)


# -----------------------------------------
# DATABASE STORAGE FUNCTIONS
# -----------------------------------------

def save_process_records(processes):

    connection = get_connection()
    cursor = connection.cursor()

    for process in processes:
        cursor.execute("""
            INSERT INTO process_records
            (pid, process_name, cpu_percent, memory_mb, status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            process["pid"],
            process["name"],
            process["cpu_percent"],
            process["memory_mb"],
            process["status"]
        ))

    connection.commit()
    connection.close()


def save_hang_records(windows):

    connection = get_connection()
    cursor = connection.cursor()

    for window in windows:
        cursor.execute("""
            INSERT INTO hang_records
            (pid, process_name, window_title, status)
            VALUES (?, ?, ?, ?)
        """, (
            window["pid"],
            window["process_name"],
            window["window_title"],
            window["status"]
        ))

    connection.commit()
    connection.close()


def save_memory_record(memory):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO memory_records
        (total_gb, used_gb, available_gb, usage_percent)
        VALUES (?, ?, ?, ?)
    """, (
        memory["total_gb"],
        memory["used_gb"],
        memory["available_gb"],
        memory["usage_percent"]
    ))

    connection.commit()
    connection.close()


def save_storage_records(disks):

    connection = get_connection()
    cursor = connection.cursor()

    for disk in disks:
        cursor.execute("""
            INSERT INTO storage_records
            (device, total_gb, used_gb, free_gb, usage_percent)
            VALUES (?, ?, ?, ?, ?)
        """, (
            disk["device"],
            disk["total_gb"],
            disk["used_gb"],
            disk["free_gb"],
            disk["usage_percent"]
        ))

    connection.commit()
    connection.close()


# -----------------------------------------
# DEADLOCK DETECTION
# -----------------------------------------

def run_deadlock_analysis():

    processes = ["P1", "P2", "P3"]

    allocations = {
        "P1": "R1",
        "P2": "R2",
        "P3": "R3"
    }

    requests = {
        "P1": "R2",
        "P2": "R3",
        "P3": "R1"
    }

    graph = {process: [] for process in processes}

    for waiting_process, requested_resource in requests.items():

        for holding_process, held_resource in allocations.items():

            if requested_resource == held_resource:
                graph[waiting_process].append(holding_process)

    visited = set()
    recursion_stack = set()

    def detect_cycle(process):

        visited.add(process)
        recursion_stack.add(process)

        for neighbor in graph[process]:

            if neighbor not in visited:

                if detect_cycle(neighbor):
                    return True

            elif neighbor in recursion_stack:
                return True

        recursion_stack.remove(process)

        return False

    deadlock_detected = False

    for process in graph:

        if process not in visited:

            if detect_cycle(process):
                deadlock_detected = True
                break

    return {
        "deadlock_detected": deadlock_detected,
        "graph": graph,
        "description": (
            "Circular wait detected in simulated processes."
            if deadlock_detected
            else "No circular wait detected."
        )
    }


def save_deadlock_record(result):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO deadlock_records
        (deadlock_detected, description)
        VALUES (?, ?)
    """, (
        int(result["deadlock_detected"]),
        result["description"]
    ))

    connection.commit()
    connection.close()


# -----------------------------------------
# HOME ROUTE
# -----------------------------------------

@app.route("/")
def home():

    return render_template("index.html")

# -----------------------------------------
# PROCESS MONITORING API
# -----------------------------------------

@app.route("/api/processes")
def processes_api():

    processes = get_running_processes(
        sample_interval=0.2,
        limit=25
    )

    save_process_records(processes)

    return jsonify({
        "total_processes": len(processes),
        "processes": processes
    })


# -----------------------------------------
# APPLICATION HANG DETECTION API
# -----------------------------------------

@app.route("/api/hangs")
def hangs_api():

    windows = get_application_windows()

    save_hang_records(windows)

    hung_count = sum(
        1 for window in windows
        if window["status"] == "NOT RESPONDING"
    )

    return jsonify({
        "total_windows": len(windows),
        "unresponsive_windows": hung_count,
        "windows": windows
    })


# -----------------------------------------
# MEMORY MONITORING API
# -----------------------------------------

@app.route("/api/memory")
def memory_api():

    memory = get_memory_information()

    top_processes = get_top_memory_processes()

    save_memory_record(memory)

    return jsonify({
        "system_memory": memory,
        "top_memory_processes": top_processes
    })


# -----------------------------------------
# STORAGE MONITORING API
# -----------------------------------------

@app.route("/api/storage")
def storage_api():

    disks = get_storage_information()

    save_storage_records(disks)

    return jsonify({
        "total_partitions": len(disks),
        "storage": disks
    })


# -----------------------------------------
# DEADLOCK DETECTION API
# -----------------------------------------

@app.route("/api/deadlock")
def deadlock_api():

    result = run_deadlock_analysis()

    save_deadlock_record(result)

    return jsonify(result)


# -----------------------------------------
# COMPLETE DASHBOARD API
# -----------------------------------------

@app.route("/api/dashboard")
def dashboard_api():

    processes = get_running_processes(
        sample_interval=0.2,
        limit=25
    )

    windows = get_application_windows()

    memory = get_memory_information()

    top_processes = get_top_memory_processes()

    disks = get_storage_information()

    deadlock = run_deadlock_analysis()

    # Save all collected monitoring data
    save_process_records(processes)
    save_hang_records(windows)
    save_memory_record(memory)
    save_storage_records(disks)
    save_deadlock_record(deadlock)

    hung_count = sum(
        1 for window in windows
        if window["status"] == "NOT RESPONDING"
    )

    return jsonify({
        "processes": {
            "total": len(processes),
            "data": processes
        },
        "hang_detection": {
            "total_windows": len(windows),
            "unresponsive_windows": hung_count,
            "data": windows
        },
        "memory": {
            "system": memory,
            "top_processes": top_processes
        },
        "storage": disks,
        "deadlock": deadlock
    })




# -----------------------------------------
# APPLICATION RECOVERY API
# -----------------------------------------

@app.route("/api/recovery", methods=["POST"])
def recovery_api():

    data = request.get_json(silent=True) or {}

    pid = data.get("pid")
    confirmed = data.get("confirmed", False)

    if pid is None:
        return jsonify({
            "success": False,
            "message": "Process ID is required."
        }), 400

    if confirmed is not True:
        return jsonify({
            "success": False,
            "message": "Recovery confirmation is required."
        }), 400

    result = recover_test_application(
        pid=pid,
        confirmed=confirmed
    )

    # Save recovery attempt in SQLite
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO recovery_records
        (pid, action, result)
        VALUES (?, ?, ?)
    """, (
        pid,
        "Graceful termination",
        result["message"]
    ))

    connection.commit()
    connection.close()

    status_code = 200 if result["success"] else 400

    return jsonify(result), status_code

# RECOVERY HISTORY API
@app.route("/api/recovery/history")
def recovery_history_api():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT pid, action, result, timestamp
        FROM recovery_records
        ORDER BY id DESC
        LIMIT 50
    """)

    rows = cursor.fetchall()
    connection.close()

    records = []

    for row in rows:
        records.append({
            "pid": row[0],
            "action": row[1],
            "result": row[2],
            "timestamp": row[3]
        })

    return jsonify({
        "total_records": len(records),
        "records": records
    })


# -----------------------------------------
# START FLASK SERVER
# -----------------------------------------

if __name__ == "__main__":

    create_tables()

    print("\nStarting OS Monitoring Flask Backend...")
    print("Open http://127.0.0.1:5000 in your browser.")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
