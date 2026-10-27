/**
 * Open Project Modal - Browse and select project folder
 */

import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useProject } from '../hooks/useProject'

interface FolderItem {
  name: string
  path: string
  isFolder: boolean
}

interface OpenProjectModalProps {
  isOpen: boolean
  onClose: () => void
}

const OpenProjectModal: React.FC<OpenProjectModalProps> = ({ isOpen, onClose }) => {
  const { openProject, loading } = useProject()
  const [currentPath, setCurrentPath] = useState('/home/flow/dev_flow')
  const [items, setItems] = useState<FolderItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loadingFolders, setLoadingFolders] = useState(false)
  const [recentProjects, setRecentProjects] = useState<FolderItem[]>([])

  useEffect(() => {
    if (isOpen) {
      loadFolders(currentPath)
      loadRecent()
    }
  }, [isOpen])

  const loadRecent = async () => {
    try {
      const res = await axios.get('/api/projects/recent')
      if (res.data.recent) {
        setRecentProjects(res.data.recent.map((p: any) => ({
          name: p.name,
          path: p.path,
          isFolder: true,
        })))
      }
    } catch (err) {
      // Silently fail on recent projects
    }
  }

  const loadFolders = async (path: string) => {
    setLoadingFolders(true)
    setError(null)
    try {
      const res = await axios.get('/api/projects/browse', {
        params: { path },
      })
      setItems(res.data.items || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load folders')
      setItems([])
    } finally {
      setLoadingFolders(false)
    }
  }

  const handleSelectFolder = (path: string) => {
    setCurrentPath(path)
    loadFolders(path)
  }

  const handleOpenProject = async () => {
    setError(null)
    try {
      await openProject(currentPath)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to open project')
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg shadow-lg max-w-2xl w-full mx-4 max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-700 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-100">Open Project</h2>
          <p className="text-xs text-gray-400 mt-1">{currentPath}</p>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {/* Recent Projects */}
          {recentProjects.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-gray-300 mb-2">Recent Projects</h3>
              <div className="space-y-1">
                {recentProjects.map(proj => (
                  <button
                    key={proj.path}
                    onClick={() => handleSelectFolder(proj.path)}
                    className={`w-full text-left px-3 py-2 rounded text-sm transition ${
                      currentPath === proj.path
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 text-gray-100 hover:bg-gray-600'
                    }`}
                  >
                    📁 {proj.name}
                  </button>
                ))}
              </div>
              <div className="border-t border-gray-700 my-4"></div>
            </div>
          )}

          {/* Folder Browser */}
          <h3 className="text-sm font-semibold text-gray-300 mb-2">Folders</h3>
          {loadingFolders ? (
            <div className="text-center py-8 text-gray-400">Loading...</div>
          ) : items.length > 0 ? (
            <div className="space-y-1">
              {items.map(item => (
                <button
                  key={item.path}
                  onClick={() => handleSelectFolder(item.path)}
                  className={`w-full text-left px-3 py-2 rounded text-sm transition font-mono text-xs ${
                    currentPath === item.path
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-100 hover:bg-gray-600'
                  }`}
                >
                  📁 {item.name}
                </button>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-400 text-sm">No folders found</div>
          )}

          {/* Error */}
          {error && (
            <div className="bg-red-900 border border-red-700 text-red-200 px-3 py-2 rounded text-sm mt-4">
              {error}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="border-t border-gray-700 px-6 py-4 flex gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-100 rounded font-medium transition disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleOpenProject}
            disabled={loading || !currentPath}
            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition disabled:opacity-50"
          >
            {loading ? 'Opening...' : 'Open'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default OpenProjectModal
