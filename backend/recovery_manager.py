
import psutil
import os
from datetime import datetime


LOG_DIRECTORY = os.path.join("output", "logs")
LOG_FILE = os.path.join(LOG_DIRECTORY, "recovery.log")


def write_recovery_log(message):

    os.makedirs(LOG_DIRECTORY, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(f"[{timestamp}] {message}\n")


def find_test_applications():

    test_processes = []

    for process in psutil.process_iter(
        ['pid', 'name', 'cmdline']
    ):
        try:
            name = process.info['name'] or ""
            command = process.info['cmdline'] or []

            command_text = " ".join(command).lower()

            # Only identify our controlled test application
            if (
                name.lower() == "python.exe"
                and "test_hang.py" in command_text
            ):
                test_processes.append({
                    "pid": process.info['pid'],
                    "name": name,
                    "process": process
                })

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess
        ):
            continue

    return test_processes


def recover_application(process_info):

    process = process_info["process"]
    pid = process_info["pid"]

    try:
        # Check that the process still exists
        if not process.is_running():
            print("Application is no longer running.")
            write_recovery_log(
                f"PID {pid}: Application was already stopped."
            )
            return

        # Verify the process is still our test application
        command = process.cmdline()
        command_text = " ".join(command).lower()

        if "test_hang.py" not in command_text:
            print("Safety check failed. Recovery cancelled.")
            write_recovery_log(
                f"PID {pid}: Safety check failed."
            )
            return

        print(f"\nSelected application: {process.name()}")
        print(f"Process ID: {pid}")

        confirmation = input(
            "Do you want to terminate this test application? (yes/no): "
        )

        if confirmation.strip().lower() != "yes":

            print("Recovery cancelled by user.")

            write_recovery_log(
                f"PID {pid}: Recovery cancelled by user."
            )
            return

        # Request graceful process termination
        process.terminate()

        try:
            process.wait(timeout=5)

            print("Test application terminated successfully.")

            write_recovery_log(
                f"PID {pid}: Test application terminated successfully."
            )

        except psutil.TimeoutExpired:

            print(
                "Application did not stop within 5 seconds. "
                "No forced termination was attempted."
            )

            write_recovery_log(
                f"PID {pid}: Graceful termination timed out."
            )

    except psutil.NoSuchProcess:

        print("Application has already exited.")

        write_recovery_log(
            f"PID {pid}: Process no longer exists."
        )

    except psutil.AccessDenied:

        print("Permission denied. Application was not terminated.")

        write_recovery_log(
            f"PID {pid}: Permission denied."
        )


def run_recovery_manager():

    print("\n" + "=" * 65)
    print("                 APPLICATION RECOVERY MANAGER")
    print("=" * 65)

    applications = find_test_applications()

    if not applications:

        print("No running test applications found.")

        print(
            "Start tests/test_hang.py before running recovery."
        )

        return

    print("\nControlled test applications found:\n")

    for index, application in enumerate(applications, start=1):

        print(
            f"{index}. {application['name']} "
            f"(PID: {application['pid']})"
        )

    try:
        choice = int(input("\nSelect application number: "))

        if choice < 1 or choice > len(applications):
            print("Invalid selection.")
            return

    except ValueError:

        print("Please enter a valid number.")
        return

    selected_application = applications[choice - 1]

    recover_application(selected_application)

    print("=" * 65)


def recover_test_application(pid, confirmed=False):
    """
    Recover only a confirmed, unresponsive test_hang.py process.
    Designed for use by the Flask dashboard.
    """

    if not confirmed:
        return {
            "success": False,
            "message": "Recovery confirmation is required."
        }

    try:
        # Verify that the selected process still exists
        process = psutil.Process(int(pid))

        if not process.is_running():
            return {
                "success": False,
                "message": "Application is no longer running."
            }

        # Verify that it is our controlled test application
        command = process.cmdline()
        command_text = " ".join(command).lower()

        if "test_hang.py" not in command_text:
            write_recovery_log(
                f"PID {pid}: Safety verification failed."
            )
            return {
                "success": False,
                "message": "Recovery denied: Not a test application."
            }

        # Recheck the current hang status
        from backend.hang_detector import get_application_windows

        windows = get_application_windows()

        is_hung = any(
            window["pid"] == int(pid)
            and window["status"] == "NOT RESPONDING"
            for window in windows
        )

        if not is_hung:
            return {
                "success": False,
                "message": "Application is not currently detected as unresponsive."
            }

        # Request graceful termination
        process.terminate()

        try:
            process.wait(timeout=5)

            message = "Test application recovered successfully."

            write_recovery_log(
                f"PID {pid}: {message}"
            )

            return {
                "success": True,
                "pid": int(pid),
                "message": message
            }

        except psutil.TimeoutExpired:

            message = "Graceful termination timed out. No forced termination attempted."

            write_recovery_log(
                f"PID {pid}: {message}"
            )

            return {
                "success": False,
                "pid": int(pid),
                "message": message
            }

    except psutil.NoSuchProcess:

        return {
            "success": False,
            "message": "Application has already exited."
        }

    except psutil.AccessDenied:

        return {
            "success": False,
            "message": "Permission denied. Application was not terminated."
        }

    except (ValueError, TypeError):

        return {
            "success": False,
            "message": "Invalid process ID."
        }

if __name__ == "__main__":

    run_recovery_manager()
