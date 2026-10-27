import React, { useState } from 'react';
import { UnifiedAgentChat } from './UnifiedAgentChat';
import { DiffViewer, type FileDiff } from './DiffViewer';
import { SettingsPanel } from './SettingsPanel';
import { useAnalysisSettings } from '../hooks/useAnalysisSettings';
import './AgentChatContainer.css';

// Phase 2D Response Structure from /api/agent/route
export interface Phase2DResponse {
  success: boolean;
  session_id: string;
  query: string;
  intent: {
    type: string;
    confidence: number;
    agents: string[];
  };
  summary: string;
  tabs: Record<string, any>;  // Structure, Metrics, Dependencies, Refactor, etc.
  actions: Array<any>;
  next_steps: string[];
  timing: {
    intent_ms: number;
    execution_ms: number;
    aggregation_ms: number;
    total_ms: number;
  };
}

interface AgentChatContainerProps {
  currentFile: string | null;
  projectPath?: string | null;
}

type MainPanel = 'chat' | 'analysis' | 'diffs' | 'settings';

export const AgentChatContainer: React.FC<AgentChatContainerProps> = ({ currentFile, projectPath }) => {
  const [activePanel, setActivePanel] = useState<MainPanel>('chat');
  const [latestResponse, setLatestResponse] = useState<Phase2DResponse | null>(null);
  const [activeAnalysisTab, setActiveAnalysisTab] = useState<string>('');
  const [diffs, setDiffs] = useState<FileDiff[]>([]);
  const [thinkingProcess, setThinkingProcess] = useState<string>('');
  const { settings } = useAnalysisSettings();

  const handleResultsReceived = (results: any) => {
    // Process Phase 2D response structure
    const response = results as Phase2DResponse;
    if (!response.success) return;

    setLatestResponse(response);

    // Build thinking process text
    const thinkingText =
      `🎯 Intent: ${response.intent.type} (${(response.intent.confidence * 100).toFixed(0)}% confidence)\n` +
      `🔧 Agents: ${response.intent.agents.join(', ')}\n` +
      `⏱️  Timing: ${response.timing.total_ms}ms (Intent: ${response.timing.intent_ms}ms, Execution: ${response.timing.execution_ms}ms, Aggregation: ${response.timing.aggregation_ms}ms)\n\n` +
      `📋 Summary:\n${response.summary}`;

    setThinkingProcess(thinkingText);

    // Set first available tab as active
    const tabKeys = Object.keys(response.tabs || {});
    if (tabKeys.length > 0) {
      setActiveAnalysisTab(tabKeys[0]);
    }
  };

  const renderAnalysisTabContent = () => {
    if (!latestResponse || !latestResponse.tabs) {
      return <div className="no-result">No analysis results yet. Send a query to get started.</div>;
    }

    if (!activeAnalysisTab || !latestResponse.tabs[activeAnalysisTab]) {
      return <div className="no-result">Select a result tab above</div>;
    }

    const tabData = latestResponse.tabs[activeAnalysisTab];

    return (
      <div className="tab-content">
        {/* Structure Tab */}
        {activeAnalysisTab === 'Structure' && (
          <div className="structure-result">
            {tabData.description && <div className="description">{tabData.description}</div>}

            {tabData.classes && Object.keys(tabData.classes).length > 0 && (
              <div className="section">
                <h4>Classes ({Object.keys(tabData.classes).length})</h4>
                <ul className="items-list">
                  {Object.keys(tabData.classes).map(className => (
                    <li key={className}>
                      <strong>{className}</strong>
                      {tabData.classes[className]?.methods && (
                        <ul className="sub-items">
                          {Object.keys(tabData.classes[className].methods).map(method => (
                            <li key={method}>{method}</li>
                          ))}
                        </ul>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {tabData.functions && Object.keys(tabData.functions).length > 0 && (
              <div className="section">
                <h4>Functions ({Object.keys(tabData.functions).length})</h4>
                <ul className="items-list">
                  {Object.keys(tabData.functions).slice(0, 30).map(funcName => (
                    <li key={funcName}>{funcName}</li>
                  ))}
                  {Object.keys(tabData.functions).length > 30 && (
                    <li className="more">... and {Object.keys(tabData.functions).length - 30} more</li>
                  )}
                </ul>
              </div>
            )}

            {tabData.imports && Object.keys(tabData.imports).length > 0 && (
              <div className="section">
                <h4>Imports ({Object.keys(tabData.imports).length})</h4>
                <ul className="items-list">
                  {Object.keys(tabData.imports).map(imp => (
                    <li key={imp}>{imp}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Metrics Tab */}
        {activeAnalysisTab === 'Metrics' && (
          <div className="metrics-result">
            {tabData.maintainability_index !== undefined && (
              <div className="metric-item">
                <strong>Maintainability Index</strong>
                <span className="value">{tabData.maintainability_index.toFixed(1)}/100</span>
              </div>
            )}

            {tabData.complexity && (
              <div className="metric-item">
                <strong>Complexity Level</strong>
                <span className="value">{tabData.complexity}</span>
              </div>
            )}

            {tabData.average_complexity !== undefined && (
              <div className="metric-item">
                <strong>Average Complexity</strong>
                <span className="value">{tabData.average_complexity.toFixed(2)}</span>
              </div>
            )}

            {tabData.number_of_classes !== undefined && (
              <div className="metric-item">
                <strong>Classes</strong>
                <span className="value">{tabData.number_of_classes}</span>
              </div>
            )}

            {tabData.number_of_functions !== undefined && (
              <div className="metric-item">
                <strong>Functions</strong>
                <span className="value">{tabData.number_of_functions}</span>
              </div>
            )}

            {tabData.lines_of_code !== undefined && (
              <div className="metric-item">
                <strong>Lines of Code</strong>
                <span className="value">{tabData.lines_of_code}</span>
              </div>
            )}

            {tabData.issues && tabData.issues.length > 0 && (
              <div className="section">
                <h4>Issues ({tabData.issues.length})</h4>
                <ul className="issues-list">
                  {tabData.issues.map((issue: string, i: number) => (
                    <li key={i} className="issue">⚠️ {issue}</li>
                  ))}
                </ul>
              </div>
            )}

            {tabData.improvements && tabData.improvements.length > 0 && (
              <div className="section">
                <h4>Suggestions</h4>
                <ul className="improvements-list">
                  {tabData.improvements.map((suggestion: string, i: number) => (
                    <li key={i} className="suggestion">💡 {suggestion}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Dependencies Tab */}
        {activeAnalysisTab === 'Dependencies' && (
          <div className="dependencies-result">
            {tabData.imports && Object.keys(tabData.imports).length > 0 && (
              <div className="section">
                <h4>External Imports ({Object.keys(tabData.imports).length})</h4>
                <ul className="items-list">
                  {Object.keys(tabData.imports).map(imp => (
                    <li key={imp}>{imp}</li>
                  ))}
                </ul>
              </div>
            )}

            {tabData.internals && Object.keys(tabData.internals).length > 0 && (
              <div className="section">
                <h4>Internal Dependencies ({Object.keys(tabData.internals).length})</h4>
                <ul className="items-list">
                  {Object.keys(tabData.internals).map(dep => (
                    <li key={dep}>{dep}</li>
                  ))}
                </ul>
              </div>
            )}

            {tabData.externals && Object.keys(tabData.externals).length > 0 && (
              <div className="section">
                <h4>External Dependencies ({Object.keys(tabData.externals).length})</h4>
                <ul className="items-list">
                  {Object.keys(tabData.externals).map(ext => (
                    <li key={ext}>{ext}</li>
                  ))}
                </ul>
              </div>
            )}

            {tabData.circular_dependencies && tabData.circular_dependencies.length > 0 && (
              <div className="section">
                <h4>⚠️ Circular Dependencies ({tabData.circular_dependencies.length})</h4>
                <ul className="items-list">
                  {tabData.circular_dependencies.map((cycle: any, i: number) => (
                    <li key={i}>{Array.isArray(cycle) ? cycle.join(' → ') : cycle}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Refactor Tab */}
        {activeAnalysisTab === 'Refactor' && (
          <div className="refactor-result">
            {tabData.recommendations && tabData.recommendations.length > 0 && (
              <div className="section">
                <h4>Recommendations</h4>
                <ul className="recommendations-list">
                  {tabData.recommendations.map((rec: string, i: number) => (
                    <li key={i}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}

            {tabData.patterns && tabData.patterns.length > 0 && (
              <div className="section">
                <h4>Suggested Patterns</h4>
                <ul className="patterns-list">
                  {tabData.patterns.map((pattern: string, i: number) => (
                    <li key={i}>{pattern}</li>
                  ))}
                </ul>
              </div>
            )}

            {tabData.priority && (
              <div className="metric-item">
                <strong>Priority</strong>
                <span className="value">{tabData.priority}</span>
              </div>
            )}
          </div>
        )}

        {/* Generic fallback for other tabs */}
        {!['Structure', 'Metrics', 'Dependencies', 'Refactor'].includes(activeAnalysisTab) && (
          <pre className="generic-content">{JSON.stringify(tabData, null, 2)}</pre>
        )}
      </div>
    );
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
              />
            </div>
            <div className="chat-lower">
              <div className="thinking-header">
                <span>🤔 Analysis Process</span>
              </div>
              <div className="thinking-content">
                {thinkingProcess || 'Send a query to see analysis details...'}
              </div>
            </div>
          </div>
        );

      case 'analysis':
        return (
          <div className="analysis-panel">
            {latestResponse && (
              <>
                <div className="analysis-summary">
                  <strong>Summary:</strong> {latestResponse.summary}
                </div>

                <div className="analysis-tabs">
                  {Object.keys(latestResponse.tabs || {}).map(tabName => (
                    <button
                      key={tabName}
                      className={`analysis-tab ${activeAnalysisTab === tabName ? 'active' : ''}`}
                      onClick={() => setActiveAnalysisTab(tabName)}
                    >
                      {tabName}
                    </button>
                  ))}
                </div>

                <div className="analysis-content">
                  {renderAnalysisTabContent()}
                </div>

                {latestResponse.next_steps && latestResponse.next_steps.length > 0 && (
                  <div className="next-steps">
                    <h4>Suggested Next Steps:</h4>
                    <ul>
                      {latestResponse.next_steps.map((step: string, i: number) => (
                        <li key={i}>{step}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}
            {!latestResponse && (
              <div className="no-result">No analysis results. Send a query in the Chat tab to get started.</div>
            )}
          </div>
        );

      case 'diffs':
        return <DiffViewer diffs={diffs} />;

      case 'settings':
        return <SettingsPanel />;

      default:
        return null;
    }
  };

  const panelTitles: Record<MainPanel, string> = {
    chat: 'Chat',
    analysis: 'Analysis',
    diffs: 'Diffs',
    settings: 'Settings',
  };

  return (
    <div className="agent-chat-container">
      <div className="panel-tabs">
        {(Object.keys(panelTitles) as MainPanel[]).map(panel => (
          <button
            key={panel}
            className={`panel-tab ${activePanel === panel ? 'active' : ''}`}
            onClick={() => setActivePanel(panel)}
          >
            {panelTitles[panel]}
            {panel === 'analysis' && latestResponse && (
              <span className="badge">{Object.keys(latestResponse.tabs || {}).length}</span>
            )}
          </button>
        ))}
      </div>
      <div className="panel-content">{renderPanelContent()}</div>
    </div>
  );
};
