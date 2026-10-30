/**
 * useAgentSettings Hook
 * 
 * Manages agent configuration state and API communication
 * for Phase 5.5 streaming settings.
 */

import { useState, useEffect, useCallback } from 'react';
import { settingsWriteHeaders } from '../services/runtimeSettings';

interface AgentConfig {
  intervention: { mode: 'queue' | 'supervisor' | 'user_prompt' };
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

interface UseAgentSettingsResult {
  config: AgentConfig | null;
  loading: boolean;
  error: string | null;
  updateConfig: (updates: Partial<AgentConfig>) => Promise<boolean>;
  resetConfig: () => Promise<boolean>;
}

// Same-origin (Vite proxies /api in dev); values persist via the shared runtime settings.
const API_BASE = '';

export function useAgentSettings(): UseAgentSettingsResult {
  const [config, setConfig] = useState<AgentConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load initial config
  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE}/api/agent/config`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        throw new Error(`Failed to load config: ${response.statusText}`);
      }

      const data: AgentConfig = await response.json();
      setConfig(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      console.error('Failed to load agent config:', err);
    } finally {
      setLoading(false);
    }
  };

  const updateConfig = useCallback(
    async (updates: Partial<AgentConfig>): Promise<boolean> => {
      try {
        setError(null);

        const response = await fetch(`${API_BASE}/api/agent/config`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', ...(await settingsWriteHeaders()) },
          body: JSON.stringify(updates),
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.error || `HTTP ${response.status}`);
        }

        const data = await response.json();
        if (data.config) {
          // Merge returned config with local state to preserve all fields
          setConfig(prev => prev ? { ...prev, ...data.config } : data.config);
        }

        return true;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError(message);
        console.error('Failed to update agent config:', err);
        return false;
      }
    },
    []
  );

  const resetConfig = useCallback(async (): Promise<boolean> => {
    try {
      setError(null);

      const response = await fetch(`${API_BASE}/api/agent/config/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(await settingsWriteHeaders()) },
      });

      if (!response.ok) {
        throw new Error(`Failed to reset config: ${response.statusText}`);
      }

      const data = await response.json();
      if (data.config) {
        setConfig(data.config);
      }

      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      console.error('Failed to reset agent config:', err);
      return false;
    }
  }, []);

  return {
    config,
    loading,
    error,
    updateConfig,
    resetConfig,
  };
}
