import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { io } from 'socket.io-client'
import ChatInput from './components/ChatInput'
import ChatHistory from './components/ChatHistory'
import FileList from './components/FileList'
import FileBrowser from './components/FileBrowser'
import CodePreview from './components/CodePreview'
import EditorTabs from './components/EditorTabs'
import AgentPanel from './components/AgentPanel'
import TerminalLog from './components/TerminalLog'
import { FeatureNav } from './components/FeatureNav'
import { ReasoningPanel } from './components/ReasoningPanel'
import { EnsemblePanel } from './components/EnsemblePanel'
import { ToolsPanel } from './components/ToolsPanel'
import { DependencyPanel } from './components/DependencyPanel'
import { RefactoringPanel } from './components/RefactoringPanel'
import { AgentChatContainer } from './components/AgentChatContainer'
import { MetricsPanel } from './components/MetricsPanel'
import { ThinkingStepsPanel } from './components/ThinkingStepsPanel'
import EmptyState from './components/EmptyState'
import CreateProjectModal from './components/CreateProjectModal'
import OpenProjectModal from './components/OpenProjectModal'
import { ProjectProvider, useProject } from './hooks/useProject'
import type { Project } from './types/project'

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

const AppContent: React.FC = () => {
  const { current: project, isEmpty, closeProject } = useProject()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showOpenModal, setShowOpenModal] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [openTabs, setOpenTabs] = useState<TabFile[]>([])
  const [selectedFile, setSelectedFile] = useState<{ path: string; content: string } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [leftPanelTab, setLeftPanelTab] = useState<'files' | 'browser' | 'logs'>('files')
  const [showConfig, setShowConfig] = useState(false)
  const [connected, setConnected] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [showAgentPanel, setShowAgentPanel] = useState(false)
  const [useHybridAgent, setUseHybridAgent] = useState(true) // NEW: Use new Hybrid Agent UI
  const [currentFeature, setCurrentFeature] = useState<'explain' | 'reasoning' | 'ensemble' | 'dependencies' | 'refactor' | 'metrics' | 'tools'>('explain')
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

  // Show Empty State if no project
  if (isEmpty) {
    return (
      <>
        <EmptyState 
          onOpenProjectModal={() => setShowOpenModal(true)}
          onCreateProjectModal={() => setShowCreateModal(true)}
        />
        <CreateProjectModal 
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
        />
        <OpenProjectModal 
          isOpen={showOpenModal}
          onClose={() => setShowOpenModal(false)}
        />
      </>
    )
  }

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-gray-100">
      {/* Header - Status + Config Link + Project Controls */}
      <div className="bg-gray-800 border-b border-gray-700 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">Project:</span>
          <span className="text-xs font-semibold text-blue-400">{project?.name}</span>
          <button
            onClick={closeProject}
            className="ml-2 px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded transition"
            title="Close project"
          >
            ✕
          </button>
        </div>
        <div className="flex items-center gap-4 text-xs">
          {/* Connection Status */}
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}
            ></div>
            <span className="text-gray-400">
              {connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          {/* Server Info */}
          <div className="text-gray-500">localhost:8000</div>
          {/* Config Link */}
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="px-2 py-1 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded transition"
            title="Settings"
          >
            ⚙️ Config
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar: Files + Browser */}
        <div className="w-64 border-r border-gray-700 bg-gray-800 flex flex-col overflow-hidden">
          {/* Sidebar Tabs */}
          <div className="flex border-b border-gray-700">
            {(['files', 'browser', 'logs'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setLeftPanelTab(tab)}
                className={`flex-1 px-2 py-2 text-xs font-medium capitalize ${
                  leftPanelTab === tab
                    ? 'border-b-2 border-blue-500 text-blue-400 bg-gray-700'
                    : 'text-gray-400 hover:text-gray-300'
                }`}
              >
                {tab === 'files' && '📁 Files'}
                {tab === 'browser' && '🗂️ Browser'}
                {tab === 'logs' && '📝 Logs'}
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="flex-1 overflow-hidden">
            {leftPanelTab === 'files' && (
              <FileList files={files} onDeleteFile={handleDeleteFile} onUploadFile={handleFileUpload} />
            )}
            {leftPanelTab === 'browser' && <FileBrowser onSelectFile={handleSelectFile} />}
            {leftPanelTab === 'logs' && <TerminalLog />}
          </div>
        </div>

        {/* Center + Right: Editor on left, Chat/Agent on right (equal width) */}
        <div className="flex-1 flex overflow-hidden">
          <>
            {/* Main Editor Area (Left) - flex-1 for equal width */}
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Editor Area: Tabs + Preview */}
              {selectedFile && (
                <>
                  <EditorTabs
                    tabs={openTabs}
                    onSelectTab={handleSelectTab}
                    onCloseTab={handleCloseTab}
                    onAskAgent={() => setShowAgentPanel(!showAgentPanel)}
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

              {!selectedFile && (
                <div className="flex-1 flex items-center justify-center text-gray-500">
                  <p>Select a file to start editing</p>
                </div>
              )}
            </div>

            {/* Right Sidebar: Chat or Hybrid Agent - flex-1 for equal width */}
            <div className="flex-1 border-l border-gray-700 bg-gray-800 flex flex-col overflow-hidden">
              {/* Use new Hybrid Agent UI */}
              {useHybridAgent ? (
                <div className="flex-1 overflow-hidden">
                  <AgentChatContainer 
                    currentFile={selectedFile?.path || null}
                    projectPath={project?.path || null}
                  />
                </div>
              ) : (
                // Old Chat/Agent UI (kept for backward compatibility)
                <>
                  {/* Tab selector with Feature Navigation */}
                  <div className="border-b border-gray-700 p-2 space-y-2">
                    <div className="flex gap-2">
                      <button
                        onClick={() => setShowAgentPanel(false)}
                        className={`flex-1 px-3 py-2 text-xs font-medium rounded transition ${
                          !showAgentPanel
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                        }`}
                      >
                        💬 Chat
                      </button>
                      <button
                        onClick={() => setShowAgentPanel(true)}
                        className={`flex-1 px-3 py-2 text-xs font-medium rounded transition ${
                          showAgentPanel
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                        }`}
                      >
                        🤖 Agent
                      </button>
                    </div>
                    
                    {/* Feature Navigation (only shown when Agent tab is active) */}
                    {showAgentPanel && (
                      <FeatureNav 
                        currentFeature={currentFeature as any}
                        onFeatureChange={(f) => setCurrentFeature(f as any)}
                      />
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 flex flex-col overflow-hidden">
                    {!showAgentPanel ? (
                      <>
                        <ChatHistory messages={messages} loading={loading} />
                        <ChatInput onSend={handleSendMessage} disabled={loading} />
                      </>
                    ) : (
                      <>
                        {/* Explain Panel (with Thinking Steps below) */}
                        {currentFeature === 'explain' && (
                          <div className="flex flex-col h-full">
                            <div className="flex-1 overflow-hidden min-h-0">
                              <AgentPanel 
                                filePath={selectedFile?.path || null}
                                onClose={() => setShowAgentPanel(false)}
                              />
                            </div>
                            <div className="h-1/3 overflow-hidden min-h-0">
                              <ThinkingStepsPanel selectedFile={selectedFile?.path || null} />
                            </div>
                          </div>
                        )}
                        
                        {/* Reasoning Panel */}
                        {currentFeature === 'reasoning' && (
                          <ReasoningPanel
                            file={selectedFile?.path}
                            isVisible={true}
                          />
                        )}
                        
                        {/* Ensemble Panel */}
                        {currentFeature === 'ensemble' && (
                          <EnsemblePanel
                            file={selectedFile?.path}
                            selectedCode={selectedFile?.content}
                            isVisible={true}
                          />
                        )}
                        
                        {/* Dependencies Panel */}
                        {currentFeature === 'dependencies' && (
                          <DependencyPanel selectedFile={selectedFile?.path || null} />
                        )}
                        
                        {/* Refactoring Panel */}
                        {currentFeature === 'refactor' && (
                          <RefactoringPanel selectedFile={selectedFile?.path || null} />
                        )}
                        
                        {/* Metrics Panel */}
                        {currentFeature === 'metrics' && (
                          <MetricsPanel selectedFile={selectedFile?.path || null} />
                        )}
                        
                        {/* Tools Panel */}
                        {currentFeature === 'tools' && (
                          <ToolsPanel isVisible={true} />
                        )}
                      </>
                    )}
                  </div>
                </>
              )}
            </div>
          </>
        </div>

        
        {/* Config Modal */}
        {showConfig && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 max-w-2xl max-h-96 overflow-auto">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold text-white">⚙️ Application Config</h2>
                <button
                  onClick={() => setShowConfig(false)}
                  className="text-gray-400 hover:text-white transition"
                  title="Close config"
                >
                  ✕
                </button>
              </div>
              <ConfigDisplay />
            </div>
          </div>
        )}
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

export default function App() {
  return (
    <ProjectProvider>
      <AppContent />
    </ProjectProvider>
  )
}
