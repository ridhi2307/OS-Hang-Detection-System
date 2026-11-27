# OS Guardian

OS Guardian combines a local Windows resource monitor with two operating-system simulations. Bash collects a host summary and starts the Python application. Flask serves the interface, psutil samples processes and resources, and SQLite records observations and recovery attempts.

## Run on Windows

Install Python 3.10 or later and Git Bash. Extract the project, open Git Bash in the folder containing `run.sh`, then run:

```bash
python -m venv venv
source venv/Scripts/activate
python -m pip install -r requirements.txt
bash run.sh
```

Open **http://127.0.0.1:5000**. Use the **Theme** menu at the top to choose System, Dark, or Light. The browser remembers your selection. Press Ctrl+C in the terminal to stop the server. The dashboard includes its chart library locally. From an activated PowerShell environment, `python run_project.py` starts the same dashboard directly.

## Classroom demonstration

1. Open **Overview**. The cards show a sample of up to 25 processes, the number of unresponsive windows, RAM utilization and the result of a simulated wait-for graph. Live charts update every 15 seconds. Use the sidebar to inspect individual processes, memory consumers and disk partitions.
2. Open **Page replacement** and run the default sequence with three frames. FIFO produces 10 faults and 3 hits. LRU produces 9 faults and 4 hits. Compare the frame contents and eviction decisions, then change the number of frames and run again.
3. Open **Deadlock detection** to follow the circular wait among three simulated processes.
4. To demonstrate recovery, start `python tests/test_hang.py` in another activated terminal. Click **Simulate application hang** in that test window. Refresh **Window health**, then open **Recovery** to confirm termination of the test application. The test window resumes after 45 seconds if left alone. Recovery attempts appear in the history.
5. Export a CSV or PDF monitoring report from the dashboard. The paging experiment is displayed separately in the lab.

The same Python paging engine can run directly from Bash:

```bash
bash run.sh lab --frames 2 --pages "0 1 0 2"
python -m unittest discover -s tests -p test_paging.py
```

Live window monitoring uses the Windows User32 API. The paging simulation uses only the Python standard library. The earlier React interface remains available in `frontend-react` as an alternative client for the Flask API.

## Project credit

Original OS Guardian project by **Ridhima Singh** · https://github.com/ridhi2307
