
import psutil
import time


def get_running_processes(sample_interval=1, limit=25):
    """
    Collect information about running processes,
    including PID, name, CPU, memory and status.
    """

    processes = []

    # Get all currently running processes
    for process in psutil.process_iter(
        ['pid', 'name', 'status', 'memory_info']
    ):
        try:
            # Initialize CPU measurement
            process.cpu_percent(interval=None)
            processes.append(process)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Wait to calculate CPU utilization
    time.sleep(sample_interval)

    process_data = []

    for process in processes:
        try:
            cpu_usage = process.cpu_percent(interval=None)

            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)

            process_data.append({
                "pid": process.pid,
                "name": process.name(),
                "cpu_percent": round(cpu_usage, 2),
                "memory_mb": round(memory_mb, 2),
                "status": process.status()
            })

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess
        ):
            continue

    # Sort processes by CPU usage
    process_data.sort(
        key=lambda process: process["cpu_percent"],
        reverse=True
    )

    return process_data[:limit]


def display_processes(processes):

    print("\n" + "=" * 95)
    print("             OS-LEVEL APPLICATION MONITORING SYSTEM")
    print("=" * 95)

    print(
        f"{'PID':<10}"
        f"{'PROCESS NAME':<30}"
        f"{'CPU (%)':<15}"
        f"{'MEMORY (MB)':<18}"
        f"{'STATUS':<15}"
    )

    print("-" * 95)

    for process in processes:
        print(
            f"{process['pid']:<10}"
            f"{process['name'][:28]:<30}"
            f"{process['cpu_percent']:<15}"
            f"{process['memory_mb']:<18}"
            f"{process['status']:<15}"
        )

    print("=" * 95)
    print(f"Total processes displayed: {len(processes)}")


if __name__ == "__main__":

    print("Collecting running process information...")

    processes = get_running_processes()

    display_processes(processes)
