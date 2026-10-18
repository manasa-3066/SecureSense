// import { useEffect, useState } from "react";
// import {
//   Activity,
//   CheckCircle2,
//   Database,
//   Cpu,
//   RefreshCw,
//   Server,
//   Shield,
//   SlidersHorizontal,
//   Wifi,
//   AlertTriangle,
// } from "lucide-react";

// import { getHealth, getModelInfo } from "../services/api";

// export default function Settings() {
//   const [health, setHealth] = useState(null);
//   const [model, setModel] = useState(null);
//   const [loading, setLoading] = useState(true);
//   const [refreshing, setRefreshing] = useState(false);
//   const [error, setError] = useState("");

//   async function loadSystemInfo(showRefresh = false) {
//     try {
//       if (showRefresh) {
//         setRefreshing(true);
//       } else {
//         setLoading(true);
//       }

//       setError("");

//       const [healthData, modelData] = await Promise.all([
//         getHealth(),
//         getModelInfo(),
//       ]);

//       setHealth(healthData);
//       setModel(modelData);
//     } catch (err) {
//       console.error("Settings loading error:", err);

//       setError(
//         err?.response?.data?.detail ||
//           "Unable to retrieve system information."
//       );
//     } finally {
//       setLoading(false);
//       setRefreshing(false);
//     }
//   }

//   useEffect(() => {
//     loadSystemInfo();
//   }, []);

//   if (loading) {
//     return (
//       <div className="flex min-h-[70vh] items-center justify-center">
//         <div className="text-center">
//           <RefreshCw className="mx-auto mb-4 h-8 w-8 animate-spin text-cyan-400" />

//           <p className="text-sm font-medium text-slate-300">
//             Loading system configuration...
//           </p>

//           <p className="mt-1 text-xs text-slate-500">
//             Checking SecureSense services
//           </p>
//         </div>
//       </div>
//     );
//   }

//   return (
//     <div className="space-y-6">
//       {/* Header */}
//       <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
//         <div>
//           <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-400">
//             <SlidersHorizontal className="h-4 w-4" />
//             System Configuration
//           </div>

//           <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
//             Settings
//           </h1>

//           <p className="mt-2 max-w-2xl text-sm text-slate-400">
//             Monitor SecureSense services, model configuration,
//             database connectivity, and detection settings.
//           </p>
//         </div>

//         <button
//           onClick={() => loadSystemInfo(true)}
//           disabled={refreshing}
//           className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm font-medium text-slate-200 transition hover:border-cyan-500/40 hover:text-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
//         >
//           <RefreshCw
//             className={`h-4 w-4 ${
//               refreshing ? "animate-spin" : ""
//             }`}
//           />
//           Refresh Status
//         </button>
//       </div>

//       {/* Error */}
//       {error && (
//         <div className="flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/5 p-4">
//           <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-400" />

//           <div>
//             <p className="text-sm font-medium text-red-300">
//               System information unavailable
//             </p>

//             <p className="mt-1 text-xs text-slate-500">
//               {error}
//             </p>
//           </div>
//         </div>
//       )}

//       {/* System status */}
//       <section>
//         <SectionHeader
//           icon={Activity}
//           title="System Status"
//           description="Live connectivity status of SecureSense services"
//         />

//         <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
//           <StatusCard
//             icon={Server}
//             title="FastAPI Backend"
//             status={
//               health?.status === "healthy" ||
//               health?.status === "ok"
//                 ? "ONLINE"
//                 : "OFFLINE"
//             }
//             detail="API service"
//             online={
//               health?.status === "healthy" ||
//               health?.status === "ok"
//             }
//           />

//           <StatusCard
//             icon={Database}
//             title="MongoDB"
//             status={
//               health?.database === "connected" ||
//               health?.mongodb === "connected" ||
//               health?.database_status === "connected"
//                 ? "CONNECTED"
//                 : "CHECKING"
//             }
//             detail="Incident persistence"
//             online={
//               health?.database === "connected" ||
//               health?.mongodb === "connected" ||
//               health?.database_status === "connected"
//             }
//           />

//           <StatusCard
//             icon={Cpu}
//             title="ML Detection Engine"
//             status={model ? "READY" : "UNAVAILABLE"}
//             detail="Random Forest classifier"
//             online={Boolean(model)}
//           />
//         </div>
//       </section>

//       {/* Model information */}
//       <section className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5">
//         <SectionHeader
//           icon={Cpu}
//           title="Machine Learning Model"
//           description="Current SecureSense threat detection configuration"
//         />

//         <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
//           <InfoCard
//             label="Model Type"
//             value={
//               model?.model_type ||
//               model?.model ||
//               "Random Forest"
//             }
//           />

//           <InfoCard
//             label="Trees"
//             value={
//               model?.n_estimators ||
//               model?.trees ||
//               model?.number_of_trees ||
//               "150"
//             }
//           />

//           <InfoCard
//             label="Features"
//             value={
//               model?.n_features ||
//               model?.features ||
//               model?.number_of_features ||
//               "69"
//             }
//           />

//           <InfoCard
//             label="Status"
//             value="Production Ready"
//             valueClass="text-emerald-400"
//           />
//         </div>
//       </section>

//       {/* Detection configuration */}
//       <section className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5">
//         <SectionHeader
//           icon={Shield}
//           title="Detection Configuration"
//           description="How SecureSense classifies and prioritizes detected events"
//         />

//         <div className="mt-5 space-y-3">
//           <ConfigurationRow
//             label="Detection Type"
//             value="Binary Classification"
//             description="BENIGN vs ATTACK"
//           />

//           <ConfigurationRow
//             label="Primary Classifier"
//             value="Random Forest"
//             description="150 decision trees"
//           />

//           <ConfigurationRow
//             label="Feature Count"
//             value="69"
//             description="Network-flow features"
//           />

//           <ConfigurationRow
//             label="Class Weighting"
//             value="Balanced"
//             description="Used during model training"
//           />

//           <ConfigurationRow
//             label="Persistence"
//             value="MongoDB"
//             description="Incident records are stored persistently"
//           />
//         </div>
//       </section>

//       {/* Risk levels */}
//       <section>
//         <SectionHeader
//           icon={AlertTriangle}
//           title="Risk Classification"
//           description="Operational interpretation used by SecureSense"
//         />

//         <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
//           <RiskCard
//             level="LOW"
//             description="Normal or benign activity"
//             className="border-emerald-500/20 bg-emerald-500/5 text-emerald-400"
//           />

//           <RiskCard
//             level="MEDIUM"
//             description="Activity requiring monitoring"
//             className="border-yellow-500/20 bg-yellow-500/5 text-yellow-400"
//           />

//           <RiskCard
//             level="HIGH"
//             description="Suspicious activity requiring attention"
//             className="border-orange-500/20 bg-orange-500/5 text-orange-400"
//           />

//           <RiskCard
//             level="CRITICAL"
//             description="Highest-priority detected threat"
//             className="border-red-500/20 bg-red-500/5 text-red-400"
//           />
//         </div>
//       </section>

//       {/* Application information */}
//       <section className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5">
//         <SectionHeader
//           icon={Wifi}
//           title="Application Information"
//           description="SecureSense platform configuration"
//         />

//         <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
//           <InfoCard
//             label="Application"
//             value="SecureSense"
//           />

//           <InfoCard
//             label="Platform"
//             value="AI-Based Cyber Threat Detection"
//           />

//           <InfoCard
//             label="Frontend"
//             value="React"
//           />

//           <InfoCard
//             label="Backend"
//             value="FastAPI"
//           />

//           <InfoCard
//             label="Database"
//             value="MongoDB"
//           />

//           <InfoCard
//             label="Detection Model"
//             value="Random Forest"
//           />
//         </div>
//       </section>

//       {/* Footer */}
//       <div className="rounded-xl border border-slate-800 bg-slate-950/40 px-5 py-4">
//         <div className="flex flex-col gap-2 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
//           <span>
//             SecureSense • AI-Based Cyber Threat Detection and
//             Incident Response Platform
//           </span>

//           <span className="flex items-center gap-2">
//             <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
//             System monitoring enabled
//           </span>
//         </div>
//       </div>
//     </div>
//   );
// }

// function SectionHeader({
//   icon: Icon,
//   title,
//   description,
// }) {
//   return (
//     <div className="flex items-start gap-3">
//       <div className="rounded-lg bg-slate-900 p-2 text-cyan-400">
//         <Icon className="h-4 w-4" />
//       </div>

//       <div>
//         <h2 className="text-sm font-semibold text-white">
//           {title}
//         </h2>

//         <p className="mt-1 text-xs text-slate-500">
//           {description}
//         </p>
//       </div>
//     </div>
//   );
// }

// function StatusCard({
//   icon: Icon,
//   title,
//   status,
//   detail,
//   online,
// }) {
//   return (
//     <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5">
//       <div className="flex items-start justify-between">
//         <div className="rounded-xl bg-slate-900 p-3 text-cyan-400">
//           <Icon className="h-5 w-5" />
//         </div>

//         <span
//           className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-semibold ${
//             online
//               ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400"
//               : "border-yellow-500/20 bg-yellow-500/10 text-yellow-400"
//           }`}
//         >
//           <span
//             className={`h-1.5 w-1.5 rounded-full ${
//               online
//                 ? "bg-emerald-400"
//                 : "bg-yellow-400"
//             }`}
//           />

//           {status}
//         </span>
//       </div>

//       <h3 className="mt-5 text-sm font-semibold text-white">
//         {title}
//       </h3>

//       <p className="mt-1 text-xs text-slate-500">
//         {detail}
//       </p>
//     </div>
//   );
// }

// function InfoCard({
//   label,
//   value,
//   valueClass = "text-slate-200",
// }) {
//   return (
//     <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
//       <p className="text-[11px] font-medium uppercase tracking-wider text-slate-500">
//         {label}
//       </p>

//       <p
//         className={`mt-2 text-sm font-semibold ${valueClass}`}
//       >
//         {value}
//       </p>
//     </div>
//   );
// }

// function ConfigurationRow({
//   label,
//   value,
//   description,
// }) {
//   return (
//     <div className="flex flex-col gap-2 rounded-xl border border-slate-800 bg-slate-900/30 p-4 sm:flex-row sm:items-center sm:justify-between">
//       <div>
//         <p className="text-sm font-medium text-slate-200">
//           {label}
//         </p>

//         <p className="mt-1 text-xs text-slate-500">
//           {description}
//         </p>
//       </div>

//       <span className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-medium text-cyan-400">
//         {value}
//       </span>
//     </div>
//   );
// }

// function RiskCard({
//   level,
//   description,
//   className,
// }) {
//   return (
//     <div className={`rounded-2xl border p-5 ${className}`}>
//       <p className="text-xs font-bold tracking-[0.15em]">
//         {level}
//       </p>

//       <p className="mt-3 text-xs leading-5 text-slate-400">
//         {description}
//       </p>
//     </div>
//   );
// }

import { useEffect, useState } from "react";

import {

  Activity,

  CheckCircle2,

  Database,

  Cpu,

  RefreshCw,

  Server,

  Shield,

  SlidersHorizontal,

  Wifi,

  AlertTriangle,

} from "lucide-react";



import { getHealth, getModelInfo } from "../services/api";



export default function Settings() {

  const [health, setHealth] = useState(null);

  const [model, setModel] = useState(null);

  const [loading, setLoading] = useState(true);

  const [refreshing, setRefreshing] = useState(false);

  const [error, setError] = useState("");



  async function loadSystemInfo(showRefresh = false) {

    try {

      if (showRefresh) {

        setRefreshing(true);

      } else {

        setLoading(true);

      }



      setError("");



      const [healthData, modelData] = await Promise.all([

        getHealth(),

        getModelInfo(),

      ]);



      setHealth(healthData);

      setModel(modelData);

    } catch (err) {

      console.error("Settings loading error:", err);



      setError(

        err?.response?.data?.detail ||

          "Unable to retrieve system information."

      );

    } finally {

      setLoading(false);

      setRefreshing(false);

    }

  }



  useEffect(() => {

    loadSystemInfo();

  }, []);



  if (loading) {

    return (

      <div className="flex min-h-[70vh] items-center justify-center">

        <div className="text-center">

          <RefreshCw className="mx-auto mb-4 h-8 w-8 animate-spin text-cyan-400" />



          <p className="text-sm font-medium text-slate-300">

            Loading system configuration...

          </p>



          <p className="mt-1 text-xs text-slate-500">

            Checking SecureSense services

          </p>

        </div>

      </div>

    );

  }



  return (

    <div className="space-y-6">

      {/* Header */}

      <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">

        <div>

          <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-400">

            <SlidersHorizontal className="h-4 w-4" />

            System Configuration

          </div>



          <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">

            Settings

          </h1>



          <p className="mt-2 max-w-2xl text-sm text-slate-400">

            Monitor SecureSense services, model configuration,

            database connectivity, and detection settings.

          </p>

        </div>



        <button

          onClick={() => loadSystemInfo(true)}

          disabled={refreshing}

          className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm font-medium text-slate-200 transition hover:border-cyan-500/40 hover:text-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"

        >

          <RefreshCw

            className={`h-4 w-4 ${

              refreshing ? "animate-spin" : ""

            }`}

          />

          Refresh Status

        </button>

      </div>



      {/* Error */}

      {error && (

        <div className="flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/5 p-4">

          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-400" />



          <div>

            <p className="text-sm font-medium text-red-300">

              System information unavailable

            </p>



            <p className="mt-1 text-xs text-slate-500">

              {error}

            </p>

          </div>

        </div>

      )}



      {/* System status */}

      <section>

        <SectionHeader

          icon={Activity}

          title="System Status"

          description="Live connectivity status of SecureSense services"

        />



        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">

          <StatusCard

            icon={Server}

            title="FastAPI Backend"

            status={

              health?.status === "healthy" ||

              health?.status === "ok"

                ? "ONLINE"

                : "OFFLINE"

            }

            detail="API service"

            online={

              health?.status === "healthy" ||

              health?.status === "ok"

            }

          />



          <StatusCard

            icon={Database}

            title="MongoDB"

            status={

              health?.database === "connected" ||

              health?.mongodb === "connected" ||

              health?.database_status === "connected"

                ? "CONNECTED"

                : "CHECKING"

            }

            detail="Incident persistence"

            online={

              health?.database === "connected" ||

              health?.mongodb === "connected" ||

              health?.database_status === "connected"

            }

          />



          <StatusCard

            icon={Cpu}

            title="ML Detection Engine"

            status={model ? "READY" : "UNAVAILABLE"}

            detail="Deep Neural Network (DNN)"

            online={Boolean(model)}

          />

        </div>

      </section>



      {/* Model information */}

      <section className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5">

        <SectionHeader

          icon={Cpu}

          title="Machine Learning Model"

          description="Current SecureSense threat detection configuration"

        />



        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">

        <InfoCard
  label="Model Type"
  value={
    model?.model_type ||
    model?.model ||
    "Deep Neural Network"
  }
/>

<InfoCard
  label="Architecture"
  value="MLP / DNN"
/>

<InfoCard
  label="Features"
  value={
    model?.n_features ||
    model?.features ||
    model?.number_of_features ||
    "69"
  }
/>

<InfoCard
  label="Status"
  value="Production Ready"
  valueClass="text-emerald-400"
/>
        </div>

      </section>



      {/* Detection configuration */}

      <section className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5">

        <SectionHeader

          icon={Shield}

          title="Detection Configuration"

          description="How SecureSense classifies and prioritizes detected events"

        />



        <div className="mt-5 space-y-3">

          <ConfigurationRow
  label="Detection Type"
  value="Binary Classification"
  description="BENIGN vs ATTACK"
/>

<ConfigurationRow
  label="Primary Classifier"
  value="Deep Neural Network"
  description="MLP architecture with fully connected layers"
/>

<ConfigurationRow
  label="Feature Count"
  value="69"
  description="Network-flow features"
/>



          <ConfigurationRow

            label="Class Weighting"

            value="Balanced"

            description="Used during model training"

          />



          <ConfigurationRow

            label="Persistence"

            value="MongoDB"

            description="Incident records are stored persistently"

          />

        </div>

      </section>



      {/* Risk levels */}

      <section>

        <SectionHeader

          icon={AlertTriangle}

          title="Risk Classification"

          description="Operational interpretation used by SecureSense"

        />



        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">

          <RiskCard

            level="LOW"

            description="Normal or benign activity"

            className="border-emerald-500/20 bg-emerald-500/5 text-emerald-400"

          />



          <RiskCard

            level="MEDIUM"

            description="Activity requiring monitoring"

            className="border-yellow-500/20 bg-yellow-500/5 text-yellow-400"

          />



          <RiskCard

            level="HIGH"

            description="Suspicious activity requiring attention"

            className="border-orange-500/20 bg-orange-500/5 text-orange-400"

          />



          <RiskCard

            level="CRITICAL"

            description="Highest-priority detected threat"

            className="border-red-500/20 bg-red-500/5 text-red-400"

          />

        </div>

      </section>



      {/* Application information */}

      <section className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5">

        <SectionHeader

          icon={Wifi}

          title="Application Information"

          description="SecureSense platform configuration"

        />



        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">

          <InfoCard

            label="Application"

            value="SecureSense"

          />



          <InfoCard

            label="Platform"

            value="DL-Based Cyber Threat Detection"

          />



          <InfoCard

            label="Frontend"

            value="React"

          />



          <InfoCard

            label="Backend"

            value="FastAPI"

          />



          <InfoCard

            label="Database"

            value="MongoDB"

          />



          <InfoCard

            label="Detection Model"

            value="Deep Neural Network"

          />

        </div>

      </section>



      {/* Footer */}

      <div className="rounded-xl border border-slate-800 bg-slate-950/40 px-5 py-4">

        <div className="flex flex-col gap-2 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">

          <span>

            SecureSense • AI-Based Cyber Threat Detection and

            Incident Response Platform

          </span>



          <span className="flex items-center gap-2">

            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />

            System monitoring enabled

          </span>

        </div>

      </div>

    </div>

  );

}



function SectionHeader({

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



function StatusCard({

  icon: Icon,

  title,

  status,

  detail,

  online,

}) {

  return (

    <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5">

      <div className="flex items-start justify-between">

        <div className="rounded-xl bg-slate-900 p-3 text-cyan-400">

          <Icon className="h-5 w-5" />

        </div>



        <span

          className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-semibold ${

            online

              ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400"

              : "border-yellow-500/20 bg-yellow-500/10 text-yellow-400"

          }`}

        >

          <span

            className={`h-1.5 w-1.5 rounded-full ${

              online

                ? "bg-emerald-400"

                : "bg-yellow-400"

            }`}

          />



          {status}

        </span>

      </div>



      <h3 className="mt-5 text-sm font-semibold text-white">

        {title}

      </h3>



      <p className="mt-1 text-xs text-slate-500">

        {detail}

      </p>

    </div>

  );

}



function InfoCard({

  label,

  value,

  valueClass = "text-slate-200",

}) {

  return (

    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">

      <p className="text-[11px] font-medium uppercase tracking-wider text-slate-500">

        {label}

      </p>



      <p

        className={`mt-2 text-sm font-semibold ${valueClass}`}

      >

        {value}

      </p>

    </div>

  );

}



function ConfigurationRow({

  label,

  value,

  description,

}) {

  return (

    <div className="flex flex-col gap-2 rounded-xl border border-slate-800 bg-slate-900/30 p-4 sm:flex-row sm:items-center sm:justify-between">

      <div>

        <p className="text-sm font-medium text-slate-200">

          {label}

        </p>



        <p className="mt-1 text-xs text-slate-500">

          {description}

        </p>

      </div>



      <span className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-medium text-cyan-400">

        {value}

      </span>

    </div>

  );

}



function RiskCard({

  level,

  description,

  className,

}) {

  return (

    <div className={`rounded-2xl border p-5 ${className}`}>

      <p className="text-xs font-bold tracking-[0.15em]">

        {level}

      </p>



      <p className="mt-3 text-xs leading-5 text-slate-400">

        {description}

      </p>

    </div>

  );

}