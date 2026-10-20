import React from 'react'

interface StatusBarProps {
  connected: boolean
  error: string | null
}

const StatusBar: React.FC<StatusBarProps> = ({ connected, error }) => {
  return (
    <div className="border-t border-gray-700 bg-gray-800 p-3 text-xs space-y-2">
      {/* Connection Status */}
      <div className="flex items-center gap-2">
        <div
          className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}
        ></div>
        <span className="text-gray-400">
          {connected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-900 bg-opacity-30 border border-red-700 rounded p-2 text-red-300">
          <p className="font-semibold text-xs mb-1">Error:</p>
          <p className="text-xs break-words">{error}</p>
        </div>
      )}

      {/* Stats */}
      <div className="pt-2 border-t border-gray-700">
        <p className="text-gray-500">
          <span className="text-gray-400">localhost:8000</span>
        </p>
      </div>
    </div>
  )
}

export default StatusBar
