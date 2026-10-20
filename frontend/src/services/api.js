const API_BASE = import.meta.env.VITE_API_BASE || '/api';

async function handleResponse(res) {
  if (!res.ok) {
    let errorDetail = 'Network response error';
    try {
      const errorJson = await res.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch (e) {
      errorDetail = await res.text();
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  // Health & diagnostics
  getHealth: () => fetch(`${API_BASE}/health`).then(handleResponse),

  // Documents
  getDocuments: () => fetch(`${API_BASE}/documents`).then(handleResponse),
  getDocument: (id) => fetch(`${API_BASE}/documents/${id}`).then(handleResponse),
  uploadDocument: (formData) =>
    fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData,
    }).then(handleResponse),
  processDocument: (id) =>
    fetch(`${API_BASE}/documents/${id}/process`, {
      method: 'POST',
    }).then(handleResponse),
  deleteDocument: (id) =>
    fetch(`${API_BASE}/documents/${id}`, {
      method: 'DELETE',
    }).then(handleResponse),
  getSeedDocuments: () => fetch(`${API_BASE}/documents/seed/list`).then(handleResponse),
  indexSeedDocument: (data) =>
    fetch(`${API_BASE}/documents/seed/index`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(handleResponse),

  // Research
  executeResearch: (data) =>
    fetch(`${API_BASE}/research`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(handleResponse),
  getResearchHistory: () => fetch(`${API_BASE}/research/history`).then(handleResponse),

  // Metrics & Red Flags
  getMetrics: (docId) => fetch(`${API_BASE}/metrics/${docId}`).then(handleResponse),
  forceExtractMetrics: (docId) =>
    fetch(`${API_BASE}/metrics/${docId}/extract`, {
      method: 'POST',
    }).then(handleResponse),
  getRedFlagsForDoc: (docId) => fetch(`${API_BASE}/metrics/${docId}/red-flags`).then(handleResponse),
  getAllRedFlags: () => fetch(`${API_BASE}/metrics/red-flags`).then(handleResponse),

  // Comparison
  compareCompanies: (data) =>
    fetch(`${API_BASE}/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(handleResponse),

  // Reports
  getReports: () => fetch(`${API_BASE}/reports`).then(handleResponse),
  getReportDetail: (id) => fetch(`${API_BASE}/reports/${id}`).then(handleResponse),
  generateReport: (data) =>
    fetch(`${API_BASE}/reports/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(handleResponse),
  getReportDownloadUrl: (id) => `${API_BASE}/reports/${id}/download`,

  // Settings
  getSettings: () => fetch(`${API_BASE}/settings`).then(handleResponse),
  updateSettings: (data) =>
    fetch(`${API_BASE}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(handleResponse),
};
