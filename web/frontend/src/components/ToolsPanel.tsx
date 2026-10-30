import React, { useEffect, useState } from 'react';
import { AgentSettingsPanel } from './AgentSettingsPanel';
import { ServerPanel } from './ServerPanel';
import { RuntimeSettingsPanel } from './RuntimeSettingsPanel';

interface LlmSummary {
  llm?: { provider: string; model: string; applies: string };
  [provider: string]: { configured?: boolean; model?: string } | any;
}

const PROVIDERS = ['ki', 'openai', 'ollama', 'mock'] as const;

function useLlmSummary(active: boolean) {
  const [summary, setSummary] = useState<LlmSummary | null>(null);
  useEffect(() => {
    if (!active) return;
    let cancelled = false;
    fetch('/api/config', { cache: 'no-store' })
      .then(res => (res.ok ? res.json() : null))
      .then(data => { if (!cancelled) setSummary(data); })
      .catch(() => { if (!cancelled) setSummary(null); });
    return () => { cancelled = true; };
  }, [active]);
  return summary;
}

interface ToolsPanelProps {
  isVisible: boolean;
}

export function ToolsPanel({ isVisible }: ToolsPanelProps) {
  const [activeTab, setActiveTab] = useState<'features' | 'agent' | 'servers' | 'settings'>('features');
  const [settings, setSettings] = useState({
    autoAnalyze: false,
    showMetrics: true,
    cacheResults: true,
  });
  const llmSummary = useLlmSummary(isVisible && activeTab === 'features');

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

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-gray-700 pb-2">
        <button onClick={() => setActiveTab('servers')}
          className={`px-3 py-2 text-sm rounded ${activeTab === 'servers' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300'}`}>
          Servers
        </button>
        <button
          onClick={() => setActiveTab('features')}
          className={`px-3 py-2 text-sm font-medium rounded transition ${
            activeTab === 'features'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          Features
        </button>
        <button
          onClick={() => setActiveTab('agent')}
          className={`px-3 py-2 text-sm font-medium rounded transition ${
            activeTab === 'agent'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          🤖 Agent
        </button>
        <button
          onClick={() => setActiveTab('settings')}
          className={`px-3 py-2 text-sm font-medium rounded transition ${
            activeTab === 'settings'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          🛠 Konfiguration
        </button>
      </div>

      {/* Features Tab */}
      {activeTab === 'features' && (
        <>
          {/* Feature Toggles */}
          <div className="space-y-3 border-b border-gray-700 pb-4">
            <h3 className="text-sm font-semibold text-gray-300">LLM Provider</h3>
            {llmSummary?.llm ? (
              <div className="text-sm text-gray-300 space-y-1">
                <div>
                  Aktiv: <strong>{llmSummary.llm.provider}</strong>
                  {llmSummary.llm.model && <> · {llmSummary.llm.model}</>}
                </div>
                <div className="text-xs text-gray-500 space-y-0.5">
                  {PROVIDERS.map(name => (
                    <div key={name}>
                      {llmSummary[name]?.configured ? '✓' : '✗'} {name}
                      {llmSummary[name]?.model ? ` (${llmSummary[name].model})` : ''}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-xs text-gray-500">Provider-Status nicht verfügbar.</div>
            )}
            <button className="text-xs text-blue-300 hover:underline" onClick={() => setActiveTab('settings')}>
              Provider/Modell ändern (wirkt ab der nächsten Anfrage) →
            </button>
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
              <div>✓ AST Analyzer: Ready</div>
            </div>
          </div>
        </>
      )}

      {/* Agent Settings Tab */}
      {activeTab === 'servers' && <ServerPanel />}
      {activeTab === 'settings' && <RuntimeSettingsPanel />}
      {activeTab === 'agent' && (
        <div className="mt-4">
          <AgentSettingsPanel />
        </div>
      )}
    </div>
  );
}
