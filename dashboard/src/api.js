import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Security events
export const getSecurityEvents = (filters = {}) => {
  return api.get('/api/security/events', { params: filters });
};

// Blocked prompts stats
export const getBlockedStats = () => {
  return api.get('/api/security/blocked-stats');
};

// Tool usage data
export const getToolUsage = (period = '24h') => {
  return api.get('/api/security/tool-usage', { params: { period } });
};

// Memory access data
export const getMemoryAccess = () => {
  return api.get('/api/security/memory-access');
};

// Anomaly alerts
export const getAnomalies = () => {
  return api.get('/api/security/anomalies');
};

export const acknowledgeAnomaly = (id) => {
  return api.post(`/api/security/anomalies/${id}/acknowledge`);
};

export default api;
