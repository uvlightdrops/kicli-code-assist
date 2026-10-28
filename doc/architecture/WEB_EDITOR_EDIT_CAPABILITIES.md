# Web IDE Editor - Current Status

## ❌ EDIT CAPABILITIES: NOT IMPLEMENTED

### Current State (Session 029)
```
✅ View/Preview Mode (Read-Only)
  - Prism.js syntax highlighting
  - File selection + tabs
  - Line numbers
  
❌ Edit Mode (NOT YET)
  - No textarea/contenteditable
  - No keyboard shortcuts
  - No save functionality
  - No backend persistence
  - No diff/changes tracking
```

---

## What Would Be Needed

### 1. Frontend (React Components)

**CodePreview.tsx Changes**
```typescript
// Current: Read-only <pre> with Prism highlighting
// Needed: 
// - Switch between View/Edit mode
// - Monaco Editor OR contenteditable textarea
// - Keyboard shortcuts: Ctrl+S, Ctrl+Z, Ctrl+/, Ctrl+F, etc.
// - Unsaved changes indicator (dot on tab)
```

**Example Edit Mode Toggle:**
```tsx
const [isEditMode, setIsEditMode] = useState(false)
const [isDirty, setIsDirty] = useState(false)

// Toolbar button: "Edit" / "Done"
// Save button: Ctrl+S
// Diff indicator: ● if isDirty
```

---

### 2. Backend (Flask Server)

**Current Endpoints:**
```
GET  /api/health           ✅
GET  /api/config           ✅
GET  /api/logs             ✅
POST /api/chat             ✅
POST /api/files/upload     ✅
GET  /api/files/{id}       ✅
```

**Missing Endpoints:**
```
PUT  /api/files/{id}       ❌ NEEDED - Save file content
GET  /api/project/files    ❌ NEEDED - Real file tree (not mock)
POST /api/files/new        ❌ NEEDED - Create new file
DELETE /api/files/{id}     ❌ NEEDED - Delete file
```

**Example PUT endpoint needed:**
```python
@app.route('/api/files/<file_id>', methods=['PUT'])
def update_file(file_id):
    data = request.json
    content = data.get('content', '')
    # Write to filesystem
    # Return: { success: true, message: "Saved" }
```

---

### 3. Implementation Checklist

**Tier 1 (MVP - Essential for Editing)**
- [ ] Edit mode toggle (Edit/Done button)
- [ ] Textarea or contenteditable for code input
- [ ] Unsaved changes indicator (● on tab)
- [ ] Ctrl+S → Save to backend
- [ ] Backend: PUT /api/files/{id} endpoint
- [ ] Show "Saved" / "Error" message
- [ ] Undo/Redo in editor

**Tier 2 (Phase 2)**
- [ ] Ctrl+Z/Ctrl+Y undo/redo
- [ ] Ctrl+/ line comment
- [ ] Ctrl+F find in file
- [ ] Ctrl+H find & replace
- [ ] Syntax highlighting while editing (auto-update)

**Tier 3 (Phase 3 - Professional)**
- [ ] Monaco Editor integration (replaces Prism + textarea)
- [ ] Auto-save every 30s
- [ ] Diff viewer (original vs. current)
- [ ] File revert button
- [ ] Keyboard shortcuts guide

---

## Why It's Not Done

1. **Read-Only Made Sense First** 
   - File browser + preview were the MVP
   - Chat integration depends on viewing files
   
2. **Editing Adds Complexity**
   - Need backend file I/O
   - Need permission handling
   - Need persistence strategy
   - Need conflict handling (if multiple users?)

3. **Editor Choice Not Finalized**
   - **Option A:** Simple textarea + Prism
     - Pros: Lightweight, easy to implement
     - Cons: Poor UX, missing shortcuts
   
   - **Option B:** Monaco Editor
     - Pros: VSCode experience, all shortcuts, Intellisense
     - Cons: ~2MB bundle size, more setup
   
   - **Option C:** CodeMirror
     - Pros: Lightweight + powerful, lots of themes
     - Cons: Less VSCode-like

---

## Recommendation for Next Step

**If you want editing NOW:**

1. Start with **simple textarea** approach
   - Lowest friction
   - Get save workflow working
   - Can upgrade to Monaco later

2. Implementation order:
   ```
   Step 1: Add textarea to CodePreview.tsx (switchable view/edit)
   Step 2: Add PUT /api/files/{id} endpoint in Flask
   Step 3: Wire Ctrl+S to save
   Step 4: Add unsaved changes indicator
   Step 5: Add basic shortcuts (Ctrl+Z, Ctrl+/, Ctrl+F)
   ```

3. Timeline: ~2-3 hours for basic editing working

**If you want professional editing:**

1. Use **Monaco Editor** from the start
   - More work upfront (~4-5 hours)
   - But all features out-of-box
   - Better long-term

---

## Files Involved

### Frontend
- `web/frontend/src/components/CodePreview.tsx` (currently read-only)
- `web/frontend/src/App.tsx` (state management for isDirty, etc.)

### Backend
- `kicli_code_assist/web/server.py` (needs new PUT endpoint)

### Config
- `web/frontend/src/hooks/useKeyboardShortcuts.ts` (new - for shortcuts)
- `web/frontend/src/components/EditorToolbar.tsx` (new - for Edit/Save buttons)

---

## Questions to Answer

1. Should editing work on uploaded files, project files, or both?
2. Should we support creation of new files?
3. Should saves go to filesystem or only to session storage?
4. Do you want auto-save, or explicit save only?
5. Should we track file changes for LLM context (e.g., "you edited main.py")?

