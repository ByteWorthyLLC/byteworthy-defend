import type {
  SystemStatus,
  MonitorStatus,
  MonitorHealth,
  ScanRequest,
  ScanResponse,
  ScanHistoryItem,
  QuarantineItem,
  ThreatInfo,
  DashboardStats,
  ConfigSection,
  AIQueryRequest,
  AIQueryResponse,
} from '@/types/api'

const API_BASE_URL = '/api/v1'

class APIClient {
  private async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`API Error: ${response.status} - ${error}`)
    }

    return response.json()
  }

  // Dashboard endpoints
  async getDashboardStats(): Promise<DashboardStats> {
    return this.fetch<DashboardStats>('/dashboard/stats')
  }

  async getSystemStatus(): Promise<SystemStatus> {
    return this.fetch<SystemStatus>('/status')
  }

  // Monitor endpoints
  async getMonitors(): Promise<MonitorStatus[]> {
    return this.fetch<MonitorStatus[]>('/monitors')
  }

  async getMonitor(monitorId: string): Promise<MonitorStatus> {
    return this.fetch<MonitorStatus>(`/monitors/${monitorId}`)
  }

  async toggleMonitor(monitorId: string, enabled: boolean): Promise<{ id: string; enabled: boolean; status: string }> {
    return this.fetch(`/monitors/${monitorId}/toggle`, {
      method: 'POST',
      body: JSON.stringify({ enabled }),
    })
  }

  async pauseMonitor(monitorId: string): Promise<{ id: string; status: string }> {
    return this.fetch(`/monitors/${monitorId}/pause`, {
      method: 'POST',
    })
  }

  async resumeMonitor(monitorId: string): Promise<{ id: string; status: string }> {
    return this.fetch(`/monitors/${monitorId}/resume`, {
      method: 'POST',
    })
  }

  async restartMonitor(monitorId: string): Promise<{ id: string; status: string }> {
    return this.fetch(`/monitors/${monitorId}/restart`, {
      method: 'POST',
    })
  }

  async getMonitorHealth(): Promise<MonitorHealth> {
    return this.fetch<MonitorHealth>('/monitors/health')
  }

  // Scan endpoints
  async triggerScan(request: ScanRequest): Promise<ScanResponse> {
    return this.fetch<ScanResponse>('/scan', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  async getScanHistory(limit: number = 20): Promise<ScanHistoryItem[]> {
    return this.fetch<ScanHistoryItem[]>(`/scan/history?limit=${limit}`)
  }

  async getActiveScans(): Promise<ScanResponse[]> {
    return this.fetch<ScanResponse[]>('/scan/active')
  }

  // Quarantine endpoints
  async getQuarantineList(): Promise<QuarantineItem[]> {
    return this.fetch<QuarantineItem[]>('/quarantine')
  }

  async restoreFromQuarantine(id: string): Promise<{ success: boolean; id: string; message: string }> {
    return this.fetch('/quarantine/restore', {
      method: 'POST',
      body: JSON.stringify({ id }),
    })
  }

  async deleteQuarantineItem(id: string): Promise<{ success: boolean; id: string; message: string }> {
    return this.fetch(`/quarantine/${id}`, {
      method: 'DELETE',
    })
  }

  // Configuration endpoints
  async getConfig(): Promise<ConfigSection> {
    return this.fetch<ConfigSection>('/config')
  }

  async updateConfig(section: string, updates: Record<string, unknown>): Promise<{ success: boolean }> {
    return this.fetch('/config', {
      method: 'PUT',
      body: JSON.stringify({ section, updates }),
    })
  }

  // AI endpoints
  async queryAI(request: AIQueryRequest): Promise<AIQueryResponse> {
    return this.fetch<AIQueryResponse>('/ai/query', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  async analyzeScript(content: string, fileType?: string): Promise<unknown> {
    return this.fetch('/ai/analyze', {
      method: 'POST',
      body: JSON.stringify({ content, file_type: fileType }),
    })
  }

  // WebSocket connection info
  async getWebSocketConnections(): Promise<{ active_connections: number }> {
    return this.fetch<{ active_connections: number }>('/ws/connections')
  }
}

export const apiClient = new APIClient()
