import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import {
  Activity,
  AlertCircle,
  Eye,
  EyeOff,
  LockKeyhole,
  LogIn,
  ShieldCheck,
  User,
} from "lucide-react";

import {
  isAuthenticated,
  login,
} from "../services/api";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // If already logged in, don't show login page again
  if (isAuthenticated()) {
    const redirectTo = location.state?.from?.pathname || "/dashboard";

    return <Navigate to={redirectTo} replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();

    setError("");

    if (!username.trim()) {
      setError("Please enter your username.");
      return;
    }

    if (!password) {
      setError("Please enter your password.");
      return;
    }

    try {
      setLoading(true);

      await login(username.trim(), password);

      const redirectTo =
        location.state?.from?.pathname || "/dashboard";

      navigate(redirectTo, { replace: true });
    } catch (err) {
      console.error("Login error:", err);

      if (err.response?.status === 401) {
        setError("Invalid username or password.");
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.message === "Network Error") {
        setError(
          "Unable to connect to the SecureSense backend."
        );
      } else {
        setError(
          "Login failed. Please check the backend and try again."
        );
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white flex">

      {/* =====================================================
          LEFT PANEL
      ====================================================== */}

      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">

        {/* Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950" />

        {/* Decorative glow */}
        <div className="absolute -top-32 -left-32 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl" />

        <div className="relative z-10 flex flex-col justify-between p-12 w-full">

          {/* Logo */}
          <div className="flex items-center gap-3">

            <div className="w-11 h-11 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center">
              <ShieldCheck className="w-6 h-6 text-blue-400" />
            </div>

            <div>
              <h1 className="text-xl font-bold tracking-tight">
                SecureSense
              </h1>

              <p className="text-xs text-slate-400">
                AI Cyber Threat Detection
              </p>
            </div>

          </div>

          {/* Main content */}
          <div className="max-w-lg">

            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs mb-6">
              <Activity className="w-3.5 h-3.5" />
              Security Operations Center
            </div>

            <h2 className="text-4xl xl:text-5xl font-bold leading-tight mb-6">
              Intelligent protection
              <span className="block text-blue-400">
                for modern networks.
              </span>
            </h2>

            <p className="text-slate-400 text-base leading-7 max-w-md">
              Monitor network activity, detect suspicious traffic,
              classify threats and manage security incidents from
              one centralized platform.
            </p>

            {/* Features */}
            <div className="mt-10 space-y-4">

              <Feature
                icon={<ShieldCheck className="w-5 h-5" />}
                title="AI-Powered Detection"
                description="Machine-learning based network threat classification."
              />

              <Feature
                icon={<Activity className="w-5 h-5" />}
                title="Real-Time Monitoring"
                description="Track detection activity and security incidents."
              />

              <Feature
                icon={<LockKeyhole className="w-5 h-5" />}
                title="Secure Access"
                description="Authenticated access to security operations."
              />

            </div>
          </div>

          {/* Footer */}
          <div className="text-xs text-slate-500">
            SecureSense • Final Year Project
          </div>

        </div>
      </div>

      {/* =====================================================
          RIGHT PANEL
      ====================================================== */}

      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-10">

        <div className="w-full max-w-md">

          {/* Mobile logo */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-10">

            <div className="w-11 h-11 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center">
              <ShieldCheck className="w-6 h-6 text-blue-400" />
            </div>

            <div>
              <h1 className="text-xl font-bold">
                SecureSense
              </h1>

              <p className="text-xs text-slate-400">
                AI Cyber Threat Detection
              </p>
            </div>

          </div>

          {/* Login card */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-7 sm:p-8 shadow-2xl">

            {/* Header */}
            <div className="mb-8">

              <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-5">
                <LogIn className="w-6 h-6 text-blue-400" />
              </div>

              <h2 className="text-2xl font-bold">
                Welcome back
              </h2>

              <p className="text-slate-400 text-sm mt-2">
                Sign in to access the SecureSense security dashboard.
              </p>

            </div>

            {/* Error */}
            {error && (
              <div className="mb-5 flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3">

                <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />

                <p className="text-sm text-red-300">
                  {error}
                </p>

              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-5">

              {/* Username */}
              <div>

                <label
                  htmlFor="username"
                  className="block text-sm font-medium text-slate-300 mb-2"
                >
                  Username
                </label>

                <div className="relative">

                  <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />

                  <input
                    id="username"
                    type="text"
                    value={username}
                    onChange={(event) =>
                      setUsername(event.target.value)
                    }
                    placeholder="Enter username"
                    autoComplete="username"
                    disabled={loading}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950/70 py-3 pl-11 pr-4 text-sm text-white placeholder-slate-600 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 disabled:opacity-60"
                  />

                </div>

              </div>

              {/* Password */}
              <div>

                <label
                  htmlFor="password"
                  className="block text-sm font-medium text-slate-300 mb-2"
                >
                  Password
                </label>

                <div className="relative">

                  <LockKeyhole className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />

                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(event) =>
                      setPassword(event.target.value)
                    }
                    placeholder="Enter password"
                    autoComplete="current-password"
                    disabled={loading}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950/70 py-3 pl-11 pr-12 text-sm text-white placeholder-slate-600 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 disabled:opacity-60"
                  />

                  <button
                    type="button"
                    onClick={() =>
                      setShowPassword((current) => !current)
                    }
                    disabled={loading}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition disabled:opacity-50"
                    aria-label={
                      showPassword
                        ? "Hide password"
                        : "Show password"
                    }
                  >
                    {showPassword ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>

                </div>

              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-blue-600 hover:bg-blue-500 active:bg-blue-700 px-4 py-3 text-sm font-semibold text-white transition shadow-lg shadow-blue-600/20 disabled:cursor-not-allowed disabled:opacity-60"
              >

                {loading ? (
                  <>
                    <span className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                    Signing in...
                  </>
                ) : (
                  <>
                    <LogIn className="w-4 h-4" />
                    Sign in
                  </>
                )}

              </button>

            </form>

            {/* Security note */}
            <div className="mt-7 pt-6 border-t border-slate-800">

              <div className="flex items-center justify-center gap-2 text-xs text-slate-500">

                <LockKeyhole className="w-3.5 h-3.5" />

                <span>
                  Protected by JWT authentication
                </span>

              </div>

            </div>

          </div>

          {/* Bottom status */}
          <div className="flex items-center justify-center gap-2 mt-6 text-xs text-slate-500">

            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />

            SecureSense authentication service

          </div>

        </div>

      </div>

    </div>
  );
}


// ============================================================
// FEATURE ITEM
// ============================================================

function Feature({ icon, title, description }) {
  return (
    <div className="flex items-start gap-4">

      <div className="w-10 h-10 rounded-lg bg-slate-800/80 border border-slate-700 flex items-center justify-center text-blue-400 shrink-0">
        {icon}
      </div>

      <div>
        <h3 className="text-sm font-semibold text-slate-200">
          {title}
        </h3>

        <p className="text-xs text-slate-500 mt-1 leading-5">
          {description}
        </p>
      </div>

    </div>
  );
}