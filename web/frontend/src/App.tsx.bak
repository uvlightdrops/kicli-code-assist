import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { io } from 'socket.io-client'
import ChatInput from './components/ChatInput'
import ChatHistory from './components/ChatHistory'
import FileList from './components/FileList'
import TerminalLog from './components/TerminalLog'
import StatusBar from './components/StatusBar'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  files?: Array<{ path: string; content: string }>
  timestamp: number
}

interface UploadedFile {
  id: string
  path: string
  size: number
}

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'chat' | 'logs' | 'config'>('chat')
  const [connected, setConnected] = useState(false)
  const socketRef = useRef<any>(null)

  // Initialize WebSocket
  useEffect(() => {
    socketRef.current = io('http://localhost:8000', {
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
    })

    socketRef.current.on('connect', () => {
      console.log('WebSocket connected')
      setConnected(true)
    })

    socketRef.current.on('disconnect', () => {
      console.log('WebSocket disconnected')
      setConnected(false)
    })

    socketRef.current.on('chat.response', (data: any) => {
      console.log('Chat response:', data)
      if (data.type === 'chunk') {
        // Append to last message or create new one
        setMessages((prev) => {
          const updated = [...prev]
          if (updated.length === 0) {
            updated.push({
              id: data.request_id,
              role: 'assistant',
              content: data.content,
              timestamp: Date.now(),
            })
          } else {
            const last = updated[updated.length - 1]
            if (last.role === 'assistant' && last.id === data.request_id) {
              last.content += data.content
            } else {
              updated.push({
                id: data.request_id,
                role: 'assistant',
                content: data.content,
                timestamp: Date.now(),
              })
            }
          }
          return updated
        })
      } else if (data.type === 'complete') {
        setLoading(false)
      } else if (data.type === 'error') {
        setError(data.error)
        setLoading(false)
      }
    })

    return () => {
      socketRef.current?.disconnect()
    }
  }, [])

  // Send message to backend
  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return

    // Add user message
    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: Date.now(),
    }
    setMessages((prev) => [...prev, userMsg])
    setLoading(true)
    setError(null)

    try {
      // Submit to backend
      const response = await axios.post('/api/chat', {
        message: text,
        files: files.map((f) => ({ path: f.path, id: f.id })),
      })

      const { request_id } = response.data

      // Subscribe to WebSocket updates
      socketRef.current.emit('subscribe', { channel: request_id })
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to send message')
      setLoading(false)
    }
  }

  // Handle file upload
  const handleFileUpload = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post('/api/files/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      setFiles((prev) => [
        ...prev,
        {
          id: response.data.file_id,
          path: response.data.path,
          size: response.data.size_bytes,
        },
      ])
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to upload file')
    }
  }

  // Delete file
  const handleDeleteFile = (fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId))
  }

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 px-4 py-3">
        <h1 className="text-2xl font-bold">kicli-assist WebIDE</h1>
        <p className="text-xs text-gray-400">Web-based code assistant IDE</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-700 bg-gray-800">
        {(['chat', 'logs', 'config'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 font-medium capitalize ${
              activeTab === tab
                ? 'border-b-2 border-blue-500 text-blue-400'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel: Chat or Logs */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {activeTab === 'chat' && (
            <>
              <ChatHistory messages={messages} loading={loading} />
              <ChatInput onSend={handleSendMessage} disabled={loading} />
            </>
          )}
          {activeTab === 'logs' && <TerminalLog />}
          {activeTab === 'config' && (
            <div className="flex-1 overflow-auto p-4">
              <ConfigDisplay />
            </div>
          )}
        </div>

        {/* Right Sidebar: Files & Status */}
        <div className="w-64 border-l border-gray-700 bg-gray-800 flex flex-col">
          <FileList files={files} onDeleteFile={handleDeleteFile} onUploadFile={handleFileUpload} />
          <StatusBar connected={connected} error={error} />
        </div>
      </div>
    </div>
  )
}

// Config Display Component
const ConfigDisplay: React.FC = () => {
  const [config, setConfig] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get('/api/config').then((res) => {
      setConfig(res.data)
      setLoading(false)
    })
  }, [])

  if (loading) return <div>Loading config...</div>

  return (
    <pre className="text-xs font-mono bg-gray-900 p-2 rounded overflow-auto">
      {JSON.stringify(config, null, 2)}
    </pre>
  )
}

export default App
