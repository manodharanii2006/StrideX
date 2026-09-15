import axios from 'axios';

const api = axios.create({ baseURL: '/api', timeout: 300_000 });

// Attach auth token to every request automatically
api.interceptors.request.use(cfg => {
  const tok = localStorage.getItem('sx_token');
  if (tok) cfg.headers['Authorization'] = `Bearer ${tok}`;
  return cfg;
});

// ── AUTH ────────────────────────────────────────────────────────────────────
export const login    = (email, pw)  => api.post('/auth/login',    { email, password: pw });
export const register = (data)       => api.post('/auth/register', data);

// ── PATIENT self-service ────────────────────────────────────────────────────
export const getPatientProfile    = ()   => api.get('/patient/profile');
export const getPatientDashboard  = ()   => api.get('/patient/dashboard');
export const getPatientAssessments= ()   => api.get('/patient/assessments');
export const getPatientBaseline   = ()   => api.get('/patient/baseline');
export const getPatientTrends     = ()   => api.get('/patient/trends');

// ── CLINICIAN – patients ────────────────────────────────────────────────────
export const getPatients       = ()     => api.get('/patients');
export const getPatient        = (id)   => api.get(`/patients/${id}`);
export const createPatient     = (data) => api.post('/patients', data);
export const getPatientHistory = (id)   => api.get(`/patients/${id}/assessments`);
export const getPatientBaselineFor = (id) => api.get(`/patients/${id}/baseline`);
export const getPatientTrendsFor   = (id) => api.get(`/patients/${id}/trends`);

// ── ASSESSMENTS ─────────────────────────────────────────────────────────────
export const createAssessment  = (data) => api.post('/assessments', data);
export const getAssessment     = (id)   => api.get(`/assessments/${id}`);
export const getAnalysisStatus = (id)   => api.get(`/assessments/${id}/status`);
export const getTimeseries     = (id)   => api.get(`/assessments/${id}/timeseries`);
export const downloadPdf       = (id)   => api.get(`/assessments/${id}/pdf`, { responseType: 'blob' });

export const uploadVideo = (id, file, onProgress) => {
  const form = new FormData();
  form.append('video', file);
  return api.post(`/assessments/${id}/upload`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: e => onProgress?.(Math.round(e.loaded * 100 / e.total)),
  });
};
export const startAnalysis = (id) => api.post(`/assessments/${id}/analyze`);

// ── DASHBOARD (clinician) ────────────────────────────────────────────────────
export const getDashboardStats = () => api.get('/dashboard/stats');

export default api;
