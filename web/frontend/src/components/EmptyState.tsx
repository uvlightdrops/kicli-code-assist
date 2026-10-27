/**
 * Empty State Component - shown when no project is open
 */

import React, { useState } from 'react'
import { useProject } from '../hooks/useProject'

interface EmptyStateProps {
  onOpenProjectModal: () => void
  onCreateProjectModal: () => void
}

const EmptyState: React.FC<EmptyStateProps> = ({ onOpenProjectModal, onCreateProjectModal }) => {
  const { error } = useProject()

  return (
    <div className="flex flex-col items-center justify-center h-full w-full bg-gray-900">
      {/* Main Content */}
      <div className="max-w-md text-center">
        <div className="mb-8">
          <div className="text-6xl mb-4">📁</div>
          <h1 className="text-2xl font-bold text-gray-100 mb-2">No Project Open</h1>
          <p className="text-gray-400 text-sm">
            Start by creating a new project or opening an existing one
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col gap-3 mb-8">
          <button
            onClick={onCreateProjectModal}
            className="flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition"
          >
            <span>+</span>
            <span>New Project</span>
          </button>
          <button
            onClick={onOpenProjectModal}
            className="flex items-center justify-center gap-2 px-6 py-3 bg-gray-700 hover:bg-gray-600 text-gray-100 rounded font-medium transition"
          >
            <span>📂</span>
            <span>Open Project</span>
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-2 rounded text-sm">
            {error}
          </div>
        )}
      </div>
    </div>
  )
}

export default EmptyState
