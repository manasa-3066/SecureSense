import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});

// ============================================================
// LOGIN
// ============================================================

export async function login(username, password) {
  const response = await api.post("/auth/login", {
    username,
    password,
  });

  const data = response.data;

  if (data.access_token) {
    localStorage.setItem("securesense_token", data.access_token);
    localStorage.setItem("securesense_username", data.username || username);
  }

  return data;
}

// ============================================================
// LOGOUT
// ============================================================

export function logout() {
  localStorage.removeItem("securesense_token");
  localStorage.removeItem("securesense_username");
}

// ============================================================
// AUTH HELPERS
// ============================================================

export function getToken() {
  return localStorage.getItem("securesense_token");
}

export function getUsername() {
  return localStorage.getItem("securesense_username");
}

export function isAuthenticated() {
  return Boolean(getToken());
}

// ============================================================
// AXIOS INTERCEPTOR
// Automatically attach JWT to protected requests
// ============================================================

api.interceptors.request.use(
  (config) => {
    const token = getToken();

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// ============================================================
// RESPONSE INTERCEPTOR
// If token expires / becomes invalid, clear authentication
// ============================================================

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      logout();

      // Don't redirect if the failed request was the login request
      if (!error.config?.url?.includes("/auth/login")) {
        window.location.href = "/login";
      }
    }

    return Promise.reject(error);
  }
);

// ============================================================
// PUBLIC BACKEND APIs
// ============================================================

export async function getHealth() {
  const response = await api.get("/health");
  return response.data;
}

export async function getModelInfo() {
  const response = await api.get("/model-info");
  return response.data;
}

// ============================================================
// INCIDENT APIs
// ============================================================

export async function getIncidents() {
  const response = await api.get("/incidents");
  return response.data;
}

export async function getOpenIncidents() {
  const response = await api.get("/incidents/open");
  return response.data;
}

export async function getIncident(incidentId) {
  const response = await api.get(`/incidents/${incidentId}`);
  return response.data;
}
export async function getThreatExplanation() {
  const response = await api.get("/threat-explanation");
  return response.data;
}

export async function resolveIncident(incidentId) {
  const response = await api.put(
    `/incidents/${incidentId}/resolve`
  );

  return response.data;
}

// ============================================================
// CSV PREDICTION
// ============================================================

export async function predictCSV(file) {
  const formData = new FormData();

  formData.append("file", file);

  const response = await api.post(
    "/predict-csv",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );

  return response.data;
}

// ============================================================
// DEFAULT API
// ============================================================

export default api;