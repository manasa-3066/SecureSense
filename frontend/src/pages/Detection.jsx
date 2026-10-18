import { useRef, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  FileCheck2,
  FileSpreadsheet,
  ShieldAlert,
  ShieldCheck,
  Upload,
  X,
} from "lucide-react";

import { predictCSV } from "../services/api";

/* ============================================================
   HELPERS
============================================================ */

function getRiskClasses(risk) {
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
      return "border-slate-700 bg-slate-800/50 text-slate-400";
  }
}

function getPredictionClasses(prediction) {
  if (prediction === "ATTACK") {
    return "border-red-500/20 bg-red-500/10 text-red-300";
  }

  return "border-emerald-500/20 bg-emerald-500/10 text-emerald-300";
}

function formatConfidence(value) {
  if (value === null || value === undefined) {
    return "—";
  }

  return `${Number(value).toFixed(2)}%`;
}

/* ============================================================
   SUMMARY CARD
============================================================ */

function SummaryCard({
  title,
  value,
  description,
  icon: Icon,
  iconClass,
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-[#0a0f1a] p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">
            {title}
          </p>

          <p className="mt-3 text-3xl font-semibold text-white">
            {value}
          </p>

          <p className="mt-2 text-xs text-slate-500">
            {description}
          </p>
        </div>

        <div
          className={`flex h-11 w-11 items-center justify-center rounded-xl ${iconClass}`}
        >
          <Icon size={20} />
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   DETECTION PAGE
============================================================ */

export default function Detection() {
  const fileInputRef = useRef(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const [expandedRows, setExpandedRows] = useState({});

  /* ==========================================================
     FILE HANDLING
  ========================================================== */

  function handleFile(file) {
    setError("");
    setResult(null);
    setExpandedRows({});

    if (!file) {
      return;
    }

    const isCSV =
      file.name.toLowerCase().endsWith(".csv");

    if (!isCSV) {
      setError("Please select a CSV file.");
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  }

  function handleFileInput(event) {
    const file = event.target.files?.[0];

    handleFile(file);
  }

  function handleDrop(event) {
    event.preventDefault();

    setDragActive(false);

    const file = event.dataTransfer.files?.[0];

    handleFile(file);
  }

  function removeFile() {
    setSelectedFile(null);
    setResult(null);
    setError("");
    setExpandedRows({});

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  /* ==========================================================
     ANALYZE
  ========================================================== */

  async function handleAnalyze() {
    if (!selectedFile) {
      setError("Please select a CSV file first.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setResult(null);
      setExpandedRows({});

      const response = await predictCSV(selectedFile);

      if (response?.error) {
        throw new Error(response.error);
      }

      setResult(response);
    } catch (err) {
      console.error("Threat detection error:", err);

      const message =
        err?.response?.data?.detail ||
        err?.response?.data?.error ||
        err?.message ||
        "Unable to analyze the uploaded file.";

      setError(message);
    } finally {
      setLoading(false);
    }
  }

  /* ==========================================================
     TOGGLE ROW
  ========================================================== */

  function toggleRow(rowNumber) {
    setExpandedRows((previous) => ({
      ...previous,
      [rowNumber]: !previous[rowNumber],
    }));
  }

  /* ==========================================================
     RESULT DATA
  ========================================================== */

  const summary = result?.security_summary;

  const results = Array.isArray(result?.results)
    ? result.results
    : [];

  /* ==========================================================
     RENDER
  ========================================================== */

  return (
    <div className="space-y-6">
      {/* ======================================================
          HEADER
      ====================================================== */}

      <section>
        <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.16em] text-cyan-400">
          <Activity size={14} />
          AI Threat Detection
        </div>

        <div className="mt-2 flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
              Threat Detection
            </h1>

            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">
  Upload network traffic data and let the SecureSense
  Deep Neural Network identify suspicious activity,
  classify risk, and create security incidents.
</p>
          </div>

          {result && (
            <div className="flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/5 px-3 py-2">
              <CheckCircle2
                size={15}
                className="text-emerald-400"
              />

              <span className="text-xs font-medium text-emerald-300">
                Analysis Complete
              </span>
            </div>
          )}
        </div>
      </section>

      {/* ======================================================
          UPLOAD CARD
      ====================================================== */}

      {!result && (
        <section className="rounded-2xl border border-slate-800 bg-[#0a0f1a] p-6 sm:p-8">
          <div className="mb-6">
            <h2 className="font-semibold text-white">
              Analyze Network Traffic
            </h2>

            <p className="mt-1 text-xs text-slate-500">
              Upload a CSV containing the required network-flow
              features.
            </p>
          </div>

          {/* Drop zone */}
          <div
            onDragEnter={(event) => {
              event.preventDefault();
              setDragActive(true);
            }}
            onDragOver={(event) => {
              event.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={(event) => {
              event.preventDefault();
              setDragActive(false);
            }}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`
              relative cursor-pointer rounded-2xl border-2 border-dashed
              p-10 text-center transition-all
              sm:p-14
              ${
                dragActive
                  ? "border-cyan-400 bg-cyan-500/5"
                  : "border-slate-800 bg-slate-950/30 hover:border-slate-700 hover:bg-slate-900/40"
              }
            `}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileInput}
              className="hidden"
            />

            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-400/10">
              <Upload size={28} />
            </div>

            <h3 className="mt-5 text-base font-semibold text-white">
              Drop your CSV file here
            </h3>

            <p className="mt-2 text-sm text-slate-500">
              or click to browse from your computer
            </p>

            <div className="mt-5 inline-flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900 px-3 py-1.5 text-[10px] font-medium uppercase tracking-wider text-slate-500">
              <FileSpreadsheet size={13} />
              CSV files only
            </div>
          </div>

          {/* Selected file */}
          {selectedFile && (
            <div className="mt-5 flex flex-col justify-between gap-4 rounded-xl border border-cyan-500/10 bg-cyan-500/[0.03] p-4 sm:flex-row sm:items-center">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400">
                  <FileCheck2 size={18} />
                </div>

                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-slate-200">
                    {selectedFile.name}
                  </p>

                  <p className="mt-1 text-xs text-slate-500">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              </div>

              <button
                onClick={(event) => {
                  event.stopPropagation();
                  removeFile();
                }}
                className="flex w-fit items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-slate-500 transition hover:bg-slate-800 hover:text-slate-200"
              >
                <X size={15} />
                Remove
              </button>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="mt-5 flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/5 p-4">
              <AlertTriangle
                size={18}
                className="mt-0.5 shrink-0 text-red-400"
              />

              <div>
                <p className="text-sm font-medium text-red-300">
                  Analysis error
                </p>

                <p className="mt-1 text-xs leading-relaxed text-red-300/70">
                  {error}
                </p>
              </div>
            </div>
          )}

          {/* Analyze button */}
          <div className="mt-6 flex justify-end">
            <button
              onClick={handleAnalyze}
              disabled={!selectedFile || loading}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-cyan-500 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {loading ? (
                <>
                  <Activity
                    size={17}
                    className="animate-pulse"
                  />
                  Analyzing Traffic...
                </>
              ) : (
                <>
                  <ShieldCheck size={17} />
                  Analyze Traffic
                </>
              )}
            </button>
          </div>

          {/* Information */}
          <div className="mt-8 grid gap-3 border-t border-slate-800 pt-6 sm:grid-cols-3">
            <div className="rounded-xl bg-slate-900/50 p-4">
              <p className="text-xs font-medium text-slate-300">
                AI Detection
              </p>

              <p className="mt-1 text-[11px] leading-relaxed text-slate-600">
  Deep Neural Network classification engine
</p>
            </div>

            <div className="rounded-xl bg-slate-900/50 p-4">
              <p className="text-xs font-medium text-slate-300">
                Risk Assessment
              </p>

              <p className="mt-1 text-[11px] leading-relaxed text-slate-600">
                Low, Medium, High and Critical risk levels
              </p>
            </div>

            <div className="rounded-xl bg-slate-900/50 p-4">
              <p className="text-xs font-medium text-slate-300">
                Incident Response
              </p>

              <p className="mt-1 text-[11px] leading-relaxed text-slate-600">
                Detected attacks are stored as incidents
              </p>
            </div>
          </div>
        </section>
      )}

      {/* ======================================================
          LOADING
      ====================================================== */}

      {loading && (
        <section className="rounded-2xl border border-cyan-500/10 bg-cyan-500/[0.03] p-6">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-500/10">
              <Activity
                size={21}
                className="animate-pulse text-cyan-400"
              />
            </div>

            <div>
              <p className="text-sm font-semibold text-white">
                SecureSense is analyzing the traffic...
              </p>

              <p className="mt-1 text-xs text-slate-500">
                The backend is processing the uploaded network-flow
                records.
              </p>
            </div>
          </div>

          <div className="mt-5 h-1.5 overflow-hidden rounded-full bg-slate-800">
            <div className="h-full w-1/2 animate-pulse rounded-full bg-cyan-400" />
          </div>
        </section>
      )}

      {/* ======================================================
          RESULTS
      ====================================================== */}

      {result && summary && (
        <>
          {/* Result header */}
          <section className="flex flex-col justify-between gap-4 rounded-2xl border border-slate-800 bg-[#0a0f1a] p-6 sm:flex-row sm:items-center">
            <div className="flex items-center gap-4">
              <div
                className={`flex h-12 w-12 items-center justify-center rounded-xl ${
                  summary.attack_flows > 0
                    ? "bg-red-500/10 text-red-400"
                    : "bg-emerald-500/10 text-emerald-400"
                }`}
              >
                {summary.attack_flows > 0 ? (
                  <ShieldAlert size={22} />
                ) : (
                  <ShieldCheck size={22} />
                )}
              </div>

              <div>
                <p className="text-xs font-medium uppercase tracking-[0.14em] text-slate-500">
                  Analysis Result
                </p>

                <h2 className="mt-1 text-xl font-semibold text-white">
                  {summary.overall_status}
                </h2>

                <p className="mt-1 text-xs text-slate-500">
                  File: {result.filename}
                </p>
              </div>
            </div>

            <button
              onClick={removeFile}
              className="inline-flex w-fit items-center gap-2 rounded-xl border border-slate-800 bg-slate-900 px-4 py-2.5 text-sm font-medium text-slate-300 transition hover:border-slate-700 hover:bg-slate-800"
            >
              <Upload size={16} />
              Analyze Another File
            </button>
          </section>

          {/* Summary cards */}
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <SummaryCard
              title="Total Flows"
              value={summary.total_flows}
              description="Network records analyzed"
              icon={FileSpreadsheet}
              iconClass="bg-cyan-500/10 text-cyan-400"
            />

            <SummaryCard
              title="Benign Flows"
              value={summary.benign_flows}
              description="Normal network activity"
              icon={ShieldCheck}
              iconClass="bg-emerald-500/10 text-emerald-400"
            />

            <SummaryCard
              title="Attack Flows"
              value={summary.attack_flows}
              description={`${summary.threat_rate}% threat rate`}
              icon={ShieldAlert}
              iconClass="bg-red-500/10 text-red-400"
            />

            <SummaryCard
              title="High / Critical"
              value={
                (summary.risk_distribution?.HIGH || 0) +
                (summary.risk_distribution?.CRITICAL || 0)
              }
              description="Priority security threats"
              icon={AlertTriangle}
              iconClass="bg-orange-500/10 text-orange-400"
            />
          </section>

          {/* Risk distribution */}
          <section className="grid gap-4 md:grid-cols-4">
            {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map(
              (risk) => (
                <div
                  key={risk}
                  className={`rounded-xl border p-4 ${getRiskClasses(
                    risk
                  )}`}
                >
                  <p className="text-[10px] font-semibold uppercase tracking-[0.15em]">
                    {risk}
                  </p>

                  <p className="mt-2 text-2xl font-semibold">
                    {summary.risk_distribution?.[risk] || 0}
                  </p>

                  <p className="mt-1 text-[11px] opacity-60">
                    Detected flows
                  </p>
                </div>
              )
            )}
          </section>

          {/* Results table */}
          <section className="rounded-2xl border border-slate-800 bg-[#0a0f1a]">
            <div className="flex flex-col justify-between gap-3 border-b border-slate-800 p-5 sm:flex-row sm:items-center">
              <div>
                <h2 className="font-semibold text-white">
                  Detection Results
                </h2>

                <p className="mt-1 text-xs text-slate-500">
                  Individual network-flow predictions from the AI
                  detection engine
                </p>
              </div>

              <span className="rounded-full border border-slate-800 bg-slate-900 px-3 py-1 text-[10px] font-medium uppercase tracking-wider text-slate-500">
                {results.length} Records
              </span>
            </div>

            <div className="overflow-x-auto">
              {results.length > 0 ? (
                <table className="w-full min-w-[800px] text-left">
                  <thead>
                    <tr className="border-b border-slate-800 text-[10px] uppercase tracking-wider text-slate-600">
                      <th className="px-5 py-3 font-medium">
                        Row
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
                        Incident
                      </th>

                      <th className="px-5 py-3 font-medium">
                        Details
                      </th>
                    </tr>
                  </thead>

                  <tbody>
                    {results.map((item, index) => {
                      const rowNumber =
                        item.row_number ??
                        item.row ??
                        index + 1;

                      const prediction =
                        item.prediction || "UNKNOWN";

                      const risk =
                        item.risk_level || "LOW";

                      const incident =
                        item.incident || null;

                      const isExpanded =
                        expandedRows[rowNumber];

                      return (
                        <tr
                          key={`${rowNumber}-${index}`}
                          className="border-b border-slate-800/60 last:border-0"
                        >
                          <td
                            colSpan="6"
                            className="p-0"
                          >
                            <div className="grid grid-cols-[80px_1fr_1fr_1fr_1.4fr_80px] items-center">
                              <div className="px-5 py-4 text-xs text-slate-500">
                                #{rowNumber}
                              </div>

                              <div className="px-5 py-4">
                                <span
                                  className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-semibold ${getPredictionClasses(
                                    prediction
                                  )}`}
                                >
                                  {prediction}
                                </span>
                              </div>

                              <div className="px-5 py-4 text-xs font-medium text-slate-300">
                                {formatConfidence(
                                  item.confidence
                                )}
                              </div>

                              <div className="px-5 py-4">
                                <span
                                  className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-semibold ${getRiskClasses(
                                    risk
                                  )}`}
                                >
                                  {risk}
                                </span>
                              </div>

                              <div className="px-5 py-4">
                                {incident ? (
                                  <div>
                                    <p className="text-xs font-medium text-slate-300">
                                      {incident.incident_id ||
                                        incident.id ||
                                        "Created"}
                                    </p>

                                    <p className="mt-1 text-[10px] text-slate-600">
                                      Incident created
                                    </p>
                                  </div>
                                ) : (
                                  <span className="text-xs text-slate-600">
                                    None
                                  </span>
                                )}
                              </div>

                              <div className="px-5 py-4">
                                <button
                                  onClick={() =>
                                    toggleRow(rowNumber)
                                  }
                                  className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-800 hover:text-slate-200"
                                >
                                  {isExpanded ? (
                                    <ChevronUp size={16} />
                                  ) : (
                                    <ChevronDown size={16} />
                                  )}
                                </button>
                              </div>
                            </div>

                            {isExpanded && (
                              <div className="border-t border-slate-800 bg-slate-950/40 px-5 py-4">
                                <div className="grid gap-4 sm:grid-cols-3">
                                  <div>
                                    <p className="text-[10px] uppercase tracking-wider text-slate-600">
                                      Prediction
                                    </p>

                                    <p className="mt-1 text-sm text-slate-300">
                                      {prediction}
                                    </p>
                                  </div>

                                  <div>
                                    <p className="text-[10px] uppercase tracking-wider text-slate-600">
                                      Confidence
                                    </p>

                                    <p className="mt-1 text-sm text-slate-300">
                                      {formatConfidence(
                                        item.confidence
                                      )}
                                    </p>
                                  </div>

                                  <div>
                                    <p className="text-[10px] uppercase tracking-wider text-slate-600">
                                      Risk Level
                                    </p>

                                    <p className="mt-1 text-sm text-slate-300">
                                      {risk}
                                    </p>
                                  </div>
                                </div>

                                {incident && (
                                  <div className="mt-4 rounded-xl border border-red-500/10 bg-red-500/[0.03] p-4">
                                    <p className="text-xs font-medium text-red-300">
                                      Incident generated
                                    </p>

                                    <p className="mt-1 text-xs text-slate-500">
                                      {incident.incident_id ||
                                        incident.id}
                                    </p>
                                  </div>
                                )}
                              </div>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              ) : (
                <div className="p-10 text-center text-sm text-slate-500">
                  No prediction results returned.
                </div>
              )}
            </div>
          </section>
        </>
      )}
    </div>
  );
}