export type ScanStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface Scan {
  scan_id: string;
  status: ScanStatus;
  path: string;
  threats_found: number;
  files_scanned: number;
  start_time: string;
  end_time?: string;
  duration_seconds?: number;
  threats: Threat[];
}

export interface Threat {
  file: string;
  threat: string;
}

export interface StatsOverview {
  total_scans: number;
  threats_found: number;
  files_quarantined: number;
  system_status: string;
  last_update?: string;
}

export interface RecentScan {
  scan_id: string;
  path: string;
  status: ScanStatus;
  threats_found: number;
  timestamp: string;
}

export interface ThreatTimelinePoint {
  date: string;
  threats: number;
}

export interface SystemStatus {
  clamav_online: boolean;
  clamav_version?: string;
  definitions_version?: string;
  last_update?: string;
}

export interface QuarantineFile {
  file_id: string;
  original_path: string;
  quarantine_path: string;
  threat_name: string;
  quarantine_date: string;
  file_size: number;
}

export interface Config {
  scanning: {
    max_file_size: number;
    scan_archives: boolean;
    excluded_paths: string[];
  };
  quarantine: {
    enabled: boolean;
    auto_quarantine: boolean;
  };
  clamav: {
    host: string;
    port: number;
    timeout: number;
  };
}
