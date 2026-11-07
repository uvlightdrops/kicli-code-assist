---
title: File Operations API
project: kicli-code-assist
scope: backend
purpose: REST API endpoints for file creation, reading, writing, and management
created: 2026-11-07 23
updated: 2026-11-07 23
update_reason: Initial documentation for file operations
status: active
relations:
  - target: README.md
    type: parent
---

# File Operations API [file-operations]

## Overview

File Operations API provides REST endpoints for TUI and Web UI to create, read, update, and manage files within a project workspace.

## Endpoints

### Read Operations

#### GET /api/project/files
List files in project directory

**Query Parameters:**
- `path` (string, optional): Subdirectory path relative to project root
- `project` (string): Project root path

**Response:**
```json
{
  "items": [
    {
      "name": "src",
      "type": "folder",
      "path": "src",
      "size_bytes": null
    },
    {
      "name": "main.py",
      "type": "file",
      "path": "main.py",
      "size_bytes": 1024
    }
  ]
}
```

---

#### GET /api/files/{file_path}
Read file content

**Headers:**
- `Range` (optional): Bytes range for large files (e.g., `bytes=0-1048576`)

**Query Parameters:**
- `project` (string): Project root path

**Response:**
```json
{
  "content": "...",
  "path": "main.py",
  "size_bytes": 1024
}
```

---

### Write Operations

#### POST /api/files
Create new file

**Request Body:**
```json
{
  "path": "src/new_module.py",
  "content": "# New module\nprint('hello')",
  "project": "/path/to/project"
}
```

**Response:**
```json
{
  "success": true,
  "path": "src/new_module.py",
  "message": "File created successfully"
}
```

**Status Codes:**
- `201 Created`: File created
- `400 Bad Request`: Invalid path or content
- `409 Conflict`: File already exists
- `500 Internal Server Error`: Write failed

---

#### PUT /api/files/{file_path}
Update existing file

**Request Body:**
```json
{
  "content": "# Updated content\nprint('updated')",
  "project": "/path/to/project"
}
```

**Response:**
```json
{
  "success": true,
  "path": "src/new_module.py",
  "message": "File updated successfully"
}
```

**Status Codes:**
- `200 OK`: File updated
- `400 Bad Request`: Invalid content
- `404 Not Found`: File not found
- `500 Internal Server Error`: Write failed

---

### Utility Operations

#### DELETE /api/files/{file_path}
Delete a file [TODO]

**Query Parameters:**
- `project` (string): Project root path

**Response:**
```json
{
  "success": true,
  "path": "src/new_module.py",
  "message": "File deleted successfully"
}
```

---

## Integration with TUI

### Workflow: Create New File

1. User presses "New File" in FileTree panel
2. TUI opens input dialog: "Enter filename"
3. User enters path (e.g., `src/utils.py`)
4. TUI calls:
   ```
   POST /api/files
   {
     "path": "src/utils.py",
     "content": "# New file\n",
     "project": "/current/project/root"
   }
   ```
5. On success (201):
   - Refresh FileTree
   - Open new file in EditorPanel
6. On conflict (409):
   - Show error: "File already exists"
7. On error (500):
   - Show error message

### Workflow: Save File

1. User presses Ctrl+S in EditorPanel
2. TUI gets current file path and content
3. TUI calls:
   ```
   PUT /api/files/src/utils.py
   {
     "content": "...",
     "project": "/current/project/root"
   }
   ```
4. On success (200):
   - Show status: "Saved"
   - Clear dirty flag
5. On error:
   - Show error message

---

## Implementation Status

| Endpoint | Status | Priority |
|----------|--------|----------|
| GET /api/project/files | ✅ Done | - |
| GET /api/files/{path} | ✅ Done | - |
| POST /api/files | 📋 TODO | P0 |
| PUT /api/files/{path} | 📋 TODO | P0 |
| DELETE /api/files/{path} | 📋 TODO | P1 |

---

## Design Decisions

1. **Path Format:** Relative paths within project (e.g., `src/main.py`) to prevent directory traversal attacks
2. **Project Parameter:** Always required in query/body to ensure operations scoped to current project
3. **No Directory Creation:** POST assumes directories exist; TUI/Web should pre-create via `mkdir` or separate endpoint
4. **No Concurrent Writes:** Each file treated independently; clients responsible for conflict resolution
5. **Large File Handling:** GET supports Range header for streaming; PUT assumes full content upload

---

## Error Handling

All endpoints return standard error responses:

```json
{
  "success": false,
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

Common error codes:
- `INVALID_PATH`: Path contains invalid characters or traversal attempt
- `FILE_NOT_FOUND`: File does not exist
- `FILE_EXISTS`: File already exists (POST only)
- `WRITE_FAILED`: Filesystem write error
- `PERMISSION_DENIED`: Insufficient permissions

---

## Security Considerations

1. **Path Validation:** All paths validated against project root; no absolute paths or `../` traversal allowed
2. **Encoding:** Paths URL-encoded; content sent as-is (no encoding assumptions)
3. **Project Scope:** All operations scoped to project root; cross-project access not supported
4. **No Execute:** Files created/updated as data only; no automatic execution

---

## Next Steps

- [ ] Implement POST /api/files
- [ ] Implement PUT /api/files/{path}
- [ ] Add error handling and validation
- [ ] Create TUI EditorPanel integration
- [ ] Add syntax validation (optional, per-language)
