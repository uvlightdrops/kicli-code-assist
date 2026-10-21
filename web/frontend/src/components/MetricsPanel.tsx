import React, { useState } from 'react';
import axios from 'axios';
import { AlertCircle, BarChart3, TrendingUp } from 'lucide-react';

export const MetricsPanel: React.FC<{ selectedFile: string | null }> = ({ selectedFile }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const analyzeMetrics = async () => {
    if (!selectedFile) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/api/agent/metrics', {
        file: selectedFile,
      });
      setResult(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze metrics');
    } finally {
      setLoading(false);
    }
  };

  const getMaintainabilityBadge = (index: number) => {
    if (index >= 80) return { color: 'bg-green-100 text-green-800', label: 'Excellent' };
    if (index >= 60) return { color: 'bg-yellow-100 text-yellow-800', label: 'Good' };
    if (index >= 40) return { color: 'bg-orange-100 text-orange-800', label: 'Fair' };
    return { color: 'bg-red-100 text-red-800', label: 'Poor' };
  };

  const getComplexityColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600';
      case 'medium': return 'text-yellow-600';
      case 'high': return 'text-orange-600';
      case 'very_high': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="flex flex-col gap-4 h-full">
      {/* Controls */}
      <div className="flex gap-2">
        <button
          onClick={analyzeMetrics}
          disabled={!selectedFile || loading}
          className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50"
        >
          {loading ? 'Analyzing...' : 'Analyze Metrics'}
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
            {/* Key Metrics */}
            <div className="grid grid-cols-2 gap-3">
              {/* Maintainability Index */}
              <div className="border rounded p-3">
                <div className="text-xs text-gray-600 mb-1">Maintainability</div>
                <div className={`px-3 py-1 rounded text-sm font-semibold ${getMaintainabilityBadge(result.maintainability_index).color}`}>
                  {result.maintainability_index.toFixed(1)} - {getMaintainabilityBadge(result.maintainability_index).label}
                </div>
              </div>

              {/* Duplication */}
              <div className="border rounded p-3">
                <div className="text-xs text-gray-600 mb-1">Code Duplication</div>
                <div className="text-lg font-semibold">{(result.duplication_ratio * 100).toFixed(1)}%</div>
              </div>

              {/* LOC */}
              <div className="border rounded p-3">
                <div className="text-xs text-gray-600 mb-1">Lines of Code</div>
                <div>
                  <div className="text-lg font-semibold">{result.total_lines}</div>
                  <div className="text-xs text-gray-500">Code: {result.code_lines} | Comments: {result.comment_lines}</div>
                </div>
              </div>

              {/* Complexity */}
              <div className="border rounded p-3">
                <div className="text-xs text-gray-600 mb-1">Avg Complexity</div>
                <div className={`text-lg font-semibold ${getComplexityColor(result.average_complexity > 5 ? 'high' : 'low')}`}>
                  {result.average_complexity.toFixed(2)}
                </div>
              </div>
            </div>

            {/* Structure */}
            <div className="bg-blue-50 border border-blue-200 rounded p-3">
              <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                <BarChart3 className="w-4 h-4" />
                Code Structure
              </h3>
              <div className="grid grid-cols-3 gap-2 text-sm">
                <div>Classes: <span className="font-semibold">{result.number_of_classes}</span></div>
                <div>Functions: <span className="font-semibold">{result.number_of_functions}</span></div>
                <div>Avg Func Length: <span className="font-semibold">{result.average_function_length.toFixed(1)} LOC</span></div>
              </div>
            </div>

            {/* Functions Table */}
            {result.functions && result.functions.length > 0 && (
              <div>
                <h3 className="font-semibold text-sm mb-2 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  Function Complexity
                </h3>
                <div className="overflow-y-auto max-h-48 bg-gray-50 rounded border border-gray-200">
                  <table className="w-full text-xs">
                    <thead className="bg-gray-200 sticky top-0">
                      <tr>
                        <th className="px-2 py-1 text-left">Function</th>
                        <th className="px-2 py-1 text-center">LOC</th>
                        <th className="px-2 py-1 text-center">Complexity</th>
                        <th className="px-2 py-1 text-center">Params</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {result.functions.map((func: any, idx: number) => (
                        <tr key={idx} className="hover:bg-gray-100">
                          <td className="px-2 py-1 font-mono">{func.name}</td>
                          <td className="px-2 py-1 text-center">{func.lines_of_code}</td>
                          <td className={`px-2 py-1 text-center font-semibold ${getComplexityColor(func.complexity_level)}`}>
                            {func.cyclomatic_complexity}
                          </td>
                          <td className="px-2 py-1 text-center">{func.number_of_parameters}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {!result && !error && !loading && (
          <div className="text-gray-500 text-center py-8">
            Select a file and click "Analyze Metrics" to get started
          </div>
        )}
      </div>
    </div>
  );
};
