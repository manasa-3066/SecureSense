import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { getIncidents } from "../services/api";

const RISK_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

function formatTimestamp(timestamp) {
  if (!timestamp) return "—";

  const date = new Date(timestamp);

  if (Number.isNaN(date.getTime())) return "—";

  return date.toLocaleString();
}

function shortDate(timestamp) {
  if (!timestamp) return "";

  const date = new Date(timestamp);

  if (Number.isNaN(date.getTime())) return "";

  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

function getRiskValue(risk) {
  return String(risk || "").toUpperCase();
}

function riskClass(risk) {
  const value = getRiskValue(risk);

  if (value === "CRITICAL") {
    return "border-red-500/30 bg-red-500/10 text-red-400";
  }

  if (value === "HIGH") {
    return "border-orange-500/30 bg-orange-500/10 text-orange-400";
  }

  if (value === "MEDIUM") {
    return "border-yellow-500/30 bg-yellow-500/10 text-yellow-400";
  }

  return "border-emerald-500/30 bg-emerald-500/10 text-emerald-400";
}

export default function Analytics() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  async function loadAnalytics(showRefresh = false) {
    try {
      if (showRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError("");

      const data = await getIncidents();

      const incidentList = Array.isArray(data)
        ? data
        : Array.isArray(data?.incidents)
          ? data.incidents
          : [];

      setIncidents(incidentList);
    } catch (err) {
      console.error("Analytics loading error:", err);

      setError(
        err?.response?.data?.detail ||
          "Unable to load analytics data from the backend."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadAnalytics();
  }, []);

  const statistics = useMemo(() => {
    const total = incidents.length;

    const attacks = incidents.filter(
      (incident) =>
        String(incident.prediction || "").toUpperCase() === "ATTACK"
    ).length;

    const benign = incidents.filter(
      (incident) =>
        String(incident.prediction || "").toUpperCase() === "BENIGN"
    ).length;

    const active = incidents.filter(
      (incident) =>
        String(incident.status || "").toUpperCase() !== "RESOLVED"
    ).length;

    const resolved = incidents.filter(
      (incident) =>
        String(incident.status || "").toUpperCase() === "RESOLVED"
    ).length;

    const high = incidents.filter(
      (incident) =>
        getRiskValue(incident.risk_level) === "HIGH"
    ).length;

    const critical = incidents.filter(
      (incident) =>
        getRiskValue(incident.risk_level) === "CRITICAL"
    ).length;

    const attackRate =
      total > 0 ? ((attacks / total) * 100).toFixed(1) : "0.0";

    const resolutionRate =
      total > 0 ? ((resolved / total) * 100).toFixed(1) : "0.0";

    const averageConfidence =
      incidents.length > 0
        ? (
            incidents.reduce(
              (sum, incident) =>
                sum + Number(incident.confidence || 0),
              0
            ) / incidents.length
          ).toFixed(1)
        : "0.0";

    return {
      total,
      attacks,
      benign,
      active,
      resolved,
      high,
      critical,
      attackRate,
      resolutionRate,
      averageConfidence,
    };
  }, [incidents]);

  const riskData = useMemo(() => {
    return RISK_ORDER.map((risk) => ({
      name: risk,
      value: incidents.filter(
        (incident) => getRiskValue(incident.risk_level) === risk
      ).length,
    }));
  }, [incidents]);

  const predictionData = useMemo(
    () => [
      {
        name: "BENIGN",
        value: statistics.benign,
      },
      {
        name: "ATTACK",
        value: statistics.attacks,
      },
    ],
    [statistics]
  );

  const statusData = useMemo(
    () => [
      {
        name: "OPEN",
        value: statistics.active,
      },
      {
        name: "RESOLVED",
        value: statistics.resolved,
      },
    ],
    [statistics]
  );

  const timelineData = useMemo(() => {
    const grouped = {};

    incidents.forEach((incident) => {
      const timestamp = incident.timestamp;

      if (!timestamp) return;

      const date = new Date(timestamp);

      if (Number.isNaN(date.getTime())) return;

      const key = date.toISOString().slice(0, 10);

      if (!grouped[key]) {
        grouped[key] = {
          date: key,
          attacks: 0,
          benign: 0,
          total: 0,
        };
      }

      const prediction = String(
        incident.prediction || ""
      ).toUpperCase();

      if (prediction === "ATTACK") {
        grouped[key].attacks += 1;
      } else {
        grouped[key].benign += 1;
      }

      grouped[key].total += 1;
    });

    return Object.values(grouped)
      .sort((a, b) => a.date.localeCompare(b.date))
      .slice(-14)
      .map((item) => ({
        ...item,
        label: shortDate(item.date),
      }));
  }, [incidents]);

  const recentIncidents = useMemo(() => {
    return [...incidents]
      .sort(
        (a, b) =>
          new Date(b.timestamp || 0) -
          new Date(a.timestamp || 0)
      )
      .slice(0, 8);
  }, [incidents]);

  const riskColors = {
    LOW: "#10b981",
    MEDIUM: "#eab308",
    HIGH: "#f97316",
    CRITICAL: "#ef4444",
  };

  if (loading) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <div className="text-center">
          <RefreshCw className="mx-auto mb-4 h-8 w-8 animate-spin text-cyan-400" />

          <p className="text-sm font-medium text-slate-300">
            Loading security analytics...
          </p>

          <p className="mt-1 text-xs text-slate-500">
            Fetching incident intelligence from SecureSense
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-8 text-center">
        <AlertTriangle className="mx-auto mb-4 h-10 w-10 text-red-400" />

        <h2 className="text-lg font-semibold text-white">
          Analytics unavailable
        </h2>

        <p className="mx-auto mt-2 max-w-lg text-sm text-slate-400">
          {error}
        </p>

        <button
          onClick={() => loadAnalytics()}
          className="mt-6 inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-medium text-slate-200 transition hover:border-cyan-500/40 hover:text-cyan-400"
        >
          <RefreshCw className="h-4 w-4" />
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div>
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-400">
            <Activity className="h-4 w-4" />
            Security Intelligence
          </div>

          <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
            Security Analytics
          </h1>

          <p className="mt-2 max-w-2xl text-sm text-slate-400">
            Monitor threat activity, incident patterns, risk distribution,
            and detection performance across SecureSense.
          </p>
        </div>

        <button
          onClick={() => loadAnalytics(true)}
          disabled={refreshing}
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm font-medium text-slate-200 transition hover:border-cyan-500/40 hover:text-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <RefreshCw
            className={`h-4 w-4 ${
              refreshing ? "animate-spin" : ""
            }`}
          />
          Refresh Analytics
        </button>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Total Incidents"
          value={statistics.total}
          subtitle="Recorded security events"
          icon={Activity}
          iconClass="bg-cyan-500/10 text-cyan-400"
        />

        <MetricCard
          title="Attack Events"
          value={statistics.attacks}
          subtitle={`${statistics.attackRate}% of incidents`}
          icon={ShieldAlert}
          iconClass="bg-red-500/10 text-red-400"
        />

        <MetricCard
          title="Active Incidents"
          value={statistics.active}
          subtitle="Require attention"
          icon={AlertTriangle}
          iconClass="bg-orange-500/10 text-orange-400"
        />

        <MetricCard
          title="Resolution Rate"
          value={`${statistics.resolutionRate}%`}
          subtitle={`${statistics.resolved} resolved incidents`}
          icon={CheckCircle2}
          iconClass="bg-emerald-500/10 text-emerald-400"
        />
      </div>

      {/* Secondary metrics */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MiniMetric
          label="High Risk"
          value={statistics.high}
          icon={AlertTriangle}
          className="text-orange-400"
        />

        <MiniMetric
          label="Critical Risk"
          value={statistics.critical}
          icon={ShieldAlert}
          className="text-red-400"
        />

        <MiniMetric
          label="Avg. Confidence"
          value={`${statistics.averageConfidence}%`}
          icon={TrendingUp}
          className="text-cyan-400"
        />

        <MiniMetric
          label="Benign Events"
          value={statistics.benign}
          icon={ShieldCheck}
          className="text-emerald-400"
        />
      </div>

      {/* Main charts */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        {/* Threat timeline */}
        <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5 xl:col-span-2">
          <ChartHeader
            title="Threat Activity"
            description="Attack and benign events over time"
          />

          <div className="mt-6 h-[320px]">
            {timelineData.length === 0 ? (
              <EmptyChart message="No timestamped incident data available yet." />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={timelineData}>
                  <defs>
                    <linearGradient
                      id="attackGradient"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="5%"
                        stopColor="#ef4444"
                        stopOpacity={0.28}
                      />
                      <stop
                        offset="95%"
                        stopColor="#ef4444"
                        stopOpacity={0}
                      />
                    </linearGradient>

                    <linearGradient
                      id="benignGradient"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="5%"
                        stopColor="#10b981"
                        stopOpacity={0.22}
                      />
                      <stop
                        offset="95%"
                        stopColor="#10b981"
                        stopOpacity={0}
                      />
                    </linearGradient>
                  </defs>

                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#1e293b"
                    vertical={false}
                  />

                  <XAxis
                    dataKey="label"
                    stroke="#64748b"
                    tickLine={false}
                    axisLine={false}
                    tick={{ fontSize: 11 }}
                  />

                  <YAxis
                    stroke="#64748b"
                    tickLine={false}
                    axisLine={false}
                    tick={{ fontSize: 11 }}
                    allowDecimals={false}
                  />

                  <Tooltip
                    contentStyle={{
                      background: "#020617",
                      border: "1px solid #1e293b",
                      borderRadius: "12px",
                      color: "#e2e8f0",
                    }}
                  />

                  <Area
                    type="monotone"
                    dataKey="attacks"
                    name="Attacks"
                    stroke="#ef4444"
                    fill="url(#attackGradient)"
                    strokeWidth={2}
                  />

                  <Area
                    type="monotone"
                    dataKey="benign"
                    name="Benign"
                    stroke="#10b981"
                    fill="url(#benignGradient)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Risk distribution */}
        <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5">
          <ChartHeader
            title="Risk Distribution"
            description="Incidents grouped by risk level"
          />

          <div className="mt-4 h-[320px]">
            {statistics.total === 0 ? (
              <EmptyChart message="No incidents available." />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={riskData}
                    cx="50%"
                    cy="45%"
                    innerRadius={72}
                    outerRadius={105}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {riskData.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={riskColors[entry.name]}
                      />
                    ))}
                  </Pie>

                  <Tooltip
                    contentStyle={{
                      background: "#020617",
                      border: "1px solid #1e293b",
                      borderRadius: "12px",
                      color: "#e2e8f0",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="grid grid-cols-2 gap-2">
            {riskData.map((item) => (
              <div
                key={item.name}
                className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-2"
              >
                <div className="flex items-center gap-2">
                  <span
                    className="h-2 w-2 rounded-full"
                    style={{
                      backgroundColor: riskColors[item.name],
                    }}
                  />

                  <span className="text-xs text-slate-400">
                    {item.name}
                  </span>
                </div>

                <span className="text-sm font-semibold text-white">
                  {item.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Distribution charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ChartCard title="Detection Outcome">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={predictionData}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#1e293b"
                vertical={false}
              />

              <XAxis
                dataKey="name"
                stroke="#64748b"
                tickLine={false}
                axisLine={false}
              />

              <YAxis
                stroke="#64748b"
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
              />

              <Tooltip
                contentStyle={{
                  background: "#020617",
                  border: "1px solid #1e293b",
                  borderRadius: "12px",
                  color: "#e2e8f0",
                }}
              />

              <Bar
                dataKey="value"
                name="Events"
                radius={[8, 8, 0, 0]}
                fill="#22d3ee"
              />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Incident Status">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={statusData}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#1e293b"
                vertical={false}
              />

              <XAxis
                dataKey="name"
                stroke="#64748b"
                tickLine={false}
                axisLine={false}
              />

              <YAxis
                stroke="#64748b"
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
              />

              <Tooltip
                contentStyle={{
                  background: "#020617",
                  border: "1px solid #1e293b",
                  borderRadius: "12px",
                  color: "#e2e8f0",
                }}
              />

              <Bar
                dataKey="value"
                name="Incidents"
                radius={[8, 8, 0, 0]}
                fill="#8b5cf6"
              />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Recent activity */}
      <div className="rounded-2xl border border-slate-800 bg-slate-950/60">
        <div className="flex flex-col justify-between gap-3 border-b border-slate-800 px-5 py-4 sm:flex-row sm:items-center">
          <div>
            <h2 className="text-sm font-semibold text-white">
              Recent Security Activity
            </h2>

            <p className="mt-1 text-xs text-slate-500">
              Latest incidents recorded by SecureSense
            </p>
          </div>

          <span className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-xs text-slate-400">
            {recentIncidents.length} recent events
          </span>
        </div>

        {recentIncidents.length === 0 ? (
          <div className="px-5 py-12 text-center text-sm text-slate-500">
            No incidents recorded yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left">
              <thead>
                <tr className="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-500">
                  <th className="px-5 py-3 font-medium">
                    Incident
                  </th>
                  <th className="px-5 py-3 font-medium">
                    Prediction
                  </th>
                  <th className="px-5 py-3 font-medium">
                    Risk
                  </th>
                  <th className="px-5 py-3 font-medium">
                    Confidence
                  </th>
                  <th className="px-5 py-3 font-medium">
                    Status
                  </th>
                  <th className="px-5 py-3 font-medium">
                    Timestamp
                  </th>
                </tr>
              </thead>

              <tbody>
                {recentIncidents.map((incident) => (
                  <tr
                    key={
                      incident.incident_id ||
                      `${incident.timestamp}-${Math.random()}`
                    }
                    className="border-b border-slate-900 transition hover:bg-slate-900/40"
                  >
                    <td className="px-5 py-4">
                      <span className="font-mono text-xs text-cyan-400">
                        {incident.incident_id || "—"}
                      </span>
                    </td>

                    <td className="px-5 py-4">
                      <span
                        className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold ${
                          String(
                            incident.prediction || ""
                          ).toUpperCase() === "ATTACK"
                            ? "border-red-500/30 bg-red-500/10 text-red-400"
                            : "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                        }`}
                      >
                        {incident.prediction || "—"}
                      </span>
                    </td>

                    <td className="px-5 py-4">
                      <span
                        className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold ${riskClass(
                          incident.risk_level
                        )}`}
                      >
                        {incident.risk_level || "—"}
                      </span>
                    </td>

                    <td className="px-5 py-4 text-sm font-medium text-slate-200">
                      {incident.confidence != null
                        ? `${Number(
                            incident.confidence
                          ).toFixed(2)}%`
                        : "—"}
                    </td>

                    <td className="px-5 py-4">
                      <span className="text-xs text-slate-400">
                        {incident.status || "OPEN"}
                      </span>
                    </td>

                    <td className="px-5 py-4 text-xs text-slate-500">
                      {formatTimestamp(incident.timestamp)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  iconClass,
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5 transition hover:border-slate-700">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
            {title}
          </p>

          <p className="mt-3 text-3xl font-bold tracking-tight text-white">
            {value}
          </p>

          <p className="mt-1 text-xs text-slate-500">
            {subtitle}
          </p>
        </div>

        <div
          className={`rounded-xl p-3 ${iconClass}`}
        >
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}

function MiniMetric({
  label,
  value,
  icon: Icon,
  className,
}) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/40 px-4 py-3">
      <div>
        <p className="text-xs text-slate-500">
          {label}
        </p>

        <p className="mt-1 text-xl font-bold text-white">
          {value}
        </p>
      </div>

      <Icon className={`h-5 w-5 ${className}`} />
    </div>
  );
}

function ChartHeader({ title, description }) {
  return (
    <div>
      <h2 className="text-sm font-semibold text-white">
        {title}
      </h2>

      <p className="mt-1 text-xs text-slate-500">
        {description}
      </p>
    </div>
  );
}

function ChartCard({ title, children }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5">
      <h2 className="mb-5 text-sm font-semibold text-white">
        {title}
      </h2>

      <div className="h-[300px]">
        {children}
      </div>
    </div>
  );
}

function EmptyChart({ message }) {
  return (
    <div className="flex h-full items-center justify-center rounded-xl border border-dashed border-slate-800">
      <p className="text-sm text-slate-500">
        {message}
      </p>
    </div>
  );
}