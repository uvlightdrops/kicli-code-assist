import React, { useState } from 'react';

interface ToolsPanelProps {
  isVisible: boolean;
}

export function ToolsPanel({ isVisible }: ToolsPanelProps) {
  const [settings, setSettings] = useState({
    autoAnalyze: false,
    showMetrics: true,
    useOllama: true,
    useOpenAI: true,
    cacheResults: true,
  });

  const handleToggle = (key: keyof typeof settings) => {
    setSettings(prev => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  if (!isVisible) return null;

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      <h2 className="text-lg font-bold text-white">⚙️ Tools & Settings</h2>

      {/* Feature Toggles */}
      <div className="space-y-3 border-b border-gray-700 pb-4">
        <h3 className="text-sm font-semibold text-gray-300">LLM Providers</h3>

        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={settings.useOpenAI}
            onChange={() => handleToggle('useOpenAI')}
            className="rounded border-gray-600"
          />
          <span className="text-sm text-gray-300">Use OpenAI (GPT-4o-mini)</span>
        </label>

        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={settings.useOllama}
            onChange={() => handleToggle('useOllama')}
            className="rounded border-gray-600"
          />
          <span className="text-sm text-gray-300">Use Ollama (Llama2)</span>
        </label>
      </div>

      {/* Analysis Settings */}
      <div className="space-y-3 border-b border-gray-700 pb-4">
        <h3 className="text-sm font-semibold text-gray-300">Analysis</h3>

        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={settings.autoAnalyze}
            onChange={() => handleToggle('autoAnalyze')}
            className="rounded border-gray-600"
          />
          <span className="text-sm text-gray-300">Auto-analyze on file open</span>
        </label>

        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={settings.showMetrics}
            onChange={() => handleToggle('showMetrics')}
            className="rounded border-gray-600"
          />
          <span className="text-sm text-gray-300">Show complexity metrics</span>
        </label>

        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={settings.cacheResults}
            onChange={() => handleToggle('cacheResults')}
            className="rounded border-gray-600"
          />
          <span className="text-sm text-gray-300">Cache analysis results</span>
        </label>
      </div>

      {/* Agent Info */}
      <div className="space-y-3 pt-4">
        <h3 className="text-sm font-semibold text-gray-300">About</h3>

        <div className="text-sm text-gray-400 space-y-2">
          <div>
            <strong className="text-gray-300">Programming Agent</strong>
            <p className="mt-1">Multi-feature code analysis with LLM ensemble voting</p>
          </div>

          <div className="text-xs text-gray-500 mt-3">
            <div>Features: Explain • Reasoning • Ensemble Voting • Tools</div>
            <div className="mt-2">Version: 0.1.0</div>
          </div>
        </div>
      </div>

      {/* Status */}
      <div className="mt-6 pt-4 border-t border-gray-700">
        <div className="text-xs text-gray-500 space-y-1">
          <div>✓ OpenAI API: Configured</div>
          <div>✓ Ollama: Available</div>
          <div>✓ AST Analyzer: Ready</div>
        </div>
      </div>
    </div>
  );
}
