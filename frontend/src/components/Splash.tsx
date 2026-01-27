import { Shield } from 'lucide-react';

interface SplashScreenProps {
  version: string;
  progress?: number;
}

export function SplashScreen({ version, progress = 0 }: SplashScreenProps) {
  return (
    <div className="fixed inset-0 bg-gradient-to-br from-blue-600 to-blue-900 flex items-center justify-center">
      <div className="text-center">
        {/* Logo */}
        <div className="mb-8 animate-pulse">
          <Shield className="w-32 h-32 text-white mx-auto drop-shadow-2xl" />
        </div>

        {/* App Name */}
        <h1 className="text-5xl font-bold text-white mb-2 drop-shadow-lg">
          HifzDefend
        </h1>

        {/* Tagline */}
        <p className="text-xl text-blue-100 mb-8">
          Preserving Your Digital Safety
        </p>

        {/* Loading Indicator */}
        <div className="w-64 mx-auto">
          <div className="h-2 bg-blue-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-white transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-sm text-blue-200 mt-2">Loading...</p>
        </div>

        {/* Version */}
        <p className="text-sm text-blue-300 mt-8">
          Version {version}
        </p>
      </div>
    </div>
  );
}
