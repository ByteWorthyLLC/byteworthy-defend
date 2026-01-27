import { useEffect, useState } from 'react';
import { Save, RotateCcw } from 'lucide-react';
import { configApi } from '../services/api';
import type { Config } from '../types';

export default function Settings() {
  const [config, setConfig] = useState<Config | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const response = await configApi.get();
      setConfig(response.data);
    } catch (error) {
      console.error('Failed to load config:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    if (!config) return;

    setSaving(true);
    try {
      await configApi.update(config);
      alert('Configuration saved successfully!');
    } catch (error) {
      console.error('Failed to save config:', error);
      alert('Failed to save configuration.');
    } finally {
      setSaving(false);
    }
  };

  const resetToDefaults = async () => {
    if (!confirm('Are you sure you want to reset to default settings?')) return;

    try {
      const response = await configApi.getDefaults();
      setConfig(response.data);
    } catch (error) {
      console.error('Failed to load defaults:', error);
      alert('Failed to reset to defaults.');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading settings...</p>
        </div>
      </div>
    );
  }

  if (!config) return null;

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Settings</h1>
        <div className="flex space-x-4">
          <button
            onClick={resetToDefaults}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center space-x-2"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Reset to Defaults</span>
          </button>
          <button
            onClick={saveConfig}
            disabled={saving}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? 'Saving...' : 'Save Changes'}</span>
          </button>
        </div>
      </div>

      <div className="space-y-6">
        {/* Scanning Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Scanning Settings
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Max File Size (bytes)
              </label>
              <input
                type="number"
                value={config.scanning.max_file_size}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    scanning: { ...config.scanning, max_file_size: parseInt(e.target.value) },
                  })
                }
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              />
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Maximum size of files to scan (100 MB = 104857600 bytes)
              </p>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="scan-archives"
                checked={config.scanning.scan_archives}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    scanning: { ...config.scanning, scan_archives: e.target.checked },
                  })
                }
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label
                htmlFor="scan-archives"
                className="ml-2 text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Scan Archive Files
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Excluded Paths (one per line)
              </label>
              <textarea
                value={config.scanning.excluded_paths.join('\n')}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    scanning: {
                      ...config.scanning,
                      excluded_paths: e.target.value.split('\n').filter((p) => p.trim()),
                    },
                  })
                }
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                placeholder="C:\Windows\System32"
              />
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Paths to exclude from scanning
              </p>
            </div>
          </div>
        </div>

        {/* Quarantine Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Quarantine Settings
          </h2>
          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="quarantine-enabled"
                checked={config.quarantine.enabled}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    quarantine: { ...config.quarantine, enabled: e.target.checked },
                  })
                }
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label
                htmlFor="quarantine-enabled"
                className="ml-2 text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Enable Quarantine
              </label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="auto-quarantine"
                checked={config.quarantine.auto_quarantine}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    quarantine: { ...config.quarantine, auto_quarantine: e.target.checked },
                  })
                }
                disabled={!config.quarantine.enabled}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 disabled:opacity-50"
              />
              <label
                htmlFor="auto-quarantine"
                className="ml-2 text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Automatically Quarantine Threats
              </label>
            </div>
          </div>
        </div>

        {/* ClamAV Settings (Read-only) */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            ClamAV Connection
          </h2>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Host
                </label>
                <input
                  type="text"
                  value={config.clamav.host}
                  disabled
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Port
                </label>
                <input
                  type="number"
                  value={config.clamav.port}
                  disabled
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400"
                />
              </div>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              ClamAV connection settings are read-only for security
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
