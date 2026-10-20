import React, { useState, useEffect } from 'react'
import axios from 'axios'

interface FileItem {
  path: string
  type: 'file' | 'directory'
  children?: FileItem[]
  expanded?: boolean
  size?: number
}

interface FileBrowserProps {
  onSelectFile: (path: string, content: string) => void
}

const FileBrowser: React.FC<FileBrowserProps> = ({ onSelectFile }) => {
  const [files, setFiles] = useState<FileItem[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set())

  // Simulate file tree (in real app, fetch from backend)
  useEffect(() => {
    const mockFiles: FileItem[] = [
      {
        path: 'src',
        type: 'directory',
        children: [
          { path: 'src/App.tsx', type: 'file', size: 6563 },
          { path: 'src/main.tsx', type: 'file', size: 236 },
          { path: 'src/index.css', type: 'file', size: 291 },
          {
            path: 'src/components',
            type: 'directory',
            children: [
              { path: 'src/components/ChatInput.tsx', type: 'file', size: 1470 },
              { path: 'src/components/ChatHistory.tsx', type: 'file', size: 2220 },
              { path: 'src/components/FileList.tsx', type: 'file', size: 2314 },
            ],
          },
        ],
      },
      {
        path: 'public',
        type: 'directory',
        children: [{ path: 'public/index.html', type: 'file', size: 368 }],
      },
      { path: 'package.json', type: 'file', size: 641 },
      { path: 'vite.config.ts', type: 'file', size: 462 },
      { path: 'tailwind.config.js', type: 'file', size: 227 },
    ]
    setFiles(mockFiles)
    setLoading(false)
  }, [])

  const toggleDir = (path: string) => {
    const newExpanded = new Set(expandedDirs)
    if (newExpanded.has(path)) {
      newExpanded.delete(path)
    } else {
      newExpanded.add(path)
    }
    setExpandedDirs(newExpanded)
  }

  const handleFileClick = async (path: string) => {
    try {
      // In real app: fetch file content from backend
      const mockContent = `// File: ${path}\n// Mock content for demo\n\nexport default function ${path.split('/').pop()?.replace(/\\.tsx?/, '')} {}`
      onSelectFile(path, mockContent)
    } catch (err) {
      console.error('Failed to load file:', err)
    }
  }

  const renderTree = (items: FileItem[], level = 0) => {
    return items.map((item, idx) => (
      <div key={`${item.path}-${idx}`} style={{ marginLeft: `${level * 16}px` }}>
        <div className="flex items-center gap-2 p-1 hover:bg-gray-700 rounded cursor-pointer text-sm">
          {item.type === 'directory' ? (
            <>
              <span
                onClick={() => toggleDir(item.path)}
                className={`w-4 h-4 flex items-center justify-center text-gray-400 ${
                  expandedDirs.has(item.path) ? 'text-gray-300' : ''
                }`}
              >
                {expandedDirs.has(item.path) ? '▼' : '▶'}
              </span>
              <span className="font-medium text-gray-300">📁 {item.path.split('/').pop()}</span>
            </>
          ) : (
            <>
              <span className="w-4 text-center text-gray-500">📄</span>
              <span
                onClick={() => handleFileClick(item.path)}
                className="text-gray-400 hover:text-blue-400 truncate"
              >
                {item.path.split('/').pop()}
              </span>
              <span className="text-xs text-gray-600 ml-auto">
                {item.size ? `${(item.size / 1024).toFixed(1)}KB` : ''}
              </span>
            </>
          )}
        </div>
        {item.type === 'directory' && expandedDirs.has(item.path) && item.children && (
          <div>{renderTree(item.children, level + 1)}</div>
        )}
      </div>
    ))
  }

  return (
    <div className="flex flex-col h-full bg-gray-800">
      <div className="border-b border-gray-700 p-2 bg-gray-800">
        <h3 className="text-xs font-semibold text-gray-400 uppercase">Files</h3>
      </div>
      <div className="flex-1 overflow-auto p-1 font-mono text-xs">
        {loading ? (
          <div className="text-gray-500 p-2">Loading...</div>
        ) : (
          renderTree(files)
        )}
      </div>
    </div>
  )
}

export default FileBrowser
