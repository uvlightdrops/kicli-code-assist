import React, { useState } from 'react';
import axios from 'axios';
import { AlertCircle, Zap, Lightbulb } from 'lucide-react';
import { useProject } from '../hooks/useProject';

export const RefactoringPanel: React.FC<{ selectedFile: string | null }> = ({ selectedFile }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const { current: currentProject } = useProject();

  const analyzeRefactoring = async () => {
    if (!selectedFile) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/api/agent/refactor', {
        file: selectedFile,
        project: currentProject?.path || '',
      });
      setResult(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze refactoring');
    } finally {
      setLoading(false);
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return 'bg-green-50 border-green-200 text-green-900';
      case 'medium': return 'bg-yellow-50 border-yellow-200 text-yellow-900';
      case 'hard': return 'bg-red-50 border-red-200 text-red-900';
      default: return 'bg-gray-50 border-gray-200 text-gray-900';
    }
  };

  const getPriorityLabel = (priority: number) => {
    const labels = ['', 'Critical', 'High', 'Medium', 'Low', 'Nice-to-have'];
    return labels[priority] || `Priority ${priority}`;
  };

  return (
    <div className="flex flex-col gap-4 h-full">
      {/* Controls */}
      <div className="flex gap-2">
        <button
          onClick={analyzeRefactoring}
          disabled={!selectedFile || loading}
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
        >
          {loading ? 'Analyzing...' : 'Analyze Refactoring'}
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
              <h3 className="font-semibold text-blue-900 mb-2">Refactoring Opportunities</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>Issues Found: <span className="font-semibold">{result.total_issues}</span></div>
                <div>Potential: <span className="font-semibold">{(result.improvement_potential * 100).toFixed(0)}%</span></div>
              </div>
            </div>

            {/* Suggestions */}
            {result.suggestions && result.suggestions.length > 0 ? (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {result.suggestions.map((suggestion: any, idx: number) => (
                  <div
                    key={idx}
                    className={`border rounded p-3 ${getDifficultyColor(suggestion.difficulty)}`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div>
                        <div className="font-semibold flex items-center gap-2">
                          <Lightbulb className="w-4 h-4" />
                          {suggestion.refactoring_type.replace(/_/g, ' ')}
                        </div>
                        <div className="text-xs mt-1">{suggestion.location}</div>
                      </div>
                      <div className="flex gap-2">
                        <span className="px-2 py-1 bg-white rounded text-xs font-semibold">
                          {getPriorityLabel(suggestion.priority)}
                        </span>
                        <span className="px-2 py-1 bg-white rounded text-xs">
                          Impact: {(suggestion.impact_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>

                    <div className="text-sm mb-2">
                      <p className="mb-2">{suggestion.explanation}</p>
                    </div>

                    {/* Before/After code snippets */}
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="bg-red-50 rounded p-2 border border-red-100 max-h-20 overflow-y-auto">
                        <div className="font-mono text-red-700 whitespace-pre-wrap break-words">
                          {suggestion.current_code}
                        </div>
                      </div>
                      <div className="bg-green-50 rounded p-2 border border-green-100 max-h-20 overflow-y-auto">
                        <div className="font-mono text-green-700 whitespace-pre-wrap break-words">
                          {suggestion.suggested_code}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : result.suggestions && result.suggestions.length === 0 ? (
              <div className="text-center text-green-700 py-8 bg-green-50 rounded">
                ✅ No refactoring issues found! Code looks good.
              </div>
            ) : null}
          </div>
        )}

        {!result && !error && !loading && (
          <div className="text-gray-500 text-center py-8">
            Select a file and click "Analyze Refactoring" to get started
          </div>
        )}
      </div>
    </div>
  );
};
