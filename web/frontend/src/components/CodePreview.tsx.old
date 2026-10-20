import React, { useEffect } from 'react'
import Prism from 'prismjs'
import 'prismjs/themes/prism-tomorrow.css'
import 'prismjs/components/prism-typescript'
import 'prismjs/components/prism-jsx'
import 'prismjs/components/prism-python'
import 'prismjs/components/prism-bash'
import 'prismjs/components/prism-json'
import 'prismjs/components/prism-yaml'

interface CodePreviewProps {
  filePath: string
  content: string
}

const getLanguage = (filePath: string): string => {
  const ext = filePath.split('.').pop()?.toLowerCase()
  const langMap: Record<string, string> = {
    tsx: 'typescript',
    ts: 'typescript',
    jsx: 'jsx',
    js: 'javascript',
    py: 'python',
    sh: 'bash',
    bash: 'bash',
    json: 'json',
    yaml: 'yaml',
    yml: 'yaml',
    css: 'css',
    html: 'html',
    md: 'markdown',
  }
  return langMap[ext || ''] || 'text'
}

const CodePreview: React.FC<CodePreviewProps> = ({ filePath, content }) => {
  const language = getLanguage(filePath)

  useEffect(() => {
    Prism.highlightAll()
  }, [content])

  return (
    <div className="flex flex-col h-full bg-gray-900 font-mono text-sm">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-700 bg-gray-800 px-3 py-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-gray-500">📄</span>
          <span className="text-gray-300 font-medium truncate">{filePath}</span>
        </div>
        <span className="text-xs text-gray-500 whitespace-nowrap ml-2">
          {language.toUpperCase()}
        </span>
      </div>

      {/* Code */}
      <div className="flex-1 overflow-auto p-3">
        <pre className="m-0 text-xs leading-relaxed">
          <code className={`language-${language}`}>{content}</code>
        </pre>
      </div>

      {/* Stats */}
      <div className="border-t border-gray-700 bg-gray-800 px-3 py-1 text-xs text-gray-500">
        {content.split('\n').length} lines • {content.length} chars
      </div>
    </div>
  )
}

export default CodePreview
