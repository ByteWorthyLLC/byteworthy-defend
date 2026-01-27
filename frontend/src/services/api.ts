import axios from 'axios';
import type { Scan, StatsOverview, RecentScan, ThreatTimelinePoint, SystemStatus, QuarantineFile, Config } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Scans API
export const scansApi = {
  create: (path: string) => api.post<Scan>('/scans', { path }),
  list: (page = 1, pageSize = 10) =>
    api.get<{ scans: Scan[]; total: number; page: number; page_size: number }>('/scans', {
      params: { page, page_size: pageSize }
    }),
  get: (scanId: string) => api.get<Scan>(`/scans/${scanId}`),
  cancel: (scanId: string) => api.delete(`/scans/${scanId}`),
};

// Stats API
export const statsApi = {
  overview: () => api.get<StatsOverview>('/stats/overview'),
  recentScans: (limit = 10) => api.get<RecentScan[]>('/stats/recent-scans', { params: { limit } }),
  threatsTimeline: (days = 7) => api.get<ThreatTimelinePoint[]>('/stats/threats-timeline', { params: { days } }),
  systemStatus: () => api.get<SystemStatus>('/stats/system-status'),
};

// Quarantine API
export const quarantineApi = {
  list: (page = 1, pageSize = 10) =>
    api.get<{ files: QuarantineFile[]; total: number; page: number; page_size: number }>('/quarantine', {
      params: { page, page_size: pageSize }
    }),
  get: (fileId: string) => api.get<QuarantineFile>(`/quarantine/${fileId}`),
  restore: (fileId: string) => api.post(`/quarantine/${fileId}/restore`),
  delete: (fileId: string) => api.delete(`/quarantine/${fileId}`),
};

// Config API
export const configApi = {
  get: () => api.get<Config>('/config'),
  update: (config: Partial<Config>) => api.put<Config>('/config', config),
  validate: (config: Partial<Config>) => api.post('/config/validate', config),
  getDefaults: () => api.get<Config>('/config/defaults'),
};

// Health check
export const healthCheck = () => api.get('/health');

export default api;
