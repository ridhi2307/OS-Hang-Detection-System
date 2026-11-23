
import psutil


def get_memory_information():

    memory = psutil.virtual_memory()

    memory_data = {
        "total_gb": round(memory.total / (1024 ** 3), 2),
        "available_gb": round(memory.available / (1024 ** 3), 2),
        "used_gb": round(memory.used / (1024 ** 3), 2),
        "usage_percent": memory.percent
    }

    return memory_data


def get_top_memory_processes(limit=10):

    processes = []

    for process in psutil.process_iter(
        ['pid', 'name', 'memory_info']
    ):
        try:
            memory_info = process.info['memory_info']

            if memory_info is None:
                continue

            memory_mb = memory_info.rss / (1024 * 1024)

            processes.append({
                "pid": process.info['pid'],
                "name": process.info['name'],
                "memory_mb": round(memory_mb, 2)
            })

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess
        ):
            continue

    processes.sort(
        key=lambda process: process["memory_mb"],
        reverse=True
    )

    return processes[:limit]


def display_memory_report(memory_data, processes):

    print("\n" + "=" * 65)
    print("              SYSTEM MEMORY ANALYSIS REPORT")
    print("=" * 65)

    print(f"Total RAM       : {memory_data['total_gb']} GB")
    print(f"Used RAM        : {memory_data['used_gb']} GB")
    print(f"Available RAM   : {memory_data['available_gb']} GB")
    print(f"Memory Usage    : {memory_data['usage_percent']}%")

    print("-" * 65)

    print(f"{'PID':<10}{'PROCESS NAME':<30}{'MEMORY (MB)':<15}")
    print("-" * 65)

    for process in processes:

        print(
            f"{process['pid']:<10}"
            f"{process['name'][:28]:<30}"
            f"{process['memory_mb']:<15}"
        )

    print("-" * 65)

    usage = memory_data["usage_percent"]

    if usage >= 90:
        print("WARNING: CRITICAL MEMORY USAGE!")

    elif usage >= 75:
        print("WARNING: HIGH MEMORY USAGE!")

    else:
        print("Memory Status: NORMAL")

    print("=" * 65)


if __name__ == "__main__":

    print("Analyzing system memory...")

    memory_data = get_memory_information()

    processes = get_top_memory_processes()

    display_memory_report(memory_data, processes)
