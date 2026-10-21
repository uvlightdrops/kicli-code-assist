import React, { useState } from 'react';
import axios from 'axios';

interface LLMResponse {
  provider: string;
  text: string;
  duration_ms: number;
  tokens_used: number;
  error?: string;
}

interface EnsembleResult {
  status: string;
  request_id: string;
  prompt: string;
  responses: LLMResponse[];
  consensus: string;
  agreement_score: number;
  total_duration_ms: number;
  error?: string;
}

interface EnsemblePanelProps {
  file?: string;
  selectedCode?: string;
  isVisible: boolean;
}

export function EnsemblePanel({ file, selectedCode, isVisible }: EnsemblePanelProps) {
  const [result, setResult] = useState<EnsembleResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [question, setQuestion] = useState('What is this code doing?');
  const [error, setError] = useState('');

  const handleEnsemble = async () => {
    if (!selectedCode && !file) {
      setError('No code selected. Please select code or open a file.');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await axios.post('/api/agent/ensemble', {
        code: selectedCode || '',
        question,
      });

      if (response.data.status === 'ok') {
        setResult(response.data);
      } else {
        setError(response.data.error || 'Ensemble voting failed');
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
      <h2 className="text-lg font-bold text-white">🎯 Ensemble Voting</h2>

      {/* Question Input */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-300">Question</label>
        <textarea
          value={question}
          onChange={e => setQuestion(e.target.value)}
          placeholder="Ask both OpenAI and Ollama..."
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm resize-none h-16"
        />
        <button
          onClick={handleEnsemble}
          disabled={loading || (!selectedCode && !file)}
          className="w-full px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Voting...' : 'Get Consensus'}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-red-900/30 border border-red-700 rounded text-red-200 text-sm">
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Agreement Score */}
          <div className="p-3 bg-indigo-900/30 border border-indigo-600 rounded">
            <div className="flex items-center justify-between mb-2">
              <span className="font-semibold text-white">Agreement Score</span>
              <span className="text-2xl font-bold text-indigo-300">
                {(result.agreement_score * 100).toFixed(0)}%
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="bg-indigo-500 h-2 rounded-full transition-all"
                style={{ width: `${result.agreement_score * 100}%` }}
              />
            </div>
          </div>

          {/* Individual Responses */}
          {result.responses.map((response, idx) => (
            <div
              key={idx}
              className={`p-3 rounded border ${
                response.error ? 'bg-red-900/20 border-red-700' : 'bg-gray-800 border-gray-700'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-white">
                  {response.provider === 'openai' ? '🤖 OpenAI (GPT-4)' : '🦙 Ollama (Llama2)'}
                </h4>
                {response.duration_ms > 0 && (
                  <span className="text-xs text-gray-400">{response.duration_ms}ms</span>
                )}
              </div>
              {response.error ? (
                <p className="text-sm text-red-300">{response.error}</p>
              ) : (
                <p className="text-sm text-gray-300 leading-relaxed">{response.text}</p>
              )}
            </div>
          ))}

          {/* Consensus */}
          <div className="p-4 bg-green-900/30 border border-green-600 rounded-lg">
            <h4 className="font-semibold text-white mb-2">✅ Consensus</h4>
            <p className="text-sm text-gray-200 leading-relaxed">{result.consensus}</p>
            <div className="mt-3 text-xs text-gray-400">
              Total: {result.total_duration_ms}ms
            </div>
          </div>
        </div>
      )}

      {!result && !loading && (
        <div className="text-center text-gray-400 text-sm py-8">
          Select code and click "Get Consensus" to ask both OpenAI and Ollama
        </div>
      )}
    </div>
  );
}
