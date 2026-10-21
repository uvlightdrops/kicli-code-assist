import React, { useState, useEffect, useRef } from 'react';
import { Loader, ChevronDown } from 'lucide-react';
import axios from 'axios';
import { io } from 'socket.io-client';

interface ThinkingStep {
  step_number: number;
  name: string;
  description: string;
  status: string; // in_progress, completed
  result?: string;
}

interface ThinkingStepsPanelProps {
  selectedFile: string | null;
}

export function ThinkingStepsPanel({ selectedFile }: ThinkingStepsPanelProps) {
  const [loading, setLoading] = useState(false);
  const [steps, setSteps] = useState<ThinkingStep[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const socketRef = useRef<any>(null);
  const requestIdRef = useRef<string>('');

  useEffect(() => {
    // Initialize WebSocket connection
    socketRef.current = io('http://localhost:8000', {
      reconnection: true,
      reconnectionDelay: 1000,
    });

    socketRef.current.on('reasoning:step_complete', (data: any) => {
      if (data.request_id === requestIdRef.current) {
        const step = data.step as ThinkingStep;
        setSteps((prev) => {
          const existing = prev.findIndex((s) => s.step_number === step.step_number);
          if (existing >= 0) {
            const updated = [...prev];
            updated[existing] = step;
            return updated;
          }
          return [...prev, step];
        });

        // Auto-scroll to bottom
        setTimeout(() => {
          if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
          }
        }, 50);
      }
    });

    return () => {
      socketRef.current?.disconnect();
    };
  }, []);

  const analyzeReasoning = async () => {
    if (!selectedFile) {
      setError('No file selected');
      return;
    }

    setLoading(true);
    setError(null);
    setSteps([]);
    requestIdRef.current = `reasoning-${Date.now()}`;

    try {
      // Subscribe to WebSocket room
      socketRef.current.emit('subscribe', { channel: `reasoning:${requestIdRef.current}` });

      // Start reasoning
      await axios.post('/api/agent/stream-reason', {
        file: selectedFile,
        query: 'Analyze this code comprehensively and provide improvement suggestions',
        request_id: requestIdRef.current,
      });

      // Wait a bit for steps to arrive
      await new Promise((resolve) => setTimeout(resolve, 500));
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || err.message || 'Analysis failed';
      setError(errorMsg);
      console.error('Reasoning error:', errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-900 border-t border-gray-700">
      {/* Header */}
      <div className="border-b border-gray-700 p-3 bg-gray-800">
        <div className="flex items-center justify-between mb-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-2 text-sm font-semibold text-gray-300 hover:text-gray-100 transition"
          >
            <ChevronDown
              size={18}
              className={`transform transition-transform ${expanded ? 'rotate-0' : '-rotate-90'}`}
            />
            💭 Thinking Process
          </button>
          <button
            onClick={analyzeReasoning}
            disabled={loading || !selectedFile}
            className={`px-3 py-1 text-xs font-medium rounded transition ${
              loading || !selectedFile
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {loading ? '🔄 Analyzing...' : '▶️ Start'}
          </button>
        </div>
        <p className="text-xs text-gray-500">
          {selectedFile ? `File: ${selectedFile}` : 'Select a file to analyze'}
        </p>
      </div>

      {/* Content */}
      {expanded && (
        <div className="flex-1 flex flex-col overflow-hidden">
          {error && (
            <div className="m-3 p-3 bg-red-900/30 border border-red-700 rounded text-sm text-red-200">
              ❌ {error}
            </div>
          )}

          {!error && steps.length === 0 && !loading && (
            <div className="flex-1 flex items-center justify-center text-gray-500 text-sm p-4">
              <p className="text-center">
                Click "Start" to begin analysis.
                <br />
                Real-time thinking steps will appear here.
              </p>
            </div>
          )}

          {(loading || steps.length > 0) && (
            <div
              ref={scrollRef}
              className="flex-1 overflow-y-auto p-3 space-y-2"
              style={{ minHeight: 0 }}
            >
              {steps.map((step) => (
                <div
                  key={step.step_number}
                  className={`p-3 rounded border-l-4 transition-all ${
                    step.status === 'completed'
                      ? 'bg-green-900/20 border-l-green-500 text-green-100'
                      : 'bg-blue-900/20 border-l-blue-500 text-blue-100'
                  }`}
                >
                  <div className="flex items-start gap-2 mb-1">
                    {step.status === 'in_progress' && (
                      <Loader size={14} className="mt-0.5 animate-spin flex-shrink-0" />
                    )}
                    {step.status === 'completed' && (
                      <span className="text-sm font-semibold flex-shrink-0">✓</span>
                    )}
                    <div className="flex-1">
                      <div className="font-semibold text-xs">
                        Step {step.step_number}: {step.name}
                      </div>
                      <p className="text-xs opacity-75 mt-1">{step.description}</p>
                    </div>
                  </div>

                  {step.result && (
                    <div className="mt-2 ml-5 text-xs bg-black/20 p-2 rounded border border-current/20 max-h-20 overflow-hidden">
                      <p className="line-clamp-3">{step.result}</p>
                    </div>
                  )}
                </div>
              ))}

              {loading && steps.length > 0 && (
                <div className="flex items-center gap-2 text-xs text-gray-400 p-2">
                  <Loader size={12} className="animate-spin" />
                  Analyzing...
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
