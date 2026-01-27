import { Outlet, NavLink } from 'react-router-dom';
import { Shield, ScanSearch, Archive, Settings } from 'lucide-react';

export default function Layout() {
  const navItems = [
    { to: '/', icon: Shield, label: 'Dashboard' },
    { to: '/scans', icon: ScanSearch, label: 'Scans' },
    { to: '/quarantine', icon: Archive, label: 'Quarantine' },
    { to: '/settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <div className="flex h-screen bg-gray-100 dark:bg-gray-900">
      {/* Sidebar */}
      <aside className="w-64 bg-white dark:bg-gray-800 shadow-lg">
        <div className="p-6">
          <div className="flex items-center space-x-3">
            <Shield className="w-8 h-8 text-blue-600" />
            <div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">HifzDefend</h1>
              <p className="text-xs text-gray-500 dark:text-gray-400">حفظ - Protection</p>
            </div>
          </div>
        </div>

        <nav className="mt-6">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-6 py-3 text-gray-700 dark:text-gray-200 hover:bg-blue-50 dark:hover:bg-gray-700 transition-colors ${
                  isActive ? 'bg-blue-50 dark:bg-gray-700 border-r-4 border-blue-600' : ''
                }`
              }
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="absolute bottom-0 w-64 p-6 border-t dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Version 0.2.0
          </p>
          <p className="text-xs text-gray-400 dark:text-gray-500">
            © 2026 HifzDefend
          </p>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
