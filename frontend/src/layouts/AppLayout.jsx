import { useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  Activity,
  BarChart3,
  Bell,
  FileText,
  LayoutDashboard,
  LogOut,
  Menu,
  Settings,
  Shield,
  ShieldAlert,
  X,
} from "lucide-react";

import { getUsername, logout } from "../services/api";
import { useBackendStatus } from "../hooks/useBackendStatus";

export default function AppLayout() {
  const navigate = useNavigate();

  const [sidebarOpen, setSidebarOpen] = useState(false);

  const { status } = useBackendStatus();

  const username = getUsername() || "admin";

  function handleLogout() {
    logout();

    setSidebarOpen(false);

    navigate("/login", { replace: true });
  }

  const navigation = [
    {
      name: "Dashboard",
      path: "/dashboard",
      icon: LayoutDashboard,
    },
    {
      name: "Threat Detection",
      path: "/detection",
      icon: ShieldAlert,
    },
    {
      name: "Incidents",
      path: "/incidents",
      icon: Bell,
    },
    {
      name: "Analytics",
      path: "/analytics",
      icon: BarChart3,
    },
    {
      name: "Reports",
      path: "/reports",
      icon: FileText,
    },
    {
      name: "Settings",
      path: "/settings",
      icon: Settings,
    },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-white">

      {/* =====================================================
          MOBILE OVERLAY
      ====================================================== */}

      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* =====================================================
          SIDEBAR
      ====================================================== */}

      <aside
        className={`
          fixed
          inset-y-0
          left-0
          z-50
          w-72
          border-r
          border-slate-800
          bg-slate-950
          transform
          transition-transform
          duration-300
          lg:translate-x-0
          ${
            sidebarOpen
              ? "translate-x-0"
              : "-translate-x-full"
          }
        `}
      >

        {/* Logo */}
        <div className="h-20 flex items-center justify-between px-6 border-b border-slate-800">

          <Link
            to="/dashboard"
            className="flex items-center gap-3"
            onClick={() => setSidebarOpen(false)}
          >

            <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center">
              <Shield className="w-5 h-5 text-blue-400" />
            </div>

            <div>
              <h1 className="font-bold text-lg tracking-tight">
                SecureSense
              </h1>

              <p className="text-[11px] text-slate-500">
                Security Operations Center
              </p>
            </div>

          </Link>

          {/* Mobile close */}
          <button
            type="button"
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden text-slate-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>

        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-1">

          <p className="px-3 pt-2 pb-3 text-[10px] font-semibold uppercase tracking-widest text-slate-600">
            Security Operations
          </p>

          {navigation.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={({ isActive }) =>
                  `
                  flex items-center gap-3
                  px-3 py-2.5
                  rounded-xl
                  text-sm
                  transition-all
                  ${
                    isActive
                      ? "bg-blue-600/15 text-blue-400 border border-blue-500/20"
                      : "text-slate-400 hover:bg-slate-800/70 hover:text-slate-200"
                  }
                  `
                }
              >
                <Icon className="w-[18px] h-[18px]" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}

        </nav>

        {/* Bottom user section */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-800">

          {/* User */}
          <div className="flex items-center gap-3 px-3 py-3 mb-2">

            <div className="w-9 h-9 rounded-full bg-blue-600/20 border border-blue-500/20 flex items-center justify-center">
              <span className="text-sm font-semibold text-blue-400">
                {username.charAt(0).toUpperCase()}
              </span>
            </div>

            <div className="min-w-0 flex-1">

              <p className="text-sm font-medium text-slate-200 truncate">
                {username}
              </p>

              <p className="text-xs text-slate-500">
                Security Administrator
              </p>

            </div>

          </div>

          {/* Logout */}
          <button
            type="button"
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
          >
            <LogOut className="w-[18px] h-[18px]" />
            <span>Sign out</span>
          </button>

        </div>

      </aside>

      {/* =====================================================
          MAIN AREA
      ====================================================== */}

      <div className="lg:pl-72 min-h-screen">

        {/* Header */}
        <header className="sticky top-0 z-30 h-20 border-b border-slate-800 bg-slate-950/90 backdrop-blur">

          <div className="h-full px-4 sm:px-6 lg:px-8 flex items-center justify-between">

            {/* Left */}
            <div className="flex items-center gap-4">

              <button
                type="button"
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden p-2 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white"
              >
                <Menu className="w-5 h-5" />
              </button>

              <div className="hidden sm:block">

                <p className="text-xs text-slate-500">
                  Security Operations Center
                </p>

                <p className="text-sm font-medium text-slate-200">
                  SecureSense Monitoring Platform
                </p>

              </div>

            </div>

            {/* Right */}
            <div className="flex items-center gap-4">

              {/* Backend status */}
              <div className="hidden sm:flex items-center gap-2">

                <span
                  className={`w-2 h-2 rounded-full ${
                    status === "online"
                      ? "bg-emerald-400 animate-pulse"
                      : status === "checking"
                      ? "bg-yellow-400"
                      : "bg-red-400"
                  }`}
                />

                <span className="text-xs text-slate-500">
                  {status === "online"
                    ? "Backend Online"
                    : status === "checking"
                    ? "Checking..."
                    : "Backend Offline"}
                </span>

              </div>

              {/* System status */}
              <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/5">

                <Activity className="w-3.5 h-3.5 text-emerald-400" />

                <span className="text-xs text-emerald-400">
                  System Operational
                </span>

              </div>

              {/* User avatar */}
              <div className="w-9 h-9 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center">

                <span className="text-sm font-semibold text-slate-300">
                  {username.charAt(0).toUpperCase()}
                </span>

              </div>

            </div>

          </div>

        </header>

        {/* Page content */}
        <main className="p-4 sm:p-6 lg:p-8">

          <Outlet />

        </main>

      </div>

    </div>
  );
}