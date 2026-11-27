import time
import unittest
from unittest.mock import patch

from backend.app import app
from backend.live_deadlock import LiveDemo


class LiveDeadlockTest(unittest.TestCase):
    def setUp(self):
        self.demo = LiveDemo()
        self.addCleanup(self.demo.close)
        patched = patch("backend.app.demo", self.demo)
        patched.start()
        self.addCleanup(patched.stop)
        self.client = app.test_client()
        self.url = "/api/lab/live-deadlock"

    def action(self, action, run_id=None):
        return self.client.post(self.url, json={"action": action, "run_id": run_id})

    def wait_for(self, phase):
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            state = self.client.get(self.url).get_json()
            if state["phase"] == phase:
                return state
            time.sleep(0.05)
        self.fail(f"Expected {phase}, got {state}")

    def test_cycle_and_recovery(self):
        run_id = self.action("start").get_json()["run_id"]
        self.assertEqual(self.action("start").status_code, 409)
        ready = self.wait_for("ready")
        self.assertEqual([w["holds"] for w in ready["workers"]], ["Printer", "Spool file"])
        self.assertEqual(self.action("advance", "old-run").status_code, 409)
        self.assertEqual(self.action("advance", run_id).status_code, 200)
        cycle = self.wait_for("circular_wait")
        self.assertTrue(cycle["cycle"])
        pids = [w["pid"] for w in cycle["workers"]]
        self.assertNotEqual(*pids)
        print("Live cycle: print PID %d waits for archive PID %d and vice versa." % tuple(pids))
        self.assertEqual([w["waits_for"] for w in cycle["workers"]], ["Spool file", "Printer"])
        self.assertEqual(self.action("recover", run_id).status_code, 200)
        done = self.wait_for("resolved")
        self.assertEqual([w["status"] for w in done["workers"]], ["Finished", "Rolled back"])
        self.assertFalse(any(w["alive"] for w in done["workers"]))

    def test_timeout_without_browser(self):
        with patch("backend.live_deadlock.LIMIT_SECONDS", 2):
            self.action("start")
        time.sleep(2.5)
        expired = self.wait_for("expired")
        self.assertFalse(any(w["alive"] for w in expired["workers"]))
        self.assertEqual(self.action("start").status_code, 200)
