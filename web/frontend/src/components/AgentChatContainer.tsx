import React, { useState } from 'react';
import { UnifiedAgentChat } from './UnifiedAgentChat';
import { DiffViewer, type FileDiff } from './DiffViewer';
import { SettingsPanel } from './SettingsPanel';
import { useAnalysisSettings } from '../hooks/useAnalysisSettings';
import './AgentChatContainer.css';

export interface AgentResult {
  type: string;
  result: any;
}

interface AgentChatContainerProps {
  currentFile: string | null;
  projectPath?: string | null;
}

type MainPanel = 'chat' | 'analysis' | 'diffs' | 'settings';

export const AgentChatContainer: React.FC<AgentChatContainerProps> = ({ currentFile, projectPath }) => {
  const [activePanel, setActivePanel] = useState<MainPanel>('chat');
  const [agentResults, setAgentResults] = useState<AgentResult[]>([]);
  const [activeAnalysisTab, setActiveAnalysisTab] = useState<string>('explain');
  const [diffs, setDiffs] = useState<FileDiff[]>([]);
  const [thinkingProcess, setThinkingProcess] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const { settings } = useAnalysisSettings();

  const handleResultsReceived = (results: any) => {
    // Process results but DON'T auto-switch panels
    const newResults = results.agents || [];
    setAgentResults(newResults);

    // Extract any diffs from results
    const newDiffs: FileDiff[] = [];
    newResults.forEach((agent: AgentResult) => {
      if (agent.result?.diffs) {
        newDiffs.push(...agent.result.diffs);
      }
    });

    if (newDiffs.length > 0) {
      setDiffs(newDiffs);
    }

    // Set first successful result as active
    if (newResults.length > 0) {
      const firstSuccessful = newResults.find((r: AgentResult) => r.result?.status !== 'error');
      if (firstSuccessful) {
        setActiveAnalysisTab(firstSuccessful.type);
      }
    }
  };

  const handleThinkingProcessUpdate = (text: string) => {
    setThinkingProcess(text);
  };

  const handleAnalysisStart = (agentType: string) => {
    setIsAnalyzing(true);
    setThinkingProcess(`Starting ${agentType} analysis...`);
    // The actual execution will be triggered by clicking buttons
    // This is just UI state management
  };

  const renderAnalysisContent = () => {
    const result = agentResults.find(r => r.type === activeAnalysisTab);
    
    if (!result) {
      return <div className="no-result">Select an analysis to view results</div>;
    }

    if (result.result?.status === 'error') {
      return (
        <div className="error-panel">
          <div className="error-icon">⚠️</div>
          <div className="error-message">{result.result.error}</div>
        </div>
      );
    }

    // Render appropriate panel based on agent type
    switch (result.type) {
      case 'explain':
        return (
          <div className="explain-result">
            {result.result.summary && (
              <div className="section">
                <h4>Summary</h4>
                <pre>{result.result.summary}</pre>
              </div>
            )}
            {result.result.classes && (
              <div className="section">
                <h4>Classes ({result.result.classes.length})</h4>
                <div className="classes-list">
                  {result.result.classes.map((cls: any) => (
                    <div key={cls.name} className="class-item">
                      <strong>{cls.name}</strong>
                      <span className="badge">{cls.methods.length} methods</span>
                      {cls.methods.length > 0 && (
                        <ul>
                          {cls.methods.map((m: string) => (
                            <li key={m}>{m}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {result.result.functions && (
              <div className="section">
                <h4>Functions ({result.result.functions.length})</h4>
                <div className="functions-list">
                  {result.result.functions.slice(0, 20).map((fn: any) => (
                    <div key={`${fn.line}-${fn.name}`} className="function-item">
                      <span className="name">{fn.name}</span>
                      <span className="complexity">complexity: {fn.complexity}</span>
                      {fn.docstring && <div className="docstring">{fn.docstring}</div>}
                    </div>
                  ))}
                  {result.result.functions.length > 20 && (
                    <div className="more">... and {result.result.functions.length - 20} more functions</div>
                  )}
                </div>
              </div>
            )}
          </div>
        );

      case 'metrics':
        return (
          <div className="metrics-result">
            {result.result.maintainability_index !== undefined && (
              <div className="metric-item">
                <strong>Maintainability Index:</strong>
                <span className="value">{result.result.maintainability_index.toFixed(1)}</span>
              </div>
            )}
            {result.result.average_complexity !== undefined && (
              <div className="metric-item">
                <strong>Average Complexity:</strong>
                <span className="value">{result.result.average_complexity.toFixed(2)}</span>
              </div>
            )}
            {result.result.number_of_functions !== undefined && (
              <div className="metric-item">
                <strong>Functions:</strong>
                <span className="value">{result.result.number_of_functions}</span>
              </div>
            )}
            {result.result.number_of_classes !== undefined && (
              <div className="metric-item">
                <strong>Classes:</strong>
                <span className="value">{result.result.number_of_classes}</span>
              </div>
            )}
            <pre>{JSON.stringify(result.result, null, 2)}</pre>
          </div>
        );

      case 'dependencies':
      case 'refactor':
      default:
        return (
          <div className="generic-result">
            <pre>{JSON.stringify(result.result, null, 2)}</pre>
          </div>
        );
    }
  };

  const renderPanelContent = () => {
    switch (activePanel) {
      case 'chat':
        return (
          <div className="chat-panel-layout">
            <div className="chat-upper">
              <UnifiedAgentChat
                currentFile={currentFile || ''}
                projectPath={projectPath || ''}
                onResultsReceived={handleResultsReceived}
                onThinkingUpdate={handleThinkingProcessUpdate}
              />
            </div>
            <div className="chat-lower">
              <div className="thinking-header">
                <span>🤔 Thinking Process</span>
                {isAnalyzing && <span className="spinner"></span>}
              </div>
              <div className="thinking-content">
                {thinkingProcess || 'Analysis results will appear here...'}
              </div>
            </div>
          </div>
        );

      case 'analysis':
        return (
          <div className="analysis-panel">
            <div className="analysis-toolbar">
              <div className="analysis-buttons">
                <button
                  className={`analysis-btn ${!currentFile ? 'disabled' : ''}`}
                  onClick={() => handleAnalysisStart('explain')}
                  disabled={!currentFile}
                  title={!currentFile ? 'Select a file first' : 'Run structure & metrics analysis'}
                >
                  📊 Explain
                </button>
                <button
                  className={`analysis-btn ${!currentFile ? 'disabled' : ''}`}
                  onClick={() => handleAnalysisStart('refactor')}
                  disabled={!currentFile}
                  title={!currentFile ? 'Select a file first' : 'Get refactoring suggestions'}
                >
                  🔧 Refactor
                </button>
                <button
                  className={`analysis-btn ${!currentFile ? 'disabled' : ''}`}
                  onClick={() => handleAnalysisStart('dependencies')}
                  disabled={!currentFile}
                  title={!currentFile ? 'Select a file first' : 'Analyze dependencies'}
                >
                  🔗 Dependencies
                </button>
              </div>
              <div className="analysis-tabs">
                {agentResults.map((result) => (
                  <button
                    key={result.type}
                    className={`analysis-tab ${activeAnalysisTab === result.type ? 'active' : ''} ${
                      result.result?.status === 'error' ? 'error' : ''
                    }`}
                    onClick={() => setActiveAnalysisTab(result.type)}
                    title={result.result?.status === 'error' ? result.result.error : result.type}
                  >
                    {result.type === 'explain' && '📊'}
                    {result.type === 'metrics' && '📈'}
                    {result.type === 'dependencies' && '🔗'}
                    {result.type === 'refactor' && '🔧'}
                    {result.type === 'suggest' && '💡'}
                    {' '}
                    {result.type}
                    {result.result?.status === 'error' && ' ⚠️'}
                  </button>
                ))}
              </div>
            </div>
            <div className="analysis-content">
              {renderAnalysisContent()}
            </div>
          </div>
        );

      case 'diffs':
        return (
          <div className="diffs-panel">
            {diffs.length > 0 ? (
              <DiffViewer
                diffs={diffs}
                onAccept={(filePath) => {
                  console.log('Accept:', filePath);
                }}
                onReject={(filePath) => {
                  console.log('Reject:', filePath);
                }}
                onAcceptAll={() => {
                  console.log('Accept all');
                }}
                onRejectAll={() => {
                  console.log('Reject all');
                }}
              />
            ) : (
              <div className="no-diffs">
                <p>No changes to review</p>
              </div>
            )}
          </div>
        );

      case 'settings':
        return <SettingsPanel />;

      default:
        return null;
    }
  };

  return (
    <div className="agent-chat-container">
      <div className="container-header">
        <h2>Agent Assistant</h2>
        <div className="header-controls">
          <button
            className={`tab-button ${activePanel === 'chat' ? 'active' : ''}`}
            onClick={() => setActivePanel('chat')}
            title="Chat with agents"
          >
            💬 Chat
          </button>
          {agentResults.length > 0 && (
            <button
              className={`tab-button ${activePanel === 'analysis' ? 'active' : ''}`}
              onClick={() => setActivePanel('analysis')}
              title={`View ${agentResults.length} analysis result(s)`}
            >
              📋 Analysis ({agentResults.length})
            </button>
          )}
          {diffs.length > 0 && (
            <button
              className={`tab-button ${activePanel === 'diffs' ? 'active' : ''}`}
              onClick={() => setActivePanel('diffs')}
              title={`Review ${diffs.length} diff(s)`}
            >
              📝 Diffs ({diffs.length})
            </button>
          )}
          <button
            className={`tab-button ${activePanel === 'settings' ? 'active' : ''}`}
            onClick={() => setActivePanel('settings')}
            title="Analysis settings"
          >
            ⚙️ Settings
          </button>
        </div>
      </div>

      <div className="container-content">
        {renderPanelContent()}
      </div>
    </div>
  );
};
