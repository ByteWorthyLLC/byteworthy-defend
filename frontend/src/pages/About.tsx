import { Shield, Heart, Code, Users } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';

export default function About() {
  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="text-center mb-12">
        <Shield className="w-20 h-20 text-blue-600 mx-auto mb-4" />
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
          HifzDefend
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-400 mb-4">
          حفظ (Hifz) - Protection/Preservation
        </p>
        <p className="text-lg text-gray-600 dark:text-gray-400">
          Preserving Your Digital Safety
        </p>
      </div>

      {/* Version Info */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Version Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex justify-between">
            <span className="text-gray-600 dark:text-gray-400">Version:</span>
            <span className="font-mono">0.3.0</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600 dark:text-gray-400">Release Date:</span>
            <span>January 27, 2026</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600 dark:text-gray-400">Build:</span>
            <span className="font-mono">Production</span>
          </div>
        </CardContent>
      </Card>

      {/* About */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Heart className="w-5 h-5 mr-2 text-red-500" />
            About HifzDefend
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-gray-700 dark:text-gray-300">
            HifzDefend is a professional Windows antivirus solution built on ClamAV,
            featuring AI-powered malware analysis, real-time protection, and behavioral
            monitoring.
          </p>
          <p className="text-gray-700 dark:text-gray-300">
            Our mission is to provide enterprise-grade security that's accessible to
            everyone, combining traditional signature-based detection with cutting-edge
            AI analysis.
          </p>
        </CardContent>
      </Card>

      {/* Features */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Key Features</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                Core Protection
              </h4>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                <li>• ClamAV virus engine</li>
                <li>• Real-time monitoring</li>
                <li>• Automatic quarantine</li>
                <li>• Scheduled scans</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                Advanced Features
              </h4>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                <li>• AI malware analysis</li>
                <li>• Behavioral detection</li>
                <li>• YARA rules engine</li>
                <li>• Threat intelligence</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Technology */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Code className="w-5 h-5 mr-2" />
            Technology Stack
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="font-semibold mb-2">Backend</p>
              <ul className="text-gray-600 dark:text-gray-400 space-y-1">
                <li>• Python 3.10+</li>
                <li>• FastAPI</li>
                <li>• ClamAV</li>
                <li>• SQLite</li>
              </ul>
            </div>
            <div>
              <p className="font-semibold mb-2">Frontend</p>
              <ul className="text-gray-600 dark:text-gray-400 space-y-1">
                <li>• React 18</li>
                <li>• TypeScript</li>
                <li>• Tailwind CSS</li>
                <li>• Vite</li>
              </ul>
            </div>
            <div>
              <p className="font-semibold mb-2">AI & Security</p>
              <ul className="text-gray-600 dark:text-gray-400 space-y-1">
                <li>• Claude AI</li>
                <li>• YARA</li>
                <li>• Cryptography</li>
                <li>• JWT</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Credits */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Users className="w-5 h-5 mr-2" />
            Credits & Acknowledgments
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <p className="font-semibold">ClamAV Team</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Open-source antivirus engine
            </p>
          </div>
          <div>
            <p className="font-semibold">Anthropic</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Claude AI for malware analysis
            </p>
          </div>
          <div>
            <p className="font-semibold">Open Source Community</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Python, React, and security tools
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Footer */}
      <div className="text-center mt-8 text-sm text-gray-500 dark:text-gray-400">
        <p>© 2026 ByteWorthy. All rights reserved.</p>
        <p className="mt-2">
          <a href="https://hifzdefend.com" className="text-blue-600 hover:underline">
            Website
          </a>
          {' • '}
          <a href="https://docs.hifzdefend.com" className="text-blue-600 hover:underline">
            Documentation
          </a>
          {' • '}
          <a href="https://github.com/byteworthy/Hafz-Defend" className="text-blue-600 hover:underline">
            GitHub
          </a>
        </p>
      </div>
    </div>
  );
}
