import { Navigate, Route, Routes } from "react-router-dom";

import AppLayout from "./layouts/AppLayout";
import ProtectedRoute from "./components/ProtectedRoute";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Detection from "./pages/Detection";
import Incidents from "./pages/Incidents";
import IncidentDetails from "./pages/IncidentDetails";
import Analytics from "./pages/Analytics";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <Routes>

      {/* =====================================================
          PUBLIC ROUTE
      ====================================================== */}

      <Route path="/login" element={<Login />} />


      {/* =====================================================
          PROTECTED ROUTES
      ====================================================== */}

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>

          <Route
            path="/dashboard"
            element={<Dashboard />}
          />

          <Route
            path="/detection"
            element={<Detection />}
          />

          <Route
            path="/incidents"
            element={<Incidents />}
          />

          <Route
            path="/incidents/:incidentId"
            element={<IncidentDetails />}
          />

          <Route
            path="/analytics"
            element={<Analytics />}
          />

          <Route
            path="/reports"
            element={<Reports />}
          />

          <Route
            path="/settings"
            element={<Settings />}
          />

        </Route>
      </Route>


      {/* =====================================================
          DEFAULT ROUTE
      ====================================================== */}

      <Route
        path="/"
        element={<Navigate to="/dashboard" replace />}
      />

      <Route
        path="*"
        element={<Navigate to="/dashboard" replace />}
      />

    </Routes>
  );
}