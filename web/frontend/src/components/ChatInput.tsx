import React from 'react'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
}

const ChatInput: React.FC<ChatInputProps> = ({ onSend, disabled = false }) => {
  const [text, setText] = React.useState('')

  const handleSubmit = () => {
    if (text.trim()) {
      onSend(text)
      setText('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.ctrlKey && e.key === 'Enter') {
      handleSubmit()
    }
  }

  return (
    <div className="border-t border-gray-700 bg-gray-800 p-4">
      <div className="flex gap-2">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type message... (Ctrl+Enter to send)"
          disabled={disabled}
          className="flex-1 bg-gray-900 border border-gray-600 rounded p-2 text-gray-100 text-sm focus:outline-none focus:border-blue-500 disabled:opacity-50"
          rows={3}
        />
        <button
          onClick={handleSubmit}
          disabled={disabled || !text.trim()}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-medium px-4 py-2 rounded h-fit"
        >
          Send
        </button>
      </div>
      <p className="text-xs text-gray-500 mt-2">
        Press <kbd className="bg-gray-700 px-1 rounded">Ctrl+Enter</kbd> or click Send
      </p>
    </div>
  )
}

export default ChatInput
