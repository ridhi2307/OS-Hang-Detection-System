
// ========================================
// OS MONITORING DASHBOARD
// ========================================
// Chart instances
let cpuChart = null;
let ramChart = null;
let diskChart = null;

// Safely display text inside HTML
function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[character]);
}


// ========================================
// MAIN DASHBOARD FUNCTION
// ========================================

async function loadDashboard(recheck=false) {

    const refreshButton = document.getElementById("refreshBtn");

    if (refreshButton.disabled) return;
    refreshButton.textContent = "Refreshing…";
    refreshButton.disabled = true;

    try {

        const response = await fetch(recheck===true ? "/api/dashboard?recheck=1" : "/api/dashboard");

        if (!response.ok) {
            throw new Error("Unable to fetch dashboard information.");
        }

        const data = await response.json();

        // Update all dashboard sections
        renderHealth(data);
        updateMemory(data.memory);
        updateStorage(data.storage);
        updateCharts(data);
        loadRecoveryHistory();

        document.getElementById("sampleStatus").textContent = "Last sampled " + new Date(data.health.checked*1000).toLocaleTimeString() + " · Dashboard refresh every 10s";

    } catch (error) {

        console.error("Dashboard error:", error);

        document.getElementById("sampleStatus").textContent = "Sample unavailable · Refresh to retry.";
    } finally {

        refreshButton.textContent = "Refresh";
        refreshButton.disabled = false;
    }
}


// ========================================
// SYSTEM OVERVIEW
// ========================================

function updateMemory(memoryData) {

    const memory = memoryData.system;

    document.getElementById("totalRam").textContent =
        memory.total_gb + " GB";

    document.getElementById("usedRam").textContent =
        memory.used_gb + " GB";

    document.getElementById("availableRam").textContent =
        memory.available_gb + " GB";

    document.getElementById("memoryPercent").textContent =
        memory.usage_percent + "%";


    const table = document.getElementById("memoryTable");

    const processes = memoryData.top_processes;

    if (!processes || processes.length === 0) {

        table.innerHTML =
            '<tr><td colspan="3">No memory information available.</td></tr>';

        return;
    }

    table.innerHTML = processes.map(process => {

        return `
            <tr>
                <td>${process.pid}</td>
                <td>${escapeHTML(process.name || "Unknown")}</td>
                <td>${process.memory_mb} MB</td>
            </tr>
        `;

    }).join("");
}


// ========================================
// STORAGE MONITORING
// ========================================

function updateStorage(disks) {

    const container =
        document.getElementById("storageContainer");

    if (!disks || disks.length === 0) {

        container.innerHTML =
            "<p>No accessible storage devices found.</p>";

        return;
    }

    container.innerHTML = disks.map(disk => {

        const usage = Math.min(
            100,
            Math.max(0, Number(disk.usage_percent) || 0)
        );

        let statusClass = "status-normal";

        if (usage >= 90) {
            statusClass = "status-danger";
        } else if (usage >= 80) {
            statusClass = "status-warning";
        }

        return `
            <div class="storage-card">

                <h3>${escapeHTML(disk.device)}</h3>

                <p>Total Space: ${disk.total_gb} GB</p>

                <p>Used Space: ${disk.used_gb} GB</p>

                <p>Free Space: ${disk.free_gb} GB</p>

                <p class="${statusClass}">
                    Usage: ${usage}%
                </p>

                <div class="progress-track">

                    <div
                        class="progress-bar"
                        style="width: ${usage}%"
                    ></div>

                </div>

            </div>
        `;

    }).join("");
}


// ========================================
// DEADLOCK DETECTION
// ========================================

function chartColor(token) {
    return getComputedStyle(document.documentElement).getPropertyValue(token).trim();
}

function syncChartTheme() {
    if (typeof Chart === "undefined") return;
    Chart.defaults.color = chartColor("--chart-label");
    Chart.defaults.borderColor = chartColor("--chart-grid");
    for (const [chart, fill] of [
        [cpuChart, chartColor("--chart-cpu")],
        [ramChart, [chartColor("--chart-cpu"), chartColor("--chart-free")]],
        [diskChart, chartColor("--chart-disk")],
        [Chart.getChart("healthChart"), null]
    ]) {
        if (chart) {
            if (fill) chart.data.datasets[0].backgroundColor = fill;
            chart.options.plugins.legend.labels.color = Chart.defaults.color;
            for (const axis of Object.values(chart.options.scales)) {
                axis.ticks.color = Chart.defaults.color;
                axis.title.color = Chart.defaults.color;
                axis.grid.color = Chart.defaults.borderColor;
                axis.border.color = Chart.defaults.borderColor;
            }
            chart.update("none");
        }
    }
}
syncChartTheme();
document.addEventListener("guardian-theme", syncChartTheme);

function updateCharts(data) {

    // Check whether Chart.js has loaded
    if (typeof Chart === "undefined") {
        console.error("Chart.js library is not loaded.");
        return;
    }

    // ------------------------------------
    // 1. CPU USAGE CHART
    // ------------------------------------

    const processes = data.processes.data
    .filter(process => process.name !== "System Idle Process")
    .slice(0, 8);

    const cpuLabels = processes.map(
        process => process.name || "Unknown"
    );

    const cpuValues = processes.map(
        process => Number(process.cpu_percent) || 0
    );

    if (cpuChart) {
        cpuChart.data.labels = cpuLabels;
        cpuChart.data.datasets[0].data = cpuValues;
        cpuChart.update();
    } else {

        cpuChart = new Chart(
            document.getElementById("cpuChart"),
            {
                type: "bar",

                data: {
                    labels: cpuLabels,

                    datasets: [{
                        label: "CPU Usage (%)",
                        data: cpuValues,
                        backgroundColor: chartColor("--chart-cpu"),
                        borderRadius: 6
                    }]
                },

                options: {
                    responsive: true,
                    maintainAspectRatio: false,

                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: "CPU Usage (%)"
                            }
                        }
                    },

                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            }
        );
    }


    // ------------------------------------
    // 2. RAM UTILIZATION CHART
    // ------------------------------------

    const memory = data.memory.system;

    const ramValues = [
        Number(memory.used_gb),
        Number(memory.available_gb)
    ];

    if (ramChart) {
        ramChart.data.datasets[0].data = ramValues;
        ramChart.update();
    } else {

        ramChart = new Chart(
            document.getElementById("ramChart"),
            {
                type: "doughnut",

                data: {
                    labels: ["Used RAM", "Available RAM"],

                    datasets: [{
                        data: ramValues,
                        backgroundColor: [
                            chartColor("--chart-cpu"),
                            chartColor("--chart-free")
                        ],
                        borderWidth: 0
                    }]
                },

                options: {
                    responsive: true,
                    maintainAspectRatio: false,

                    plugins: {
                        legend: {
                            position: "bottom"
                        }
                    }
                }
            }
        );
    }


    // ------------------------------------
    // 3. DISK USAGE CHART
    // ------------------------------------

    const disks = data.storage;

    const diskLabels = disks.map(
        disk => disk.device
    );

    const diskValues = disks.map(
        disk => Number(disk.usage_percent) || 0
    );

    if (diskChart) {
        diskChart.data.labels = diskLabels;
        diskChart.data.datasets[0].data = diskValues;
        diskChart.update();
    } else {

        diskChart = new Chart(
            document.getElementById("diskChart"),
            {
                type: "bar",

                data: {
                    labels: diskLabels,

                    datasets: [{
                        label: "Disk Usage (%)",
                        data: diskValues,
                        backgroundColor: chartColor("--chart-disk"),
                        borderRadius: 6
                    }]
                },

                options: {
                    responsive: true,
                    maintainAspectRatio: false,

                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,

                            title: {
                                display: true,
                                text: "Storage Used (%)"
                            }
                        }
                    },

                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            }
        );
    }
}

// ========================================
// APPLICATION RECOVERY TABLE
// ========================================

async function loadRecoveryHistory() {

    const tableBody = document.getElementById("recoveryHistoryBody");

    try {

        const response = await fetch("/api/recovery/history");

        if (!response.ok) {
            throw new Error("Unable to load recovery history.");
        }

        const data = await response.json();

        if (data.records.length === 0) {

            tableBody.innerHTML = `
                <tr>
                    <td colspan="4">No recovery records yet.</td>
                </tr>
            `;

            return;
        }

        tableBody.innerHTML = data.records.map(record => `
            <tr>
                <td>${escapeHTML(record.pid)}</td>
                <td>${escapeHTML(record.action)}</td>
                <td>${escapeHTML(record.result)}</td>
                <td>${escapeHTML(record.timestamp)}</td>
            </tr>
        `).join("");

    } catch (error) {

        console.error("Recovery history error:", error);

    }
}

// ========================================
// REQUEST APPLICATION RECOVERY
// ========================================

document.addEventListener("DOMContentLoaded", function () {

    loadDashboard();

    // Refresh the dashboard every ten seconds
    setInterval(loadDashboard, 10000);

});
