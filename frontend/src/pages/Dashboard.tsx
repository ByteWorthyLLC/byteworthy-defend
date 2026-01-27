import { useEffect, useState } from 'react';
import { Activity, AlertTriangle, Archive, Shield } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { statsApi } from '../services/api';
import type { StatsOverview, RecentScan, ThreatTimelinePoint } from '../types';

export default function Dashboard() {
  const [stats, setStats] = useState<StatsOverview | null>(null);
  const [recentScans, setRecentScans] = useState<RecentScan[]>([]);
  const [timeline, setTimeline] = useState<ThreatTimelinePoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [statsRes, scansRes, timelineRes] = await Promise.all([
        statsApi.overview(),
        statsApi.recentScans(5),
        statsApi.threatsTimeline(7),
      ]);

      setStats(statsRes.data);
      setRecentScans(scansRes.data);
      setTimeline(timelineRes.data);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">Dashboard</h1>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          icon={Activity}
          title="Total Scans"
          value={stats?.total_scans || 0}
          color="blue"
        />
        <StatCard
          icon={AlertTriangle}
          title="Threats Found"
          value={stats?.threats_found || 0}
          color="red"
        />
        <StatCard
          icon={Archive}
          title="Files Quarantined"
          value={stats?.files_quarantined || 0}
          color="yellow"
        />
        <StatCard
          icon={Shield}
          title="System Status"
          value={stats?.system_status || 'unknown'}
          color={stats?.system_status === 'online' ? 'green' : 'gray'}
          isStatus
        />
      </div>

      {/* Threats Timeline Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Threats Timeline (Last 7 Days)
        </h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={timeline}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="date" stroke="#9CA3AF" />
            <YAxis stroke="#9CA3AF" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1F2937',
                border: 'none',
                borderRadius: '0.5rem',
                color: '#F3F4F6',
              }}
            />
            <Line type="monotone" dataKey="threats" stroke="#EF4444" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Recent Scans */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Recent Scans</h2>
        <div className="space-y-3">
          {recentScans.map((scan) => (
            <div
              key={scan.scan_id}
              className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
            >
              <div className="flex-1">
                <p className="font-medium text-gray-900 dark:text-white truncate">{scan.path}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {new Date(scan.timestamp).toLocaleString()}
                </p>
              </div>
              <div className="flex items-center space-x-3">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusBadgeColor(scan.status)}`}>
                  {scan.status}
                </span>
                {scan.threats_found > 0 && (
                  <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm font-medium">
                    {scan.threats_found} threats
                  </span>
                )}
              </div>
            </div>
          ))}
          {recentScans.length === 0 && (
            <p className="text-center text-gray-500 dark:text-gray-400 py-8">
              No recent scans
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, title, value, color, isStatus }: {
  icon: any;
  title: string;
  value: number | string;
  color: string;
  isStatus?: boolean;
}) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400',
    red: 'bg-red-100 text-red-600 dark:bg-red-900/20 dark:text-red-400',
    yellow: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/20 dark:text-yellow-400',
    green: 'bg-green-100 text-green-600 dark:bg-green-900/20 dark:text-green-400',
    gray: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {isStatus ? (
              <span className={`capitalize ${value === 'online' ? 'text-green-600' : 'text-gray-500'}`}>
                {value}
              </span>
            ) : (
              value
            )}
          </p>
        </div>
        <div className={`p-3 rounded-full ${colorClasses[color as keyof typeof colorClasses]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
}

function getStatusBadgeColor(status: string) {
  const colors = {
    pending: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
    running: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
    completed: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
    failed: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
    cancelled: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
  };
  return colors[status as keyof typeof colors] || colors.pending;
}
