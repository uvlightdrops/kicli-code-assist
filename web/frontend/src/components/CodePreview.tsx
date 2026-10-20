import React, { useState, useRef, useEffect } from 'react'
import Editor from '@monaco-editor/react'
import { initVimMode } from 'monaco-vim'

interface CodePreviewProps {
  filePath: string
  content: string
  isDirty?: boolean
  onContentChange?: (content: string) => void
  onSave?: (content: string) => void
  isSaving?: boolean
}

const CodePreview: React.FC<CodePreviewProps> = ({
  filePath,
  content,
  isDirty = false,
  onContentChange,
  onSave,
  isSaving = false,
}) => {
  const [isEditMode, setIsEditMode] = useState(false)
  const [currentContent, setCurrentContent] = useState(content)
  const [vimMode, setVimMode] = useState(() => localStorage.getItem('vimMode') === 'true')
  const [showCreateFile, setShowCreateFile] = useState(false)
  const [newFileName, setNewFileName] = useState('')
  const [createError, setCreateError] = useState('')
  const editorRef = useRef<any>(null)
  const statusRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setCurrentContent(content)
  }, [content, filePath])

  const getLanguageFromPath = (path: string): string => {
    const ext = path.split('.').pop()?.toLowerCase() || ''
    const languageMap: Record<string, string> = {
      py: 'python',
      ts: 'typescript',
      tsx: 'typescript',
      js: 'javascript',
      jsx: 'javascript',
      yaml: 'yaml',
      yml: 'yaml',
      json: 'json',
      md: 'markdown',
      go: 'go',
      rs: 'rust',
      java: 'java',
      cpp: 'cpp',
      c: 'c',
      sh: 'shell',
      bash: 'shell',
      sql: 'sql',
      html: 'html',
      css: 'css',
      xml: 'xml',
    }
    return languageMap[ext] || 'plaintext'
  }

  const handleEditorMount = (editor: any) => {
    editorRef.current = editor
    
    if (vimMode) {
      initVimMode(editor, statusRef.current)
    }
    
    editor.focus()
  }

  const toggleVimMode = () => {
    const newVimMode = !vimMode
    setVimMode(newVimMode)
    localStorage.setItem('vimMode', newVimMode ? 'true' : 'false')
    
    if (editorRef.current) {
      if (newVimMode) {
        initVimMode(editorRef.current, statusRef.current)
      } else {
        editorRef.current.getModel()?.setValue(currentContent)
      }
    }
  }

  const handleOpenFind = () => {
    if (editorRef.current) {
      editorRef.current.getAction('editor.action.find')?.run()
    }
  }

  const handleOpenReplace = () => {
    if (editorRef.current) {
      editorRef.current.getAction('editor.action.replace')?.run()
    }
  }

  const handleCreateFile = async () => {
    if (!newFileName.trim()) {
      setCreateError('File name cannot be empty')
      return
    }

    try {
      const response = await fetch('/api/files/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newFileName,
          content: currentContent,
        }),
      })

      if (!response.ok) {
        const error = await response.json()
        setCreateError(error.error || 'Failed to create file')
        return
      }

      const data = await response.json()
      setShowCreateFile(false)
      setNewFileName('')
      setCreateError('')
      
      if (onSave) {
        await onSave(currentContent)
      }
    } catch (error) {
      setCreateError(error instanceof Error ? error.message : 'Unknown error')
    }
  }

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      setCurrentContent(value)
      onContentChange?.(value)
    }
  }

  const handleSave = async () => {
    if (onSave) {
      await onSave(currentContent)
      setIsEditMode(false)
    }
  }

  const handleCancel = () => {
    setCurrentContent(content)
    setIsEditMode(false)
  }

  const handleKeyDown = (e: KeyboardEvent) => {
    if (isEditMode && (e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault()
      handleSave()
    }
  }

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isEditMode, currentContent])

  const language = getLanguageFromPath(filePath)

  return (
    <div className="flex flex-col h-full bg-gray-900 border border-gray-700 rounded overflow-hidden">
      {/* Toolbar */}
      <div className="bg-gray-800 border-b border-gray-700 px-3 py-2 flex items-center justify-between">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <span className="text-xs font-mono text-gray-400 truncate">{filePath}</span>
          <span className="text-xs text-gray-500">({language})</span>
          {isDirty && !isEditMode && <span className="text-yellow-500 text-xs">●</span>}
          {isSaving && <span className="text-blue-400 text-xs animate-pulse">Saving...</span>}
        </div>

        <div className="flex items-center gap-2">
          {isEditMode && (
            <>
              <button
                onClick={toggleVimMode}
                title={vimMode ? 'Vim Mode: ON (press :q to exit)' : 'Vim Mode: OFF (Vi keybindings disabled)'}
                className={`px-2 py-1 text-xs rounded transition font-mono ${
                  vimMode
                    ? 'bg-purple-600 hover:bg-purple-700 text-white'
                    : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                }`}
              >
                {vimMode ? '⌨ Vim' : '⌨'}
              </button>
              <button
                onClick={handleOpenFind}
                title="Find (Ctrl+F)"
                className="px-2 py-1 text-xs rounded transition bg-gray-700 hover:bg-gray-600 text-gray-300"
              >
                🔍
              </button>
              <button
                onClick={handleOpenReplace}
                title="Find & Replace (Ctrl+H)"
                className="px-2 py-1 text-xs rounded transition bg-gray-700 hover:bg-gray-600 text-gray-300"
              >
                🔄
              </button>
            </>
          )}
          {!isEditMode ? (
            <>
              <button
                onClick={() => setIsEditMode(true)}
                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition"
              >
                Edit
              </button>
              <button
                onClick={() => setShowCreateFile(true)}
                title="Create new file from current content"
                className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white text-xs rounded transition"
              >
                💾 Save As
              </button>
            </>
          ) : (
            <>
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="px-3 py-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white text-xs rounded transition"
              >
                Save (Ctrl+S)
              </button>
              <button
                onClick={handleCancel}
                className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white text-xs rounded transition"
              >
                Cancel
              </button>
            </>
          )}
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-hidden">
          <Editor
            height="100%"
            language={language}
            value={currentContent}
            onChange={handleEditorChange}
            onMount={handleEditorMount}
            theme="vs-dark"
            options={{
              readOnly: !isEditMode,
              minimap: { enabled: false },
              fontSize: 13,
              lineNumbers: 'on',
              wordWrap: 'on',
              automaticLayout: true,
              padding: { top: 10, bottom: 10 },
              scrollBeyondLastLine: false,
            }}
          />
        </div>

        {/* Vim Status Line (only when vim mode active) */}
        {isEditMode && vimMode && (
          <div
            ref={statusRef}
            className="bg-gray-950 border-t border-purple-600 px-3 py-1 text-xs text-purple-400 font-mono"
            style={{ minHeight: '20px' }}
          />
        )}
      </div>

      {/* Create File Modal */}
      {showCreateFile && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 border border-gray-600 rounded shadow-lg p-4 max-w-md w-full mx-4">
            <h3 className="text-sm font-semibold text-white mb-3">Save File As</h3>
            
            <input
              type="text"
              placeholder="Enter filename (e.g., newfile.py)"
              value={newFileName}
              onChange={(e) => {
                setNewFileName(e.target.value)
                setCreateError('')
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleCreateFile()
                if (e.key === 'Escape') setShowCreateFile(false)
              }}
              autoFocus
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 mb-3"
            />
            
            {createError && (
              <div className="text-red-400 text-xs mb-3">{createError}</div>
            )}
            
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => {
                  setShowCreateFile(false)
                  setCreateError('')
                }}
                className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white text-xs rounded transition"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateFile}
                className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white text-xs rounded transition"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CodePreview
