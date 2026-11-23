
import psutil


def get_storage_information():

    partitions = psutil.disk_partitions()

    storage_data = []

    for partition in partitions:

        try:
            usage = psutil.disk_usage(partition.mountpoint)

            storage_data.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "filesystem": partition.fstype,
                "total_gb": round(usage.total / (1024 ** 3), 2),
                "used_gb": round(usage.used / (1024 ** 3), 2),
                "free_gb": round(usage.free / (1024 ** 3), 2),
                "usage_percent": usage.percent
            })

        except (PermissionError, OSError):
            continue

    return storage_data


def display_storage_report(storage_data):

    print("\n" + "=" * 95)
    print("                 SYSTEM STORAGE MONITORING REPORT")
    print("=" * 95)

    print(
        f"{'DEVICE':<15}"
        f"{'MOUNT POINT':<15}"
        f"{'TOTAL (GB)':<15}"
        f"{'USED (GB)':<15}"
        f"{'FREE (GB)':<15}"
        f"{'USAGE (%)':<12}"
    )

    print("-" * 95)

    for disk in storage_data:

        print(
            f"{disk['device'][:13]:<15}"
            f"{disk['mountpoint'][:13]:<15}"
            f"{disk['total_gb']:<15}"
            f"{disk['used_gb']:<15}"
            f"{disk['free_gb']:<15}"
            f"{disk['usage_percent']:<12}"
        )

        if disk["usage_percent"] >= 90:
            print("WARNING: CRITICAL STORAGE USAGE!")

        elif disk["usage_percent"] >= 80:
            print("WARNING: HIGH STORAGE USAGE!")

    if not storage_data:
        print("No accessible disk partitions found.")

    print("=" * 95)


if __name__ == "__main__":

    print("Scanning system storage...")

    storage_data = get_storage_information()

    display_storage_report(storage_data)
