
# OS Guardian
### OS-Level Application Hang Detection and Recovery System

OS Guardian is a system monitoring application designed to monitor running processes, detect unresponsive applications, analyze memory and storage utilization, identify simulated deadlocks, and perform controlled application recovery.

## Features

- **Process Monitoring:** Monitor running processes, CPU usage, and memory consumption.
- **Hang Detection:** Detect unresponsive Windows applications.
- **Memory Analysis:** Monitor system RAM utilization.
- **Storage Monitoring:** Track disk usage across partitions.
- **Deadlock Detection:** Identify circular waits using a simulated wait-for graph.
- **Application Recovery:** Safely terminate a controlled, unresponsive test application.
- **Recovery History:** Store and display recovery attempts using SQLite.

## Technologies Used

### Backend
- Python
- Flask
- Psutil
- PyWin32
- SQLite

### Frontend
- React.js
- Tailwind CSS
- Recharts
- Lucide React

### Development Tools
- VS Code
- Git and GitHub

## Project Structure

```text
OS-Hang-Detection-System/
├── backend/
├── frontend/
├── frontend-react/
├── tests/
├── config/
├── database/
├── docs/
├── output/
├── screenshots/
├── requirements.txt
└── README.md
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/ridhi2307/OS-Hang-Detection-System.git
cd OS-Hang-Detection-System
```

### 2. Create a Python virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Install frontend dependencies

```bash
cd frontend-react
npm install
```

### 5. Start the Flask backend

Open a terminal in the project root:

```bash
python -m backend.app
```

### 6. Start the React frontend

Open another terminal:

```bash
cd frontend-react
npm run dev
```

Open the local URL displayed by Vite, usually:

http://localhost:5173/

## Safety and Limitations

- Hang detection currently monitors visible Windows application windows.
- Deadlock detection uses a simulated wait-for graph.
- Recovery is restricted to the controlled test application.
- Recovery uses graceful termination and does not force-kill arbitrary processes.

## Project Status

Core monitoring, hang detection, simulated deadlock detection, controlled recovery, and recovery history have been implemented and tested.

Further improvements and testing are ongoing.

## Author

Ridhima Singh

GitHub: https://github.com/ridhi2307
