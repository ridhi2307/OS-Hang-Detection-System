# OS Guardian
### OS-Level Application Hang Detection and Recovery System

OS Guardian is an integrated Python-and-Bash application designed to simulate and analyze major operating-system resource-management functions. It monitors running processes, detects unresponsive applications, analyzes memory and storage utilization, identifies simulated deadlocks, and provides controlled application recovery.

## Features

- **Process Monitoring:** Monitor running processes, CPU usage, memory consumption, and process status.
- **Hang Detection:** Identify unresponsive Windows applications.
- **Memory Analysis:** Monitor system RAM utilization and memory-consuming processes.
- **Storage Monitoring:** Track disk usage across available partitions.
- **Deadlock Detection:** Demonstrate circular waits using a simulated wait-for graph.
- **Application Recovery:** Perform controlled recovery of a test application.
- **Recovery History:** Store and display recovery attempts using SQLite.
- **Analytics and Reports:** Generate analytical results and export reports in CSV and PDF formats.
- **System Information Collection:** Use Bash commands and PowerShell to collect system-level information.

## Technologies Used

### Backend
- Python
- Flask
- Psutil
- PyWin32
- SQLite

### Frontend
- React.js
- Vite
- Recharts
- Lucide React
- CSS

### System-Level Integration
- Bash
- Git Bash
- PowerShell

### Development Tools
- VS Code
- Git and GitHub

## Project Architecture

OS Guardian uses Python for system monitoring, resource analysis, application recovery, and backend API services. Bash handles shell-level system information collection and automates application startup. The React frontend communicates with the Flask backend through REST API endpoints.

## Project Structure

```text
OS-Hang-Detection-System/
├── backend/
│   ├── analytics.py
│   ├── app.py
│   ├── database.py
│   ├── deadlock_detector.py
│   ├── hang_detector.py
│   ├── memory_analyzer.py
│   ├── process_monitor.py
│   ├── recovery_manager.py
│   ├── report_generator.py
│   └── storage_monitor.py
├── frontend/
├── frontend-react/
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── config/
├── database/
├── docs/
├── output/
├── screenshots/
├── tests/
├── requirements.txt
├── run.sh
├── run_project.py
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/ridhi2307/OS-Hang-Detection-System.git
cd OS-Hang-Detection-System
```

### 2. Create and activate a Python virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Python dependencies

```powershell
pip install -r requirements.txt
```

### 4. Install frontend dependencies

```powershell
cd frontend-react
npm install
cd ..
```

### 5. Run OS Guardian

**Recommended: Using Git Bash**

Open Git Bash in the project directory and execute:

```bash
bash run.sh
```

This script collects system information, activates the Python virtual environment, and launches the Flask backend and React frontend.

Alternatively, you can start the backend and frontend separately:

**Backend:**
```powershell
python -m backend.app
```

**Frontend (in another terminal):**
```powershell
cd frontend-react
npm run dev
```

Open the application at:

http://localhost:5173/

The Flask backend runs at:

http://127.0.0.1:5000/

## Safety and Limitations

- Hang detection monitors visible Windows application windows.
- Deadlock detection currently uses a simulated wait-for graph.
- Recovery is restricted to the controlled test application.
- Recovery uses graceful termination rather than forcefully terminating arbitrary processes.
- Bash system-information collection runs through Git Bash on Windows; detailed resource monitoring is handled by Python.

## Project Status

Core monitoring, hang detection, memory and storage analysis, simulated deadlock detection, controlled recovery, recovery history, and report generation have been implemented.

Testing and further improvements are ongoing.

## Author

**Ridhima Singh**

GitHub: https://github.com/ridhi2307