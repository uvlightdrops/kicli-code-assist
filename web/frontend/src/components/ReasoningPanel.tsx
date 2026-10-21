import React, { useState, useEffect, useRef } from 'react';
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
  const stepsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest thinking step
  useEffect(() => {
    if (stepsEndRef.current) {
      stepsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [result?.thinking]);

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
    <div className="h-full flex flex-col overflow-hidden">
      {/* Top Section: Query Input (1/3) */}
      <div className="flex-none p-4 space-y-3 border-b border-gray-700 bg-gray-800/50">
        <h2 className="text-lg font-bold text-white">🧠 Reasoning</h2>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-300">Question</label>
          <textarea
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="What would you like to know about this code?"
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm resize-none h-16"
          />
          <button
            onClick={handleReason}
            disabled={loading || !file}
            className="w-full px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors text-sm font-medium"
          >
            {loading ? '⏳ Thinking...' : '▶ Start Reasoning'}
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="p-3 bg-red-900/30 border border-red-700 rounded text-red-200 text-sm">
            {error}
          </div>
        )}
      </div>

      {/* Bottom Section: Thinking Steps (2/3) - Auto Scroll */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {result ? (
          <>
            {/* Metadata */}
            <div className="sticky top-0 bg-gray-800 p-2 border-b border-gray-700 text-sm text-gray-400 font-medium">
              ⏱ {result.total_duration_ms}ms • 🎯 {(result.confidence * 100).toFixed(0)}% confidence
            </div>

            {/* Thinking Steps */}
            {result.thinking.map((step, idx) => (
              <div
                key={idx}
                className={`p-3 rounded border transition-all ${
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
                  <span className="text-xs px-2 py-1 rounded bg-gray-700/60 text-gray-300 whitespace-nowrap ml-2">
                    {step.duration_ms}ms
                  </span>
                </div>
                <p className="text-xs text-gray-300 leading-relaxed">{step.content}</p>
              </div>
            ))}

            {/* Conclusion */}
            {result.conclusion && (
              <div className="p-3 bg-blue-900/30 border border-blue-600 rounded-lg sticky bottom-0">
                <h4 className="font-semibold text-white text-sm mb-1">💡 Conclusion</h4>
                <p className="text-xs text-gray-200 leading-relaxed">{result.conclusion}</p>
              </div>
            )}

            {/* Scroll anchor */}
            <div ref={stepsEndRef} />
          </>
        ) : loading ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <div className="text-3xl mb-2">🤔</div>
              <p className="text-sm">Analyzing code structure...</p>
            </div>
          </div>
        ) : (
          <div className="text-center text-gray-400 text-sm py-8">
            Select a file and click "Start Reasoning" to see thinking steps
          </div>
        )}
      </div>
    </div>
  );
}
