from flask import Flask, jsonify, render_template, request, send_file
from backend.live_deadlock import demo
from backend.graph_lab import SCENARIOS, simulate
from backend.resource_labs import LABS
from backend.paging import compare_pages
from backend.process_monitor import get_running_processes
from backend.hang_detector import get_application_windows
from backend.memory_analyzer import (
    get_memory_information,
    get_top_memory_processes
)
from backend.storage_monitor import get_storage_information
from backend.database import create_tables, get_connection
from backend import health
from backend.recovery_manager import apply_action, controlled
import psutil
from contextlib import closing
from backend.report_generator import (
    generate_csv_report,
    generate_pdf_report
)


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

    # Legacy API clients expect a wait-for graph for the three-process exercise.
    final = simulate(SCENARIOS["Three-process circular wait"])[-1]
    graph = {}
    for i, request_row in enumerate(final["requests"]):
        graph[f"P{i+1}"] = [
            f"P{j+1}" for j,allocation in enumerate(final["held"])
            if any(request and held for request,held in zip(request_row,allocation))
        ]
    return dict(deadlock_detected=bool(final["deadlocked"]), graph=graph, description=final["text"])


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

    return render_template("index.html", labs=LABS, scenarios=SCENARIOS)

# -----------------------------------------
# PROCESS MONITORING API
# -----------------------------------------

@app.route("/api/lab/live-deadlock", methods=["GET", "POST"])
def live_deadlock_api():
    if request.method == "GET":
        return jsonify(demo.snapshot())
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or data.get("action") not in ("start", "advance", "recover"):
        return jsonify(error="Choose a demo action."), 400
    try:
        if data["action"] == "start":
            return jsonify(demo.start())
        return jsonify(demo.act(data["action"], data.get("run_id")))
    except ValueError as error:
        return jsonify(error=str(error)), 409


@app.post("/api/lab/graph")
def graph_lab():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Submit a scenario."), 400
    try:
        return jsonify(steps=simulate(data.get("scenario"), data.get("victim")))
    except ValueError as error:
        return jsonify(error=str(error)), 400


@app.post("/api/lab/<name>")
def resource_lab_api(name):
    if name not in LABS:
        return jsonify(error="Unknown simulation."), 404
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Submit a simulation workload."), 400
    try:
        return jsonify(LABS[name]["simulate"](data))
    except ValueError as error:
        return jsonify(error=str(error)), 400


@app.post("/api/lab/paging")
def paging_api():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Submit a page sequence and frame count."), 400
    try:
        return jsonify(compare_pages(data.get("pages"), data.get("frames")))
    except ValueError as error:
        return jsonify(error=str(error)), 400


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

    processes = get_running_processes(sample_interval=0.2, limit=None)
    snapshot = health.sample(force=request.args.get("recheck")=="1")
    windows = snapshot["windows"]
    snapshot = {**snapshot, "apps": [app.copy() for app in snapshot["apps"]]}
    for item in snapshot["apps"]:
        item["supported"] = False
        if item["incident"]:
            try:
                item["supported"] = controlled(psutil.Process(item["pid"]))
            except psutil.Error:
                pass

    memory = get_memory_information()

    top_processes = get_top_memory_processes()

    disks = get_storage_information()

    deadlock = run_deadlock_analysis()

    # Save all collected monitoring data
    save_process_records(processes[:25])
    save_hang_records(windows)
    save_memory_record(memory)
    save_storage_records(disks)
    # Educational simulations do not count as host incidents.

    hung_count = sum(
        1 for window in windows
        if window["status"] == "NOT RESPONDING"
    )

    return jsonify({
        "health": snapshot, "cpu": psutil.cpu_percent(interval=0.1), "running": len(psutil.pids()),
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

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or data.get("confirmed") is not True:
        return jsonify(success=False, message="Explicit confirmation required."), 400
    try:
        incident = data.get("incident")
        if "incident" not in data and type(data.get("pid")) is int:
            # The original React client sends only a confirmed PID.
            match = next((a for a in health.sample()["apps"] if a["pid"] == data["pid"]), None)
            incident = match["incident"] if match else None
        result = apply_action(data.get("pid"), incident, data.get("method","end"))
        return jsonify(result), 200 if result["success"] else 409
    except ValueError as error:
        return jsonify(success=False,message=str(error)), 409


@app.post("/api/health/threshold")
def set_threshold():
    data = request.get_json(silent=True)
    seconds = data.get("seconds") if isinstance(data, dict) else None
    if type(seconds) is not int or not 2 <= seconds <= 60:
        return jsonify(error="Choose a threshold from 2 to 60 seconds."), 400
    with closing(get_connection()) as db, db:
        db.execute("UPDATE detection_settings SET seconds=? WHERE id=1",(seconds,))
    return jsonify(seconds=seconds)


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


@app.route("/api/reports/csv", methods=["GET"])
def download_csv_report():
    report_path = generate_csv_report()

    return send_file(
        report_path,
        as_attachment=True,
        download_name="OS_Guardian_System_Report.csv",
        mimetype="text/csv"
    )


@app.route("/api/reports/pdf", methods=["GET"])
def download_pdf_report():
    report_path = generate_pdf_report()

    return send_file(
        report_path,
        as_attachment=True,
        download_name="OS_Guardian_System_Report.pdf",
        mimetype="application/pdf"
    )

# -----------------------------------------
# START FLASK SERVER
# -----------------------------------------

if __name__ == "__main__":

    create_tables()
    health.start_monitor()

    print("\nStarting OS Monitoring Flask Backend...")
    print("Open http://127.0.0.1:5000 in your browser.")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
