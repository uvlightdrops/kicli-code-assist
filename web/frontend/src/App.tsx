import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { io } from 'socket.io-client'
import ChatInput from './components/ChatInput'
import ChatHistory from './components/ChatHistory'
import FileList from './components/FileList'
import FileBrowser from './components/FileBrowser'
import CodePreview from './components/CodePreview'
import EditorTabs from './components/EditorTabs'
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

interface TabFile {
  path: string
  content: string
  active: boolean
  originalContent?: string // Track original for dirty checking
}

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [openTabs, setOpenTabs] = useState<TabFile[]>([])
  const [selectedFile, setSelectedFile] = useState<{ path: string; content: string } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'chat' | 'logs' | 'config'>('chat')
  const [leftPanelTab, setLeftPanelTab] = useState<'files' | 'browser'>('files')
  const [connected, setConnected] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
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
      if (data.type === 'chunk') {
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

  // Handle file selection from browser
  const handleSelectFile = (path: string, content: string) => {
    // Check if already open
    const existing = openTabs.find((t) => t.path === path)
    if (existing) {
      setSelectedFile({ path, content })
      setOpenTabs(openTabs.map((t) => ({ ...t, active: t.path === path })))
    } else {
      // Add new tab with originalContent for dirty tracking
      const newTab: TabFile = { path, content, active: true, originalContent: content }
      setOpenTabs([...openTabs.map((t) => ({ ...t, active: false })), newTab])
      setSelectedFile({ path, content })
    }
  }

  const handleSelectTab = (path: string) => {
    const tab = openTabs.find((t) => t.path === path)
    if (tab) {
      setSelectedFile({ path: tab.path, content: tab.content })
      setOpenTabs(openTabs.map((t) => ({ ...t, active: t.path === path })))
    }
  }

  const handleCloseTab = (path: string) => {
    const remaining = openTabs.filter((t) => t.path !== path)
    setOpenTabs(remaining)
    if (selectedFile?.path === path) {
      setSelectedFile(remaining.length > 0 ? { path: remaining[0].path, content: remaining[0].content } : null)
    }
  }

  // Handle content changes in editor
  const handleContentChange = (newContent: string) => {
    if (!selectedFile) return
    
    // Update selected file
    setSelectedFile({ ...selectedFile, content: newContent })
    
    // Update tab with new content
    setOpenTabs(
      openTabs.map((t) =>
        t.path === selectedFile.path ? { ...t, content: newContent } : t
      )
    )
  }

  // Save file to backend
  const handleSaveFile = async (content: string) => {
    if (!selectedFile) return
    
    setIsSaving(true)
    try {
      const response = await axios.put(`/api/files/save`, {
        path: selectedFile.path,
        content: content,
      })
      
      // Update tab's originalContent to mark as saved
      setOpenTabs(
        openTabs.map((t) =>
          t.path === selectedFile.path
            ? { ...t, originalContent: content }
            : t
        )
      )
      
      setError(null)
      // Show brief success message
      console.log('File saved:', selectedFile.path)
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || 'Failed to save file'
      setError(errorMsg)
      console.error('Save error:', errorMsg)
    } finally {
      setIsSaving(false)
    }
  }

  // Check if current file has unsaved changes
  const currentTabIsDirty = selectedFile
    ? openTabs.find((t) => t.path === selectedFile.path)?.content !==
      openTabs.find((t) => t.path === selectedFile.path)?.originalContent
    : false

  // Send message to backend
  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return

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
      const response = await axios.post('/api/chat', {
        message: text,
        files: [
          ...files.map((f) => ({ path: f.path, id: f.id })),
          ...(selectedFile ? [{ path: selectedFile.path, content: selectedFile.content }] : []),
        ],
      })

      const { request_id } = response.data
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
        <p className="text-xs text-gray-400">AI-powered code assistant with file browser & preview</p>
      </div>

      {/* Main Tabs */}
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

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar: Files + Browser */}
        <div className="w-64 border-r border-gray-700 bg-gray-800 flex flex-col overflow-hidden">
          {/* Sidebar Tabs */}
          <div className="flex border-b border-gray-700">
            {(['files', 'browser'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setLeftPanelTab(tab)}
                className={`flex-1 px-2 py-2 text-xs font-medium capitalize ${
                  leftPanelTab === tab
                    ? 'border-b-2 border-blue-500 text-blue-400 bg-gray-700'
                    : 'text-gray-400 hover:text-gray-300'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="flex-1 overflow-hidden">
            {leftPanelTab === 'files' && (
              <FileList files={files} onDeleteFile={handleDeleteFile} onUploadFile={handleFileUpload} />
            )}
            {leftPanelTab === 'browser' && <FileBrowser onSelectFile={handleSelectFile} />}
          </div>
        </div>

        {/* Center: Chat or Logs or Config */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {activeTab === 'chat' && (
            <>
              {/* Editor Area: Tabs + Preview */}
              {selectedFile && (
                <>
                  <EditorTabs
                    tabs={openTabs}
                    onSelectTab={handleSelectTab}
                    onCloseTab={handleCloseTab}
                  />
                  <div className="flex-1 overflow-auto">
                    <CodePreview 
                      filePath={selectedFile.path} 
                      content={selectedFile.content}
                      isDirty={currentTabIsDirty}
                      onContentChange={handleContentChange}
                      onSave={handleSaveFile}
                      isSaving={isSaving}
                    />
                  </div>
                </>
              )}

              {/* Chat Area */}
              <div className={`${selectedFile ? 'h-64 border-t border-gray-700' : 'flex-1'} flex flex-col`}>
                <ChatHistory messages={messages} loading={loading} />
                <ChatInput onSend={handleSendMessage} disabled={loading} />
              </div>
            </>
          )}
          {activeTab === 'logs' && <TerminalLog />}
          {activeTab === 'config' && (
            <div className="flex-1 overflow-auto p-4">
              <ConfigDisplay />
            </div>
          )}
        </div>

        {/* Right Sidebar: Status */}
        <div className="w-64 border-l border-gray-700 bg-gray-800">
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
