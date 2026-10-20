import React from 'react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

interface ChatHistoryProps {
  messages: Message[]
  loading: boolean
}

const ChatHistory: React.FC<ChatHistoryProps> = ({ messages, loading }) => {
  const endRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="flex-1 overflow-auto bg-gray-900 p-4 space-y-4">
      {messages.length === 0 && !loading && (
        <div className="flex items-center justify-center h-full text-gray-500 text-center">
          <div>
            <p className="text-lg mb-2">No messages yet</p>
            <p className="text-sm">Start by typing a message or loading a file</p>
          </div>
        </div>
      )}
      
      {messages.map((msg) => (
        <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
          <div
            className={`max-w-2xl p-3 rounded ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-100 border border-gray-700'
            }`}
          >
            <div className="text-xs mb-1 opacity-70">
              {msg.role === 'user' ? 'You' : 'Assistant'} •{' '}
              {new Date(msg.timestamp).toLocaleTimeString()}
            </div>
            <div className="text-sm whitespace-pre-wrap break-words">{msg.content}</div>
          </div>
        </div>
      ))}

      {loading && (
        <div className="flex justify-start">
          <div className="bg-gray-800 text-gray-100 border border-gray-700 p-3 rounded">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
          </div>
        </div>
      )}

      <div ref={endRef} />
    </div>
  )
}

export default ChatHistory
