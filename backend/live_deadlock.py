"""A bounded two-process demonstration using private multiprocessing locks."""
import atexit
import multiprocessing as mp
import threading
import time
import uuid

LIMIT_SECONDS = 60
NAMES = ("Print job", "Archive job")
RESOURCES = ("Printer", "Spool file")
STARTING, HOLDING, WAITING, DONE, ROLLED_BACK, EXPIRED = range(6)
LABELS = ("Starting", "Holding first lock", "Waiting for second lock",
          "Finished", "Rolled back", "Time limit reached")


def worker(slot, locks, states, advance, rollback, deadline):
    first, second = locks[slot], locks[1-slot]
    if not first.acquire(timeout=max(0, deadline-time.monotonic())):
        states[slot] = EXPIRED
        return
    try:
        states[slot] = HOLDING
        while time.monotonic() < deadline:
            if slot == 1 and rollback.is_set():
                states[slot] = ROLLED_BACK
                return
            if not advance.wait(0.1):
                continue
            if second.acquire(timeout=0.1):
                try:
                    states[slot] = DONE
                finally:
                    second.release()
                return
            states[slot] = WAITING
        states[slot] = EXPIRED
    finally:
        first.release()


class LiveDemo:
    def __init__(self):
        self.guard = threading.Lock()
        self.ctx = mp.get_context("spawn")
        self.processes = []
        self.run_id = None

    def snapshot(self):
        with self.guard:
            return self._snapshot()

    def _snapshot(self):
        if not self.run_id:
            return dict(phase="idle", workers=[], run_id=None, cycle=False)
        states = list(self.states)
        alive = [p.is_alive() for p in self.processes]
        cycle = all(alive) and states == [WAITING, WAITING]
        if not any(alive):
            for p in self.processes:
                p.join()
            if any(p.exitcode != 0 for p in self.processes):
                phase = "failed"
            elif EXPIRED in states:
                phase = "expired"
            else:
                phase = "resolved"
        elif self.rollback.is_set():
            phase = "recovering"
        elif cycle:
            phase = "circular_wait"
        elif self.advance.is_set():
            phase = "requesting"
        elif states == [HOLDING, HOLDING]:
            phase = "ready"
        else:
            phase = "starting"
        rows = []
        for i, p in enumerate(self.processes):
            state = states[i]
            owns = alive[i] and state in (HOLDING, WAITING)
            rows.append(dict(name=NAMES[i], pid=p.pid, alive=alive[i],
                             status=LABELS[state] if alive[i] or p.exitcode == 0 else "Exited unexpectedly",
                             holds=RESOURCES[i] if owns else None,
                             waits_for=RESOURCES[1-i] if alive[i] and state == WAITING else None))
        return dict(run_id=self.run_id, phase=phase, cycle=cycle, workers=rows,
                    seconds_left=max(0, int(self.deadline-time.monotonic())) if any(alive) else 0)

    def start(self):
        with self.guard:
            if any(p.is_alive() for p in self.processes):
                raise ValueError("A demo is already running.")
            for p in self.processes:
                p.join()
                p.close()
            self.processes = []
            self.run_id = None
            self.states = self.ctx.Array("i", [STARTING, STARTING])
            self.advance = self.ctx.Event()
            self.rollback = self.ctx.Event()
            self.deadline = time.monotonic() + LIMIT_SECONDS
            # Keep parent handles alive until both spawned children have opened them.
            self.locks = [self.ctx.Lock(), self.ctx.Lock()]
            try:
                for i in range(2):
                    p = self.ctx.Process(target=worker, name=NAMES[i], daemon=True,
                                         args=(i, self.locks, self.states, self.advance,
                                               self.rollback, self.deadline))
                    p.start()
                    self.processes.append(p)
            except Exception:
                self._stop()
                raise
            self.run_id = uuid.uuid4().hex
            return self._snapshot()

    def act(self, action, run_id):
        with self.guard:
            state = self._snapshot()
            if not run_id or run_id != self.run_id:
                raise ValueError("This run has ended. Refresh the demo status.")
            if action == "advance" and state["phase"] == "ready":
                self.advance.set()
            elif action == "recover" and state["phase"] == "circular_wait":
                self.rollback.set()
            else:
                raise ValueError("That action is unavailable at this stage.")
            return self._snapshot()

    def _stop(self):
        for p in self.processes:
            if p.is_alive():
                p.terminate()
            p.join()
            p.close()
        self.processes = []
        self.run_id = None

    def close(self):
        with self.guard:
            self._stop()


demo = LiveDemo()
atexit.register(demo.close)
