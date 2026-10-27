import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './UnifiedAgentChat.css';

interface ChatMessage {
  role: 'user' | 'agent';
  content: string;
  timestamp: Date;
  agentTypes?: string[];
  agentResults?: any[]; // Full agent results for rendering
}

interface AgentSession {
  id: string;
  project_path: string;
  current_file: string;
  scope: 'folder' | 'project';
  created_at: string;
}

export const UnifiedAgentChat: React.FC<{
  currentFile: string;
  projectPath?: string;
  onResultsReceived?: (results: any) => void;
}> = ({ currentFile, projectPath, onResultsReceived }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [scope, setScope] = useState<'folder' | 'project'>('folder');
  const [isLoading, setIsLoading] = useState(false);
  const [session, setSession] = useState<AgentSession | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tokenCount, setTokenCount] = useState(0);
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null); // Which agent result is expanded
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !currentFile || isLoading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/agent/route', {
        query: inputValue,
        file_path: currentFile,
        scope: scope,
        project: projectPath || localStorage.getItem('currentProject') || '',
      });

      const agentResponse: ChatMessage = {
        role: 'agent',
        content: `Analysis completed with ${response.data.agents?.length || 0} agents`,
        timestamp: new Date(),
        agentTypes: response.data.agents?.map((a: any) => a.type) || [],
        agentResults: response.data.agents || [], // Store full results
      };

      setMessages(prev => [...prev, agentResponse]);
      setSession(response.data.session || null);
      setTokenCount(response.data.token_count || 0);

      // Notify parent component of results
      if (onResultsReceived) {
        onResultsReceived(response.data);
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || err.message || 'Failed to process query';
      setError(errorMsg);

      const errorMessage: ChatMessage = {
        role: 'agent',
        content: `Error: ${errorMsg}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="unified-agent-chat">
      <div className="chat-header">
        <h3>Agent Chat</h3>
        <div className="scope-selector">
          <label>
            <input
              type="radio"
              value="folder"
              checked={scope === 'folder'}
              onChange={(e) => setScope(e.target.value as 'folder')}
            />
            Folder Only
          </label>
          <label>
            <input
              type="radio"
              value="project"
              checked={scope === 'project'}
              onChange={(e) => setScope(e.target.value as 'project')}
            />
            Project-Wide
          </label>
        </div>
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-state">
            <p>Start a conversation with the agent</p>
            <p className="hint">
              Ask questions like: "Explain this module" or "What can I improve?"
            </p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className={`message message-${msg.role}`}>
              <div className="message-header">
                <span className="role">{msg.role === 'user' ? 'You' : 'Agent'}</span>
                <span className="time">
                  {msg.timestamp.toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              </div>
              <div className="message-content">{msg.content}</div>
              {msg.agentTypes && msg.agentTypes.length > 0 && (
                <div className="agent-types">
                  {msg.agentTypes.map(type => (
                    <button
                      key={type}
                      className={`agent-badge ${expandedAgent === type ? 'active' : ''}`}
                      onClick={() => setExpandedAgent(expandedAgent === type ? null : type)}
                      title={`Click to ${expandedAgent === type ? 'collapse' : 'expand'} ${type} results`}
                    >
                      {type}
                    </button>
                  ))}
                </div>
              )}
              {/* Expanded Agent Result */}
              {expandedAgent && msg.agentResults && (
                <div className="agent-result-expanded">
                  {msg.agentResults
                    .filter(r => r.type === expandedAgent)
                    .map(result => (
                      <div key={result.type} className="result-detail">
                        {result.result.status === 'error' ? (
                          <div className="result-error">
                            Error: {result.result.error}
                          </div>
                        ) : (
                          <div className="result-content">
                            {/* Explain result */}
                            {result.type === 'explain' && result.result.summary && (
                              <pre className="result-text">{result.result.summary}</pre>
                            )}
                            {result.type === 'explain' && result.result.classes && (
                              <div className="result-section">
                                <strong>Classes ({result.result.classes.length}):</strong>
                                <ul>
                                  {result.result.classes.map((cls: any) => (
                                    <li key={cls.name}>
                                      {cls.name} ({cls.methods.length} methods)
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {result.type === 'explain' && result.result.functions && (
                              <div className="result-section">
                                <strong>Functions ({result.result.functions.length}):</strong>
                                <ul>
                                  {result.result.functions.slice(0, 10).map((fn: any) => (
                                    <li key={`${fn.line}-${fn.name}`}>
                                      {fn.name} (complexity: {fn.complexity})
                                    </li>
                                  ))}
                                  {result.result.functions.length > 10 && (
                                    <li>... and {result.result.functions.length - 10} more</li>
                                  )}
                                </ul>
                              </div>
                            )}
                            {/* Generic result */}
                            {JSON.stringify(result.result).length < 1000 && (
                              <pre className="result-json">{JSON.stringify(result.result, null, 2)}</pre>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                </div>
              )}
            </div>
          ))
        )}
        {isLoading && (
          <div className="message message-agent loading">
            <div className="spinner"></div>
            <span>Processing query...</span>
          </div>
        )}
        {error && (
          <div className="message message-error">
            <div className="error-icon">⚠️</div>
            <div className="error-content">{error}</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        {tokenCount > 0 && (
          <div className="token-info">
            Tokens used: {tokenCount}
          </div>
        )}
        <div className="input-wrapper">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Describe what you want the agent to analyze..."
            disabled={isLoading || !currentFile}
            rows={3}
          />
          <button
            onClick={handleSendMessage}
            disabled={isLoading || !currentFile || !inputValue.trim()}
            className="send-button"
            title={!currentFile ? 'Please select a file first' : ''}
          >
            {isLoading ? 'Analyzing...' : 'Send'}
          </button>
        </div>
        {!currentFile && (
          <div className="help-text">Select a file to start analyzing</div>
        )}
      </div>
    </div>
  );
};
