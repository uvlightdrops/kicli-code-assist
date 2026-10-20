import React, { useState, useEffect } from 'react'
import axios from 'axios'

interface FileItem {
  name: string
  type: 'file' | 'folder'
  path: string
  size_bytes?: number
}

interface FileBrowserProps {
  onSelectFile: (path: string, content: string) => void
}

const FileBrowser: React.FC<FileBrowserProps> = ({ onSelectFile }) => {
  const [currentPath, setCurrentPath] = useState('')
  const [items, setItems] = useState<FileItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [breadcrumb, setBreadcrumb] = useState<string[]>(['dev_flow'])
  const [loadingFile, setLoadingFile] = useState<string | null>(null)

  // Load files from backend
  useEffect(() => {
    loadFiles(currentPath)
  }, [currentPath])

  const loadFiles = async (path: string) => {
    setLoading(true)
    setError('')
    try {
      const response = await axios.get('/api/project/files', {
        params: { path: path || '' },
      })
      setItems(response.data.items)
      setBreadcrumb(['dev_flow', ...path.split('/').filter(Boolean)])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load files')
      setItems([])
    } finally {
      setLoading(false)
    }
  }

  const handleFolderClick = (folder: FileItem) => {
    setCurrentPath(folder.path)
  }

  const handleFileClick = async (file: FileItem) => {
    setLoadingFile(file.path)
    try {
      const response = await axios.get(`/api/files/${file.path}`, {
        headers: { 'Range': 'bytes=0-1048576' }, // First 1MB
      })
      onSelectFile(file.path, response.data.content || '')
    } catch (err) {
      setError(`Failed to load file: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setLoadingFile(null)
    }
  }

  const navigateToBreadcrumb = (index: number) => {
    if (index === 0) {
      setCurrentPath('')
    } else {
      const path = breadcrumb.slice(1, index + 1).join('/')
      setCurrentPath(path)
    }
  }

  const goUp = () => {
    const parts = currentPath.split('/').filter(Boolean)
    if (parts.length > 0) {
      parts.pop()
      setCurrentPath(parts.join('/'))
    }
  }

  return (
    <div className="flex flex-col h-full bg-gray-800">
      {/* Header */}
      <div className="border-b border-gray-700 p-2 bg-gray-900">
        <h3 className="text-xs font-semibold text-gray-400 uppercase mb-2">Project Files</h3>
        
        {/* Breadcrumb */}
        <div className="flex items-center gap-1 text-xs text-gray-400 mb-2 overflow-x-auto">
          {breadcrumb.map((part, idx) => (
            <div key={idx} className="flex items-center gap-1 whitespace-nowrap">
              {idx > 0 && <span className="text-gray-600">/</span>}
              <button
                onClick={() => navigateToBreadcrumb(idx)}
                className="hover:text-blue-400 transition"
              >
                {part}
              </button>
            </div>
          ))}
        </div>

        {/* Navigation Buttons */}
        {currentPath && (
          <button
            onClick={goUp}
            className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded transition"
          >
            ⬆ Up
          </button>
        )}
      </div>

      {/* File List */}
      <div className="flex-1 overflow-auto p-1 font-mono text-xs">
        {error && <div className="text-red-400 p-2 text-xs">{error}</div>}
        
        {loading ? (
          <div className="text-gray-500 p-2">Loading...</div>
        ) : items.length === 0 ? (
          <div className="text-gray-500 p-2">No files</div>
        ) : (
          items.map((item) => (
            <div
              key={item.path}
              onClick={() => item.type === 'folder' ? handleFolderClick(item) : handleFileClick(item)}
              className={`flex items-center gap-2 p-2 rounded cursor-pointer transition ${
                item.type === 'folder'
                  ? 'text-gray-300 hover:bg-gray-700'
                  : `text-gray-400 hover:bg-gray-700 ${loadingFile === item.path ? 'bg-blue-900' : ''}`
              }`}
            >
              {item.type === 'folder' ? (
                <>
                  <span className="text-gray-500">📁</span>
                  <span className="font-medium truncate">{item.name}</span>
                  <span className="text-gray-600 ml-auto">→</span>
                </>
              ) : (
                <>
                  <span className="text-gray-600">📄</span>
                  <span className="truncate flex-1">{item.name}</span>
                  {item.size_bytes && (
                    <span className="text-gray-600 whitespace-nowrap">
                      {(item.size_bytes / 1024).toFixed(1)}KB
                    </span>
                  )}
                  {loadingFile === item.path && (
                    <span className="text-blue-400 animate-pulse">⏳</span>
                  )}
                </>
              )}
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-gray-700 p-2 text-xs text-gray-500 bg-gray-900">
        <div>Root: ~/dev_flow</div>
        {currentPath && <div className="truncate">{currentPath}</div>}
      </div>
    </div>
  )
}

export default FileBrowser
