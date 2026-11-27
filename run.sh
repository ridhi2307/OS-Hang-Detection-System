#!/bin/bash

# ==========================================
# OS GUARDIAN
# Integrated Python and Bash Application
# ==========================================

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$PROJECT_DIR" || exit 1
if [[ -f venv/Scripts/activate ]]; then
    source venv/Scripts/activate || exit 1
fi
case "${1:-}" in
    cpu|disk|allocation) exec python -m backend.resource_labs "$@" ;;
esac
if [[ ${1:-} == "lab" ]]; then
    shift
    exec python -m backend.paging "$@"
fi

echo "=========================================="
echo "          OS GUARDIAN"
echo "     SYSTEM RESOURCE MONITOR"
echo "=========================================="

# 1. System Information
echo ""
echo "[1] SYSTEM INFORMATION"
echo "------------------------------------------"

echo "Operating System : $(uname -s)"
echo "Architecture     : $(uname -m)"
echo "Current User     : $(whoami)"
echo "Date             : $(date)"

# 2. CPU Information
echo ""
echo "[2] CPU INFORMATION"
echo "------------------------------------------"

echo "Processor details:"
if command -v nproc >/dev/null 2>&1; then
    echo "Available CPU cores: $(nproc)"
else
    echo "CPU core information unavailable"
fi

# 3. Memory Information
echo ""
echo "[3] MEMORY INFORMATION"
echo "------------------------------------------"

if command -v free >/dev/null 2>&1; then
    free -h
else
    echo "Memory statistics will be collected by Python."
fi

# 4. Disk Information
echo ""
echo "[4] STORAGE INFORMATION"
echo "------------------------------------------"

df -h

# 5. Running Processes
echo ""
echo "[5] RUNNING PROCESSES"
echo "------------------------------------------"

# Windows process information
if command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -Command \
    "Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 Id,ProcessName,CPU | Format-Table -AutoSize"
else
    ps -eo pid,comm | head -n 11
fi

echo ""
echo "=========================================="
echo "   SYSTEM INFORMATION COLLECTION DONE"
echo "=========================================="
# 6. Launch OS Guardian

echo ""
echo "=========================================="
echo "       STARTING OS GUARDIAN"
echo "=========================================="

exec python run_project.py
