# Project Management System

Implementiert ein benutzerfreundliches Project Management System für die kicli-code-assist IDE.

## Features

### 1. **Empty State**
- Wenn keine Project aktiv ist, zeigt die IDE einen leeren Screen
- Call-to-Action Buttons für "New Project" und "Open Project"
- Responsive Design mit Icon + Text

### 2. **Create Project Modal**
- Projekt-Name eingeben
- Location (Parent Path) angeben (validiert gegen `/home/flow/dev_flow`)
- Template wählen (Empty, Node.js, Python)
- Automatische `.gitignore` und optionale Template-Dateien

### 3. **Open Project Modal**
- Browser für bestehende Ordner
- Recent Projects Liste (aus Cache)
- Folder Picker mit Breadcrumb Navigation
- Validierung der Path-Sicherheit

### 4. **Project State & Persistence**
- Aktuelles Project wird in App-State gespeichert
- Persistierung in localStorage (automatisches Laden beim Refresh)
- Header zeigt Project-Name mit Close-Button

### 5. **Breadcrumb Navigation**
- FileBrowser Breadcrumb aktualisiert automatisch
- Format: `PROJECT FILES → {ProjectName} → {folder1} → {folder2}`
- Consistent mit Project Root Sicherheitsgrenze

## API Endpoints

### `GET /api/projects/current`
Aktuelles offenes Project abrufen.

```json
{
  "success": true,
  "data": null
}
```

### `POST /api/projects/open`
Project öffnen (validiert Path).

```bash
curl -X POST http://localhost:8000/api/projects/open \
  -H "Content-Type: application/json" \
  -d '{"path":"/home/flow/dev_flow/kicli-code-assist"}'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "476909aa-0a5e-42bb-b9d7-c0ef4767595f",
    "name": "kicli-code-assist",
    "path": "/home/flow/dev_flow/kicli-code-assist",
    "rootPath": "/home/flow/dev_flow",
    "createdAt": "2026-10-27T10:29:54.699464",
    "lastOpened": "2026-10-27T10:29:54.699492",
    "type": "mixed",
    "isGitRepo": true
  }
}
```

### `POST /api/projects/create`
Neues Project erstellen.

```bash
curl -X POST http://localhost:8000/api/projects/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-project",
    "parentPath": "/home/flow/dev_flow",
    "template": "empty"
  }'
```

**Template Optionen:**
- `empty`: Minimal setup mit `.gitignore`
- `node`: Node.js Project mit `package.json`
- `python`: Python Project mit `requirements.txt`

### `GET /api/projects/browse`
Folder Browser für Project Selection.

```bash
curl 'http://localhost:8000/api/projects/browse?path=/home/flow/dev_flow'
```

**Response:**
```json
{
  "items": [
    {
      "name": "kicli-code-assist",
      "path": "/home/flow/dev_flow/kicli-code-assist",
      "isFolder": true
    }
  ]
}
```

### `GET /api/projects/recent`
Recent Projects aus Cache.

```bash
curl http://localhost:8000/api/projects/recent
```

## Frontend Components

### `EmptyState.tsx`
Leerer Zustand mit Aktionsbuttons.

```tsx
import EmptyState from './components/EmptyState'

<EmptyState 
  onOpenProjectModal={() => setShowOpenModal(true)}
  onCreateProjectModal={() => setShowCreateModal(true)}
/>
```

### `CreateProjectModal.tsx`
Modal zum Erstellen eines neuen Projects.

```tsx
<CreateProjectModal 
  isOpen={showCreateModal}
  onClose={() => setShowCreateModal(false)}
/>
```

### `OpenProjectModal.tsx`
Modal zum Öffnen eines bestehenden Projects.

```tsx
<OpenProjectModal 
  isOpen={showOpenModal}
  onClose={() => setShowOpenModal(false)}
/>
```

### `useProject Hook`
Context Hook für Project State Management.

```tsx
import { useProject } from './hooks/useProject'

const { current, isEmpty, openProject, createProject, closeProject } = useProject()
```

## Security

- **Path Validation**: Alle Paths sind auf `/home/flow/dev_flow` limitiert
- **Safe Navigation**: FileBrowser kann nicht über Project Root hinaus
- **Metadata Storage**: Projects speichern Metadata in `.kicli_project` JSON-Datei

## File Structure

```
/home/flow/dev_flow/
├── kicli-code-assist/
│   ├── .kicli_project          # Project metadata
│   ├── web/
│   │   ├── frontend/src/
│   │   │   ├── types/project.ts          # Project type definitions
│   │   │   ├── hooks/useProject.tsx      # Context & hooks
│   │   │   ├── components/
│   │   │   │   ├── EmptyState.tsx
│   │   │   │   ├── CreateProjectModal.tsx
│   │   │   │   ├── OpenProjectModal.tsx
│   │   │   │   └── FileBrowser.tsx       # Updated with project awareness
│   │   │   └── App.tsx                   # Updated with ProjectProvider
│   │   └── server.py                     # Backend APIs
│   └── ...
└── .kicli_recent_projects       # Cache für Recent Projects
```

## Development

### Run Frontend Dev Server
```bash
cd web/frontend
npm run dev
```

### Run Backend
```bash
cd /path/to/kicli-code-assist
python3 -m kicli_code_assist.web.server
```

### Test APIs
```bash
# Create project
curl -X POST http://localhost:8000/api/projects/create \
  -H "Content-Type: application/json" \
  -d '{"name":"test","parentPath":"/home/flow/dev_flow","template":"empty"}'

# Open project
curl -X POST http://localhost:8000/api/projects/open \
  -H "Content-Type: application/json" \
  -d '{"path":"/home/flow/dev_flow/kicli-code-assist"}'

# Browse folders
curl 'http://localhost:8000/api/projects/browse?path=/home/flow/dev_flow'
```

## Future Enhancements

- [ ] Recent projects history persistence (cache file)
- [ ] Project settings/metadata editor
- [ ] Project templates with scaffolding
- [ ] Git integration (detect repos)
- [ ] Workspace/multi-project support
- [ ] Project favorites/pinning
