"""Single outstanding request vector per process; interchangeable resource instances."""
from copy import deepcopy

SCENARIOS = {
    "No deadlock": dict(capacity=[1,1], allocation=[[1,0],[0,0]], requests=[[0,1],[1,0]]),
    "Two-process deadlock": dict(capacity=[1,1], allocation=[[1,0],[0,1]], requests=[[0,1],[1,0]]),
    "Three-process circular wait": dict(capacity=[1,1,1], allocation=[[1,0,0],[0,1,0],[0,0,1]],
                                       requests=[[0,1,0],[0,0,1],[1,0,0]]),
    "Multiple resource instances": dict(capacity=[2,1], allocation=[[1,0],[0,1],[1,0]], requests=[[0,1],[1,0],[0,0]])
}


def simulate(spec, recovery=None):
    if not isinstance(spec, dict):
        raise ValueError("Enter a scenario object.")
    cap, alloc, req = (deepcopy(spec.get(k)) for k in ("capacity","allocation","requests"))
    def vector(v, n):
        return isinstance(v,list) and len(v)==n and all(type(x) is int and 0<=x<=16 for x in v)
    if not isinstance(cap,list) or not 1<=len(cap)<=6 or not vector(cap,len(cap)) or min(cap)<1:
        raise ValueError("Specify 1–6 resource capacities, each between 1 and 16.")
    if not isinstance(alloc,list) or not 1<=len(alloc)<=8 or not isinstance(req,list) or len(req)!=len(alloc):
        raise ValueError("Provide allocation and request rows for 1–8 processes.")
    if not all(vector(row,len(cap)) for row in alloc+req):
        raise ValueError("Each matrix row needs one nonnegative integer per resource.")
    if any(sum(col)>c for col,c in zip(zip(*alloc),cap)) or any(a+r>c for aa,rr in zip(alloc,req) for a,r,c in zip(aa,rr,cap)):
        raise ValueError("Allocations and per-process claims must fit resource capacities.")
    victims = [] if recovery is None else recovery if isinstance(recovery,list) else [recovery]
    if len(victims)>len(alloc) or any(type(p) is not int for p in victims):
        raise ValueError("Select simulated process IDs from the current run.")
    victims = victims.copy()
    count = len(alloc)
    held = [[0]*len(cap) for _ in alloc]
    waiting = deepcopy(held)
    available = cap.copy()
    finished = set()
    frames = []
    def fits(need, supply):
        return all(r<=a for r,a in zip(need,supply))
    def snapshot(text):
        work = available.copy()
        remaining = set(range(count))-finished
        while True:
            i = next((x for x in sorted(remaining) if fits(waiting[x],work)),None)
            if i is None:
                break
            work = [a+b for a,b in zip(work,held[i])]
            remaining.remove(i)
        frames.append(dict(text=text,available=available.copy(),held=deepcopy(held),requests=deepcopy(waiting),
                           finished=sorted(finished),deadlocked=sorted(i for i in remaining if any(held[i]))))
    def release(i):
        for j,units in enumerate(held[i]):
            available[j] += units
        held[i] = [0]*len(cap)
        waiting[i] = [0]*len(cap)
        finished.add(i)
    snapshot("All instances are available.")
    for i,row in enumerate(alloc):
        for j,units in enumerate(row):
            if units:
                waiting[i][j] = units
                snapshot(f"P{i+1} requests {units} of R{j+1}.")
                available[j] -= units
                held[i][j] = units
                waiting[i][j] = 0
                snapshot(f"R{j+1} grants {units} to P{i+1}.")
    for i,row in enumerate(req):
        if any(row):
            waiting[i] = row.copy()
            snapshot(f"P{i+1} requests " + ", ".join(f"{v} × R{j+1}" for j,v in enumerate(row) if v) + ".")
    while len(finished)<count:
        i = next((i for i in range(count) if i not in finished and fits(waiting[i],available)),None)
        if i is None:
            snapshot("No remaining request fits. No holder can finish and release enough instances.")
            if not victims:
                break
            recovery = victims.pop(0)
            if recovery not in frames[-1]["deadlocked"]:
                raise ValueError("Select a deadlocked resource holder.")
            release(recovery)
            snapshot(f"Terminated simulated P{recovery+1}. Its allocations returned to the available pool.")
            continue
        if any(waiting[i]):
            for j,units in enumerate(waiting[i]):
                available[j] -= units
                held[i][j] += units
            waiting[i] = [0]*len(cap)
            snapshot(f"P{i+1} receives its outstanding request and can run.")
        release(i)
        snapshot(f"P{i+1} finishes and releases all its instances.")
    return frames
