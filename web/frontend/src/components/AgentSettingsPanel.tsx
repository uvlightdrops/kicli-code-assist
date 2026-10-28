/**
 * Agent Settings Panel
 * 
 * Displays and allows modification of agent streaming configuration:
 * - Intervention strategy (queue, supervisor, user_prompt)
 * - Thinking detail level (minimal, balanced, verbose)
 * - Auto-rollback behavior
 * 
 * Phase 5.5: Agent Transparency Architecture
 */

import React, { useState, useEffect } from 'react';
import { useAgentSettings } from '../hooks/useAgentSettings';
import './AgentSettingsPanel.css';

interface AgentConfig {
  intervention: {
    mode: 'queue' | 'supervisor' | 'user_prompt';
  };
  streaming: {
    thinking_detail: 'minimal' | 'balanced' | 'verbose';
    state_broadcast_rate: number;
    websocket_timeout: number;
  };
  rollback: {
    auto_on_error: boolean;
    log_error_artifacts: boolean;
    preserve_branch: boolean;
  };
  state: {
    persistence: 'json' | 'sqlite';
    retention: 'session' | '7days' | 'permanent';
    export_on_completion: boolean;
  };
}

export function AgentSettingsPanel() {
  const { config, loading, error, updateConfig } = useAgentSettings();
  const [localConfig, setLocalConfig] = useState<AgentConfig | null>(config);
  const [hasChanges, setHasChanges] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  useEffect(() => {
    setLocalConfig(config);
    setHasChanges(false);
  }, [config]);

  const handleInterventionModeChange = (mode: AgentConfig['intervention']['mode']) => {
    if (!localConfig) return;
    const updated = {
      ...localConfig,
      intervention: { ...localConfig.intervention, mode },
    };
    setLocalConfig(updated);
    setHasChanges(true);
  };

  const handleThinkingDetailChange = (detail: AgentConfig['streaming']['thinking_detail']) => {
    if (!localConfig) return;
    const updated = {
      ...localConfig,
      streaming: { ...localConfig.streaming, thinking_detail: detail },
    };
    setLocalConfig(updated);
    setHasChanges(true);
  };

  const handleAutoRollbackToggle = () => {
    if (!localConfig) return;
    const updated = {
      ...localConfig,
      rollback: {
        ...localConfig.rollback,
        auto_on_error: !localConfig.rollback.auto_on_error,
      },
    };
    setLocalConfig(updated);
    setHasChanges(true);
  };

  const handleSave = async () => {
    if (!localConfig || !hasChanges) return;

    setSaveStatus('saving');
    const success = await updateConfig({
      intervention: { mode: localConfig.intervention.mode },
      streaming: { thinking_detail: localConfig.streaming.thinking_detail },
      rollback: { auto_on_error: localConfig.rollback.auto_on_error },
    } as Partial<AgentConfig>);

    if (success) {
      setSaveStatus('saved');
      setHasChanges(false);
      setTimeout(() => setSaveStatus('idle'), 2000);
    } else {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 3000);
    }
  };

  if (loading) {
    return <div className="agent-settings-panel loading">Loading settings...</div>;
  }

  if (!localConfig) {
    return <div className="agent-settings-panel error">Failed to load settings</div>;
  }

  return (
    <div className="agent-settings-panel">
      <div className="settings-header">
        <h3>🤖 Agent Streaming Settings</h3>
        <span className="settings-subtitle">Configure real-time agent behavior</span>
      </div>

      <div className="settings-content">
        {/* Intervention Strategy Section */}
        <div className="settings-section">
          <div className="section-header">
            <h4>📋 Intervention Strategy</h4>
            <p className="section-desc">
              How agent handles conflicting commands from WebUI and Supervisor
            </p>
          </div>

          <div className="setting-item">
            <label>Mode when both WebUI and Supervisor send commands:</label>
            <div className="radio-group">
              <label className="radio-label">
                <input
                  type="radio"
                  name="intervention_mode"
                  value="queue"
                  checked={localConfig.intervention.mode === 'queue'}
                  onChange={(e) =>
                    handleInterventionModeChange(
                      e.target.value as AgentConfig['intervention']['mode']
                    )
                  }
                />
                <span className="radio-text">
                  <strong>Queue (FIFO)</strong>
                  <br />
                  <small>Process commands in order received</small>
                </span>
              </label>

              <label className="radio-label">
                <input
                  type="radio"
                  name="intervention_mode"
                  value="supervisor"
                  checked={localConfig.intervention.mode === 'supervisor'}
                  onChange={(e) =>
                    handleInterventionModeChange(
                      e.target.value as AgentConfig['intervention']['mode']
                    )
                  }
                />
                <span className="radio-text">
                  <strong>Supervisor Priority</strong>
                  <br />
                  <small>CLI supervisor commands always win</small>
                </span>
              </label>

              <label className="radio-label">
                <input
                  type="radio"
                  name="intervention_mode"
                  value="user_prompt"
                  checked={localConfig.intervention.mode === 'user_prompt'}
                  onChange={(e) =>
                    handleInterventionModeChange(
                      e.target.value as AgentConfig['intervention']['mode']
                    )
                  }
                />
                <span className="radio-text">
                  <strong>User Decides</strong>
                  <br />
                  <small>Ask at conflict time (recommended)</small>
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* Thinking Detail Section */}
        <div className="settings-section">
          <div className="section-header">
            <h4>💭 Thinking Detail Level</h4>
            <p className="section-desc">How verbose agent reasoning appears in UI</p>
          </div>

          <div className="setting-item">
            <label>Thinking visibility:</label>
            <div className="radio-group">
              <label className="radio-label">
                <input
                  type="radio"
                  name="thinking_detail"
                  value="minimal"
                  checked={localConfig.streaming.thinking_detail === 'minimal'}
                  onChange={(e) =>
                    handleThinkingDetailChange(
                      e.target.value as AgentConfig['streaming']['thinking_detail']
                    )
                  }
                />
                <span className="radio-text">
                  <strong>Minimal</strong>
                  <br />
                  <small>Only major decisions (file creation, test runs)</small>
                </span>
              </label>

              <label className="radio-label">
                <input
                  type="radio"
                  name="thinking_detail"
                  value="balanced"
                  checked={localConfig.streaming.thinking_detail === 'balanced'}
                  onChange={(e) =>
                    handleThinkingDetailChange(
                      e.target.value as AgentConfig['streaming']['thinking_detail']
                    )
                  }
                />
                <span className="radio-text">
                  <strong>Balanced</strong> ✓ Recommended
                  <br />
                  <small>Decisions + reasoning (good detail level)</small>
                </span>
              </label>

              <label className="radio-label">
                <input
                  type="radio"
                  name="thinking_detail"
                  value="verbose"
                  checked={localConfig.streaming.thinking_detail === 'verbose'}
                  onChange={(e) =>
                    handleThinkingDetailChange(
                      e.target.value as AgentConfig['streaming']['thinking_detail']
                    )
                  }
                />
                <span className="radio-text">
                  <strong>Verbose</strong>
                  <br />
                  <small>All steps including rejected options (for debugging)</small>
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* Auto-Rollback Section */}
        <div className="settings-section">
          <div className="section-header">
            <h4>⟲ Error Recovery</h4>
            <p className="section-desc">How agent handles errors during execution</p>
          </div>

          <div className="setting-item">
            <div className="toggle-container">
              <label className="toggle-label">
                <input
                  type="checkbox"
                  className="toggle-input"
                  checked={localConfig.rollback.auto_on_error}
                  onChange={handleAutoRollbackToggle}
                />
                <span className="toggle-slider"></span>
              </label>
              <div className="toggle-text">
                <strong>Automatic Rollback on Error</strong>
                <p>
                  {localConfig.rollback.auto_on_error
                    ? '✓ Agent auto-rollbacks on errors (faster recovery)'
                    : '○ Agent prompts before rollback (more control)'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Broadcast Rate */}
        <div className="settings-section">
          <div className="section-header">
            <h4>⚡ Performance</h4>
            <p className="section-desc">State update frequency and timeouts</p>
          </div>

          <div className="setting-item">
            <label>
              State broadcast rate:
              <span className="value">{localConfig.streaming.state_broadcast_rate} updates/sec</span>
            </label>
            <input
              type="range"
              min="1"
              max="50"
              value={localConfig.streaming.state_broadcast_rate}
              onChange={(e) => {
                if (localConfig) {
                  const updated = {
                    ...localConfig,
                    streaming: {
                      ...localConfig.streaming,
                      state_broadcast_rate: parseInt(e.target.value),
                    },
                  };
                  setLocalConfig(updated);
                  setHasChanges(true);
                }
              }}
              className="slider"
            />
            <small>Higher = more frequent updates, more WebSocket traffic</small>
          </div>

          <div className="setting-item">
            <label>
              WebSocket timeout:
              <span className="value">{localConfig.streaming.websocket_timeout}s</span>
            </label>
            <input
              type="range"
              min="10"
              max="300"
              step="10"
              value={localConfig.streaming.websocket_timeout}
              onChange={(e) => {
                if (localConfig) {
                  const updated = {
                    ...localConfig,
                    streaming: {
                      ...localConfig.streaming,
                      websocket_timeout: parseInt(e.target.value),
                    },
                  };
                  setLocalConfig(updated);
                  setHasChanges(true);
                }
              }}
              className="slider"
            />
            <small>Time before disconnection if no heartbeat</small>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="settings-footer">
        {error && <div className="error-message">⚠️ {error}</div>}
        {saveStatus === 'saved' && (
          <div className="success-message">✓ Settings saved successfully</div>
        )}
        {saveStatus === 'error' && (
          <div className="error-message">✗ Failed to save settings</div>
        )}

        <div className="button-group">
          <button
            className="btn btn-secondary"
            onClick={() => {
              setLocalConfig(config);
              setHasChanges(false);
            }}
            disabled={!hasChanges || saveStatus === 'saving'}
          >
            Reset
          </button>

          <button
            className={`btn btn-primary ${saveStatus === 'saving' ? 'loading' : ''}`}
            onClick={handleSave}
            disabled={!hasChanges || saveStatus === 'saving'}
          >
            {saveStatus === 'saving' ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
}
