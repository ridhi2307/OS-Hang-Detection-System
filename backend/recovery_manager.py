"""Confirmed actions on the bundled Windows test application."""
import subprocess
import sys
import time
from contextlib import closing
from pathlib import Path

import psutil

from backend.database import get_connection
from backend.hang_detector import get_application_windows
from backend import health

TEST_APP = Path(__file__).resolve().parents[1] / "tests" / "test_hang.py"


def controlled(process):
    try:
        args = process.cmdline()
        if len(args) < 2 or Path(process.exe()).resolve() != Path(sys.executable).resolve():
            return False
        script = Path(args[1])
        if not script.is_absolute():
            script = Path(process.cwd()) / script
        return script.resolve() == TEST_APP
    except (psutil.Error, OSError):
        return False


def apply_action(pid, incident, method):
    if type(pid) is not int or type(incident) is not int or method not in ("end", "restart"):
        raise ValueError("Select a confirmed incident and a supported action.")
    with health.guard, closing(get_connection()) as db, db:
        row = db.execute("SELECT name,born,status FROM incidents WHERE id=? AND pid=? AND closed IS NULL",
                         (incident,pid)).fetchone()
        if not row or row[2] not in ("Unresponsive","Failed"):
            raise ValueError("This incident is no longer eligible for recovery.")
        name,born,_ = row
        db.execute("UPDATE incidents SET status='Recovering' WHERE id=?", (incident,))
        health.record(db, incident, name, pid, "Attempt started", method, time.time())
    success = False
    try:
        p = psutil.Process(pid)
        if p.create_time() != born or not controlled(p):
            raise ValueError("Automatic actions are supported only for the bundled test application.")
        if not any(w["pid"] == pid and w["born"] == born and w["status"] == "NOT RESPONDING"
                   for w in get_application_windows()):
            raise ValueError("The target no longer has a confirmed stalled window.")
        p.terminate()
        p.wait(timeout=5)
        outcome, message = "Exit verified", "The original process exited."
        if method == "restart":
            child = subprocess.Popen([sys.executable,str(TEST_APP)], cwd=TEST_APP.parent)
            deadline = time.monotonic()+10
            while time.monotonic() < deadline:
                if child.poll() is not None:
                    raise ValueError("The replacement process exited before verification.")
                if any(w["pid"] == child.pid and w["status"] == "RESPONDING" for w in get_application_windows()):
                    break
                time.sleep(0.25)
            else:
                raise ValueError(f"Replacement PID {child.pid} started but no responsive window was verified.")
            outcome, message = "Restart verified", f"Original exit verified. Responsive replacement PID {child.pid}."
        success = True
    except (ValueError, psutil.Error, OSError) as error:
        outcome, message = "Failed", str(error)
    with health.guard, closing(get_connection()) as db, db:
        now = time.time()
        db.execute("UPDATE incidents SET status=?,closed=? WHERE id=?", (outcome, now if success else None, incident))
        health.record(db, incident, name, pid, outcome, message, now)
        db.execute("INSERT INTO recovery_records(pid,action,result) VALUES(?,?,?)", (pid,method,message))
    return dict(success=success, message=message)



def run_recovery_manager():
    from backend.database import create_tables
    create_tables()
    health.start_monitor()
    print("Waiting for repeat Windows observations…")
    threshold = health.sample()["threshold"]
    time.sleep(threshold+4)
    apps = [a for a in health.sample(True)["apps"] if a["incident"]]
    if not apps:
        print("No confirmed unresponsive applications.")
        return
    for a in apps:
        print(a["pid"], a["process_name"], a["state"])
    try:
        pid = int(input("PID of the bundled test app to end: "))
        app = next((a for a in apps if a["pid"]==pid), None)
        if app and input(f"End test process {pid}? Type yes to confirm: ").strip().lower()=="yes":
            print(apply_action(pid,app["incident"],"end")["message"])
    except ValueError as error:
        print(error)


if __name__ == "__main__":
    run_recovery_manager()
