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
    let errorDetail = `HTTP error ${response.status}`;
    try {
      const errText = await response.text();
      try {
        const errJson = JSON.parse(errText);
        errorDetail = errJson.detail || JSON.stringify(errJson);
      } catch {
        errorDetail = errText || errorDetail;
      }
    } catch {
      // fallback
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
    }),
    getAnalysisPlan: async (caseId) => apiRequest(`/cases/${caseId}/analysis-plan`),
    runAnalysis: async (caseId) => apiRequest(`/cases/${caseId}/run-analysis`, {
      method: "POST"
    }),
    getTelemetry: async (caseId) => apiRequest(`/cases/${caseId}/engine-telemetry`)
  },

  engines: {
    list: async () => apiRequest("/engines"),
    get: async (id) => apiRequest(`/engines/${id}`),
    resolveDag: async (targets = ["R04"]) => apiRequest(`/engines/dag/resolve?${targets.map(t => `targets=${t}`).join('&')}`)
  },

  evidence: {
    list: async (caseId) => apiRequest(`/cases/${caseId}/evidence`),
    upload: async (caseId, formData) => {
      return apiRequest(`/cases/${caseId}/evidence`, {
        method: "POST",
        body: formData
      });
    },
    getProvenance: async (caseId, evidenceId) => apiRequest(`/cases/${caseId}/evidence/${evidenceId}/provenance`)
  },

  observations: {
    list: async (caseId, department = null) => {
      const query = department ? `?department=${department}` : "";
      return apiRequest(`/cases/${caseId}/observations${query}`);
    }
  },

  entities: {
    list: async (caseId) => apiRequest(`/cases/${caseId}/entities`),
    confirm: async (caseId, entityId, linkId = null) => {
      if (linkId) {
        return apiRequest(`/cases/${caseId}/entities/${entityId}/links/${linkId}/confirm`, {
          method: "POST"
        });
      }
      return apiRequest(`/cases/${caseId}/entities/${entityId}/confirm`, {
        method: "POST"
      });
    },
    autoLink: async (caseId) => apiRequest(`/cases/${caseId}/entities/auto-link`, {
      method: "POST"
    })
  },

  timelines: {
    getCorrelated: async (caseId) => apiRequest(`/cases/${caseId}/timelines/correlated`),
    getSources: async (caseId) => apiRequest(`/cases/${caseId}/timelines/sources`),
    correlate: async (caseId) => apiRequest(`/cases/${caseId}/timelines/correlate`, {
      method: "POST"
    })
  },

  gapsConflicts: {
    list: async (caseId) => apiRequest(`/cases/${caseId}/gaps-conflicts`),
    detect: async (caseId) => apiRequest(`/cases/${caseId}/gaps-conflicts/detect`, {
      method: "POST"
    })
  },

  findings: {
    list: async (caseId, department = null) => {
      const query = department ? `?department=${department}` : "";
      return apiRequest(`/cases/${caseId}/findings${query}`);
    },
    claims: async (caseId) => apiRequest(`/cases/${caseId}/claims`)
  },

  reconstruction: {
    list: async (caseId) => apiRequest(`/cases/${caseId}/hypotheses`),
    generate: async (caseId) => apiRequest(`/cases/${caseId}/hypotheses/generate`, {
      method: "POST"
    }),
    review: async (caseId, hypothesisId, payload) => apiRequest(`/cases/${caseId}/hypotheses/${hypothesisId}/review`, {
      method: "POST",
      body: JSON.stringify(payload)
    })
  },

  verification: {
    listPending: async (caseId) => apiRequest(`/cases/${caseId}/verifications/pending`),
    verifyObservation: async (caseId, obsId, payload) => apiRequest(`/cases/${caseId}/verifications/observations/${obsId}`, {
      method: "POST",
      body: JSON.stringify(payload)
    }),
    verifyFinding: async (caseId, findingId, payload) => apiRequest(`/cases/${caseId}/verifications/findings/${findingId}`, {
      method: "POST",
      body: JSON.stringify(payload)
    })
  },

  copilot: {
    ask: async (caseId, question, mode = "EVIDENCE_ONLY") => apiRequest(`/cases/${caseId}/copilot/query`, {
      method: "POST",
      body: JSON.stringify({
        query: question,
        mode
      })
    })
  },

  reports: {
    generate: async (caseId, title = "Evidence Reconstruction Report") => apiRequest(`/cases/${caseId}/reports/generate`, {
      method: "POST"
    }),
    list: async (caseId) => apiRequest(`/cases/${caseId}/reports`),
    get: async (caseId, reportId) => apiRequest(`/cases/${caseId}/reports/${reportId}`)
  }
};
