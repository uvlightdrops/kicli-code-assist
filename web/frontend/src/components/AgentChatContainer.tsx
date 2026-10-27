import React, { useState } from 'react';
import { UnifiedAgentChat } from './UnifiedAgentChat';
import { DiffViewer, type FileDiff, parseDiffLines } from './DiffViewer';
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

type PanelType = 'chat' | 'diffs' | 'settings';

export const AgentChatContainer: React.FC<AgentChatContainerProps> = ({ currentFile, projectPath }) => {
  const [activePanel, setActivePanel] = useState<PanelType>('chat');
  const [agentResults, setAgentResults] = useState<AgentResult[]>([]);
  const [diffs, setDiffs] = useState<FileDiff[]>([]);
  const [resultTabs, setResultTabs] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<string | null>(null);
  const { settings } = useAnalysisSettings();

  const handleResultsReceived = (results: any) => {
    // Process results and extract diffs if available
    const newResults = results.agents || [];
    setAgentResults(newResults);

    // Extract any diffs from results
    const newDiffs: FileDiff[] = [];
    newResults.forEach((agent: AgentResult) => {
      // Check if result contains diff data
      if (agent.result?.diffs) {
        newDiffs.push(...agent.result.diffs);
      }
    });

    if (newDiffs.length > 0) {
      setDiffs(newDiffs);
      setActivePanel('diffs');
    }

    // Update result tabs based on agent types
    const tabs = newResults
      .map((a: AgentResult) => a.type)
      .filter((t: string) => t);
    setResultTabs(tabs);
    if (tabs.length > 0) {
      setActiveTab(tabs[0]);
    }
  };

  const renderPanelContent = () => {
    switch (activePanel) {
      case 'chat':
        return (
          <UnifiedAgentChat
            currentFile={currentFile || ''}
            projectPath={projectPath || ''}
            onResultsReceived={handleResultsReceived}
          />
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
        <h2>Agent Analysis</h2>
        <div className="header-controls">
          <button
            className={`tab-button ${activePanel === 'chat' ? 'active' : ''}`}
            onClick={() => setActivePanel('chat')}
            title="Chat with agents"
          >
            💬 Chat
          </button>
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

      {agentResults.length > 0 && activePanel === 'chat' && (
        <div className="results-summary">
          <div className="summary-header">Results</div>
          <div className="summary-tags">
            {agentResults.map((result) => (
              <span key={result.type} className="summary-tag">
                {result.type === 'explain' && '📊'}
                {result.type === 'metrics' && '📈'}
                {result.type === 'refactor' && '🔧'}
                {result.type === 'dependencies' && '🔗'}
                {result.type === 'suggest' && '💡'}
                {' '}
                {result.type}
                {result.result?.status === 'error' && ' ⚠️'}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
