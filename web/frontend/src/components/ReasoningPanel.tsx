import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface ThinkingStep {
  step: number;
  title: string;
  content: string;
  duration_ms: number;
  status: string;
}

interface ReasoningResult {
  status: string;
  request_id: string;
  file: string;
  query: string;
  thinking: ThinkingStep[];
  conclusion: string;
  confidence: number;
  total_duration_ms: number;
  error?: string;
}

interface ReasoningPanelProps {
  file?: string;
  isVisible: boolean;
}

export function ReasoningPanel({ file, isVisible }: ReasoningPanelProps) {
  const [result, setResult] = useState<ReasoningResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('How can this code be improved?');
  const [error, setError] = useState('');

  const handleReason = async () => {
    if (!file) {
      setError('No file selected');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await axios.post('/api/agent/reason', {
        file,
        query,
      });

      if (response.data.status === 'ok') {
        setResult(response.data);
      } else {
        setError(response.data.error || 'Reasoning failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!isVisible) return null;

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      <h2 className="text-lg font-bold text-white">🧠 Reasoning</h2>

      {/* Query Input */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-300">Question</label>
        <textarea
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="What would you like to know about this code?"
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm resize-none h-20"
        />
        <button
          onClick={handleReason}
          disabled={loading || !file}
          className="w-full px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Thinking...' : 'Start Reasoning'}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-red-900/30 border border-red-700 rounded text-red-200 text-sm">
          {error}
        </div>
      )}

      {/* Thinking Steps */}
      {result && (
        <div className="space-y-3">
          <div className="text-sm text-gray-400">
            Total time: {result.total_duration_ms}ms • Confidence: {(result.confidence * 100).toFixed(0)}%
          </div>

          {result.thinking.map((step, idx) => (
            <div
              key={idx}
              className={`p-3 rounded border ${
                step.status === 'error'
                  ? 'bg-red-900/20 border-red-700'
                  : step.status === 'complete'
                  ? 'bg-green-900/20 border-green-700'
                  : 'bg-yellow-900/20 border-yellow-700'
              }`}
            >
              <div className="flex items-start justify-between mb-1">
                <h4 className="font-semibold text-sm text-white">
                  {step.step}. {step.title}
                </h4>
                <span className="text-xs px-2 py-1 rounded bg-opacity-50 bg-gray-600 text-gray-300">
                  {step.duration_ms}ms
                </span>
              </div>
              <p className="text-sm text-gray-300 leading-relaxed">{step.content}</p>
            </div>
          ))}

          {/* Conclusion */}
          <div className="p-4 bg-blue-900/30 border border-blue-600 rounded-lg">
            <h4 className="font-semibold text-white mb-2">💡 Conclusion</h4>
            <p className="text-sm text-gray-200 leading-relaxed">{result.conclusion}</p>
          </div>
        </div>
      )}

      {!result && !loading && (
        <div className="text-center text-gray-400 text-sm py-8">
          Select a file and click "Start Reasoning" to analyze code
        </div>
      )}
    </div>
  );
}
