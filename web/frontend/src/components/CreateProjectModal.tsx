/**
 * Create Project Modal
 */

import React, { useState } from 'react'
import { useProject } from '../hooks/useProject'

interface CreateProjectModalProps {
  isOpen: boolean
  onClose: () => void
}

const CreateProjectModal: React.FC<CreateProjectModalProps> = ({ isOpen, onClose }) => {
  const { createProject, loading } = useProject()
  const [formData, setFormData] = useState({
    name: '',
    parentPath: '/home/flow/dev_flow',
    template: 'empty',
  })
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!formData.name.trim()) {
      setError('Project name is required')
      return
    }

    try {
      await createProject(formData.name, formData.parentPath, formData.template)
      setFormData({ name: '', parentPath: '/home/flow/dev_flow', template: 'empty' })
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project')
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg shadow-lg max-w-md w-full mx-4">
        {/* Header */}
        <div className="border-b border-gray-700 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-100">Create New Project</h2>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Project Name */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Project Name
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={e => setFormData(d => ({ ...d, name: e.target.value }))}
              placeholder="e.g., my-project"
              className="w-full px-3 py-2 bg-gray-700 text-gray-100 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
              disabled={loading}
              autoFocus
            />
          </div>

          {/* Parent Path */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Location
            </label>
            <input
              type="text"
              value={formData.parentPath}
              onChange={e => setFormData(d => ({ ...d, parentPath: e.target.value }))}
              className="w-full px-3 py-2 bg-gray-700 text-gray-100 border border-gray-600 rounded focus:outline-none focus:border-blue-500 text-xs font-mono"
              disabled={loading}
            />
            <p className="text-xs text-gray-500 mt-1">Must be within /home/flow/dev_flow</p>
          </div>

          {/* Template */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Template
            </label>
            <select
              value={formData.template}
              onChange={e => setFormData(d => ({ ...d, template: e.target.value }))}
              className="w-full px-3 py-2 bg-gray-700 text-gray-100 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
              disabled={loading}
            >
              <option value="empty">Empty</option>
              <option value="node">Node.js</option>
              <option value="python">Python</option>
            </select>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-900 border border-red-700 text-red-200 px-3 py-2 rounded text-sm">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-100 rounded font-medium transition disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default CreateProjectModal
