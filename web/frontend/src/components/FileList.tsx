import React from 'react'

interface UploadedFile {
  id: string
  path: string
  size: number
}

interface FileListProps {
  files: UploadedFile[]
  onDeleteFile: (fileId: string) => void
  onUploadFile: (file: File) => void
}

const FileList: React.FC<FileListProps> = ({ files, onDeleteFile, onUploadFile }) => {
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      onUploadFile(file)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-gray-700 p-3 bg-gray-800">
        <h3 className="text-sm font-semibold text-gray-300 mb-2">Context Files</h3>
        <button
          onClick={() => fileInputRef.current?.click()}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium py-1 px-2 rounded"
        >
          Load File (L)
        </button>
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      <div className="flex-1 overflow-auto">
        {files.length === 0 ? (
          <div className="p-3 text-xs text-gray-500 text-center">No files loaded</div>
        ) : (
          <div className="divide-y divide-gray-700">
            {files.map((file) => (
              <div key={file.id} className="p-2 bg-gray-800 hover:bg-gray-750 text-xs">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex-1 truncate">
                    <p className="truncate text-gray-300 font-mono">{file.path}</p>
                    <p className="text-gray-500 text-xs">{(file.size / 1024).toFixed(1)} KB</p>
                  </div>
                  <button
                    onClick={() => onDeleteFile(file.id)}
                    className="text-red-400 hover:text-red-300 font-bold p-1"
                    title="Remove file"
                  >
                    ×
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default FileList
