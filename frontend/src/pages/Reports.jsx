import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Download,
  FileText,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";

import { getIncidents } from "../services/api";

function formatTimestamp(timestamp) {
  if (!timestamp) return "—";

  const date = new Date(timestamp);

  if (Number.isNaN(date.getTime())) return "—";

  return date.toLocaleString();
}

function riskClass(risk) {
  const value = String(risk || "").toUpperCase();

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

export default function Reports() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  async function loadReports(showRefresh = false) {
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
      console.error("Reports loading error:", err);

      setError(
        err?.response?.data?.detail ||
          "Unable to load report data from the backend."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadReports();
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

    const open = incidents.filter(
      (incident) =>
        String(incident.status || "").toUpperCase() !== "RESOLVED"
    ).length;

    const resolved = incidents.filter(
      (incident) =>
        String(incident.status || "").toUpperCase() === "RESOLVED"
    ).length;

    const low = incidents.filter(
      (incident) =>
        String(incident.risk_level || "").toUpperCase() === "LOW"
    ).length;

    const medium = incidents.filter(
      (incident) =>
        String(incident.risk_level || "").toUpperCase() === "MEDIUM"
    ).length;

    const high = incidents.filter(
      (incident) =>
        String(incident.risk_level || "").toUpperCase() === "HIGH"
    ).length;

    const critical = incidents.filter(
      (incident) =>
        String(incident.risk_level || "").toUpperCase() === "CRITICAL"
    ).length;

    const averageConfidence =
      total > 0
        ? (
            incidents.reduce(
              (sum, incident) =>
                sum + Number(incident.confidence || 0),
              0
            ) / total
          ).toFixed(2)
        : "0.00";

    const attackRate =
      total > 0
        ? ((attacks / total) * 100).toFixed(2)
        : "0.00";

    const resolutionRate =
      total > 0
        ? ((resolved / total) * 100).toFixed(2)
        : "0.00";

    return {
      total,
      attacks,
      benign,
      open,
      resolved,
      low,
      medium,
      high,
      critical,
      averageConfidence,
      attackRate,
      resolutionRate,
    };
  }, [incidents]);

  const recentIncidents = useMemo(() => {
    return [...incidents]
      .sort(
        (a, b) =>
          new Date(b.timestamp || 0) -
          new Date(a.timestamp || 0)
      )
      .slice(0, 15);
  }, [incidents]);

  function downloadCSV() {
    if (incidents.length === 0) {
      return;
    }

    const headers = [
      "Incident ID",
      "Timestamp",
      "Prediction",
      "Confidence",
      "Risk Level",
      "Status",
    ];

    const rows = incidents.map((incident) => [
      incident.incident_id || "",
      incident.timestamp || "",
      incident.prediction || "",
      incident.confidence ?? "",
      incident.risk_level || "",
      incident.status || "",
    ]);

    const csvContent = [
      headers,
      ...rows,
    ]
      .map((row) =>
        row
          .map((value) =>
            `"${String(value).replaceAll('"', '""')}"`
          )
          .join(",")
      )
      .join("\n");

    const blob = new Blob([csvContent], {
      type: "text/csv;charset=utf-8;",
    });

    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");

    link.href = url;
    link.download = `securesense-security-report-${new Date()
      .toISOString()
      .slice(0, 10)}.csv`;

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  }

  function printReport() {
    window.print();
  }

  if (loading) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <div className="text-center">
          <RefreshCw className="mx-auto mb-4 h-8 w-8 animate-spin text-cyan-400" />

          <p className="text-sm font-medium text-slate-300">
            Preparing security report...
          </p>

          <p className="mt-1 text-xs text-slate-500">
            Collecting incident intelligence from SecureSense
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
          Report unavailable
        </h2>

        <p className="mx-auto mt-2 max-w-lg text-sm text-slate-400">
          {error}
        </p>

        <button
          onClick={() => loadReports()}
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
            <FileText className="h-4 w-4" />
            Security Reporting
          </div>

          <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
            Security Reports
          </h1>

          <p className="mt-2 max-w-2xl text-sm text-slate-400">
            Generate an operational summary of detected threats,
            incident status, risk levels, and detection activity.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => loadReports(true)}
            disabled={refreshing}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm font-medium text-slate-200 transition hover:border-cyan-500/40 hover:text-cyan-400 disabled:opacity-60"
          >
            <RefreshCw
              className={`h-4 w-4 ${
                refreshing ? "animate-spin" : ""
              }`}
            />
            Refresh
          </button>

          <button
            onClick={downloadCSV}
            disabled={incidents.length === 0}
            className="inline-flex items-center gap-2 rounded-xl bg-cyan-500 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Download className="h-4 w-4" />
            Export CSV
          </button>

          <button
            onClick={printReport}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm font-medium text-slate-200 transition hover:border-slate-600 hover:text-white"
          >
            <FileText className="h-4 w-4" />
            Print Report
          </button>
        </div>
      </div>

      {/* Report banner */}
      <div className="rounded-2xl border border-cyan-500/20 bg-gradient-to-r from-cyan-500/10 via-slate-950/70 to-slate-950/60 p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="rounded-xl bg-cyan-500/10 p-3 text-cyan-400">
              <ShieldCheck className="h-6 w-6" />
            </div>

            <div>
              <h2 className="font-semibold text-white">
                SecureSense Security Assessment
              </h2>

              <p className="mt-1 text-xs text-slate-400">
                Report generated from currently stored incident records.
              </p>
            </div>
          </div>

          <div className="text-left sm:text-right">
            <p className="text-xs uppercase tracking-wider text-slate-500">
              Report Date
            </p>

            <p className="mt-1 text-sm font-medium text-slate-200">
              {new Date().toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Overview */}
      <section>
        <SectionTitle
          icon={BarChart3}
          title="Executive Summary"
          description="Current security posture based on recorded incidents"
        />

        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <ReportCard
            title="Total Incidents"
            value={statistics.total}
            description="Recorded events"
            icon={ActivityIcon}
            iconClass="text-cyan-400 bg-cyan-500/10"
          />

          <ReportCard
            title="Attack Events"
            value={statistics.attacks}
            description={`${statistics.attackRate}% of total events`}
            icon={ShieldAlert}
            iconClass="text-red-400 bg-red-500/10"
          />

          <ReportCard
            title="Open Incidents"
            value={statistics.open}
            description="Awaiting resolution"
            icon={AlertTriangle}
            iconClass="text-orange-400 bg-orange-500/10"
          />

          <ReportCard
            title="Resolved"
            value={statistics.resolved}
            description={`${statistics.resolutionRate}% resolution rate`}
            icon={CheckCircle2}
            iconClass="text-emerald-400 bg-emerald-500/10"
          />
        </div>
      </section>

      {/* Detection summary */}
      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5">
          <SectionTitle
            icon={ShieldAlert}
            title="Detection Summary"
            description="Prediction outcomes recorded by SecureSense"
          />

          <div className="mt-5 space-y-4">
            <ProgressRow
              label="Attack"
              value={statistics.attacks}
              total={statistics.total}
              className="bg-red-500"
            />

            <ProgressRow
              label="Benign"
              value={statistics.benign}
              total={statistics.total}
              className="bg-emerald-500"
            />
          </div>

          <div className="mt-6 grid grid-cols-2 gap-3">
            <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4">
              <p className="text-xs text-slate-500">
                Attack Events
              </p>

              <p className="mt-2 text-2xl font-bold text-red-400">
                {statistics.attacks}
              </p>
            </div>

            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
              <p className="text-xs text-slate-500">
                Benign Events
              </p>

              <p className="mt-2 text-2xl font-bold text-emerald-400">
                {statistics.benign}
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5">
          <SectionTitle
            icon={AlertTriangle}
            title="Risk Assessment"
            description="Distribution of incident risk levels"
          />

          <div className="mt-5 grid grid-cols-2 gap-3">
            <RiskBox
              label="LOW"
              value={statistics.low}
              className="text-emerald-400 border-emerald-500/20 bg-emerald-500/5"
            />

            <RiskBox
              label="MEDIUM"
              value={statistics.medium}
              className="text-yellow-400 border-yellow-500/20 bg-yellow-500/5"
            />

            <RiskBox
              label="HIGH"
              value={statistics.high}
              className="text-orange-400 border-orange-500/20 bg-orange-500/5"
            />

            <RiskBox
              label="CRITICAL"
              value={statistics.critical}
              className="text-red-400 border-red-500/20 bg-red-500/5"
            />
          </div>

          <div className="mt-5 rounded-xl border border-slate-800 bg-slate-900/50 p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">
                Average Detection Confidence
              </span>

              <span className="text-sm font-bold text-cyan-400">
                {statistics.averageConfidence}%
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Incident table */}
      <section className="rounded-2xl border border-slate-800 bg-slate-950/60">
        <div className="border-b border-slate-800 px-5 py-4">
          <SectionTitle
            icon={FileText}
            title="Incident Register"
            description="Latest recorded security incidents"
          />
        </div>

        {recentIncidents.length === 0 ? (
          <div className="px-5 py-14 text-center">
            <ShieldCheck className="mx-auto mb-3 h-9 w-9 text-emerald-400" />

            <p className="text-sm font-medium text-white">
              No incidents recorded
            </p>

            <p className="mt-1 text-xs text-slate-500">
              Run a detection analysis to generate security events.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[850px] text-left">
              <thead>
                <tr className="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-500">
                  <th className="px-5 py-3 font-medium">
                    Incident ID
                  </th>

                  <th className="px-5 py-3 font-medium">
                    Timestamp
                  </th>

                  <th className="px-5 py-3 font-medium">
                    Prediction
                  </th>

                  <th className="px-5 py-3 font-medium">
                    Confidence
                  </th>

                  <th className="px-5 py-3 font-medium">
                    Risk
                  </th>

                  <th className="px-5 py-3 font-medium">
                    Status
                  </th>
                </tr>
              </thead>

              <tbody>
                {recentIncidents.map((incident) => (
                  <tr
                    key={incident.incident_id}
                    className="border-b border-slate-900 hover:bg-slate-900/40"
                  >
                    <td className="px-5 py-4">
                      <span className="font-mono text-xs text-cyan-400">
                        {incident.incident_id || "—"}
                      </span>
                    </td>

                    <td className="px-5 py-4 text-xs text-slate-500">
                      {formatTimestamp(incident.timestamp)}
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

                    <td className="px-5 py-4 text-sm font-medium text-slate-200">
                      {incident.confidence != null
                        ? `${Number(
                            incident.confidence
                          ).toFixed(2)}%`
                        : "—"}
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

                    <td className="px-5 py-4">
                      <span className="text-xs text-slate-400">
                        {incident.status || "OPEN"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Report footer */}
      <div className="rounded-xl border border-slate-800 bg-slate-950/40 px-5 py-4">
        <div className="flex flex-col gap-2 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
          <span>
            SecureSense • AI-Based Cyber Threat Detection and
            Incident Response Platform
          </span>

          <span>
            Data source: SecureSense incident database
          </span>
        </div>
      </div>
    </div>
  );
}

function SectionTitle({
  icon: Icon,
  title,
  description,
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="rounded-lg bg-slate-900 p-2 text-cyan-400">
        <Icon className="h-4 w-4" />
      </div>

      <div>
        <h2 className="text-sm font-semibold text-white">
          {title}
        </h2>

        <p className="mt-1 text-xs text-slate-500">
          {description}
        </p>
      </div>
    </div>
  );
}

function ReportCard({
  title,
  value,
  description,
  icon: Icon,
  iconClass,
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs uppercase tracking-wider text-slate-500">
            {title}
          </p>

          <p className="mt-3 text-3xl font-bold text-white">
            {value}
          </p>

          <p className="mt-1 text-xs text-slate-500">
            {description}
          </p>
        </div>

        <div className={`rounded-xl p-3 ${iconClass}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}

function ProgressRow({
  label,
  value,
  total,
  className,
}) {
  const percentage =
    total > 0 ? (value / total) * 100 : 0;

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs font-medium text-slate-400">
          {label}
        </span>

        <span className="text-xs font-semibold text-slate-300">
          {value} ({percentage.toFixed(1)}%)
        </span>
      </div>

      <div className="h-2 overflow-hidden rounded-full bg-slate-800">
        <div
          className={`h-full rounded-full ${className}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

function RiskBox({
  label,
  value,
  className,
}) {
  return (
    <div className={`rounded-xl border p-4 ${className}`}>
      <p className="text-[11px] font-semibold tracking-wider">
        {label}
      </p>

      <p className="mt-2 text-2xl font-bold">
        {value}
      </p>
    </div>
  );
}

function ActivityIcon({ className }) {
  return <Activity className={className} />;
}