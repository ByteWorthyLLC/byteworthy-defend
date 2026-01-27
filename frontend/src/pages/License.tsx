import { useEffect, useState } from 'react';
import { Key, CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';

interface LicenseInfo {
  status: string;
  license_type?: string;
  customer_email?: string;
  expires_at?: string;
  features?: {
    ai_analysis: boolean;
    real_time_protection: boolean;
    cloud_backup: boolean;
    priority_support: boolean;
  };
  error?: string;
  warnings?: string[];
}

export default function License() {
  const [licenseInfo, setLicenseInfo] = useState<LicenseInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [activating, setActivating] = useState(false);
  const [licenseKey, setLicenseKey] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadLicenseInfo();
  }, []);

  const loadLicenseInfo = async () => {
    try {
      const response = await fetch('/api/v1/licensing/info');
      const data = await response.json();
      setLicenseInfo(data);
    } catch (err) {
      console.error('Failed to load license info:', err);
    } finally {
      setLoading(false);
    }
  };

  const activateLicense = async () => {
    if (!licenseKey.trim()) {
      setError('Please enter a license key');
      return;
    }

    setActivating(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('/api/v1/licensing/activate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ license_key: licenseKey }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Activation failed');
      }

      const data = await response.json();
      setSuccess('License activated successfully!');
      setLicenseKey('');
      await loadLicenseInfo();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Activation failed');
    } finally {
      setActivating(false);
    }
  };

  const deactivateLicense = async () => {
    if (!confirm('Are you sure you want to deactivate this license?')) {
      return;
    }

    try {
      const response = await fetch('/api/v1/licensing/deactivate', {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Deactivation failed');
      }

      setSuccess('License deactivated successfully');
      await loadLicenseInfo();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Deactivation failed');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading license info...</p>
        </div>
      </div>
    );
  }

  const isActive = licenseInfo?.status === 'active';
  const isUnlicensed = licenseInfo?.status === 'unlicensed';

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex items-center mb-8">
        <Key className="w-8 h-8 text-blue-600 mr-3" />
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">License Management</h1>
      </div>

      {/* Current License Status */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center">
            {isActive ? (
              <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
            ) : isUnlicensed ? (
              <XCircle className="w-5 h-5 text-gray-400 mr-2" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-yellow-600 mr-2" />
            )}
            {isActive ? 'Active License' : isUnlicensed ? 'No Active License' : 'License Issue'}
          </CardTitle>
          <CardDescription>
            {isActive
              ? 'Your HifzDefend installation is properly licensed'
              : isUnlicensed
              ? 'Activate a license to unlock all features'
              : licenseInfo?.error}
          </CardDescription>
        </CardHeader>

        {isActive && licenseInfo && (
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">License Type</p>
                <p className="font-semibold capitalize">{licenseInfo.license_type}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Licensed To</p>
                <p className="font-semibold">{licenseInfo.customer_email}</p>
              </div>
              {licenseInfo.expires_at && (
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Expires</p>
                  <p className="font-semibold">
                    {new Date(licenseInfo.expires_at).toLocaleDateString()}
                  </p>
                </div>
              )}
            </div>

            {licenseInfo.warnings && licenseInfo.warnings.length > 0 && (
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                <div className="flex">
                  <AlertTriangle className="w-5 h-5 text-yellow-600 mr-2 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-semibold text-yellow-800 dark:text-yellow-200 mb-1">
                      Warnings
                    </p>
                    <ul className="text-sm text-yellow-700 dark:text-yellow-300 space-y-1">
                      {licenseInfo.warnings.map((warning, i) => (
                        <li key={i}>• {warning}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {licenseInfo.features && (
              <div>
                <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                  Enabled Features
                </p>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(licenseInfo.features).map(([key, enabled]) => (
                    <div key={key} className="flex items-center">
                      {enabled ? (
                        <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                      ) : (
                        <XCircle className="w-4 h-4 text-gray-400 mr-2" />
                      )}
                      <span className="text-sm capitalize">
                        {key.replace(/_/g, ' ')}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="pt-4 border-t">
              <Button
                onClick={deactivateLicense}
                variant="outline"
                className="text-red-600 hover:text-red-700"
              >
                Deactivate License
              </Button>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Activate License */}
      <Card>
        <CardHeader>
          <CardTitle>Activate License</CardTitle>
          <CardDescription>
            Enter your license key to activate HifzDefend
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <div className="flex">
                <XCircle className="w-5 h-5 text-red-600 mr-2 flex-shrink-0" />
                <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
              </div>
            </div>
          )}

          {success && (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <div className="flex">
                <CheckCircle className="w-5 h-5 text-green-600 mr-2 flex-shrink-0" />
                <p className="text-sm text-green-800 dark:text-green-200">{success}</p>
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              License Key
            </label>
            <input
              type="text"
              value={licenseKey}
              onChange={(e) => setLicenseKey(e.target.value)}
              placeholder="XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={activating}
            />
          </div>

          <Button
            onClick={activateLicense}
            disabled={!licenseKey.trim() || activating}
            className="w-full"
          >
            {activating ? 'Activating...' : 'Activate License'}
          </Button>

          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="flex">
              <Info className="w-5 h-5 text-blue-600 mr-2 flex-shrink-0" />
              <div className="text-sm text-blue-800 dark:text-blue-200">
                <p className="font-semibold mb-1">Need a license?</p>
                <p>
                  Visit{' '}
                  <a href="https://hifzdefend.com" className="underline">
                    hifzdefend.com
                  </a>{' '}
                  to purchase or start a free trial.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
