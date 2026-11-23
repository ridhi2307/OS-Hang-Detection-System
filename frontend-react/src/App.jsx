
import { useState, useEffect } from "react";
import {
  LayoutDashboard,
  Cpu,
  Activity,
  MemoryStick,
  HardDrive,
  Network,
  ShieldCheck,
  RefreshCw,
  Bell,
  Search,
  Menu,
} from "lucide-react";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const navigation = [
  { name: "Overview", icon: LayoutDashboard },
  { name: "Process Monitor", icon: Cpu },
  { name: "Hang Detection", icon: Activity },
  { name: "Memory & Storage", icon: MemoryStick },
  { name: "Deadlock Detection", icon: Network },
  { name: "Recovery Center", icon: ShieldCheck },
];

function App() {
  const [activePage, setActivePage] = useState("Overview");
  const [dashboardData, setDashboardData] = useState(null);
  const [apiError, setApiError] = useState("");
  const [history, setHistory] = useState([]);
  const [recoveryHistory, setRecoveryHistory] = useState([]);

  // Fetch dashboard information
  const fetchDashboard = async () => {
    try {
      const response = await fetch("/api/dashboard");

      if (!response.ok) {
        throw new Error("Unable to fetch dashboard data");
      }

      const data = await response.json();

      setDashboardData(data);

      setHistory((previous) => [
        ...previous.slice(-19),
        {
          time: new Date().toLocaleTimeString(),
          cpu: data.processes.data
            .filter((process) => process.name !== "System Idle Process")
            .reduce(
              (total, process) => total + process.cpu_percent,
              0
            ),
          memory: data.memory.system.usage_percent,
        },
      ]);

      setApiError("");
    } catch (error) {
      setApiError(error.message);
    }
  };

  // Fetch recovery history
  const fetchRecoveryHistory = async () => {
    try {
      const response = await fetch("/api/recovery/history");

      if (!response.ok) {
        throw new Error("Unable to fetch recovery history");
      }

      const data = await response.json();
      setRecoveryHistory(data.records ?? []);
    } catch (error) {
      console.error("Recovery history error:", error);
    }
  };

  // Dashboard refresh
  useEffect(() => {
    fetchDashboard();

    const interval = setInterval(fetchDashboard, 30000);

    return () => clearInterval(interval);
  }, []);

  // Recovery history refresh
  useEffect(() => {
    fetchRecoveryHistory();

    const interval = setInterval(fetchRecoveryHistory, 30000);

    return () => clearInterval(interval);
  }, []);

  // Recover the controlled test application
  const requestRecovery = async (pid) => {
    const confirmed = globalThis.window.confirm(
      `Recover the test application with PID ${pid}?`
    );

    if (!confirmed) return;

    try {
      const response = await fetch("/api/recovery", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          pid: pid,
          confirmed: true,
        }),
      });

      const result = await response.json();

      globalThis.window.alert(result.message);

      await fetchDashboard();
      await fetchRecoveryHistory();
    } catch (error) {
      globalThis.window.alert(
        "Recovery request failed: " + error.message
      );
    }
  };

  // Only show the controlled test application
  const testApplications = (
    dashboardData?.hang_detection?.data ?? []
  ).filter(
    (item) =>
      item.process_name.toLowerCase() === "python.exe" &&
      item.window_title.toLowerCase().includes(
        "os hang detection - test application"
      )
  );

  return (
    <div className="min-h-screen bg-[#090d18] text-slate-200">
      <div className="flex min-h-screen">

        {/* Sidebar */}
        <aside className="hidden w-64 border-r border-slate-800 bg-[#0d1321] p-5 md:block">

          <div className="mb-10 flex items-center gap-3">
            <div className="rounded-xl bg-blue-600 p-3">
              <Activity size={23} />
            </div>

            <div>
              <h1 className="text-lg font-bold text-white">
                OS Guardian
              </h1>
              <p className="text-xs text-slate-500">
                System Monitoring
              </p>
            </div>
          </div>

          <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-slate-500">
            Main Menu
          </p>

          <nav className="space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              const active = activePage === item.name;

              return (
                <button
                  key={item.name}
                  onClick={() => setActivePage(item.name)}
                  className={`flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm transition ${
                    active
                      ? "bg-blue-600 text-white shadow-lg shadow-blue-950/40"
                      : "text-slate-400 hover:bg-slate-800 hover:text-white"
                  }`}
                >
                  <Icon size={19} />
                  {item.name}
                </button>
              );
            })}
          </nav>

          <div className="mt-12 rounded-xl border border-emerald-900/50 bg-emerald-950/30 p-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-emerald-400">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              Monitoring Ready
            </div>

            <p className="mt-2 text-xs text-slate-400">
              System monitoring dashboard
            </p>
          </div>
        </aside>

        {/* Main Content */}
        <main className="min-w-0 flex-1">

          {/* Top Bar */}
          <header className="flex items-center justify-between border-b border-slate-800 bg-[#0d1321] px-5 py-4 md:px-8">

            <div className="flex items-center gap-3">
              <Menu className="text-slate-400 md:hidden" />

              <div>
                <h2 className="text-xl font-bold text-white">
                  {activePage}
                </h2>

                <p className="text-xs text-slate-500">
                  OS-Level Application Hang Detection & Recovery
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <button className="rounded-lg p-2 text-slate-400 hover:bg-slate-800">
                <Search size={19} />
              </button>

              <button className="relative rounded-lg p-2 text-slate-400 hover:bg-slate-800">
                <Bell size={19} />
                <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-blue-500" />
              </button>

              <button className="flex items-center gap-2 rounded-lg bg-slate-800 px-3 py-2 text-sm">
                <RefreshCw size={15} />
                <span className="hidden sm:inline">
                  Live Monitor
                </span>
              </button>
            </div>
          </header>

          {/* Dashboard Body */}
          <section className="p-5 md:p-8">

            <div className="mb-7">
              <p className="text-sm text-slate-400">
                Welcome to OS Guardian
              </p>

              <p className="mt-2 text-xs text-emerald-400">
                {apiError
                  ? `Backend connection error: ${apiError}`
                  : dashboardData
                    ? "● Connected to Python Flask Backend"
                    : "● Connecting to backend..."}
              </p>

              <h3 className="mt-1 text-2xl font-bold text-white">
                System Overview
              </h3>

              <p className="mt-2 text-sm text-slate-500">
                Monitor processes, detect application hangs, and manage
                controlled recovery.
              </p>
            </div>

            {/* Statistics Cards */}
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">

              <StatCard
                title="Total Processes"
                value={dashboardData?.processes?.total ?? "--"}
                subtitle="Running system processes"
                icon={Cpu}
              />

              <StatCard
                title="Unresponsive Windows"
                value={
                  dashboardData?.hang_detection?.unresponsive_windows ?? "--"
                }
                subtitle="Detected application hangs"
                icon={Activity}
              />

              <StatCard
                title="Memory Usage"
                value={
                  dashboardData?.memory?.system
                    ? `${dashboardData.memory.system.usage_percent}%`
                    : "--"
                }
                subtitle="System RAM utilization"
                icon={MemoryStick}
              />

              <StatCard
                title="Storage Devices"
                value={dashboardData?.storage?.length ?? "--"}
                subtitle="Detected disk partitions"
                icon={HardDrive}
              />

            </div>

            {/* CPU and Memory Charts */}
            <div className="mt-7 grid grid-cols-1 gap-5 xl:grid-cols-2">

              {/* CPU Chart */}
              <div className="rounded-2xl border border-slate-800 bg-[#111827] p-6">
                <h4 className="font-semibold text-white">
                  CPU Monitoring
                </h4>

                <p className="mt-2 text-sm text-slate-500">
                  Aggregate CPU usage across monitored processes
                </p>

                <div className="mt-6 h-64 w-full">
                  {history.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={history}>
                        <CartesianGrid
                          stroke="#263244"
                          strokeDasharray="3 3"
                        />

                        <XAxis
                          dataKey="time"
                          stroke="#94a3b8"
                          tick={{ fontSize: 11 }}
                        />

                        <YAxis stroke="#94a3b8" />

                        <Tooltip
                          contentStyle={{
                            backgroundColor: "#111827",
                            border: "1px solid #334155",
                            borderRadius: "10px",
                          }}
                        />

                        <Line
                          type="monotone"
                          dataKey="cpu"
                          name="Aggregate CPU Usage"
                          stroke="#3b82f6"
                          strokeWidth={2}
                          dot={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex h-full items-center justify-center text-sm text-slate-500">
                      Waiting for CPU data...
                    </div>
                  )}
                </div>
              </div>

              {/* Memory Chart */}
              <div className="rounded-2xl border border-slate-800 bg-[#111827] p-6">
                <h4 className="font-semibold text-white">
                  Memory Analysis
                </h4>

                <p className="mt-2 text-sm text-slate-500">
                  System RAM utilization over time
                </p>

                <div className="mt-6 h-64 w-full">
                  {history.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={history}>
                        <CartesianGrid
                          stroke="#263244"
                          strokeDasharray="3 3"
                        />

                        <XAxis
                          dataKey="time"
                          stroke="#94a3b8"
                          tick={{ fontSize: 11 }}
                        />

                        <YAxis
                          domain={[0, 100]}
                          stroke="#94a3b8"
                        />

                        <Tooltip
                          contentStyle={{
                            backgroundColor: "#111827",
                            border: "1px solid #334155",
                            borderRadius: "10px",
                          }}
                          formatter={(value) => [
                            `${value}%`,
                            "RAM Usage",
                          ]}
                        />

                        <Line
                          type="monotone"
                          dataKey="memory"
                          name="RAM Usage"
                          stroke="#a78bfa"
                          strokeWidth={2}
                          dot={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex h-full items-center justify-center text-sm text-slate-500">
                      Waiting for memory data...
                    </div>
                  )}
                </div>
              </div>

            </div>

            {/* Process Monitor */}
            <div className="mt-7 rounded-2xl border border-slate-800 bg-[#111827] p-6">

              <div className="mb-5 flex items-center justify-between">
                <div>
                  <h4 className="font-semibold text-white">
                    Top Running Processes
                  </h4>

                  <p className="mt-2 text-sm text-slate-500">
                    Live process information from Windows
                  </p>
                </div>

                <span className="rounded-lg bg-blue-500/10 px-3 py-2 text-xs text-blue-400">
                  Live Data
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="border-b border-slate-700 text-slate-400">
                    <tr>
                      <th className="px-4 py-3">Process Name</th>
                      <th className="px-4 py-3">PID</th>
                      <th className="px-4 py-3">CPU Usage</th>
                      <th className="px-4 py-3">Memory</th>
                      <th className="px-4 py-3">Status</th>
                    </tr>
                  </thead>

                  <tbody>
                    {(dashboardData?.processes?.data ?? [])
                      .slice(0, 10)
                      .map((process) => (
                        <tr
                          key={process.pid}
                          className="border-b border-slate-800 text-slate-300 hover:bg-slate-800/50"
                        >
                          <td className="px-4 py-4 font-medium text-white">
                            {process.name}
                          </td>

                          <td className="px-4 py-4">
                            {process.pid}
                          </td>

                          <td className="px-4 py-4">
                            {process.cpu_percent.toFixed(1)}%
                          </td>

                          <td className="px-4 py-4">
                            {process.memory_mb.toFixed(1)} MB
                          </td>

                          <td className="px-4 py-4">
                            <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs text-emerald-400">
                              {process.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Hang Detection */}
            <div className="mt-7 rounded-2xl border border-slate-800 bg-[#111827] p-6">

              <div className="mb-5">
                <h4 className="font-semibold text-white">
                  Application Hang Detection
                </h4>

                <p className="mt-2 text-sm text-slate-500">
                  Monitoring visible Windows applications for unresponsive windows
                </p>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="border-b border-slate-700 text-slate-400">
                    <tr>
                      <th className="px-4 py-3">Application</th>
                      <th className="px-4 py-3">Window Title</th>
                      <th className="px-4 py-3">PID</th>
                      <th className="px-4 py-3">Status</th>
                    </tr>
                  </thead>

                  <tbody>
                    {(dashboardData?.hang_detection?.data ?? []).map(
                      (window, index) => (
                        <tr
                          key={`${window.pid}-${index}`}
                          className="border-b border-slate-800 text-slate-300"
                        >
                          <td className="px-4 py-4 font-medium text-white">
                            {window.process_name}
                          </td>

                          <td className="max-w-xs truncate px-4 py-4">
                            {window.window_title || "Untitled"}
                          </td>

                          <td className="px-4 py-4">
                            {window.pid}
                          </td>

                          <td className="px-4 py-4">
                            <span
                              className={`rounded-full px-3 py-1 text-xs ${
                                window.status === "NOT RESPONDING"
                                  ? "bg-red-500/10 text-red-400"
                                  : "bg-emerald-500/10 text-emerald-400"
                              }`}
                            >
                              {window.status}
                            </span>
                          </td>
                        </tr>
                      )
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Memory and Storage */}
            <div className="mt-7 grid grid-cols-1 gap-5 xl:grid-cols-2">

              {/* Memory Details */}
              <div className="rounded-2xl border border-slate-800 bg-[#111827] p-6">
                <h4 className="font-semibold text-white">
                  System Memory Details
                </h4>

                <p className="mt-2 text-sm text-slate-500">
                  Real-time RAM utilization
                </p>

                {dashboardData?.memory?.system && (
                  <div className="mt-6 space-y-5">
                    {[
                      [
                        "Total RAM",
                        `${dashboardData.memory.system.total_gb} GB`,
                      ],
                      [
                        "Used RAM",
                        `${dashboardData.memory.system.used_gb} GB`,
                      ],
                      [
                        "Available RAM",
                        `${dashboardData.memory.system.available_gb} GB`,
                      ],
                      [
                        "RAM Usage",
                        `${dashboardData.memory.system.usage_percent}%`,
                      ],
                    ].map(([label, value]) => (
                      <div
                        key={label}
                        className="flex justify-between border-b border-slate-800 pb-3"
                      >
                        <span className="text-sm text-slate-400">
                          {label}
                        </span>

                        <span className="text-sm font-semibold text-white">
                          {value}
                        </span>
                      </div>
                    ))}

                    <div className="h-3 overflow-hidden rounded-full bg-slate-800">
                      <div
                        className="h-full rounded-full bg-blue-500"
                        style={{
                          width: `${dashboardData.memory.system.usage_percent}%`,
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Storage Details */}
              <div className="rounded-2xl border border-slate-800 bg-[#111827] p-6">
                <h4 className="font-semibold text-white">
                  Disk Storage Analysis
                </h4>

                <p className="mt-2 text-sm text-slate-500">
                  Storage utilization by drive
                </p>

                <div className="mt-6 space-y-6">
                  {(dashboardData?.storage ?? []).map((disk) => (
                    <div key={disk.device}>
                      <div className="mb-2 flex justify-between">
                        <span className="font-medium text-white">
                          {disk.device}
                        </span>

                        <span className="text-sm text-slate-400">
                          {disk.usage_percent}%
                        </span>
                      </div>

                      <div className="h-3 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className="h-full rounded-full bg-violet-500"
                          style={{
                            width: `${disk.usage_percent}%`,
                          }}
                        />
                      </div>

                      <p className="mt-2 text-xs text-slate-500">
                        {disk.used_gb} GB used of {disk.total_gb} GB
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Deadlock Detection */}
            <div className="mt-7 rounded-2xl border border-slate-800 bg-[#111827] p-6">
              <h4 className="font-semibold text-white">
                Deadlock Detection
              </h4>

              <p className="mt-2 text-sm text-slate-500">
                Wait-for graph and circular wait analysis
              </p>

              {dashboardData?.deadlock && (
                <>
                  <div
                    className={`mt-5 rounded-xl p-4 ${
                      dashboardData.deadlock.deadlock_detected
                        ? "border border-red-900 bg-red-950/30"
                        : "border border-emerald-900 bg-emerald-950/30"
                    }`}
                  >
                    <p
                      className={`font-semibold ${
                        dashboardData.deadlock.deadlock_detected
                          ? "text-red-400"
                          : "text-emerald-400"
                      }`}
                    >
                      {dashboardData.deadlock.deadlock_detected
                        ? "⚠ Circular Wait Detected"
                        : "✓ No Deadlock Detected"}
                    </p>

                    <p className="mt-2 text-sm text-slate-400">
                      {dashboardData.deadlock.description}
                    </p>
                  </div>

                  <h5 className="mb-3 mt-6 text-sm font-semibold text-white">
                    Wait-for Graph
                  </h5>

                  <div className="flex flex-wrap items-center justify-center gap-4">
                    {Object.entries(
                      dashboardData.deadlock.graph ?? {}
                    ).map(([process, waitingFor]) => (
                      <div
                        key={process}
                        className="flex items-center gap-3"
                      >
                        <div className="rounded-xl border border-blue-500/40 bg-blue-500/10 px-5 py-4 text-center">
                          <p className="font-bold text-blue-400">
                            {process}
                          </p>

                          <p className="mt-1 text-xs text-slate-400">
                            Waiting for
                          </p>

                          <p className="mt-1 font-semibold text-white">
                            {waitingFor.join(", ")}
                          </p>
                        </div>

                        <span className="text-xl text-blue-400">
                          →
                        </span>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>

            {/* Recovery Center */}
            <div className="mt-7 rounded-2xl border border-slate-800 bg-[#111827] p-6">

              <div className="mb-5">
                <h4 className="font-semibold text-white">
                  Application Recovery Center
                </h4>

                <p className="mt-2 text-sm text-slate-500">
                  Recover only the controlled test application when it becomes unresponsive
                </p>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="border-b border-slate-700 text-slate-400">
                    <tr>
                      <th className="px-4 py-3">Application</th>
                      <th className="px-4 py-3">PID</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Action</th>
                    </tr>
                  </thead>

                  <tbody>
                    {testApplications.length > 0 ? (
                      testApplications.map((item, index) => (
                        <tr
                          key={`${item.pid}-${index}`}
                          className="border-b border-slate-800"
                        >
                          <td className="px-4 py-4 text-white">
                            Application Hang Simulator
                          </td>

                          <td className="px-4 py-4 text-slate-300">
                            {item.pid}
                          </td>

                          <td className="px-4 py-4">
                            <span
                              className={
                                item.status === "NOT RESPONDING"
                                  ? "text-red-400"
                                  : "text-emerald-400"
                              }
                            >
                              {item.status}
                            </span>
                          </td>

                          <td className="px-4 py-4">
                            <button
                              disabled={item.status !== "NOT RESPONDING"}
                              onClick={() => requestRecovery(item.pid)}
                              className="rounded-lg bg-red-600 px-3 py-2 text-xs font-semibold text-white hover:bg-red-500 disabled:cursor-not-allowed disabled:opacity-40"
                            >
                              Recover
                            </button>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td
                          colSpan="4"
                          className="px-4 py-6 text-center text-slate-500"
                        >
                          No test application currently detected. Start the test simulator to use recovery.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Recovery History */}
            <div className="mt-7 rounded-2xl border border-slate-800 bg-[#111827] p-6">

              <div className="mb-5">
                <h4 className="font-semibold text-white">
                  Recovery History
                </h4>

                <p className="mt-2 text-sm text-slate-500">
                  Previous application recovery attempts recorded by the backend
                </p>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="border-b border-slate-700 text-slate-400">
                    <tr>
                      <th className="px-4 py-3">PID</th>
                      <th className="px-4 py-3">Action</th>
                      <th className="px-4 py-3">Result</th>
                      <th className="px-4 py-3">Date &amp; Time</th>
                    </tr>
                  </thead>

                  <tbody>
                    {recoveryHistory.length > 0 ? (
                      recoveryHistory.map((record, index) => (
                        <tr
                          key={`${record.pid}-${record.timestamp}-${index}`}
                          className="border-b border-slate-800 text-slate-300"
                        >
                          <td className="px-4 py-4">
                            {record.pid ?? "—"}
                          </td>

                          <td className="px-4 py-4">
                            {record.action ?? "—"}
                          </td>

                          <td className="px-4 py-4">
                            <span
                              className={
                                (record.result ?? "")
                                  .toLowerCase()
                                  .includes("success")
                                  ? "text-emerald-400"
                                  : "text-amber-400"
                              }
                            >
                              {record.result ?? "Unknown"}
                            </span>
                          </td>

                          <td className="px-4 py-4 text-slate-400">
                            {record.timestamp ?? "—"}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td
                          colSpan="4"
                          className="px-4 py-6 text-center text-slate-500"
                        >
                          No recovery attempts recorded yet.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* System Status */}
            <div className="mt-7 rounded-2xl border border-slate-800 bg-[#111827] p-6">
              <h4 className="font-semibold text-white">
                System Status
              </h4>

              <p className="mt-2 text-sm text-slate-500">
                Monitoring modules connected to the Python backend.
              </p>

              <div className="mt-5 flex flex-wrap gap-3">
                {[
                  "Process Monitor",
                  "Hang Detector",
                  "Memory Analyzer",
                  "Deadlock Detector",
                  "Recovery Manager",
                ].map((module) => (
                  <span
                    key={module}
                    className="rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2 text-xs text-slate-300"
                  >
                    {module}
                  </span>
                ))}
              </div>
            </div>

          </section>
        </main>
      </div>
    </div>
  );
}

function StatCard({ title, value, subtitle, icon: Icon }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-[#111827] p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">{title}</p>

        <div className="rounded-xl bg-blue-500/10 p-3 text-blue-400">
          <Icon size={21} />
        </div>
      </div>

      <h3 className="mt-5 text-3xl font-bold text-white">
        {value}
      </h3>

      <p className="mt-2 text-xs text-slate-500">
        {subtitle}
      </p>
    </div>
  );
}

export default App;
