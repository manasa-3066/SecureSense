import { useEffect, useMemo, useState } from "react";

import {

  Activity,

  AlertTriangle,

  CheckCircle2,

  Clock3,

  Database,

  RefreshCw,

  ShieldAlert,

  ShieldCheck,


  Zap,

} from "lucide-react";



import {

  Area,

  AreaChart,

  CartesianGrid,

  Cell,

  Pie,

  PieChart,

  ResponsiveContainer,

  Tooltip,

  XAxis,

  YAxis,

} from "recharts";



import { getIncidents, getModelInfo } from "../services/api";



/* ============================================================

   HELPERS

\============================================================ */



function formatDate(timestamp) {

  if (!timestamp) return "—";



  const date = new Date(timestamp);



  if (Number.isNaN(date.getTime())) {

    return "—";

  }



  return date.toLocaleString("en-IN", {

    day: "2-digit",

    month: "short",

    year: "numeric",

    hour: "2-digit",

    minute: "2-digit",

  });

}



function formatShortDate(timestamp) {

  if (!timestamp) return "";



  const date = new Date(timestamp);



  if (Number.isNaN(date.getTime())) {

    return "";

  }



  return date.toLocaleDateString("en-IN", {

    day: "2-digit",

    month: "short",

  });

}



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



function getStatusClasses(status) {

  if (status === "OPEN") {

    return "border-red-500/20 bg-red-500/10 text-red-300";

  }



  if (status === "RESOLVED") {

    return "border-emerald-500/20 bg-emerald-500/10 text-emerald-300";

  }



  return "border-slate-700 bg-slate-800/50 text-slate-400";

}



/* ============================================================

   STAT CARD

\============================================================ */



function StatCard({

  title,

  value,

  description,

  icon: Icon,

  iconClass,

}) {

  return (

    <div className="group relative overflow-hidden rounded-2xl border border-slate-800 bg-[#0a0f1a] p-5 transition-all duration-300 hover:border-slate-700 hover:bg-[#0c1220]">

      <div className="absolute right-0 top-0 h-24 w-24 rounded-full bg-cyan-500/5 blur-3xl transition-all group-hover:bg-cyan-500/10" />



      <div className="relative">

        <div className="flex items-start justify-between">

          <div>

            <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">

              {title}

            </p>



            <p className="mt-3 text-3xl font-semibold tracking-tight text-white">

              {value}

            </p>

          </div>



          <div

            className={`flex h-11 w-11 items-center justify-center rounded-xl ${iconClass}`}

          >

            <Icon size={20} />

          </div>

        </div>



        <p className="mt-4 text-xs text-slate-500">

          {description}

        </p>

      </div>

    </div>

  );

}



/* ============================================================

   DASHBOARD

\============================================================ */



export default function Dashboard() {

  const [incidents, setIncidents] = useState([]);

  const [modelInfo, setModelInfo] = useState(null);



  const [loading, setLoading] = useState(true);

  const [refreshing, setRefreshing] = useState(false);

  const [error, setError] = useState("");



  async function loadDashboard(showRefresh = false) {

    try {

      setError("");



      if (showRefresh) {

        setRefreshing(true);

      } else {

        setLoading(true);

      }



      const [incidentResponse, modelResponse] =

        await Promise.all([

          getIncidents(),

          getModelInfo(),

        ]);



      const incidentList =

        Array.isArray(incidentResponse?.incidents)

          ? incidentResponse.incidents

          : [];



      setIncidents(incidentList);

      setModelInfo(modelResponse);

    } catch (err) {

      console.error("Dashboard loading error:", err);



      setError(

        "Unable to load security data from the SecureSense backend."

      );

    } finally {

      setLoading(false);

      setRefreshing(false);

    }

  }



  useEffect(() => {

    loadDashboard();

  }, []);



  /* ==========================================================

     DERIVED METRICS

  ========================================================== */



  const metrics = useMemo(() => {

    const total = incidents.length;



    const active = incidents.filter(

      (incident) => incident.status === "OPEN"

    ).length;



    const resolved = incidents.filter(

      (incident) => incident.status === "RESOLVED"

    ).length;



    const high = incidents.filter(

      (incident) => incident.risk_level === "HIGH"

    ).length;



    const critical = incidents.filter(

      (incident) => incident.risk_level === "CRITICAL"

    ).length;



    return {

      total,

      active,

      resolved,

      high,

      critical,

      serious: high + critical,

    };

  }, [incidents]);



  /* ==========================================================

     RISK DISTRIBUTION

  ========================================================== */



  const riskData = useMemo(() => {

    const counts = {

      LOW: 0,

      MEDIUM: 0,

      HIGH: 0,

      CRITICAL: 0,

    };



    incidents.forEach((incident) => {

      if (counts[incident.risk_level] !== undefined) {

        counts[incident.risk_level] += 1;

      }

    });



    return [

      {

        name: "Low",

        value: counts.LOW,

        color: "#10b981",

      },

      {

        name: "Medium",

        value: counts.MEDIUM,

        color: "#f59e0b",

      },

      {

        name: "High",

        value: counts.HIGH,

        color: "#f97316",

      },

      {

        name: "Critical",

        value: counts.CRITICAL,

        color: "#ef4444",

      },

    ];

  }, [incidents]);



  /* ==========================================================

     STATUS DISTRIBUTION

  ========================================================== */



  const statusData = useMemo(() => {

    return [

      {

        name: "Open",

        value: metrics.active,

      },

      {

        name: "Resolved",

        value: metrics.resolved,

      },

    ];

  }, [metrics]);



  /* ==========================================================

     THREAT ACTIVITY

  ========================================================== */



  const activityData = useMemo(() => {

    const grouped = {};



    incidents.forEach((incident) => {

      const key = formatShortDate(incident.timestamp);



      if (!key) return;



      if (!grouped[key]) {

        grouped[key] = {

          date: key,

          attacks: 0,

        };

      }



      grouped[key].attacks += 1;

    });



    return Object.values(grouped).slice(-7);

  }, [incidents]);



  /* ==========================================================

     RECENT INCIDENTS

  ========================================================== */



  const recentIncidents = useMemo(() => {

    return [...incidents]

      .sort(

        (a, b) =>

          new Date(b.timestamp) - new Date(a.timestamp)

      )

      .slice(0, 6);

  }, [incidents]);



  /* ==========================================================

     LOADING STATE

  ========================================================== */



  if (loading) {

    return (

      <div className="space-y-6">

        <div>

          <div className="h-4 w-32 animate-pulse rounded bg-slate-800" />



          <div className="mt-3 h-9 w-72 animate-pulse rounded bg-slate-800" />



          <div className="mt-3 h-4 w-96 max-w-full animate-pulse rounded bg-slate-800" />

        </div>



        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">

          {[1, 2, 3, 4].map((item) => (

            <div

              key={item}

              className="h-36 animate-pulse rounded-2xl border border-slate-800 bg-[#0a0f1a]"

            />

          ))}

        </div>



        <div className="grid gap-6 xl:grid-cols-3">

          <div className="h-80 animate-pulse rounded-2xl border border-slate-800 bg-[#0a0f1a] xl:col-span-2" />



          <div className="h-80 animate-pulse rounded-2xl border border-slate-800 bg-[#0a0f1a]" />

        </div>

      </div>

    );

  }



  /* ==========================================================

     ERROR STATE

  ========================================================== */



  if (error) {

    return (

      <div className="flex min-h-[60vh] items-center justify-center">

        <div className="max-w-md rounded-2xl border border-red-500/20 bg-red-500/5 p-8 text-center">

          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-red-500/10 text-red-400">

            <ShieldAlert size={22} />

          </div>



          <h2 className="mt-5 text-lg font-semibold text-white">

            Security data unavailable

          </h2>



          <p className="mt-2 text-sm leading-relaxed text-slate-400">

            {error}

          </p>



          <button

            onClick={() => loadDashboard()}

            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-cyan-500 px-4 py-2.5 text-sm font-medium text-slate-950 transition hover:bg-cyan-400"

          >

            <RefreshCw size={16} />

            Retry connection

          </button>

        </div>

      </div>

    );

  }



  /* ==========================================================

     MAIN DASHBOARD

  ========================================================== */



  return (

    <div className="space-y-6">

      {/* ======================================================

          PAGE HEADER

      ====================================================== */}



      <section className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">

        <div>

          <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.16em] text-cyan-400">

            <Activity size={14} />

            Security Overview

          </div>



          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">

            Security Dashboard

          </h1>



          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">

            Monitor detected threats, investigate active incidents,

            and track the current SecureSense security posture.

          </p>

        </div>



        <button

          onClick={() => loadDashboard(true)}

          disabled={refreshing}

          className="inline-flex w-fit items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/70 px-4 py-2.5 text-sm font-medium text-slate-300 transition hover:border-slate-700 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"

        >

          <RefreshCw

            size={16}

            className={refreshing ? "animate-spin" : ""}

          />



          {refreshing ? "Refreshing..." : "Refresh"}

        </button>

      </section>



      {/* ======================================================

          STAT CARDS

      ====================================================== */}



      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">

        <StatCard

          title="Total Incidents"

          value={metrics.total}

          description="Detected attack incidents stored in MongoDB"

          icon={ShieldAlert}

          iconClass="bg-red-500/10 text-red-400"

        />



        <StatCard

          title="Active Incidents"

          value={metrics.active}

          description="Incidents currently requiring attention"

          icon={AlertTriangle}

          iconClass="bg-orange-500/10 text-orange-400"

        />



        <StatCard

          title="Resolved Incidents"

          value={metrics.resolved}

          description="Incidents marked as resolved"

          icon={CheckCircle2}

          iconClass="bg-emerald-500/10 text-emerald-400"

        />



        <StatCard

          title="High / Critical"

          value={metrics.serious}

          description={`${metrics.high} high • ${metrics.critical} critical`}

          icon={Zap}

          iconClass="bg-amber-500/10 text-amber-400"

        />

      </section>



      {/* ======================================================
          MODEL STATUS
      ====================================================== */}

      <section className="rounded-2xl border border-cyan-500/10 bg-gradient-to-r from-cyan-500/[0.04] to-transparent p-5">
        <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-center">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-400/10">
              <Activity size={22} />
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-slate-500">Detection Engine</p>
              <h2 className="mt-1 text-lg font-semibold text-white">{modelInfo?.model || "Deep Neural Network"}</h2>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div><p className="text-[11px] uppercase tracking-wider text-slate-600">Architecture</p><p className="mt-1 text-sm font-semibold text-slate-200">{modelInfo?.architecture || "MLP / DNN"}</p></div>
            <div><p className="text-[11px] uppercase tracking-wider text-slate-600">Features</p><p className="mt-1 text-sm font-semibold text-slate-200">{modelInfo?.number_of_features ?? "69"}</p></div>
            <div><p className="text-[11px] uppercase tracking-wider text-slate-600">Threshold</p><p className="mt-1 text-sm font-semibold text-slate-200">{modelInfo?.decision_threshold ?? "0.41"}</p></div>
            <div><p className="text-[11px] uppercase tracking-wider text-slate-600">Status</p><div className="mt-1 flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-emerald-400" /><span className="text-sm font-semibold text-emerald-300">{modelInfo?.status || "Loaded"}</span></div></div>
          </div>
        </div>
      </section>

      



      <section className="grid gap-6 xl:grid-cols-3">

        {/* Activity */}

        <div className="rounded-2xl border border-slate-800 bg-[#0a0f1a] p-5 xl:col-span-2">

          <div className="flex items-start justify-between">

            <div>

              <h2 className="font-semibold text-white">

                Threat Activity

              </h2>



              <p className="mt-1 text-xs text-slate-500">

                Detected incidents over recent activity periods

              </p>

            </div>



            <div className="rounded-lg bg-cyan-500/10 p-2 text-cyan-400">

              <Activity size={17} />

            </div>

          </div>



          <div className="mt-6 h-64">

            {activityData.length > 0 ? (

              <ResponsiveContainer width="100%" height="100%">

                <AreaChart data={activityData}>

                  <defs>

                    <linearGradient

                      id="threatGradient"

                      x1="0"

                      y1="0"

                      x2="0"

                      y2="1"

                    >

                      <stop

                        offset="0%"

                        stopColor="#22d3ee"

                        stopOpacity={0.25}

                      />



                      <stop

                        offset="100%"

                        stopColor="#22d3ee"

                        stopOpacity={0}

                      />

                    </linearGradient>

                  </defs>



                  <CartesianGrid

                    stroke="#1e293b"

                    strokeDasharray="3 3"

                    vertical={false}

                  />



                  <XAxis

                    dataKey="date"

                    tick={{

                      fill: "#64748b",

                      fontSize: 11,

                    }}

                    axisLine={false}

                    tickLine={false}

                  />



                  <YAxis

                    allowDecimals={false}

                    tick={{

                      fill: "#64748b",

                      fontSize: 11,

                    }}

                    axisLine={false}

                    tickLine={false}

                  />



                  <Tooltip

                    contentStyle={{

                      backgroundColor: "#0f172a",

                      border: "1px solid #1e293b",

                      borderRadius: "12px",

                      color: "#e2e8f0",

                    }}

                  />



                  <Area

                    type="monotone"

                    dataKey="attacks"

                    stroke="#22d3ee"

                    strokeWidth={2}

                    fill="url(#threatGradient)"

                  />

                </AreaChart>

              </ResponsiveContainer>

            ) : (

              <div className="flex h-full items-center justify-center rounded-xl border border-dashed border-slate-800">

                <div className="text-center">

                  <Clock3 className="mx-auto h-7 w-7 text-slate-700" />



                  <p className="mt-3 text-sm text-slate-500">

                    No incident activity available yet

                  </p>

                </div>

              </div>

            )}

          </div>

        </div>



        {/* Risk */}

        <div className="rounded-2xl border border-slate-800 bg-[#0a0f1a] p-5">

          <div>

            <h2 className="font-semibold text-white">

              Risk Distribution

            </h2>



            <p className="mt-1 text-xs text-slate-500">

              Current incident severity

            </p>

          </div>



          <div className="relative mt-4 h-56">

            {incidents.length > 0 ? (

              <>

                <ResponsiveContainer width="100%" height="100%">

                  <PieChart>

                    <Pie

                      data={riskData}

                      dataKey="value"

                      nameKey="name"

                      cx="50%"

                      cy="50%"

                      innerRadius={58}

                      outerRadius={82}

                      paddingAngle={3}

                    >

                      {riskData.map((entry) => (

                        <Cell

                          key={entry.name}

                          fill={entry.color}

                        />

                      ))}

                    </Pie>



                    <Tooltip

                      contentStyle={{

                        backgroundColor: "#0f172a",

                        border: "1px solid #1e293b",

                        borderRadius: "12px",

                        color: "#e2e8f0",

                      }}

                    />

                  </PieChart>

                </ResponsiveContainer>



                <div className="pointer-events-none absolute inset-0 flex items-center justify-center">

                  <div className="text-center">

                    <p className="text-2xl font-semibold text-white">

                      {incidents.length}

                    </p>



                    <p className="text-[10px] uppercase tracking-wider text-slate-500">

                      Incidents

                    </p>

                  </div>

                </div>

              </>

            ) : (

              <div className="flex h-full items-center justify-center">

                <div className="text-center">

                  <ShieldCheck className="mx-auto h-8 w-8 text-slate-700" />



                  <p className="mt-3 text-sm text-slate-500">

                    No incidents recorded

                  </p>

                </div>

              </div>

            )}

          </div>



          <div className="space-y-2">

            {riskData.map((risk) => (

              <div

                key={risk.name}

                className="flex items-center justify-between"

              >

                <div className="flex items-center gap-2">

                  <span

                    className="h-2.5 w-2.5 rounded-full"

                    style={{

                      backgroundColor: risk.color,

                    }}

                  />



                  <span className="text-xs text-slate-400">

                    {risk.name}

                  </span>

                </div>



                <span className="text-xs font-semibold text-slate-200">

                  {risk.value}

                </span>

              </div>

            ))}

          </div>

        </div>

      </section>



      {/* ======================================================

          INCIDENT STATUS + DATABASE

      ====================================================== */}



      <section className="grid gap-6 lg:grid-cols-3">

        <div className="rounded-2xl border border-slate-800 bg-[#0a0f1a] p-5">

          <div className="flex items-center gap-3">

            <div className="rounded-lg bg-slate-800 p-2 text-slate-300">

              <Database size={17} />

            </div>



            <div>

              <h2 className="font-semibold text-white">

                Incident Status

              </h2>



              <p className="text-xs text-slate-500">

                MongoDB-backed incident lifecycle

              </p>

            </div>

          </div>



          <div className="mt-6 space-y-4">

            <div>

              <div className="mb-2 flex justify-between text-xs">

                <span className="text-slate-400">

                  Open

                </span>



                <span className="font-medium text-red-300">

                  {metrics.active}

                </span>

              </div>



              <div className="h-2 overflow-hidden rounded-full bg-slate-800">

                <div

                  className="h-full rounded-full bg-red-400 transition-all"

                  style={{

                    width:

                      metrics.total > 0

                        ? `${(metrics.active / metrics.total) * 100}%`

                        : "0%",

                  }}

                />

              </div>

            </div>



            <div>

              <div className="mb-2 flex justify-between text-xs">

                <span className="text-slate-400">

                  Resolved

                </span>



                <span className="font-medium text-emerald-300">

                  {metrics.resolved}

                </span>

              </div>



              <div className="h-2 overflow-hidden rounded-full bg-slate-800">

                <div

                  className="h-full rounded-full bg-emerald-400 transition-all"

                  style={{

                    width:

                      metrics.total > 0

                        ? `${(metrics.resolved / metrics.total) * 100}%`

                        : "0%",

                  }}

                />

              </div>

            </div>

          </div>

        </div>



        {/* Recent incidents */}

        <div className="rounded-2xl border border-slate-800 bg-[#0a0f1a] p-5 lg:col-span-2">

          <div className="flex items-center justify-between">

            <div>

              <h2 className="font-semibold text-white">

                Recent Incidents

              </h2>



              <p className="mt-1 text-xs text-slate-500">

                Latest detected security incidents

              </p>

            </div>



            <span className="rounded-full border border-slate-800 bg-slate-900 px-3 py-1 text-[10px] font-medium uppercase tracking-wider text-slate-500">

              Live Data

            </span>

          </div>



          <div className="mt-5 overflow-x-auto">

            {recentIncidents.length > 0 ? (

              <table className="w-full min-w-[650px] text-left">

                <thead>

                  <tr className="border-b border-slate-800 text-[10px] uppercase tracking-wider text-slate-600">

                    <th className="pb-3 font-medium">

                      Incident

                    </th>



                    <th className="pb-3 font-medium">

                      Threat

                    </th>



                    <th className="pb-3 font-medium">

                      Risk

                    </th>



                    <th className="pb-3 font-medium">

                      Confidence

                    </th>



                    <th className="pb-3 font-medium">

                      Status

                    </th>

                  </tr>

                </thead>



                <tbody>

                  {recentIncidents.map((incident) => (

                    <tr

                      key={incident.incident_id}

                      className="border-b border-slate-800/60 last:border-0"

                    >

                      <td className="py-4">

                        <div>

                          <p className="text-xs font-medium text-slate-200">

                            {incident.incident_id}

                          </p>



                          <p className="mt-1 text-[10px] text-slate-600">

                            {formatDate(incident.timestamp)}

                          </p>

                        </div>

                      </td>



                      <td className="py-4">

                        <span className="inline-flex items-center gap-1.5 text-xs font-medium text-red-300">

                          <span className="h-1.5 w-1.5 rounded-full bg-red-400" />

                          {incident.prediction || "ATTACK"}

                        </span>

                      </td>



                      <td className="py-4">

                        <span

                          className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-semibold ${getRiskClasses(

                            incident.risk_level

                          )}`}

                        >

                          {incident.risk_level}

                        </span>

                      </td>



                      <td className="py-4 text-xs font-medium text-slate-300">

                        {incident.confidence != null

                          ? `${incident.confidence}%`

                          : "—"}

                      </td>



                      <td className="py-4">

                        <span

                          className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-semibold ${getStatusClasses(

                            incident.status

                          )}`}

                        >

                          {incident.status}

                        </span>

                      </td>

                    </tr>

                  ))}

                </tbody>

              </table>

            ) : (

              <div className="flex min-h-40 items-center justify-center rounded-xl border border-dashed border-slate-800">

                <div className="text-center">

                  <ShieldCheck className="mx-auto h-7 w-7 text-slate-700" />



                  <p className="mt-3 text-sm text-slate-500">

                    No security incidents available

                  </p>



                  <p className="mt-1 text-xs text-slate-600">

                    Analyze network traffic to generate incidents.

                  </p>

                </div>

              </div>

            )}

          </div>

        </div>

      </section>

    </div>

  );

}