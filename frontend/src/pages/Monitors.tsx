import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import {
  useMonitors,
  useMonitorHealth,
  useToggleMonitor,
  usePauseMonitor,
  useResumeMonitor,
  useRestartMonitor,
} from '@/hooks/useAPI'
import {
  Activity,
  Pause,
  Play,
  RotateCw,
  AlertCircle,
  CheckCircle2,
  XCircle,
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

const monitorDescriptions: Record<string, string> = {
  registry: 'Monitors Windows Registry for unauthorized changes',
  powershell: 'Detects suspicious PowerShell script execution',
  network: 'Monitors network connections for malicious activity',
  clipboard: 'Tracks clipboard activity for data exfiltration',
  cryptominer: 'Detects cryptocurrency mining malware',
  dns: 'Monitors DNS queries for command & control communication',
  download: 'Scans downloaded files in real-time',
  hardware: 'Monitors hardware changes and USB devices',
  spyware: 'Detects spyware and keylogger activity',
  ransomware: 'Identifies ransomware behavior patterns',
  package: 'Monitors package manager installations',
  docker: 'Tracks Docker container security',
  ide: 'Monitors IDE and development tool activity',
}

export function Monitors() {
  const { data: monitors, isLoading } = useMonitors()
  const { data: health } = useMonitorHealth()
  const toggleMonitor = useToggleMonitor()
  const pauseMonitor = usePauseMonitor()
  const resumeMonitor = useResumeMonitor()
  const restartMonitor = useRestartMonitor()

  const handleToggle = async (monitorId: string, enabled: boolean) => {
    await toggleMonitor.mutateAsync({ monitorId, enabled })
  }

  const handlePause = async (monitorId: string) => {
    await pauseMonitor.mutateAsync(monitorId)
  }

  const handleResume = async (monitorId: string) => {
    await resumeMonitor.mutateAsync(monitorId)
  }

  const handleRestart = async (monitorId: string) => {
    await restartMonitor.mutateAsync(monitorId)
  }

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />
      case 'stopped':
        return <XCircle className="h-5 w-5 text-gray-500" />
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      default:
        return <Activity className="h-5 w-5 text-yellow-500" />
    }
  }

  const getStatusBadge = (status: string) => {
    const variants = {
      running: { variant: 'success' as const, text: 'Running' },
      stopped: { variant: 'outline' as const, text: 'Stopped' },
      error: { variant: 'destructive' as const, text: 'Error' },
      paused: { variant: 'warning' as const, text: 'Paused' },
    }

    const badgeInfo = variants[status.toLowerCase() as keyof typeof variants] || {
      variant: 'outline' as const,
      text: status,
    }

    return <Badge variant={badgeInfo.variant}>{badgeInfo.text}</Badge>
  }

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <Activity className="mx-auto h-12 w-12 animate-pulse text-primary" />
          <p className="mt-4 text-muted-foreground">Loading monitors...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Security Monitors</h1>
          <p className="text-muted-foreground">
            Real-time threat detection and monitoring system
          </p>
        </div>
        {health && (
          <Badge
            variant={health.healthy ? 'success' : 'destructive'}
            className="text-base"
          >
            {health.healthy ? '✓ All Healthy' : `⚠ ${health.unhealthy_monitors} Issues`}
          </Badge>
        )}
      </div>

      {/* Health Summary */}
      {health && (
        <Card>
          <CardHeader>
            <CardTitle>System Health</CardTitle>
            <CardDescription>Overall monitoring system status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-4">
              <div>
                <div className="text-2xl font-bold">{health.total_monitors}</div>
                <p className="text-xs text-muted-foreground">Total Monitors</p>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">
                  {health.running_monitors}
                </div>
                <p className="text-xs text-muted-foreground">Running</p>
              </div>
              <div>
                <div className="text-2xl font-bold text-red-600">
                  {health.unhealthy_monitors}
                </div>
                <p className="text-xs text-muted-foreground">Unhealthy</p>
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {health.manager_running ? '✓' : '✗'}
                </div>
                <p className="text-xs text-muted-foreground">Manager Status</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Monitor Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {monitors?.map((monitor) => (
          <Card key={monitor.id} className="relative">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  {getStatusIcon(monitor.status)}
                  <CardTitle className="text-lg">{monitor.name}</CardTitle>
                </div>
                <Switch
                  checked={monitor.enabled}
                  onCheckedChange={(checked) => handleToggle(monitor.id, checked)}
                  disabled={toggleMonitor.isPending}
                />
              </div>
              <CardDescription>
                {monitorDescriptions[monitor.id] || 'Security monitoring service'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Status Badge */}
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Status</span>
                {getStatusBadge(monitor.status)}
              </div>

              {/* Stats */}
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Events</span>
                  <span className="font-medium">{monitor.event_count}</span>
                </div>
                {monitor.last_event && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Last Event</span>
                    <span className="font-medium">
                      {formatDistanceToNow(new Date(monitor.last_event), {
                        addSuffix: true,
                      })}
                    </span>
                  </div>
                )}
              </div>

              {/* Error Message */}
              {monitor.error_message && (
                <div className="rounded-md bg-destructive/10 p-2">
                  <p className="text-xs text-destructive">{monitor.error_message}</p>
                </div>
              )}

              {/* Control Buttons */}
              {monitor.enabled && (
                <div className="flex gap-2">
                  {monitor.status.toLowerCase() === 'running' ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePause(monitor.id)}
                      disabled={pauseMonitor.isPending}
                      className="flex-1"
                    >
                      <Pause className="mr-1 h-4 w-4" />
                      Pause
                    </Button>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleResume(monitor.id)}
                      disabled={resumeMonitor.isPending}
                      className="flex-1"
                    >
                      <Play className="mr-1 h-4 w-4" />
                      Resume
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleRestart(monitor.id)}
                    disabled={restartMonitor.isPending}
                    className="flex-1"
                  >
                    <RotateCw className="mr-1 h-4 w-4" />
                    Restart
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
