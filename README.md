# OS Hang Detection System

OS Hang Detection System combines live Windows application health and verified recovery with five operating-system simulations. Bash collects a host summary and starts the Python application. Flask serves the interface, psutil samples processes and resources, and SQLite records observations and recovery attempts.

## Run on Windows

Install Python 3.10 or later and Git Bash. Extract the project, open Git Bash in the folder containing `run.sh`, then run:

```bash
python -m venv venv
source venv/Scripts/activate
python -m pip install -r requirements.txt
bash run.sh
```

Open **http://127.0.0.1:5000**. Use the **Theme** menu at the top to choose System, Dark, or Light. The browser remembers your selection. Press Ctrl+C in the terminal to stop the server. The dashboard includes its chart library locally. From an activated PowerShell environment, `python run_project.py` starts the same dashboard directly.

## Application monitoring and recovery

Run the Flask dashboard in the interactive Windows session containing the applications you want to monitor. A background sampler checks visible titled windows about every four seconds. Windows hung-window detection and a bounded WM_NULL message probe provide responsiveness evidence. The default six-second confirmation interval requires repeat observations. Change it in **Application health**. Inconclusive probes appear as Unknown. CPU and RAM are diagnostic context only.

The dashboard groups windows by PID and process creation time. SQLite stores incident openings, verified responses, window disappearance, actions and failure reasons. Start the bundled test window with `python tests/test_hang.py`, press its hang button, then watch **Application health**. In **Recovery**, recheck any incident or explicitly confirm ending/restarting the bundled test app. Restart success requires the original process to exit and a responsive replacement window. Ending a process is logged separately. Other applications support observation and rechecking.

## Interactive resource graph

Select a scenario in **Deadlock detection**. Step through requests and grants, or play the timeline. The detector tests outstanding requests against available instances and releases simulated allocations of processes that can finish. At a deadlocked final state select a victim and inspect the new completion sequence. The custom editor lets you set process and resource counts, capacities, allocations and requests. Its JSON view supports pasting a full scenario. The live two-worker Windows experiment is available below the simulator.

## Scheduling and allocation experiments

Open **CPU scheduling**, **Disk scheduling**, or **Memory allocation** in the sidebar. Pick a preset or edit the workload, then select **Run comparison**. Each result includes a policy comparison, a decision trace with step controls, and a CSV download containing the inputs, metrics and all decisions.

| Experiment | Policies | What to investigate |
| --- | --- | --- |
| CPU scheduling | FCFS, non-preemptive SJF, SRTF, non-preemptive priority, round robin | Compare average wait, turnaround and first response in ticks. Select a dispatch on the timeline. Change the quantum and compare again. |
| Disk scheduling | FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK | Compare total head travel for the same queue on a 200-cylinder disk. All requests are available initially. |
| Memory allocation | First fit, best fit, worst fit | Track the free space in each block. On the fragmentation preset, best fit serves all four requests while first fit and worst fit serve three. |

CPU experiments use one processor, known CPU bursts and zero dispatch overhead. Memory experiments use separate holes with no deallocation. All inputs are simulated. Run the same comparisons from Git Bash to print CSV summaries:

```bash
bash run.sh cpu --arrivals "0 1 2 3" --bursts "8 4 2 1" --quantum 2
bash run.sh disk --head 53 --requests "98 183 37 122 14 124 65 67"
bash run.sh allocation --holes "100 500 200 300 600" --requests "212 417 112 426"
```

## Classroom demonstration

1. Open **Overview** to inspect application health, recent incidents, verified restarts and real resource metrics.
2. Open **Page replacement** and run the default sequence with three frames. FIFO produces 10 faults and 3 hits. LRU produces 9 faults and 4 hits. Compare the frame contents and eviction decisions, then change the number of frames and run again.
3. Open **Deadlock detection → Start workers**. The print and archive jobs run as two local Python processes. Match their PIDs in Task Manager’s Details view. Choose **Request second locks** and inspect the reciprocal waits. Choose **Roll back archive job** to let the print job finish. Each worker enforces a 60-second deadline if you leave the page. The printer and spool file in the example are private synchronization locks. The interactive resource graph on the same page includes a three-process cycle.
4. To demonstrate recovery, start `python tests/test_hang.py` in another activated terminal. Click **Simulate application hang** in that test window. Refresh **Window health**, then open **Recovery** to confirm termination of the test application. The test window resumes after 45 seconds if left alone. Recovery attempts appear in the history.
5. Export a CSV or PDF monitoring report from the dashboard. The paging experiment is displayed separately in the lab.

The same Python paging engine can run directly from Bash:

```bash
bash run.sh lab --frames 2 --pages "0 1 0 2"
python -m unittest discover -s tests
```

Live window monitoring uses the Windows User32 API. The paging simulation uses only the Python standard library. The earlier React interface remains available in `frontend-react` as an alternative client for the Flask API.

## Verification

Run `python -m unittest discover -s tests` from the project folder. The Windows desktop recovery test is opt-in because it opens, freezes, restarts and ends disposable copies of the bundled test window. To include it, run `OSHD_DESKTOP_TEST=1 python -m unittest discover -s tests` in Git Bash on an interactive Windows desktop. Tests use temporary databases.

## Project credit

Original OS Guardian project by **Ridhima Singh** · https://github.com/ridhi2307
