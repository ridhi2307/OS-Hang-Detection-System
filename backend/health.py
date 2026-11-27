"""Window-health sampling and durable incident transitions."""
import sqlite3
import logging
import threading
import time
from contextlib import closing

from backend.database import get_connection
from backend.hang_detector import get_application_windows

guard = threading.RLock()
pending = {}
last_sample = 0
cache = {}
thread = None


def record(db, incident, name, pid, event, detail, now):
    db.execute("INSERT INTO health_events(incident,name,pid,event,detail,at) VALUES(?,?,?,?,?,?)",
               (incident, name, pid, event, detail, now))


def sample(force=False):
    global last_sample, cache
    with guard:
        now = time.time()
        if cache and not force and now-last_sample < 2:
            return cache
        windows = get_application_windows()
        with closing(get_connection()) as db, db:
            threshold = db.execute("SELECT seconds FROM detection_settings").fetchone()[0]
            apps = {}
            seen = set()
            for w in windows:
                key = (w["pid"], w["born"], w["hwnd"])
                raw = w["status"]
                if raw == "NOT RESPONDING":
                    start, count = pending.get(key, (now, 0))
                    pending[key] = (start, count+1)
                    seen.add(key)
                    state = "Unresponsive" if count and now-start >= threshold else "Checking"
                else:
                    start = None
                    state = "Healthy" if raw == "RESPONDING" else "Unknown"
                w.update(state=state, since=start, checked=now)
                identity = key[:2]
                ranks = ["Healthy", "Unknown", "Checking", "Unresponsive"]
                if identity not in apps or ranks.index(state) > ranks.index(apps[identity]["state"]):
                    apps[identity] = w.copy()
            for key in pending.keys() - seen:
                del pending[key]
            active = {(pid,born):(iid,status,hwnd) for iid,pid,born,status,hwnd in db.execute(
                "SELECT id,pid,born,status,hwnd FROM incidents WHERE closed IS NULL")}
            for key, app in apps.items():
                incident, status, hwnd = active.get(key, (None, None, None))
                if not incident and app["state"] == "Unresponsive":
                    incident = db.execute("INSERT INTO incidents(pid,born,name,title,started,status,hwnd) VALUES(?,?,?,?,?,?,?)",
                          (*key,app["process_name"],app["window_title"],app["since"],"Unresponsive",app["hwnd"])).lastrowid
                    record(db, incident, app["process_name"], key[0], "Hang detected",
                           f"Windows reported a stalled message loop across checks spanning {threshold}s.", now)
                elif incident and status == "Recovering":
                    app["state"] = status
                elif incident and app["state"] == "Healthy":
                    verified = any(w["hwnd"]==hwnd and w["state"]=="Healthy" for w in windows)
                    outcome = "Responsive again" if verified else "Window gone"
                    detail = "Original window answered a message probe." if verified else "Original window no longer observable."
                    db.execute("UPDATE incidents SET closed=?,status=? WHERE id=?", (now,outcome,incident))
                    record(db, incident, app["process_name"], key[0], outcome, detail, now)
                    incident = None
                elif incident and status == "Failed":
                    app["state"] = status
                app["incident"] = incident
            for key in active.keys() - apps.keys():
                incident,status,_ = active[key]
                if status == "Recovering":
                    continue
                db.execute("UPDATE incidents SET closed=?,status='Window gone' WHERE id=?", (now,incident))
                name = db.execute("SELECT name FROM incidents WHERE id=?", (incident,)).fetchone()[0]
                record(db, incident, name, key[0], "Window gone", "Window no longer observable.", now)
            counts = {state:sum(a["state"] == state for a in apps.values()) for state in
                      ("Healthy","Unresponsive","Recovering","Failed","Checking","Unknown")}
            if now-last_sample >= 2 or not cache:
                db.execute("INSERT INTO health_samples(at,total,healthy,hung) VALUES(?,?,?,?)",
                           (now,len(apps),counts["Healthy"],counts["Unresponsive"]+counts["Failed"]))
            db.row_factory = sqlite3.Row
            events = [dict(row) for row in db.execute("SELECT * FROM health_events ORDER BY id DESC LIMIT 100")]
            history = [dict(row) for row in db.execute("SELECT * FROM health_samples ORDER BY at DESC LIMIT 60")][::-1]
            if history:
                first = db.execute("SELECT max(at) FROM health_samples WHERE at<?",(history[0]["at"],)).fetchone()[0] or 0
                starts = [row[0] for row in db.execute("SELECT at FROM health_events WHERE event='Hang detected' AND at>? AND at<=?",(first,now))]
                for point in history:
                    point["detected"] = sum(first < t <= point["at"] for t in starts)
                    first = point["at"]
            counts["Recovering"] = db.execute("SELECT COUNT(*) FROM incidents WHERE status='Recovering' AND closed IS NULL").fetchone()[0]
            successes = db.execute("SELECT COUNT(*) FROM health_events WHERE event='Restart verified'").fetchone()[0]
        last_sample = now
        cache = dict(apps=list(apps.values()), windows=windows, counts=counts, events=events, history=history,
                     successes=successes, checked=now, threshold=threshold)
        return cache


def start_monitor():
    global thread
    with guard:
        if thread and thread.is_alive():
            return
        with closing(get_connection()) as db, db:
            for incident,name,pid in db.execute("SELECT id,name,pid FROM incidents WHERE status='Recovering' AND closed IS NULL").fetchall():
                db.execute("UPDATE incidents SET status='Failed' WHERE id=?", (incident,))
                record(db, incident, name, pid, "Failed", "Monitor restarted before recovery could be verified.", time.time())
        def monitor():
            while True:
                try:
                    sample()
                except Exception:
                    logging.exception("Window sampling failed")
                time.sleep(4)
        thread = threading.Thread(target=monitor, name="window-health", daemon=True)
        thread.start()
