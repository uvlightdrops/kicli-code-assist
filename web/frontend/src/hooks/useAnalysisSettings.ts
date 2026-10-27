import { useState, useCallback } from 'react';

export type AnalysisScope = 'folder' | 'project';

export interface AnalysisSettings {
  scope: AnalysisScope;
  autoReview: boolean;
  tabStrategy: 'tabs' | 'sidebar' | 'split';
}

const DEFAULT_SETTINGS: AnalysisSettings = {
  scope: 'folder',
  autoReview: true,
  tabStrategy: 'tabs',
};

const STORAGE_KEY = 'kicli_analysis_settings';

export function useAnalysisSettings() {
  const [settings, setSettings] = useState<AnalysisSettings>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : DEFAULT_SETTINGS;
    } catch {
      return DEFAULT_SETTINGS;
    }
  });

  const updateSettings = useCallback((updates: Partial<AnalysisSettings>) => {
    setSettings(prev => {
      const newSettings = { ...prev, ...updates };
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(newSettings));
      } catch {
        console.warn('Failed to save analysis settings to localStorage');
      }
      return newSettings;
    });
  }, []);

  const updateScope = useCallback((scope: AnalysisScope) => {
    updateSettings({ scope });
  }, [updateSettings]);

  return { settings, updateSettings, updateScope };
}
