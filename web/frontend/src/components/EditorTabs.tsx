import React from 'react'

interface TabFile {
  path: string
  content: string
  active: boolean
}

interface EditorTabsProps {
  tabs: TabFile[]
  onSelectTab: (path: string) => void
  onCloseTab: (path: string) => void
}

const EditorTabs: React.FC<EditorTabsProps> = ({ tabs, onSelectTab, onCloseTab }) => {
  if (tabs.length === 0) {
    return (
      <div className="border-b border-gray-700 bg-gray-800 p-2">
        <p className="text-xs text-gray-500 text-center">No files open</p>
      </div>
    )
  }

  return (
    <div className="flex gap-0 border-b border-gray-700 bg-gray-800 overflow-x-auto">
      {tabs.map((tab) => (
        <div
          key={tab.path}
          onClick={() => onSelectTab(tab.path)}
          className={`flex items-center gap-2 px-3 py-2 text-sm whitespace-nowrap cursor-pointer border-b-2 transition-colors ${
            tab.active
              ? 'border-blue-500 text-gray-100 bg-gray-750'
              : 'border-transparent text-gray-400 hover:text-gray-300'
          }`}
        >
          <span>📄</span>
          <span>{tab.path.split('/').pop()}</span>
          <button
            onClick={(e) => {
              e.stopPropagation()
              onCloseTab(tab.path)
            }}
            className="ml-1 text-gray-500 hover:text-red-400 font-bold"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  )
}

export default EditorTabs
