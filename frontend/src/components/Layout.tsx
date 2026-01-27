import { Outlet, NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Shield,
  Scan,
  Archive,
  Brain,
  FileText,
  Settings,
  Activity,
  Key,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Badge } from './ui/badge'
import { useSystemStatus } from '@/hooks/useAPI'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Monitors', href: '/monitors', icon: Activity },
  { name: 'Scanner', href: '/scanner', icon: Scan },
  { name: 'Quarantine', href: '/quarantine', icon: Archive },
  { name: 'AI Assistant', href: '/ai', icon: Brain },
  { name: 'Logs', href: '/logs', icon: FileText },
  { name: 'License', href: '/license', icon: Key },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Layout() {
  const { data: systemStatus } = useSystemStatus()

  const getProtectionBadge = () => {
    const status = systemStatus?.protection_status || 'unknown'
    const variants = {
      enabled: { variant: 'success' as const, text: 'Protected' },
      disabled: { variant: 'destructive' as const, text: 'Disabled' },
      paused: { variant: 'warning' as const, text: 'Paused' },
      error: { variant: 'destructive' as const, text: 'Error' },
      unknown: { variant: 'outline' as const, text: 'Unknown' },
    }

    const badgeInfo = variants[status as keyof typeof variants] || variants.unknown

    return <Badge variant={badgeInfo.variant}>{badgeInfo.text}</Badge>
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-64 border-r bg-card">
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center gap-2 border-b px-6">
            <Shield className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-lg font-bold">HifzDefend</h1>
              <p className="text-xs text-muted-foreground">Real-time Protection</p>
            </div>
          </div>

          {/* Status Badge */}
          <div className="border-b px-6 py-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Status</span>
              {getProtectionBadge()}
            </div>
            {systemStatus && (
              <div className="mt-2 text-xs text-muted-foreground">
                <div className="flex justify-between">
                  <span>Active Monitors</span>
                  <span>
                    {systemStatus.monitors.active}/{systemStatus.monitors.total}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Threats (Total)</span>
                  <span>{systemStatus.threats.total}</span>
                </div>
              </div>
            )}
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 px-3 py-4">
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                end={item.href === '/'}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  )
                }
              >
                <item.icon className="h-5 w-5" />
                {item.name}
              </NavLink>
            ))}
          </nav>

          {/* Footer */}
          <div className="border-t px-6 py-4">
            <p className="text-xs text-muted-foreground">
              Version 0.3.0
              <br />
              © 2024 HifzDefend
            </p>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <div className="container mx-auto p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
