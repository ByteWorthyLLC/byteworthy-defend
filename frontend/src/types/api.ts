// API Types matching backend Pydantic models

export interface SystemStatus {
  protection_status: string
  monitors: {
    active: number
    total: number
  }
  threats: {
    today: number
    week: number
    total: number
  }
  last_scan: string | null
  last_update: string | null
  resources: {
    cpu_usage: number
    memory_usage: number
  }
}

export interface MonitorStatus {
  id: string
  name: string
  status: string
  enabled: boolean
  event_count: number
  last_event: string | null
  error_message: string | null
}

export interface MonitorHealth {
  healthy: boolean
  manager_running: boolean
  total_monitors: number
  running_monitors: number
  unhealthy_monitors: number
  monitors: Array<{
    name: string
    healthy: boolean
    running: boolean
    errors: number
    last_check: string | null
    status_message: string
  }>
}

export interface ScanRequest {
  path: string
  recursive: boolean
}

export interface ThreatDetail {
  name: string
  path: string
  quarantined: boolean
}

export interface ScanResponse {
  scan_id: string
  path: string
  files_scanned: number
  threats_found: number
  threats: ThreatDetail[]
  status: string
}

export interface ScanHistoryItem {
  id: string
  path: string
  started_at: string
  completed_at: string | null
  status: string
  files_scanned: number
  threats_found: number
}

export interface QuarantineItem {
  id: string
  original_path: string
  threat_name: string
  quarantined_at: string
  size: number
}

export interface ThreatInfo {
  id: string
  name: string
  severity: string
  detected_at: string
  path: string
  quarantined: boolean
  description: string | null
}

export interface DashboardStats {
  protection_enabled: boolean
  monitors_active: number
  monitors_total: number
  threats_today: number
  threats_week: number
  threats_total: number
  recent_scans: ScanHistoryItem[]
  recent_threats: ThreatInfo[]
  system_resources: {
    cpu_usage: number
    memory_usage: number
  }
}

export interface ConfigSection {
  clamav?: {
    host: string
    port: number
    timeout: number
  }
  scanning?: {
    max_file_size: number
    scan_archives: boolean
    scan_recursively: boolean
  }
  monitoring?: {
    enabled: boolean
    watch_paths: string[]
  }
  quarantine?: {
    enabled: boolean
    auto_quarantine: boolean
  }
}

export interface AIQueryRequest {
  query: string
  context?: string
}

export interface AIQueryResponse {
  query: string
  response: string
  sources: string[]
  cost: number | null
}

// WebSocket message types
export interface WebSocketMessage {
  type: string
  timestamp: string
  data: Record<string, unknown>
  priority: number
}

export type EventType =
  | 'service_started'
  | 'service_stopped'
  | 'monitor_started'
  | 'monitor_stopped'
  | 'scan_started'
  | 'scan_completed'
  | 'threat_detected'
  | 'config_changed'
  | 'system_update'
  | 'initial_status'
  | 'ping'
  | 'pong'
