"""Deterministic classroom simulations. All inputs describe virtual resources."""
import argparse
import csv
import re
import sys
from collections import deque


def numbers(text, label, low, high, limit=20):
    tokens = re.split(r"[\s,]+", text.strip()) if isinstance(text, str) and len(text) <= 512 else []
    if not 1 <= len(tokens) <= limit or any(not re.fullmatch(r"[0-9]{1,4}", n) for n in tokens):
        raise ValueError(f"{label} needs 1–{limit} whole numbers between {low} and {high}.")
    values = list(map(int, tokens))
    if any(n < low or n > high for n in values):
        raise ValueError(f"{label} must be between {low} and {high}.")
    return values


def cpu(data):
    arrivals = numbers(data.get("arrivals"), "Arrivals", 0, 99, 12)
    bursts = numbers(data.get("bursts"), "Bursts", 1, 30, 12)
    quantum, = numbers(data.get("quantum"), "Quantum", 1, 30, 1)
    if len(arrivals) != len(bursts):
        raise ValueError("Enter one arrival time for each CPU burst.")
    runs = []
    for policy in ("FCFS", "Shortest job first", "Round robin"):
        pending = deque(sorted(range(len(bursts)), key=lambda i: (arrivals[i], i)))
        ready = []
        remaining = bursts.copy()
        first = {}
        finish = {}
        trace = []
        now = 0
        while pending or ready:
            if not ready and pending and now < arrivals[pending[0]]:
                until = arrivals[pending[0]]
                trace.append([now, until, "Idle", "No process ready"])
                now = until
            while pending and arrivals[pending[0]] <= now:
                ready.append(pending.popleft())
            if policy == "Shortest job first":
                ready.sort(key=lambda i: (bursts[i], arrivals[i], i))
            i = ready.pop(0)
            first.setdefault(i, now)
            duration = min(quantum, remaining[i]) if policy == "Round robin" else remaining[i]
            remaining[i] -= duration
            trace.append([now, now + duration, f"P{i+1}", "Completed" if not remaining[i] else "Quantum expired"])
            now += duration
            while pending and arrivals[pending[0]] <= now:
                ready.append(pending.popleft())
            if remaining[i]:
                ready.append(i)
            else:
                finish[i] = now
        count = len(bursts)
        turnaround = sum(finish[i] - arrivals[i] for i in finish)
        metrics = [round((turnaround-sum(bursts))/count, 2), round(turnaround/count, 2),
                   round(sum(first[i]-arrivals[i] for i in first)/count, 2)]
        runs.append(dict(name=policy, metrics=metrics, steps=trace))
    return dict(metrics=["Mean wait (ticks)", "Mean turnaround (ticks)", "Mean response (ticks)"],
                columns=["Start", "End", "Process", "Decision"], runs=runs)


def disk(data):
    requests = numbers(data.get("requests"), "Cylinders", 0, 199)
    head, = numbers(data.get("head"), "Starting cylinder", 0, 199, 1)
    runs = []
    for policy in ("FCFS", "Shortest seek first", "LOOK (up first)"):
        queue = requests.copy()
        if policy.startswith("LOOK"):
            queue = sorted(x for x in queue if x >= head) + sorted((x for x in queue if x < head), reverse=True)
        pos = head
        total = 0
        steps = []
        while queue:
            index = min(range(len(queue)), key=lambda i: abs(queue[i]-pos)) if policy == "Shortest seek first" else 0
            target = queue.pop(index)
            distance = abs(target-pos)
            total += distance
            steps.append([pos, target, distance, total])
            pos = target
        runs.append(dict(name=policy, metrics=[total, round(total/len(requests), 2)], steps=steps))
    return dict(metrics=["Total travel (cylinders)", "Mean travel / request"],
                columns=["From", "To", "Distance", "Cumulative travel"], runs=runs)


def allocation(data):
    holes = numbers(data.get("holes"), "Free blocks", 1, 999)
    requests = numbers(data.get("requests"), "Allocation requests", 1, 999)
    runs = []
    for policy in ("First fit", "Best fit", "Worst fit"):
        free = holes.copy()
        placed = 0
        steps = []
        for size in requests:
            fits = [i for i, space in enumerate(free) if space >= size]
            if fits:
                i = fits[0]
                if policy == "Best fit":
                    i = min(fits, key=free.__getitem__)
                elif policy == "Worst fit":
                    i = max(fits, key=free.__getitem__)
                free[i] -= size
                placed += 1
                outcome = f"Placed in B{i+1}"
            else:
                outcome = "Fragmented free space" if sum(free) >= size else "Insufficient free space"
            steps.append([size, outcome, " · ".join(map(str, free)), sum(free)])
        runs.append(dict(name=policy, metrics=[placed, sum(free), max(free)], steps=steps))
    return dict(metrics=["Requests placed", "Free units", "Largest hole"], columns=["Request", "Decision", "Free units by block", "Total free"], runs=runs)


LABS = {
    "cpu": dict(title="CPU scheduling", description="Compare how a single CPU handles arriving jobs. Waiting measures time in the ready queue. Response measures time until the first dispatch.",
                fields=[("arrivals", "Arrival times"), ("bursts", "CPU bursts"), ("quantum", "Round-robin quantum")],
                presets={"Long job first": ["0 1 2 3", "8 4 2 1", "2"], "Idle intervals": ["2 9 10", "3 2 1", "1"]}, simulate=cpu),
    "disk": dict(title="Disk scheduling", description="Service a queue on a simulated disk with cylinders 0–199. LOOK starts toward higher cylinders and reverses at the last pending request in that direction.",
                 fields=[("requests", "Cylinder queue"), ("head", "Starting cylinder")],
                 presets={"Mixed requests": ["98 183 37 122 14 124 65 67", "53"], "Repeated cylinders": ["40 40 10 90 50", "40"]}, simulate=disk),
    "allocation": dict(title="Memory allocation", description="Place requests into separate contiguous free blocks. Each allocation splits one block. Compare what happens when enough memory remains in total but no single block fits.",
                       fields=[("holes", "Free block sizes"), ("requests", "Allocation requests")],
                       presets={"Fragmentation": ["100 500 200 300 600", "212 417 112 426"], "Exact fits": ["16 32 64", "32 16 64"]}, simulate=allocation)
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="lab", required=True)
    for name, spec in LABS.items():
        cmd = commands.add_parser(name, help=spec["title"])
        for (field, label), default in zip(spec["fields"], next(iter(spec["presets"].values()))):
            cmd.add_argument("--" + field, default=default, help=label)
    args = vars(parser.parse_args())
    try:
        result = LABS[args.pop("lab")]["simulate"](args)
    except ValueError as error:
        parser.error(str(error))
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["Policy", *result["metrics"]])
    writer.writerows([run["name"], *run["metrics"]] for run in result["runs"])


if __name__ == "__main__":
    main()
