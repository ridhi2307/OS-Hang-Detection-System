import csv
import os
from datetime import datetime

from backend.analytics import (
    get_process_statistics,
    get_hang_statistics,
    get_memory_statistics,
    get_deadlock_statistics,
    get_recovery_statistics
)

from backend.process_monitor import get_running_processes
from backend.hang_detector import get_application_windows

from backend.memory_analyzer import (
    get_memory_information,
    get_top_memory_processes
)

from backend.storage_monitor import get_storage_information
from backend.database import get_connection




BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REPORT_DIR = os.path.join(
    BASE_DIR,
    "output",
    "reports"
)


# --------------------------------------------------
# CSV REPORT GENERATION
# --------------------------------------------------

def recent_health_events():
    from contextlib import closing
    with closing(get_connection()) as db:
        return db.execute("""
            SELECT datetime(at,'unixepoch','localtime'),name,pid,event,detail
            FROM health_events ORDER BY id DESC LIMIT 50
        """).fetchall()


def generate_csv_report():

    os.makedirs(REPORT_DIR, exist_ok=True)

    process_stats = get_process_statistics()
    hang_count = get_hang_statistics()
    memory_stats = get_memory_statistics()
    deadlock_count = get_deadlock_statistics()
    recovery_stats = get_recovery_statistics()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    filename = f"system_report_{timestamp}.csv"
    file_path = os.path.join(REPORT_DIR, filename)

    report_data = [
        ["SYSTEM ANALYTICS AND HEALTH REPORT", ""],
        ["Generated At", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        [],
        ["PROCESS STATISTICS", ""],
        ["Total Process Records", process_stats["total_records"]],
        ["Average CPU Usage (%)", process_stats["average_cpu"]],
        ["Average Process Memory (MB)", process_stats["average_memory"]],
        [],
        ["APPLICATION HANG STATISTICS", ""],
        ["Detected Application Hangs", hang_count],
        [],
        ["MEMORY STATISTICS", ""],
        ["Average RAM Usage (%)", memory_stats["average_usage"]],
        ["Maximum RAM Usage (%)", memory_stats["maximum_usage"]],
        [],
        ["DEADLOCK STATISTICS", ""],
        ["Simulated deadlock observations", deadlock_count],
        [],
        ["RECOVERY STATISTICS", ""],
        ["Total Recovery Attempts", recovery_stats["total_attempts"]],
        ["Successful Recoveries", recovery_stats["successful_recoveries"]]
    ]

    report_data.extend([[], ["RECENT INCIDENT ACTIVITY"], ["Local time","Application","PID","Event","Detail"]])
    report_data.extend(recent_health_events())
    with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerows(report_data)

    return file_path


# --------------------------------------------------
# COLLECT DETAILED SYSTEM INFORMATION
# --------------------------------------------------

def get_detailed_report_data():

    processes = get_running_processes()
    windows = get_application_windows()
    memory_info = get_memory_information()
    top_memory = get_top_memory_processes()
    storage_info = get_storage_information()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT pid, action, result, timestamp
        FROM recovery_records
        ORDER BY id DESC
        LIMIT 10
    """)

    recovery_history = cursor.fetchall()

    connection.close()

    return {
        "processes": processes,
        "windows": windows,
        "memory": memory_info,
        "top_memory": top_memory,
        "storage": storage_info,
        "recovery_history": recovery_history
    }


# --------------------------------------------------
# GENERATE SYSTEM RECOMMENDATIONS
# --------------------------------------------------

def generate_recommendations(
    memory_stats,
    hang_count,
    deadlock_count,
    storage_info
):

    recommendations = []

    # Memory recommendations
    if memory_stats["average_usage"] >= 85:

        recommendations.append([
            "High RAM Usage",
            "Close unnecessary applications and browser tabs. "
            "Consider a RAM upgrade if the issue continues."
        ])

    # Storage recommendations
    for disk in storage_info:

        usage = disk.get("percent", 0)

        if usage >= 85:

            recommendations.append([
                "Low Storage Space",
                f"Drive {disk.get('device', 'Unknown')} is "
                f"{usage}% full. Remove temporary files "
                "and unnecessary data."
            ])

    # Application hang recommendations
    if hang_count > 0:

        recommendations.append([
            "Unresponsive Applications",
            "Save your work regularly and close unnecessary "
            "applications. Use controlled recovery for the "
            "OS Hang Detection System test application."
        ])

    # Deadlock recommendations
    if deadlock_count > 0:

        recommendations.append([
            "Deadlock Detected",
            "Review the simulated wait-for graph and identify "
            "circular resource dependencies."
        ])

    # Healthy system message
    if not recommendations:

        recommendations.append([
            "System Health",
            "No major issues were detected. Continue regular "
            "system monitoring."
        ])

    return recommendations


# --------------------------------------------------
# PDF REPORT GENERATION
# --------------------------------------------------

def generate_pdf_report():
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle
    )


    os.makedirs(REPORT_DIR, exist_ok=True)

    # Get analytics
    process_stats = get_process_statistics()
    hang_count = get_hang_statistics()
    memory_stats = get_memory_statistics()
    deadlock_count = get_deadlock_statistics()
    recovery_stats = get_recovery_statistics()

    # Get detailed system information
    details = get_detailed_report_data()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    filename = f"system_report_{timestamp}.pdf"
    file_path = os.path.join(REPORT_DIR, filename)

    document = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=35,
        leftMargin=35,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    elements = []

    # --------------------------------------------------
    # TABLE HELPER FUNCTION
    # --------------------------------------------------

    def add_section(title, data, widths=None):

        if title:
            elements.append(
                Paragraph(title, styles["Heading2"])
            )
            elements.append(Spacer(1, 8))

        table = Table(
            data,
            colWidths=widths,
            repeatRows=1
        )

        table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1E293B")
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#F1F5F9")
                    ]
                )
            ])
        )

        elements.append(table)
        elements.append(Spacer(1, 18))

    # --------------------------------------------------
    # REPORT TITLE
    # --------------------------------------------------

    elements.append(
        Paragraph("OS HANG DETECTION SYSTEM", styles["Title"])
    )

    elements.append(
        Paragraph(
            "SYSTEM ANALYTICS AND HEALTH REPORT",
            styles["Heading2"]
        )
    )

    elements.append(Spacer(1, 12))

    elements.append(
        Paragraph(
            f"Generated At: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 20))

    # --------------------------------------------------
    # Recent incident evidence precedes the resource appendix.
    from xml.sax.saxutils import escape
    activity = [["Local time", "Application / PID", "Event", "Evidence"]]
    for at,name,pid,event,detail in recent_health_events():
        cells = [at, f"{name} / {pid}", event, detail]
        activity.append([Paragraph(escape(str(value)), styles["BodyText"]) for value in cells])
    if len(activity) == 1:
        activity.append(["—","—","No incidents","No confirmed events recorded."])
    add_section("Recent application incidents", activity, [95,105,90,180])

    # 1. PROJECT INTRODUCTION
    # --------------------------------------------------

    elements.append(
        Paragraph(
            "ABOUT OS HANG DETECTION SYSTEM",
            styles["Heading1"]
        )
    )

    elements.append(
        Paragraph(
            "OS Hang Detection System is an OS-level application monitoring and "
            "recovery system designed to monitor system resources, "
            "identify unresponsive applications, demonstrate "
            "deadlock detection and maintain recovery records.",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 15))

    # --------------------------------------------------
    # 2. MODULE EXPLANATIONS
    # --------------------------------------------------

    module_data = [
        ["Module", "Explanation"],

        [
            "Process Monitoring",
            "Monitors running processes and their CPU and memory usage."
        ],

        [
            "Hang Detection",
            "Identifies visible application windows that stop responding."
        ],

        [
            "Memory Analysis",
            "Monitors RAM utilization and identifies memory-heavy processes."
        ],

        [
            "Storage Monitoring",
            "Checks disk capacity, used space and available space."
        ],

        [
            "Deadlock Detection",
            "Uses a simulated wait-for graph and cycle detection to "
            "demonstrate circular resource dependencies."
        ],

        [
            "Recovery Management",
            "Safely verifies and gracefully terminates the controlled "
            "test application when it becomes unresponsive."
        ]
    ]

    add_section(
        "OS HANG DETECTION SYSTEM MODULE EXPLANATIONS",
        module_data,
        [125, 320]
    )

    # --------------------------------------------------
    # 3. SYSTEM ANALYTICS SUMMARY
    # --------------------------------------------------

    summary = [
        ["Category", "Metric", "Value"],

        [
            "Process",
            "Total Process Records",
            process_stats["total_records"]
        ],

        [
            "Process",
            "Average CPU Usage",
            f'{process_stats["average_cpu"]}%'
        ],

        [
            "Process",
            "Average Process Memory",
            f'{process_stats["average_memory"]} MB'
        ],

        [
            "Hang Detection",
            "Detected Application Hangs",
            hang_count
        ],

        [
            "Memory",
            "Average RAM Usage",
            f'{memory_stats["average_usage"]}%'
        ],

        [
            "Memory",
            "Maximum RAM Usage",
            f'{memory_stats["maximum_usage"]}%'
        ],

        [
            "Deadlock",
            "Simulated deadlock observations",
            deadlock_count
        ],

        [
            "Recovery",
            "Total Recovery Attempts",
            recovery_stats["total_attempts"]
        ],

        [
            "Recovery",
            "Successful Recoveries",
            recovery_stats["successful_recoveries"]
        ]
    ]

    add_section(
        "1. SYSTEM ANALYTICS SUMMARY",
        summary,
        [115, 230, 130]
    )

    # --------------------------------------------------
    # 4. TOP CPU-CONSUMING PROCESSES
    # --------------------------------------------------

    cpu_data = [
        ["PID", "Process Name", "CPU (%)", "Memory (MB)"]
    ]

    for process in details["processes"][:10]:

        cpu_data.append([
            str(process.get("pid", "N/A")),
            str(process.get("name", "Unknown"))[:25],
            str(process.get("cpu_percent", 0)),
            str(process.get("memory_mb", 0))
        ])

    if len(cpu_data) == 1:

        cpu_data.append([
            "-",
            "No process data available",
            "-",
            "-"
        ])

    add_section(
        "2. TOP CPU-CONSUMING PROCESSES",
        cpu_data,
        [65, 190, 90, 110]
    )

    # --------------------------------------------------
    # 5. APPLICATION HANG DETAILS
    # --------------------------------------------------

    hang_data = [
        ["Application", "PID", "Status"]
    ]

    for window in details["windows"]:

        hang_data.append([
            str(window.get("window_title", "Unknown"))[:35],
            str(window.get("pid", "N/A")),
            str(window.get("status", "Unknown"))
        ])

    if len(hang_data) == 1:

        hang_data.append([
            "No application windows found",
            "-",
            "-"
        ])

    add_section(
        "3. APPLICATION HANG DETAILS",
        hang_data,
        [250, 90, 115]
    )

    # --------------------------------------------------
    # 6. MEMORY ANALYSIS
    # --------------------------------------------------

    memory_data = [
        ["Metric", "Value"]
    ]

    if isinstance(details["memory"], dict):

        for key, value in details["memory"].items():

            memory_data.append([
                str(key),
                str(value)
            ])

    else:

        memory_data.append([
            "System Memory",
            str(details["memory"])
        ])

    add_section(
        "4. SYSTEM MEMORY ANALYSIS",
        memory_data,
        [250, 205]
    )

    # Top memory-consuming processes
    top_memory_data = [
        ["PID", "Process Name", "Memory (MB)"]
    ]

    for process in details["top_memory"][:10]:

        top_memory_data.append([
            str(process.get("pid", "N/A")),
            str(process.get("name", "Unknown"))[:30],
            str(process.get("memory_mb", 0))
        ])

    if len(top_memory_data) == 1:

        top_memory_data.append([
            "-",
            "No memory data available",
            "-"
        ])

    add_section(
        "TOP MEMORY-CONSUMING PROCESSES",
        top_memory_data,
        [75, 260, 120]
    )

    # --------------------------------------------------
    # 7. STORAGE ANALYSIS
    # --------------------------------------------------

    storage_data = [
        ["Drive", "Total", "Used", "Free", "Usage"]
    ]

    for disk in details["storage"]:

        storage_data.append([
            str(disk.get("device", "N/A")),
            str(disk.get("total", "N/A")),
            str(disk.get("used", "N/A")),
            str(disk.get("free", "N/A")),
            str(disk.get("percent", "N/A"))
        ])

    if len(storage_data) == 1:

        storage_data.append([
            "-",
            "-",
            "-",
            "-",
            "No data"
        ])

    add_section(
        "5. STORAGE ANALYSIS",
        storage_data,
        [75, 95, 95, 95, 65]
    )

    # --------------------------------------------------
    # 8. DEADLOCK ANALYSIS
    # --------------------------------------------------

    deadlock_data = [
        ["Metric", "Result"],

        [
            "Simulated deadlock observations",
            str(deadlock_count)
        ],

        [
            "Detection Method",
            "Simulated Wait-For Graph"
        ],

        [
            "Explanation",
            "Cycles in the simulated resource wait-for graph"
        ]
    ]

    add_section(
        "6. DEADLOCK ANALYSIS",
        deadlock_data,
        [170, 285]
    )

    # --------------------------------------------------
    # 9. RECOVERY HISTORY
    # --------------------------------------------------

    recovery_data = [
        ["PID", "Action", "Result", "Timestamp"]
    ]

    for record in details["recovery_history"]:

        recovery_data.append([
            str(record[0]),
            str(record[1]),
            str(record[2])[:35],
            str(record[3])
        ])

    if len(recovery_data) == 1:

        recovery_data.append([
            "-",
            "-",
            "No recovery records",
            "-"
        ])

    add_section(
        "7. RECOVERY HISTORY",
        recovery_data,
        [55, 80, 170, 150]
    )

    # --------------------------------------------------
    # 10. SYSTEM RECOMMENDATIONS
    # --------------------------------------------------

    recommendations = generate_recommendations(
        memory_stats,
        hang_count,
        deadlock_count,
        details["storage"]
    )

    recommendation_data = [
        ["Detected Issue", "Recommended Action"]
    ]

    recommendation_data.extend(recommendations)

    add_section(
        "8. SYSTEM IMPROVEMENT RECOMMENDATIONS",
        recommendation_data,
        [145, 300]
    )

    # --------------------------------------------------
    # 11. CONCLUSION
    # --------------------------------------------------

    elements.append(
        Paragraph(
            "9. CONCLUSION",
            styles["Heading2"]
        )
    )

    elements.append(
        Paragraph(
            "OS Hang Detection System provides process monitoring, application "
            "hang detection, memory and storage analysis, simulated "
            "deadlock detection and controlled recovery. The "
            "recommendations in this report can help users improve "
            "system resource management and reliability.",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 15))

    elements.append(
        Paragraph(
            "Report generated by OS Hang Detection System.",
            styles["Italic"]
        )
    )

    # Generate PDF
    document.build(elements)

    return file_path


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":

    csv_path = generate_csv_report()

    print("\nCSV report generated successfully!")
    print("Saved at:", csv_path)

    pdf_path = generate_pdf_report()

    print("\nPDF report generated successfully!")
    print("Saved at:", pdf_path)
