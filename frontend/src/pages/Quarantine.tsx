import { useEffect, useState } from 'react';
import { Trash2, RotateCcw } from 'lucide-react';
import { quarantineApi } from '../services/api';
import type { QuarantineFile } from '../types';

export default function Quarantine() {
  const [files, setFiles] = useState<QuarantineFile[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    try {
      const response = await quarantineApi.list(1, 20);
      setFiles(response.data.files);
    } catch (error) {
      console.error('Failed to load quarantine files:', error);
    } finally {
      setLoading(false);
    }
  };

  const restoreFile = async (fileId: string) => {
    if (!confirm('Are you sure you want to restore this file? It may be dangerous.')) return;

    try {
      await quarantineApi.restore(fileId);
      await loadFiles();
      alert('File restore requested (implementation pending)');
    } catch (error) {
      console.error('Failed to restore file:', error);
      alert('Failed to restore file.');
    }
  };

  const deleteFile = async (fileId: string) => {
    if (!confirm('Are you sure you want to permanently delete this file?')) return;

    try {
      await quarantineApi.delete(fileId);
      await loadFiles();
    } catch (error) {
      console.error('Failed to delete file:', error);
      alert('Failed to delete file.');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading quarantine...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">Quarantine Management</h1>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                File Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Original Path
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Threat Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Date
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Size
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {files.map((file) => (
              <tr key={file.file_id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {file.file_id}
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-xs">
                    {file.original_path}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-xs font-medium">
                    {file.threat_name}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {new Date(file.quarantine_date).toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {(file.file_size / 1024).toFixed(2)} KB
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="flex justify-end space-x-2">
                    <button
                      onClick={() => restoreFile(file.file_id)}
                      className="text-blue-600 hover:text-blue-900 dark:text-blue-400"
                      title="Restore file"
                    >
                      <RotateCcw className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => deleteFile(file.file_id)}
                      className="text-red-600 hover:text-red-900 dark:text-red-400"
                      title="Delete permanently"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {files.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 dark:text-gray-400">No quarantined files</p>
          </div>
        )}
      </div>
    </div>
  );
}
