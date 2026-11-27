# OS Hang Detection System

A local Windows application that detects stalled application windows, records hang incidents, and verifies recovery. The dashboard shows which applications need attention, how long they have been unresponsive, and what happened after a recovery attempt. Five interactive labs demonstrate the operating-system algorithms behind resource management.

## Run the dashboard

Use Windows, Python 3.10 or newer, and Git Bash. Run the monitor in the same desktop session as the applications you want to observe.

```bash
git clone https://github.com/ridhi2307/OS-Hang-Detection-System.git
cd OS-Hang-Detection-System
python -m venv venv
source venv/Scripts/activate
python -m pip install -r requirements.txt
bash run.sh
```

Open [the local dashboard](http://127.0.0.1:5000). The Bash launcher collects a host summary and starts Flask. From PowerShell, an existing environment can launch the same dashboard with `./venv/Scripts/python.exe run_project.py`. Press **Ctrl+C** in the server terminal to stop it.

## Demonstrate a real hang and recovery

1. Leave the dashboard running. In a second Git Bash terminal in the project folder, run `./venv/Scripts/python.exe tests/test_hang.py`.
2. In the test window, click **Simulate application hang**. Its UI thread pauses for 45 seconds. Use **Window health** to inspect its title, PID and Windows responsiveness result.
3. Open **Application health**. Watch the process move from **Checking** to **Unresponsive** after repeated stalled observations meet the confirmation interval. The default is six seconds. The background monitor samples about every four seconds and the dashboard refreshes every ten seconds. **Refresh** requests a new dashboard snapshot.
4. In **Recovery**, choose **Restart test application** and confirm. The system verifies that the original PID exited and that the replacement process has a responsive window. Look for **Restart verified** and the replacement PID in the incident log.
5. To demonstrate spontaneous recovery instead, let the full 45 seconds elapse. A successful probe of the original window records **Responsive again**. Choosing **End test application** records a verified exit separately.

Restart and end actions apply to the bundled test application and require explicit confirmation. For other applications, the monitor provides evidence and a recheck. Windows hang detection and a bounded window-message probe supply the responsiveness signal. An inconclusive probe appears as **Unknown**. CPU usage and memory pressure provide context when investigating a possible cause.

## Monitoring workspace

| Page | What it shows |
| --- | --- |
| Overview | Monitored and healthy apps, confirmed hangs, recoveries in progress, verified restarts, health trends, recent activity, CPU, RAM and disk usage. |
| Application health | One entry per visible application process, filters by state, detection duration and history, and an adjustable confirmation interval. |
| Window health | Individual visible, titled windows with their owning PIDs, probe results and last check times. One process can own several windows. |
| Processes | Search by name or PID, sort by CPU or memory, and open process details to inspect start time and associated windows. |
| Recovery | Active incidents, supported actions, timestamps, attempt results and failure reasons. |
| Memory and Storage | Physical memory, resident memory by process, drive capacity, usage and free space. |

Use the header to export monitoring reports as CSV or PDF and select a dark, light or system theme. SQLite persists incident and recovery history in `database/os_monitor.db`.

## Simulation labs

Each lab accepts an example or custom workload. Playback controls let you pause, change speed, or revisit the decision that caused a particular result.

| Lab | Algorithms and experiments |
| --- | --- |
| CPU scheduling | Compare FCFS, non-preemptive SJF, SRTF, non-preemptive priority and round robin. The Gantt timeline and per-process results show completion, waiting, turnaround and response times. |
| Disk scheduling | Compare FCFS, SSTF, SCAN, C-SCAN, LOOK and C-LOOK. Follow the head across cylinders 0–199 and compare total travel. |
| Memory allocation | Compare first fit, best fit and worst fit. On the fragmentation preset, inspect why a request can fail even when enough free units remain across separate blocks. |
| Page replacement | Step through FIFO, LRU and Optimal. On the default 13-reference workload with three frames, they produce 10, 9 and 7 page faults respectively. |
| Deadlock detection | Follow requests and allocations on a directed graph. Try a safe scenario, a two- or three-process cycle, multiple resource instances, or a custom allocation matrix. Release a simulated victim and inspect which processes can finish. |

**Live deadlock experiment.** On the Deadlock detection page, choose **Start workers** to launch two local Python processes. Match their PIDs in Task Manager, then choose **Request second locks**. Each worker holds the private lock the other needs. **Roll back archive job** releases a lock so the print worker can finish. Both workers have a 60-second deadline.

To reproduce lab results in Git Bash, use the same Python engines from the command line:

```bash
bash run.sh cpu --arrivals "0 1 2 3" --bursts "8 4 2 1" --priorities "2 1 3 1" --quantum 2
bash run.sh disk --head 53 --requests "98 183 37 122 14 124 65 67"
bash run.sh allocation --holes "100 500 200 300 600" --requests "212 417 112 426"
bash run.sh lab --frames 3 --pages "7 0 1 2 0 3 0 4 2 3 0 3 2"
```

## Implementation and tests

The [Flask backend](backend/app.py) connects the [Windows window probes](backend/hang_detector.py), [incident tracker](backend/health.py), and [recovery verification](backend/recovery_manager.py). The current dashboard uses [Flask templates](frontend/templates/) and [local JavaScript and CSS](frontend/static/). The earlier React client is available in [frontend-react](frontend-react/).

Run the standard tests from the project folder with the virtual environment active:

```bash
python -m unittest discover -s tests
```

To also exercise real hang detection, restart and termination on disposable test windows, run the desktop suite in an interactive Windows session:

```bash
OSHD_DESKTOP_TEST=1 python -m unittest discover -s tests
```

## Project credit

Original OS Guardian project by Ridhima Singh & Priya Bora.
