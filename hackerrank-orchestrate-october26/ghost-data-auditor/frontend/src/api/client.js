import axios from 'axios';

// Base API URL: prefer env var, or '/api' when using Vite dev proxy
const API_BASE = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '/api';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' }
});

// Resilient fallback: if Vite proxy (/api) is unreachable, fallback directly to Flask (http://127.0.0.1:5000/api)
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config;
    if (!config || config._retriedDirect) {
      return Promise.reject(error);
    }
    const isNetworkOrProxyError = !error.response || [502, 503, 504].includes(error.response?.status);
    if (isNetworkOrProxyError && config.baseURL === '/api' && typeof window !== 'undefined') {
      config._retriedDirect = true;
      config.baseURL = 'http://127.0.0.1:5000/api';
      return client(config);
    }
    return Promise.reject(error);
  }
);

export const getHealth = () => client.get('/health');
export const getDashboardStats = () => client.get('/dashboard/stats');
export const getRequests = (params) => client.get('/requests', { params });
export const getRequestDetail = (caseId) => client.get('/requests/' + caseId);
export const runAudit = () => client.post('/audit/run');
export const getAuditStatus = () => client.get('/audit/status');
export const getEvidence = (params) => client.get('/evidence', { params });
export const searchEvidence = (q) => client.get('/evidence/search', { params: { q } });
export const getRemediation = () => client.get('/remediation');
export const getEvaluationReport = () => client.get('/evaluation/report');
export default client;

