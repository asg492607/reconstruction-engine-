const API_BASE = "";

export const getToken = () => localStorage.getItem("rre_jwt_token");
export const setToken = (token) => localStorage.setItem("rre_jwt_token", token);
export const removeToken = () => {
  localStorage.removeItem("rre_jwt_token");
  localStorage.removeItem("rre_user_info");
};

export const getSavedUser = () => {
  try {
    const raw = localStorage.getItem("rre_user_info");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};
export const setSavedUser = (user) => localStorage.setItem("rre_user_info", JSON.stringify(user));

async function apiRequest(endpoint, options = {}) {
  const token = getToken();
  const headers = {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {})
  };

  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  });

  if (response.status === 401) {
    // If unauthorized, clear token
    // removeToken();
  }

  if (!response.ok) {
    let errorDetail = "An unexpected error occurred.";
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || JSON.stringify(errJson);
    } catch {
      errorDetail = await response.text();
    }
    throw new Error(errorDetail || `HTTP error ${response.status}`);
  }

  return response.json();
}

export const api = {
  auth: {
    firebaseSync: async (idToken, role, department, fullName) => {
      const data = await apiRequest("/auth/firebase-sync", {
        method: "POST",
        body: JSON.stringify({
          id_token: idToken,
          role,
          department,
          full_name: fullName
        })
      });
      setToken(data.access_token);
      setSavedUser(data);
      return data;
    },
    login: async (email, password) => {
      const data = await apiRequest("/auth/login/json", {
        method: "POST",
        body: JSON.stringify({ email, password })
      });
      setToken(data.access_token);
      setSavedUser(data);
      return data;
    },
    register: async (payload) => {
      return apiRequest("/auth/register", {
        method: "POST",
        body: JSON.stringify(payload)
      });
    },
    getMe: async () => apiRequest("/auth/me")
  },

  cases: {
    list: async () => apiRequest("/cases"),
    get: async (id) => apiRequest(`/cases/${id}`),
    create: async (payload) => apiRequest("/cases", {
      method: "POST",
      body: JSON.stringify(payload)
    })
  },

  evidence: {
    list: async (caseId) => apiRequest(`/evidence/case/${caseId}`),
    upload: async (caseId, formData) => {
      return apiRequest(`/evidence/upload?case_id=${caseId}`, {
        method: "POST",
        body: formData
      });
    },
    getProvenance: async (evidenceId) => apiRequest(`/evidence/${evidenceId}/provenance`)
  },

  observations: {
    list: async (caseId, department = null) => {
      const query = department ? `?department=${department}` : "";
      return apiRequest(`/observations/case/${caseId}${query}`);
    }
  },

  entities: {
    list: async (caseId) => apiRequest(`/entities/case/${caseId}`),
    confirm: async (caseId, entityId) => apiRequest(`/entities/${entityId}/confirm`, {
      method: "PATCH"
    })
  },

  timelines: {
    getCorrelated: async (caseId) => apiRequest(`/timelines/correlated/${caseId}`)
  },

  gapsConflicts: {
    list: async (caseId) => apiRequest(`/gaps-conflicts/${caseId}`),
    detect: async (caseId) => apiRequest(`/gaps-conflicts/${caseId}/detect`, {
      method: "POST"
    })
  },

  findings: {
    list: async (caseId) => apiRequest(`/findings/case/${caseId}`)
  },

  reconstruction: {
    list: async (caseId) => apiRequest(`/reconstruction/case/${caseId}`),
    generate: async (caseId) => apiRequest(`/reconstruction/generate/${caseId}`, {
      method: "POST"
    })
  },

  verification: {
    list: async (caseId) => apiRequest(`/verification/case/${caseId}`),
    verifyFinding: async (findingId, payload) => apiRequest(`/verification/finding/${findingId}`, {
      method: "POST",
      body: JSON.stringify(payload)
    }),
    submitHypothesis: async (caseId, payload) => apiRequest(`/verification/hypothesis/${caseId}`, {
      method: "POST",
      body: JSON.stringify(payload)
    })
  },

  copilot: {
    ask: async (caseId, question, mode = "EVIDENCE_ONLY") => apiRequest("/copilot/ask", {
      method: "POST",
      body: JSON.stringify({
        case_id: caseId,
        question,
        mode
      })
    })
  },

  reports: {
    generate: async (caseId, title = "Official Case Reconstruction Dossier") => apiRequest(`/reports/generate/${caseId}`, {
      method: "POST",
      body: JSON.stringify({ title })
    }),
    get: async (reportId) => apiRequest(`/reports/${reportId}`)
  }
};
