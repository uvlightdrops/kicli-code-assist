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
        // Restart editor to disable vim mode
        editorRef.current.getModel()?.setValue(currentContent)
      }
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
          )}
          {!isEditMode ? (
            <button
              onClick={() => setIsEditMode(true)}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition"
            >
              Edit
            </button>
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
              // Find & Replace
              find: {
                seedSearchStringFromSelection: true,
                autoFindInSelection: 'never',
              },
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
    </div>
  )
}

export default CodePreview
