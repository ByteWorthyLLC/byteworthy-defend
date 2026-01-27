import { useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useDashboardStats } from '@/hooks/useAPI'
import { useWebSocket } from '@/hooks/useWebSocket'
import { Shield, Activity, AlertTriangle, Clock, Cpu, HardDrive } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts'

export function Dashboard() {
  const { data: stats, refetch } = useDashboardStats()

  // WebSocket connection for real-time updates
  const { lastMessage, isConnected } = useWebSocket({
    onMessage: (message) => {
      // Refetch stats when relevant events occur
      if (
        message.type === 'scan_completed' ||
        message.type === 'threat_detected' ||
        message.type === 'monitor_started' ||
        message.type === 'monitor_stopped'
      ) {
        refetch()
      }
    },
  })

  if (!stats) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <Shield className="mx-auto h-12 w-12 animate-pulse text-primary" />
          <p className="mt-4 text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  const threatData = [
    { name: 'Today', value: stats.threats_today, color: '#ef4444' },
    { name: 'This Week', value: stats.threats_week, color: '#f97316' },
    { name: 'Total', value: stats.threats_total, color: '#eab308' },
  ]

  const monitorData = [
    { name: 'Active', value: stats.monitors_active, color: '#22c55e' },
    { name: 'Inactive', value: stats.monitors_total - stats.monitors_active, color: '#6b7280' },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Real-time protection monitoring and system overview
        </p>
        {isConnected && (
          <Badge variant="success" className="mt-2">
            <Activity className="mr-1 h-3 w-3" />
            Live
          </Badge>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Protection Status */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Protection</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.protection_enabled ? 'Enabled' : 'Disabled'}
            </div>
            <p className="text-xs text-muted-foreground">
              {stats.monitors_active} of {stats.monitors_total} monitors active
            </p>
          </CardContent>
        </Card>

        {/* Threats Today */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Threats Today</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.threats_today}</div>
            <p className="text-xs text-muted-foreground">
              {stats.threats_week} this week
            </p>
          </CardContent>
        </Card>

        {/* CPU Usage */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.system_resources.cpu_usage.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">System resource usage</p>
          </CardContent>
        </Card>

        {/* Memory Usage */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Memory</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.system_resources.memory_usage.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">RAM consumption</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Threat Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Threat Distribution</CardTitle>
            <CardDescription>Detected threats over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={threatData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {threatData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Monitor Status */}
        <Card>
          <CardHeader>
            <CardTitle>Monitor Status</CardTitle>
            <CardDescription>Active vs inactive monitors</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={monitorData}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Recent Scans */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Scans</CardTitle>
            <CardDescription>Last 5 scan operations</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stats.recent_scans.slice(0, 5).map((scan) => (
                <div
                  key={scan.id}
                  className="flex items-center justify-between border-b pb-2 last:border-0"
                >
                  <div className="flex-1">
                    <p className="text-sm font-medium">{scan.path}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(scan.started_at), { addSuffix: true })}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm">
                      {scan.files_scanned} files
                    </p>
                    {scan.threats_found > 0 && (
                      <Badge variant="destructive" className="text-xs">
                        {scan.threats_found} threats
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
              {stats.recent_scans.length === 0 && (
                <p className="text-sm text-muted-foreground">No recent scans</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Recent Threats */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Threats</CardTitle>
            <CardDescription>Latest threat detections</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stats.recent_threats.slice(0, 5).map((threat) => (
                <div
                  key={threat.id}
                  className="flex items-center justify-between border-b pb-2 last:border-0"
                >
                  <div className="flex-1">
                    <p className="text-sm font-medium">{threat.name}</p>
                    <p className="text-xs text-muted-foreground">{threat.path}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(threat.detected_at), { addSuffix: true })}
                    </p>
                  </div>
                  <div>
                    <Badge
                      variant={
                        threat.severity === 'critical'
                          ? 'destructive'
                          : threat.severity === 'high'
                          ? 'warning'
                          : 'secondary'
                      }
                    >
                      {threat.severity}
                    </Badge>
                  </div>
                </div>
              ))}
              {stats.recent_threats.length === 0 && (
                <p className="text-sm text-muted-foreground">No threats detected</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
