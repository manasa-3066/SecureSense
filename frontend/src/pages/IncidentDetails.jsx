import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Clock3,
  ShieldAlert,
  ShieldCheck,
  UserRound,
} from "lucide-react";

import {
  getIncident,
  resolveIncident,
  getThreatExplanation,
} from "../services/api";

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

export default function IncidentDetails() {
  const { incidentId } = useParams();
  const navigate = useNavigate();

  const [incident, setIncident] = useState(null);
  const [loading, setLoading] = useState(true);
  const [resolving, setResolving] = useState(false);
  const [error, setError] = useState("");
  const [threatExplanation, setThreatExplanation] = useState(null);
  const [explanationLoading, setExplanationLoading] = useState(true);
  async function loadIncident() {
    try {
      setLoading(true);
      setError("");

      const response = await getIncident(incidentId);

      setIncident(
        response?.incident || response
      );
    } catch (err) {
      console.error("Incident loading error:", err);

      setError(
        err?.response?.data?.detail ||
          "Unable to load this incident."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
  loadIncident();

  async function loadThreatExplanation() {
    try {
      setExplanationLoading(true);

      const response = await getThreatExplanation();

      setThreatExplanation(response);
    } catch (err) {
      console.error("Threat explanation error:", err);
      setThreatExplanation(null);
    } finally {
      setExplanationLoading(false);
    }
  }

  loadThreatExplanation();
}, [incidentId]);

  async function handleResolve() {
    if (!incident || incident.status === "RESOLVED") {
      return;
    }

    const confirmed = window.confirm(
      "Are you sure you want to resolve this incident?"
    );

    if (!confirmed) return;

    try {
      setResolving(true);
      setError("");

      const response =
        await resolveIncident(incident.incident_id);

      setIncident(
        response?.incident || {
          ...incident,
          status: "RESOLVED",
        }
      );
    } catch (err) {
      console.error("Incident resolution error:", err);

      setError(
        err?.response?.data?.detail ||
          "Unable to resolve this incident."
      );
    } finally {
      setResolving(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-40 animate-pulse rounded bg-slate-800" />
        <div className="h-48 animate-pulse rounded-2xl bg-[#0a0f1a]" />
        <div className="h-64 animate-pulse rounded-2xl bg-[#0a0f1a]" />
      </div>
    );
  }

  if (error && !incident) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="max-w-md rounded-2xl border border-red-500/20 bg-red-500/5 p-8 text-center">
          <ShieldAlert className="mx-auto text-red-400" size={28} />

          <h2 className="mt-4 text-lg font-semibold text-white">
            Incident unavailable
          </h2>

          <p className="mt-2 text-sm text-slate-400">
            {error}
          </p>

          <button
            onClick={() => navigate("/incidents")}
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-cyan-500 px-4 py-2.5 text-sm font-semibold text-slate-950 hover:bg-cyan-400"
          >
            <ArrowLeft size={16} />
            Back to incidents
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <section className="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
        <div>
          <button
            onClick={() => navigate("/incidents")}
            className="mb-4 inline-flex items-center gap-2 text-xs font-medium text-slate-500 transition hover:text-slate-200"
          >
            <ArrowLeft size={15} />
            Back to Incident Management
          </button>

          <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.16em] text-cyan-400">
            <ShieldAlert size={14} />
            Incident Investigation
          </div>

          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white">
            {incident?.incident_id}
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Review detection information and incident status.
          </p>
        </div>

        {incident?.status !== "RESOLVED" && (
          <button
            onClick={handleResolve}
            disabled={resolving}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-500 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <CheckCircle2 size={17} />

            {resolving
              ? "Resolving..."
              : "Resolve Incident"}
          </button>
        )}
      </section>

      {/* Error */}
      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4 text-sm text-red-300">
          {error}
        </div>
      )}

      {/* Main status */}
      <section className="grid gap-4 lg:grid-cols-3">
        <div className="rounded-2xl border border-slate-800 bg-[#0a0f1a] p-6 lg:col-span-2">
          <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-start">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-red-500/10 text-red-400">
                <ShieldAlert size={25} />
              </div>

              <div>
                <p className="text-xs uppercase tracking-[0.14em] text-slate-500">
                  Detection
                </p>

                <h2 className="mt-1 text-2xl font-semibold text-white">
                  {incident?.prediction || "ATTACK"}
                </h2>
              </div>
            </div>

            <span
              className={`inline-flex w-fit rounded-full border px-3 py-1.5 text-xs font-semibold ${riskClasses(
                incident?.risk_level
              )}`}
            >
              {incident?.risk_level || "UNKNOWN"} RISK
            </span>
          </div>

          <div className="mt-8 grid gap-5 sm:grid-cols-3">
            <div>
              <p className="text-[10px] uppercase tracking-wider text-slate-600">
                Confidence
              </p>

              <p className="mt-2 text-lg font-semibold text-slate-200">
                {incident?.confidence != null
                  ? `${incident.confidence}%`
                  : "—"}
              </p>
            </div>

            <div>
              <p className="text-[10px] uppercase tracking-wider text-slate-600">
                Status
              </p>

              <p
                className={`mt-2 text-lg font-semibold ${
                  incident?.status === "RESOLVED"
                    ? "text-emerald-300"
                    : "text-red-300"
                }`}
              >
                {incident?.status || "OPEN"}
              </p>
            </div>

            <div>
              <p className="text-[10px] uppercase tracking-wider text-slate-600">
                Detected
              </p>

              <p className="mt-2 text-sm font-medium text-slate-300">
                {formatDate(incident?.timestamp)}
              </p>
            </div>
          </div>
        </div>

        {/* Priority */}
        <div className="rounded-2xl border border-slate-800 bg-[#0a0f1a] p-6">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-orange-500/10 p-2 text-orange-400">
              <AlertTriangle size={18} />
            </div>

            <div>
              <p className="text-xs uppercase tracking-wider text-slate-600">
                Priority
              </p>

              <p className="mt-1 text-lg font-semibold text-white">
                {incident?.risk_level === "CRITICAL"
                  ? "Immediate Attention"
                  : incident?.risk_level === "HIGH"
                  ? "High Priority"
                  : "Standard Review"}
              </p>
            </div>
          </div>

          <div className="mt-6 rounded-xl border border-slate-800 bg-slate-950/40 p-4">
            <div className="flex items-center gap-2">
              <Clock3 size={15} className="text-slate-500" />

              <span className="text-xs text-slate-400">
                Detection timestamp
              </span>
            </div>

            <p className="mt-2 text-sm text-slate-300">
              {formatDate(incident?.timestamp)}
            </p>
          </div>
        </div>
      </section>

      {/* Detection metadata */}
      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-[#0a0f1a] p-6">
          <div className="flex items-center gap-3">
            <ShieldCheck
              size={18}
              className="text-cyan-400"
            />

            <div>
              <h2 className="font-semibold text-white">
                Detection Summary
              </h2>

              <p className="mt-1 text-xs text-slate-500">
                Classification produced by the SecureSense ML engine
              </p>
            </div>
          </div>

          <div className="mt-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800/70 pb-4">
              <span className="text-sm text-slate-500">
                Prediction
              </span>

              <span className="text-sm font-medium text-red-300">
                {incident?.prediction || "ATTACK"}
              </span>
            </div>

            <div className="flex items-center justify-between border-b border-slate-800/70 pb-4">
              <span className="text-sm text-slate-500">
                Risk Level
              </span>

              <span
                className={`rounded-full border px-2.5 py-1 text-[10px] font-semibold ${riskClasses(
                  incident?.risk_level
                )}`}
              >
                {incident?.risk_level}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-500">
                Confidence
              </span>

              <span className="text-sm font-medium text-slate-200">
                {incident?.confidence != null
                  ? `${incident.confidence}%`
                  : "—"}
              </span>
            </div>
          </div>
        </div>

        {/* Incident metadata */}
        <div className="rounded-2xl border border-slate-800 bg-[#0a0f1a] p-6">
          <div className="flex items-center gap-3">
            <UserRound
              size={18}
              className="text-cyan-400"
            />

            <div>
              <h2 className="font-semibold text-white">
                Incident Metadata
              </h2>

              <p className="mt-1 text-xs text-slate-500">
                Incident lifecycle information
              </p>
            </div>
          </div>

          <div className="mt-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800/70 pb-4">
              <span className="text-sm text-slate-500">
                Incident ID
              </span>

              <span className="text-xs font-medium text-slate-300">
                {incident?.incident_id || "—"}
              </span>
            </div>

            <div className="flex items-center justify-between border-b border-slate-800/70 pb-4">
              <span className="text-sm text-slate-500">
                Status
              </span>

              <span className="text-sm font-medium text-slate-300">
                {incident?.status || "OPEN"}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-500">
                Resolved At
              </span>

              <span className="text-xs font-medium text-slate-300">
                {formatDate(incident?.resolved_at)}
              </span>
            </div>
          </div>
        </div>
      </section>
      {/* Threat Explanation */}
<section className="rounded-2xl border border-cyan-500/10 bg-[#0a0f1a] p-6">
  <div className="flex items-center gap-3">
    <div className="rounded-lg bg-cyan-500/10 p-2 text-cyan-400">
      <ShieldCheck size={18} />
    </div>

    <div>
      <h2 className="font-semibold text-white">
        Why Was This Threat Detected?
      </h2>

      <p className="mt-1 text-xs text-slate-500">
        DNN-based detection reasoning
      </p>
    </div>
  </div>

  {explanationLoading ? (
    <div className="mt-6 space-y-3">
      {[1, 2, 3, 4].map((item) => (
        <div
          key={item}
          className="h-10 animate-pulse rounded-lg bg-slate-800"
        />
      ))}
    </div>
  ) : (
    <div className="mt-6 space-y-5">

      {/* Explanation */}
      <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
        <p className="text-sm leading-6 text-slate-300">
          SecureSense's{" "}
          <span className="font-semibold text-cyan-300">
            Deep Neural Network
          </span>{" "}
          analyzed 69 validated network-flow features and classified this
          traffic as{" "}
          <span className="font-semibold text-red-300">
            {incident?.prediction || "ATTACK"}
          </span>
          .
        </p>

        <p className="mt-3 text-sm leading-6 text-slate-400">
          The traffic was classified based on its predicted attack
          probability and the configured decision threshold.
        </p>
      </div>

      {/* Detection Details */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">

        {/* Prediction */}
        <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
          <p className="text-xs text-slate-500">
            Classification
          </p>

          <p className="mt-2 text-lg font-semibold text-red-300">
            {incident?.prediction || "ATTACK"}
          </p>
        </div>

        {/* Confidence */}
        <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
          <p className="text-xs text-slate-500">
            Model Confidence
          </p>

          <p className="mt-2 text-lg font-semibold text-cyan-300">
            {incident?.confidence != null
              ? `${incident.confidence}%`
              : "N/A"}
          </p>
        </div>

        {/* Model */}
        <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
          <p className="text-xs text-slate-500">
            Detection Model
          </p>

          <p className="mt-2 text-sm font-semibold text-slate-200">
            Deep Neural Network
          </p>
        </div>

        {/* Features */}
        <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
          <p className="text-xs text-slate-500">
            Input Features
          </p>

          <p className="mt-2 text-sm font-semibold text-slate-200">
            69 validated features
          </p>
        </div>
      </div>

      {/* Decision Threshold */}
      <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
        <div className="flex items-center justify-between">
          <p className="text-xs text-slate-500">
            Decision Threshold
          </p>

          <p className="text-sm font-semibold text-cyan-300">
            18%
          </p>
        </div>

        <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-800">
          <div
            className="h-full rounded-full bg-cyan-400"
            style={{ width: "18%" }}
          />
        </div>

        <p className="mt-3 text-[11px] leading-5 text-slate-500">
          A traffic flow is classified as an attack when the DNN's
          predicted attack probability reaches or exceeds this threshold.
        </p>
      </div>

      {/* Honest explanation note */}
      <div className="rounded-xl border border-cyan-500/10 bg-cyan-500/5 p-4">
        <p className="text-[11px] leading-5 text-slate-400">
  SecureSense uses a Deep Neural Network for threat detection.
  The explanation is based on the model prediction, confidence,
  and configured decision threshold rather than tree-based feature importance.
</p>
      </div>

    </div>
  )}
</section>
      {/* Lifecycle */}
      <section className="rounded-2xl border border-slate-800 bg-[#0a0f1a] p-6">
        <h2 className="font-semibold text-white">
          Incident Lifecycle
        </h2>

        <p className="mt-1 text-xs text-slate-500">
          Current state of the security incident
        </p>

        <div className="mt-8 flex items-center">
          <div className="flex flex-1 items-center">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-400/20">
              <ShieldAlert size={17} />
            </div>

            <div className="ml-3">
              <p className="text-xs font-semibold text-slate-200">
                Detected
              </p>

              <p className="mt-1 text-[10px] text-slate-600">
                {formatDate(incident?.timestamp)}
              </p>
            </div>
          </div>

          <div className="h-px flex-1 bg-slate-800" />

          <div className="flex flex-1 items-center justify-end">
            <div className="mr-3 text-right">
              <p className="text-xs font-semibold text-slate-200">
                Resolved
              </p>

              <p className="mt-1 text-[10px] text-slate-600">
                {formatDate(incident?.resolved_at)}
              </p>
            </div>

            <div
              className={`flex h-10 w-10 items-center justify-center rounded-full ${
                incident?.status === "RESOLVED"
                  ? "bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-400/20"
                  : "bg-slate-800 text-slate-600"
              }`}
            >
              <CheckCircle2 size={17} />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}