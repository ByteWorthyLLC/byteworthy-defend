import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import type { ScanRequest } from '@/types/api'

// Query keys
export const queryKeys = {
  dashboardStats: ['dashboard', 'stats'] as const,
  systemStatus: ['system', 'status'] as const,
  monitors: ['monitors'] as const,
  monitor: (id: string) => ['monitors', id] as const,
  monitorHealth: ['monitors', 'health'] as const,
  scanHistory: (limit: number) => ['scans', 'history', limit] as const,
  activeScans: ['scans', 'active'] as const,
  quarantine: ['quarantine'] as const,
  config: ['config'] as const,
}

// Dashboard hooks
export function useDashboardStats() {
  return useQuery({
    queryKey: queryKeys.dashboardStats,
    queryFn: () => apiClient.getDashboardStats(),
    refetchInterval: 30000, // Refetch every 30 seconds
  })
}

export function useSystemStatus() {
  return useQuery({
    queryKey: queryKeys.systemStatus,
    queryFn: () => apiClient.getSystemStatus(),
    refetchInterval: 10000, // Refetch every 10 seconds
  })
}

// Monitor hooks
export function useMonitors() {
  return useQuery({
    queryKey: queryKeys.monitors,
    queryFn: () => apiClient.getMonitors(),
    refetchInterval: 5000, // Refetch every 5 seconds
  })
}

export function useMonitor(monitorId: string) {
  return useQuery({
    queryKey: queryKeys.monitor(monitorId),
    queryFn: () => apiClient.getMonitor(monitorId),
    enabled: !!monitorId,
  })
}

export function useMonitorHealth() {
  return useQuery({
    queryKey: queryKeys.monitorHealth,
    queryFn: () => apiClient.getMonitorHealth(),
    refetchInterval: 15000, // Refetch every 15 seconds
  })
}

export function useToggleMonitor() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ monitorId, enabled }: { monitorId: string; enabled: boolean }) =>
      apiClient.toggleMonitor(monitorId, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.monitors })
      queryClient.invalidateQueries({ queryKey: queryKeys.monitorHealth })
    },
  })
}

export function usePauseMonitor() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (monitorId: string) => apiClient.pauseMonitor(monitorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.monitors })
    },
  })
}

export function useResumeMonitor() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (monitorId: string) => apiClient.resumeMonitor(monitorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.monitors })
    },
  })
}

export function useRestartMonitor() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (monitorId: string) => apiClient.restartMonitor(monitorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.monitors })
    },
  })
}

// Scan hooks
export function useScanHistory(limit: number = 20) {
  return useQuery({
    queryKey: queryKeys.scanHistory(limit),
    queryFn: () => apiClient.getScanHistory(limit),
  })
}

export function useActiveScans() {
  return useQuery({
    queryKey: queryKeys.activeScans,
    queryFn: () => apiClient.getActiveScans(),
    refetchInterval: 2000, // Refetch every 2 seconds when scanning
  })
}

export function useTriggerScan() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request: ScanRequest) => apiClient.triggerScan(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.scanHistory(20) })
      queryClient.invalidateQueries({ queryKey: queryKeys.activeScans })
    },
  })
}

// Quarantine hooks
export function useQuarantine() {
  return useQuery({
    queryKey: queryKeys.quarantine,
    queryFn: () => apiClient.getQuarantineList(),
  })
}

export function useRestoreFromQuarantine() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => apiClient.restoreFromQuarantine(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.quarantine })
    },
  })
}

export function useDeleteQuarantineItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => apiClient.deleteQuarantineItem(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.quarantine })
    },
  })
}

// Config hooks
export function useConfig() {
  return useQuery({
    queryKey: queryKeys.config,
    queryFn: () => apiClient.getConfig(),
  })
}

export function useUpdateConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ section, updates }: { section: string; updates: Record<string, unknown> }) =>
      apiClient.updateConfig(section, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.config })
    },
  })
}
