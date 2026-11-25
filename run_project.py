import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend-react"

backend = subprocess.Popen(
    [sys.executable, "-m", "backend.app"],
    cwd=ROOT
)

time.sleep(3)

frontend = subprocess.Popen(
    ["npm", "run", "dev", "--", "--host", "127.0.0.1"],
    cwd=FRONTEND,
    shell=True
)

try:
    time.sleep(5)
    webbrowser.open("http://localhost:5173/")

    print("\nOS Guardian is running!")
    print("Open: http://localhost:5173/")
    print("Press Ctrl+C to stop both servers.")

    while True:
        if backend.poll() is not None:
            print("Backend stopped unexpectedly.")
            break
        if frontend.poll() is not None:
            print("Frontend stopped unexpectedly.")
            break
        time.sleep(1)

except KeyboardInterrupt:
    print("\nStopping OS Guardian...")

finally:
    backend.terminate()
    frontend.terminate()
    print("OS Guardian stopped.")
