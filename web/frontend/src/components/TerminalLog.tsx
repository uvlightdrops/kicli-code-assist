import React, { useState, useEffect } from 'react'
import axios from 'axios'

const TerminalLog: React.FC = () => {
  const [logs, setLogs] = useState<string[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await axios.get('/api/logs', { params: { lines: 50 } })
        setLogs(response.data.logs)
      } catch (err) {
        console.error('Failed to fetch logs:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchLogs()
    const interval = setInterval(fetchLogs, 2000) // Refresh every 2s

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex-1 overflow-auto bg-gray-900 p-4">
      {loading ? (
        <div className="text-gray-500">Loading logs...</div>
      ) : logs.length === 0 ? (
        <div className="text-gray-500">No logs yet</div>
      ) : (
        <pre className="text-xs font-mono text-gray-300 whitespace-pre-wrap break-words">
          {logs.join('')}
        </pre>
      )}
    </div>
  )
}

export default TerminalLog
