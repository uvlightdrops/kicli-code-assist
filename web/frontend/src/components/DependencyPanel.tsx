import React, { useState } from 'react';
import axios from 'axios';
import { AlertCircle, Package, Link2 } from 'lucide-react';
import { useProject } from '../hooks/useProject';

export const DependencyPanel: React.FC<{ selectedFile: string | null }> = ({ selectedFile }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const { current: currentProject } = useProject();

  const analyzeDependencies = async () => {
    if (!selectedFile) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/api/agent/dependencies', {
        path: selectedFile,
        is_dir: false,
        project: currentProject?.path || '',
      });
      setResult(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze dependencies');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-4 h-full">
      {/* Controls */}
      <div className="flex gap-2">
        <button
          onClick={analyzeDependencies}
          disabled={!selectedFile || loading}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          {loading ? 'Analyzing...' : 'Analyze Dependencies'}
        </button>
        {selectedFile && <span className="text-sm text-gray-600">{selectedFile}</span>}
      </div>

      {/* Results */}
      <div className="flex-1 overflow-y-auto">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded p-3 flex gap-2">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <span className="text-sm text-red-700">{error}</span>
          </div>
        )}

        {result && (
          <div className="space-y-4">
            {/* Summary */}
            <div className="bg-blue-50 border border-blue-200 rounded p-3">
              <h3 className="font-semibold text-blue-900 mb-2">Dependency Summary</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>Total Imports: <span className="font-semibold">{result.total_imports}</span></div>
                <div>External Packages: <span className="font-semibold">{result.external_packages?.length || 0}</span></div>
                <div>Circular Deps: <span className="font-semibold text-red-600">{result.circular_dependencies?.length || 0}</span></div>
                <div>Unused Imports: <span className="font-semibold text-orange-600">{result.unused_imports_count || 0}</span></div>
              </div>
            </div>

            {/* External Packages */}
            {result.external_packages && result.external_packages.length > 0 && (
              <div>
                <h3 className="font-semibold text-sm mb-2 flex items-center gap-2">
                  <Package className="w-4 h-4" />
                  External Packages ({result.external_packages.length})
                </h3>
                <div className="bg-gray-50 rounded p-2">
                  <div className="flex flex-wrap gap-2">
                    {result.external_packages.map((pkg: string, i: number) => (
                      <span key={i} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                        {pkg}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Circular Dependencies */}
            {result.circular_dependencies && result.circular_dependencies.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded p-3">
                <h3 className="font-semibold text-red-900 mb-2 flex items-center gap-2">
                  <Link2 className="w-4 h-4" />
                  ⚠️ Circular Dependencies
                </h3>
                <ul className="text-sm text-red-700 space-y-1">
                  {result.circular_dependencies.map((dep: [string, string], i: number) => (
                    <li key={i}>{dep[0]} ↔ {dep[1]}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Modules */}
            {result.modules && Object.keys(result.modules).length > 0 && (
              <div>
                <h3 className="font-semibold text-sm mb-2">Analyzed Modules</h3>
                <div className="space-y-2 bg-gray-50 rounded p-2 max-h-48 overflow-y-auto">
                  {Object.entries(result.modules).map(([modPath, modInfo]: [string, any]) => (
                    <div key={modPath} className="text-xs border-l-2 border-blue-300 pl-2">
                      <div className="font-mono text-blue-700">{modPath}</div>
                      <div className="text-gray-600">
                        {modInfo.imports?.length || 0} imports
                        {modInfo.unused_imports?.length > 0 && ` (${modInfo.unused_imports.length} unused)`}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {!result && !error && !loading && (
          <div className="text-gray-500 text-center py-8">
            Select a file and click "Analyze Dependencies" to get started
          </div>
        )}
      </div>
    </div>
  );
};
