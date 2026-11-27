import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from backend import database, health
from backend.app import app
from backend.graph_lab import SCENARIOS, simulate
from backend.paging import compare_pages
from backend.recovery_manager import TEST_APP
from backend.resource_labs import cpu, disk


class Algorithms(unittest.TestCase):
    def test_graphs_and_recovery(self):
        for name,spec in SCENARIOS.items():
            last = simulate(spec)[-1]
            if name in ("Two-process deadlock", "Three-process circular wait"):
                self.assertEqual(len(last["deadlocked"]),len(spec["allocation"]))
                last = simulate(spec,0)[-1]
            self.assertEqual(last["available"],spec["capacity"])
            self.assertFalse(last["deadlocked"])
        with self.assertRaises(ValueError):
            simulate(dict(capacity=[1],allocation=[[2]],requests=[[0]]))

    def test_two_independent_cycles(self):
        spec = dict(capacity=[1,1,1,1], allocation=[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],
                    requests=[[0,1,0,0],[1,0,0,0],[0,0,0,1],[0,0,1,0]])
        self.assertEqual(simulate(spec,[0])[-1]["deadlocked"],[2,3])
        self.assertEqual(simulate(spec,[0,2])[-1]["available"],spec["capacity"])

    def test_preemption_and_priority(self):
        runs = cpu(dict(arrivals="0 1 1",bursts="6 2 1",priorities="5 1 2",quantum="2"))["runs"]
        self.assertEqual([s[2] for s in runs[3]["steps"]],["P1","P3","P2","P1"])
        self.assertEqual([j[4] for j in runs[3]["jobs"]],[9,4,2])
        self.assertEqual([s[2] for s in runs[4]["steps"]],["P1","P2","P3"])

    def test_disk_and_optimal(self):
        runs = disk(dict(head="50",requests="50 80 20"))["runs"]
        self.assertEqual([r["metrics"][0] for r in runs],[90,90,90,328,368,90])
        self.assertEqual(compare_pages("7 0 1 2 0 3 0 4 2 3 0 3 2",3)["Optimal"]["faults"],7)


class HealthTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        patcher = patch.object(database,"DATABASE_PATH",str(Path(temp.name)/"test.db"))
        patcher.start()
        self.addCleanup(patcher.stop)
        database.create_tables()
        health.cache = {}
        health.pending.clear()
        self.client = app.test_client()

    def test_confirm_once_and_resolve(self):
        window=dict(pid=42,born=1,hwnd=2,process_name="Sample",window_title="Document",status="NOT RESPONDING")
        with patch.object(health,"get_application_windows",return_value=[window]), patch.object(health.time,"time",side_effect=[100,103,107,110,111]):
            states=[health.sample(True)["apps"][0]["state"] for _ in range(4)]
            self.assertEqual(states,["Checking","Checking","Unresponsive","Unresponsive"])
            window["status"]="RESPONDING"
            self.assertEqual(health.sample(True)["apps"][0]["state"],"Healthy")
        with closing(database.get_connection()) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM incidents").fetchone()[0],1)
            self.assertEqual(db.execute("SELECT event FROM health_events ORDER BY id").fetchall(),[("Hang detected",),("Responsive again",)])
        self.assertEqual(self.client.post("/api/recovery",json={"pid":42}).status_code,400)

    def test_denied_recovery_records_failure(self):
        import psutil
        pid = os.getpid()
        with closing(database.get_connection()) as db, db:
            incident = db.execute("INSERT INTO incidents(pid,born,name,title,started,status) VALUES(?,?,?,?,?,?)",
                         (pid,psutil.Process().create_time(),"Test runner","",time.time(),"Unresponsive")).lastrowid
        response = self.client.post("/api/recovery", json=dict(pid=pid,incident=incident,confirmed=True,method="restart"))
        self.assertEqual(response.status_code,409)
        with closing(database.get_connection()) as db:
            self.assertEqual(db.execute("SELECT status FROM incidents").fetchone()[0],"Failed")
            self.assertEqual(db.execute("SELECT event FROM health_events ORDER BY id").fetchall(),[("Attempt started",),("Failed",)])

    @unittest.skipUnless(os.environ.get("OSHD_DESKTOP_TEST")=="1","interactive Windows desktop test")
    def test_real_recovery(self):
        self.client.post("/api/health/threshold",json={"seconds":2})
        real_popen = subprocess.Popen
        for method in ("restart","end"):
            with self.subTest(method=method):
                children=[]
                def launch(*args, **kwargs):
                    child=real_popen(*args,**kwargs)
                    children.append(child)
                    return child
                with patch("backend.recovery_manager.subprocess.Popen",side_effect=launch):
                    old=launch([sys.executable,str(TEST_APP),"--auto-hang"])
                    try:
                        deadline=time.monotonic()+32
                        while time.monotonic()<deadline:
                            sample=health.sample(True)
                            incident=next((w for w in sample["apps"] if w["pid"]==old.pid and w["incident"]),None)
                            if incident: break
                            time.sleep(.6)
                        else: self.fail("Windows did not confirm the test window hang")
                        result=self.client.post("/api/recovery",json=dict(pid=old.pid,incident=incident["incident"],method=method,confirmed=True))
                        self.assertEqual(result.status_code,200,result.json)
                        self.assertIsNotNone(old.poll())
                        if method=="restart":
                            self.assertEqual(len(children),2)
                            self.assertTrue(any(w["pid"]==children[1].pid and w["state"]=="Healthy" for w in health.sample(True)["apps"]))
                        print(method,result.json["message"])
                    finally:
                        for child in children:
                            if child.poll() is None: child.terminate()
                            child.wait(timeout=5)
        self.assertEqual(health.sample(True)["successes"],1)
