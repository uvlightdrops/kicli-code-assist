import React, { useState } from 'react'
import axios from 'axios'
import { useProject } from '../hooks/useProject'

interface AgentExplanation {
  status: string
  file: string
  summary: string
  functions: Array<{
    name: string
    line: number
    complexity: number
    docstring: string
    params: string[]
  }>
  classes: string[]
  imports: Array<{
    line: number
    module: string
    name: string | null
  }>
  affected_files: number
  context: Record<string, string>
}

interface Suggestion {
  type: string
  message: string
  details?: string
}

interface AgentSuggestions {
  status: string
  file: string
  summary: string
  suggestions: Suggestion[]
}

interface AgentPanelProps {
  filePath: string | null
  onClose?: () => void
}

const AgentPanel: React.FC<AgentPanelProps> = ({ filePath, onClose }) => {
  const [explanation, setExplanation] = useState<AgentExplanation | null>(null)
  const [suggestions, setSuggestions] = useState<AgentSuggestions | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'explain' | 'suggest'>('explain')
  const { current: currentProject } = useProject()

  const handleExplain = async () => {
    if (!filePath) {
      setError('No file selected')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await axios.post('/api/agent/explain', {
        file: filePath,
        line: 1,
        project: currentProject?.path || '',
      })

      if (response.status === 200) {
        setExplanation(response.data)
        setActiveTab('explain')
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSuggest = async () => {
    if (!filePath) {
      setError('No file selected')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await axios.post('/api/agent/suggest', {
        file: filePath,
        project: currentProject?.path || '',
      })

      if (response.status === 200) {
        setSuggestions(response.data)
        setActiveTab('suggest')
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full bg-gray-900 border-l border-gray-700">
      {/* Header with buttons */}
      <div className="border-b border-gray-700 p-4 space-y-2">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-gray-100">Programming Agent</h2>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-300 text-lg"
            >
              ×
            </button>
          )}
        </div>

        {filePath && (
          <p className="text-xs text-gray-500 truncate">
            File: {filePath.split('/').pop()}
          </p>
        )}

        {error && (
          <div className="text-xs bg-red-900 text-red-100 p-2 rounded">
            {error}
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-2">
          <button
            onClick={handleExplain}
            disabled={!filePath || loading}
            className="flex-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white text-xs font-medium rounded transition"
          >
            {loading && activeTab === 'explain' ? 'Analyzing...' : '🔍 Explain'}
          </button>
          <button
            onClick={handleSuggest}
            disabled={!filePath || loading}
            className="flex-1 px-3 py-1.5 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 text-white text-xs font-medium rounded transition"
          >
            {loading && activeTab === 'suggest' ? 'Analyzing...' : '💡 Suggest'}
          </button>
        </div>
      </div>

      {/* Tab selector */}
      <div className="flex border-b border-gray-700 bg-gray-800">
        <button
          onClick={() => setActiveTab('explain')}
          className={`flex-1 px-4 py-2 text-xs font-medium transition ${
            activeTab === 'explain'
              ? 'border-b-2 border-blue-500 text-blue-400'
              : 'text-gray-400 hover:text-gray-300'
          }`}
        >
          Explanation
        </button>
        <button
          onClick={() => setActiveTab('suggest')}
          className={`flex-1 px-4 py-2 text-xs font-medium transition ${
            activeTab === 'suggest'
              ? 'border-b-2 border-green-500 text-green-400'
              : 'text-gray-400 hover:text-gray-300'
          }`}
        >
          Suggestions
        </button>
      </div>

      {/* Content area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {activeTab === 'explain' && explanation && (
          <ExplanationView explanation={explanation} />
        )}

        {activeTab === 'suggest' && suggestions && (
          <SuggestionsView suggestions={suggestions} />
        )}

        {!explanation && !suggestions && !loading && (
          <div className="text-center text-gray-500 py-8">
            <p className="text-sm">Click a button above to analyze</p>
          </div>
        )}
      </div>
    </div>
  )
}

// Sub-component: Display explanation
const ExplanationView: React.FC<{ explanation: AgentExplanation }> = ({
  explanation,
}) => {
  return (
    <>
      {/* Summary */}
      <div className="bg-gray-800 rounded p-3 border border-gray-700">
        <p className="text-xs font-bold text-gray-300 mb-2">Summary</p>
        <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">
          {explanation.summary}
        </p>
      </div>

      {/* Functions */}
      {explanation.functions.length > 0 && (
        <div className="bg-gray-800 rounded p-3 border border-gray-700">
          <p className="text-xs font-bold text-blue-300 mb-2">
            Functions ({explanation.functions.length})
          </p>
          <div className="space-y-2">
            {explanation.functions.slice(0, 5).map((fn, idx) => (
              <div key={idx} className="text-xs bg-gray-900 p-2 rounded border border-gray-700">
                <p className="text-blue-300 font-mono">
                  {fn.name}() <span className="text-gray-500">@L{fn.line}</span>
                </p>
                {fn.docstring && (
                  <p className="text-gray-400 mt-1 text-xs">
                    {fn.docstring.split('\n')[0]}
                  </p>
                )}
              </div>
            ))}
            {explanation.functions.length > 5 && (
              <p className="text-xs text-gray-500">
                +{explanation.functions.length - 5} more functions
              </p>
            )}
          </div>
        </div>
      )}

      {/* Imports */}
      {explanation.imports.length > 0 && (
        <div className="bg-gray-800 rounded p-3 border border-gray-700">
          <p className="text-xs font-bold text-green-300 mb-2">
            Imports ({explanation.imports.length})
          </p>
          <div className="space-y-1">
            {explanation.imports.slice(0, 8).map((imp, idx) => (
              <p key={idx} className="text-xs text-gray-400 font-mono">
                <span className="text-green-400">import</span> {imp.module}
                {imp.name && <span className="text-gray-500"> as {imp.name}</span>}
              </p>
            ))}
            {explanation.imports.length > 8 && (
              <p className="text-xs text-gray-500">
                +{explanation.imports.length - 8} more imports
              </p>
            )}
          </div>
        </div>
      )}

      {/* Affected files */}
      <div className="bg-gray-800 rounded p-3 border border-gray-700">
        <p className="text-xs text-gray-400">
          <span className="font-bold">Affected files:</span> {explanation.affected_files}
        </p>
      </div>
    </>
  )
}

// Sub-component: Display suggestions
const SuggestionsView: React.FC<{ suggestions: AgentSuggestions }> = ({
  suggestions,
}) => {
  const getSeverityColor = (type: string): string => {
    if (type.includes('high') || type.includes('critical')) return 'red'
    if (type.includes('medium')) return 'yellow'
    return 'blue'
  }

  return (
    <>
      {/* Summary */}
      <div className="bg-gray-800 rounded p-3 border border-gray-700">
        <p className="text-xs font-bold text-gray-300">{suggestions.summary}</p>
      </div>

      {/* Suggestions list */}
      {suggestions.suggestions.length > 0 ? (
        <div className="space-y-2">
          {suggestions.suggestions.map((sugg, idx) => {
            const severity = getSeverityColor(sugg.type)
            const severityColors = {
              red: 'bg-red-900 text-red-100 border-red-700',
              yellow: 'bg-yellow-900 text-yellow-100 border-yellow-700',
              blue: 'bg-blue-900 text-blue-100 border-blue-700',
            }

            return (
              <div
                key={idx}
                className={`rounded p-3 border ${severityColors[severity as keyof typeof severityColors]}`}
              >
                <p className="text-xs font-bold mb-1">[{sugg.type}]</p>
                <p className="text-xs leading-relaxed">{sugg.message}</p>
                {sugg.details && (
                  <p className="text-xs mt-2 opacity-80">{sugg.details}</p>
                )}
              </div>
            )
          })}
        </div>
      ) : (
        <div className="text-center text-gray-500 py-8">
          <p className="text-sm">No suggestions at this time</p>
        </div>
      )}
    </>
  )
}

export default AgentPanel
