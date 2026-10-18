import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowUpDown,
  CheckCircle2,
  Eye,
  Filter,
  RefreshCw,
  Search,
  ShieldAlert,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { getIncidents } from "../services/api";

function riskClasses(risk) {
  switch (risk) {
    case "CRITICAL":
      return "border-red-500/20 bg-red-500/10 text-red-300";

    case "HIGH":
      return "border-orange-500/20 bg-orange-500/10 text-orange-300";

    case "MEDIUM":
      return "border-amber-500/20 bg-amber-500/10 text-amber-300";

    case "LOW":
      return "border-emerald-500/20 bg-emerald-500/10 text-emerald-300";

    default:
      return "border-slate-700 bg-slate-800 text-slate-400";
  }
}

function statusClasses(status) {
  if (status === "RESOLVED") {
    return "border-emerald-500/20 bg-emerald-500/10 text-emerald-300";
  }

  return "border-red-500/20 bg-red-500/10 text-red-300";
}

function formatDate(timestamp) {
  if (!timestamp) return "—";

  const date = new Date(timestamp);

  if (Number.isNaN(date.getTime())) return "—";

  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function Incidents() {
  const navigate = useNavigate();

  const [incidents, setIncidents] = useState([]);

  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  async function loadIncidents(showRefresh = false) {
    try {
      setError("");

      if (showRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      const response = await getIncidents();

      const data = Array.isArray(response?.incidents)
        ? response.incidents
        : [];

      setIncidents(data);
    } catch (err) {
      console.error("Incident loading error:", err);

      setError(
        err?.response?.data?.detail ||
          "Unable to load incidents."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadIncidents();
  }, []);

  const filteredIncidents = useMemo(() => {
    return incidents
      .filter((incident) => {
        if (riskFilter === "ALL") return true;

        return incident.risk_level === riskFilter;
      })
      .filter((incident) => {
        if (statusFilter === "ALL") return true;

        return incident.status === statusFilter;
      })
      .filter((incident) => {
        if (!search.trim()) return true;

        const query = search.toLowerCase();

        return (
          incident.incident_id
            ?.toLowerCase()
            .includes(query) ||
          incident.prediction
            ?.toLowerCase()
            .includes(query) ||
          incident.risk_level
            ?.toLowerCase()
            .includes(query) ||
          incident.status
            ?.toLowerCase()
            .includes(query)
        );
      });
  }, [
    incidents,
    search,
    riskFilter,
    statusFilter,
  ]);

  const statistics = useMemo(() => {
    const active = incidents.filter(
      (item) => item.status === "OPEN"
    ).length;

    const resolved = incidents.filter(
      (item) => item.status === "RESOLVED"
    ).length;

    const critical = incidents.filter(
      (item) => item.risk_level === "CRITICAL"
    ).length;

    const high = incidents.filter(
      (item) => item.risk_level === "HIGH"
    ).length;

    return {
      total: incidents.length,
      active,
      resolved,
      critical,
      high,
    };
  }, [incidents]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <section className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div>
          <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.16em] text-cyan-400">
            <ShieldAlert size={14} />
            Security Operations
          </div>

          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            Incident Management
          </h1>

          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">
            Investigate detected threats, review severity, and
            manage the lifecycle of security incidents.
          </p>
        </div>

        <button
          onClick={() => loadIncidents(true)}
          disabled={refreshing}
          className="inline-flex w-fit items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/70 px-4 py-2.5 text-sm font-medium text-slate-300 transition hover:border-slate-700 hover:bg-slate-800 disabled:opacity-50"
        >
          <RefreshCw
            size={16}
            className={refreshing ? "animate-spin" : ""}
          />

          {refreshing ? "Refreshing..." : "Refresh"}
        </button>
      </section>

      {/* Stats */}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <div className="rounded-2xl border border-slate-800 bg-[#0a0f1a] p-5">
          <p className="text-[10px] uppercase tracking-[0.14em] text-slate-600">
            Total
          </p>

          <p className="mt-3 text-2xl font-semibold text-white">
            {statistics.total}
          </p>
        </div>

        <div className="rounded-2xl border border-red-500/10 bg-red-500/[0.03] p-5">
          <p className="text-[10px] uppercase tracking-[0.14em] text-slate-600">
            Active
          </p>

          <p className="mt-3 text-2xl font-semibold text-red-300">
            {statistics.active}
          </p>
        </div>

        <div className="rounded-2xl border border-emerald-500/10 bg-emerald-500/[0.03] p-5">
          <p className="text-[10px] uppercase tracking-[0.14em] text-slate-600">
            Resolved
          </p>

          <p className="mt-3 text-2xl font-semibold text-emerald-300">
            {statistics.resolved}
          </p>
        </div>

        <div className="rounded-2xl border border-orange-500/10 bg-orange-500/[0.03] p-5">
          <p className="text-[10px] uppercase tracking-[0.14em] text-slate-600">
            High
          </p>

          <p className="mt-3 text-2xl font-semibold text-orange-300">
            {statistics.high}
          </p>
        </div>

        <div className="rounded-2xl border border-red-500/10 bg-red-500/[0.03] p-5">
          <p className="text-[10px] uppercase tracking-[0.14em] text-slate-600">
            Critical
          </p>

          <p className="mt-3 text-2xl font-semibold text-red-400">
            {statistics.critical}
          </p>
        </div>
      </section>

      {/* Filters */}
      <section className="rounded-2xl border border-slate-800 bg-[#0a0f1a] p-4">
        <div className="flex flex-col gap-3 xl:flex-row">
          {/* Search */}
          <div className="relative flex-1">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600"
            />

            <input
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
              placeholder="Search incident ID, prediction, risk..."
              className="w-full rounded-xl border border-slate-800 bg-slate-950/50 py-2.5 pl-10 pr-4 text-sm text-slate-200 outline-none placeholder:text-slate-600 focus:border-cyan-500/40"
            />
          </div>

          {/* Risk */}
          <div className="relative">
            <Filter
              size={14}
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-600"
            />

            <select
              value={riskFilter}
              onChange={(event) =>
                setRiskFilter(event.target.value)
              }
              className="appearance-none rounded-xl border border-slate-800 bg-slate-950/50 py-2.5 pl-9 pr-9 text-sm text-slate-300 outline-none focus:border-cyan-500/40"
            >
              <option value="ALL">All Risks</option>
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
              <option value="CRITICAL">Critical</option>
            </select>
          </div>

          {/* Status */}
          <div className="relative">
            <select
              value={statusFilter}
              onChange={(event) =>
                setStatusFilter(event.target.value)
              }
              className="appearance-none rounded-xl border border-slate-800 bg-slate-950/50 py-2.5 px-4 pr-9 text-sm text-slate-300 outline-none focus:border-cyan-500/40"
            >
              <option value="ALL">All Status</option>
              <option value="OPEN">Open</option>
              <option value="RESOLVED">Resolved</option>
            </select>
          </div>
        </div>
      </section>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/5 p-4">
          <AlertTriangle
            size={18}
            className="mt-0.5 text-red-400"
          />

          <div>
            <p className="text-sm font-medium text-red-300">
              Unable to load incidents
            </p>

            <p className="mt-1 text-xs text-red-300/70">
              {error}
            </p>
          </div>
        </div>
      )}

      {/* Table */}
      <section className="overflow-hidden rounded-2xl border border-slate-800 bg-[#0a0f1a]">
        <div className="flex items-center justify-between border-b border-slate-800 p-5">
          <div>
            <h2 className="font-semibold text-white">
              Security Incidents
            </h2>

            <p className="mt-1 text-xs text-slate-500">
              {filteredIncidents.length} incidents matching current
              filters
            </p>
          </div>

          <ArrowUpDown
            size={17}
            className="text-slate-600"
          />
        </div>

        {loading ? (
          <div className="space-y-3 p-5">
            {[1, 2, 3, 4, 5].map((item) => (
              <div
                key={item}
                className="h-14 animate-pulse rounded-xl bg-slate-900"
              />
            ))}
          </div>
        ) : filteredIncidents.length === 0 ? (
          <div className="flex min-h-72 items-center justify-center p-8">
            <div className="text-center">
              <CheckCircle2
                size={32}
                className="mx-auto text-slate-700"
              />

              <h3 className="mt-4 text-sm font-semibold text-slate-300">
                No incidents found
              </h3>

              <p className="mt-1 text-xs text-slate-600">
                Try changing your search or filters.
              </p>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[950px] text-left">
              <thead>
                <tr className="border-b border-slate-800 text-[10px] uppercase tracking-wider text-slate-600">
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
                    Timestamp
                  </th>

                  <th className="px-5 py-3 font-medium">
                    Status
                  </th>

                  <th className="px-5 py-3 text-right font-medium">
                    Action
                  </th>
                </tr>
              </thead>

              <tbody>
                {filteredIncidents.map((incident) => (
                  <tr
                    key={incident.incident_id}
                    className="border-b border-slate-800/60 transition hover:bg-slate-900/40 last:border-0"
                  >
                    <td className="px-5 py-4">
                      <p className="text-xs font-semibold text-slate-200">
                        {incident.incident_id}
                      </p>
                    </td>

                    <td className="px-5 py-4">
                      <span className="inline-flex items-center gap-2 text-xs font-medium text-red-300">
                        <span className="h-1.5 w-1.5 rounded-full bg-red-400" />

                        {incident.prediction}
                      </span>
                    </td>

                    <td className="px-5 py-4">
                      <span
                        className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-semibold ${riskClasses(
                          incident.risk_level
                        )}`}
                      >
                        {incident.risk_level}
                      </span>
                    </td>

                    <td className="px-5 py-4 text-xs font-medium text-slate-300">
                      {incident.confidence != null
                        ? `${incident.confidence}%`
                        : "—"}
                    </td>

                    <td className="px-5 py-4 text-xs text-slate-500">
                      {formatDate(incident.timestamp)}
                    </td>

                    <td className="px-5 py-4">
                      <span
                        className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-semibold ${statusClasses(
                          incident.status
                        )}`}
                      >
                        {incident.status}
                      </span>
                    </td>

                    <td className="px-5 py-4 text-right">
                      <button
                        onClick={() =>
                          navigate(
                            `/incidents/${incident.incident_id}`
                          )
                        }
                        className="inline-flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-xs font-medium text-slate-300 transition hover:border-cyan-500/30 hover:bg-cyan-500/5 hover:text-cyan-300"
                      >
                        <Eye size={14} />
                        Investigate
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}