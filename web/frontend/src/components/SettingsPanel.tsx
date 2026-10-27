import React from 'react';
import { AnalysisScope, useAnalysisSettings } from '../hooks/useAnalysisSettings';
import './SettingsPanel.css';

export const SettingsPanel: React.FC = () => {
  const { settings, updateScope } = useAnalysisSettings();

  return (
    <div className="settings-panel">
      <h3>Analysis Settings</h3>

      <div className="settings-group">
        <label className="setting-label">Parsing Scope</label>
        <p className="setting-description">
          Controls the depth of code analysis
        </p>
        
        <div className="scope-options">
          <label className="radio-option">
            <input
              type="radio"
              value="folder"
              checked={settings.scope === 'folder'}
              onChange={(e) => updateScope(e.target.value as AnalysisScope)}
            />
            <span className="radio-text">
              <span className="radio-title">Folder Only</span>
              <span className="radio-desc">Analyzes only current file's folder. Fast, focused.</span>
            </span>
          </label>

          <label className="radio-option">
            <input
              type="radio"
              value="project"
              checked={settings.scope === 'project'}
              onChange={(e) => updateScope(e.target.value as AnalysisScope)}
            />
            <span className="radio-text">
              <span className="radio-title">Project-Wide</span>
              <span className="radio-desc">Analyzes entire project (like PyCharm). Comprehensive.</span>
            </span>
          </label>
        </div>
      </div>

      <div className="settings-divider"></div>

      <div className="settings-info">
        <div className="info-icon">ℹ️</div>
        <div className="info-text">
          <p className="info-title">Smart Agent Selection</p>
          <p className="info-desc">
            When you describe what you want, the system automatically runs the 
            relevant agents (Explain + Metrics always together). Follow-ups remember 
            your session context.
          </p>
        </div>
      </div>
    </div>
  );
};
