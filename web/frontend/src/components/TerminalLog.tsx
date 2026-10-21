import React, { useState } from 'react'

const TerminalLog: React.FC = () => {
  // TODO: Implement /api/logs endpoint if needed
  // For now, show a placeholder message
  const [logs] = useState<string[]>([])

  return (
    <div className="flex-1 overflow-auto bg-gray-900 p-4 flex items-center justify-center">
      <div className="text-center text-gray-500">
        <p className="text-lg mb-2">📋 Terminal Logs</p>
        <p className="text-xs">Log viewing coming soon...</p>
      </div>
    </div>
  )
}

export default TerminalLog
