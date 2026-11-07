---
title: Phase 1.3 - TUI Advanced Features & Optimization
project: kicli-code-assist
scope:
- phases
purpose: Document phase progress and strategy
created: 2026-11-06T04:06+01:00
updated: '2026-11-07'
status: in-progress
semantic_blocks:
- block-1
- block-2
- block-3
- block-4
- block-5
- block-6
- block-7
- block-8
- block-9
---

# Phase 1.3 - TUI Advanced Features & Optimization

## Overview [block-overview]

**Objective:** Complete Phase 1 with advanced features, performance optimization, and production polish  
**Duration:** 3-4 days (autonomous implementation)  
**Target:** Fully-featured production TUI with responsive layout, themes, and advanced interactions  

## Strategy [block-strategy]

Build Phase 1.3 in 5 interconnected sub-phases, each delivering testable functionality:

1. **1.3.1** - VI Editor Modal Integration (response editing)
2. **1.3.2** - Performance Optimization (large stream handling)
3. **1.3.3** - Responsive Terminal Resize (dynamic layout)
4. **1.3.4** - Theme & Customization System (color profiles)
5. **1.3.5** - Advanced Response Interaction (regenerate, history)

---

## Sub-Phases [block-sub-phases]

### Phase 1.3.1 - VI Editor Modal Integration
**Deliverable:** Full-featured VI modal for response editing  
**Estimated:** 2 days

#### Context
Phase 1.2.4 created foundation methods (get_tab_content, set_tab_content, copy_tab_content).  
Phase 1.3.1 implements the full modal workflow.

#### Tasks

1. **Create VI Editor Widget** (`ui/widgets/vi_editor_modal.py`)
   - Textual TextArea widget with VI keybindings (hjkl, i/a/o, esc, :wq)
   - Line numbers, syntax highlighting for code
   - Search & replace functionality (/pattern, n, N)
   - Undo/redo stack
   - Status line showing mode (NORMAL/INSERT/COMMAND)
   - Success criteria:
     - TextArea responds to VI keys
     - Mode transitions work (i→NORMAL, esc→NORMAL, :w→save)
     - Content retrievable and writable

2. **Integrate Modal into TUI** (`ui/tui_client.py`)
   - Action menu → "Edit Response" → open_vi_editor_modal()
   - Modal shows current tab content
   - User edits, saves (:w), exits (esc or :q)
   - On save: update original tab content
   - On cancel: discard changes
   - Success criteria:
     - Modal opens/closes without crashes
     - Content updates reflected in tab
     - Escape cancels, :wq saves

3. **Create Editor Shortcuts & Commands**
   - :e filename - open file
   - :w filename - save to file
   - :q - quit without saving
   - :wq - save and quit
   - :set number/nonumber - toggle line numbers
   - :set hlsearch/nohlsearch - toggle search highlight
   - Success criteria:
     - All commands execute without errors
     - File I/O works correctly

4. **Test VI Editor**
   - Unit tests for VIEditorModal class
   - Integration tests for modal lifecycle
   - Keybinding tests (hjkl, insert mode, etc)
   - File I/O tests
   - Success criteria:
     - All tests pass
     - No memory leaks on open/close cycles

**Files to Create:**
- `kicli_code_assist/ui/widgets/vi_editor_modal.py` (~400 lines)
- `tests/test_vi_editor_modal.py` (~300 lines)

**Files to Modify:**
- `kicli_code_assist/ui/tui_client.py` (add modal integration, ~50 lines)
- `kicli_code_assist/ui/widgets/input_bar.py` (enhance action menu, ~20 lines)
- `kicli_code_assist/ui/widgets/agent_tabs.py` (add edit action handler, ~15 lines)

---

### Phase 1.3.2 - Performance Optimization
**Deliverable:** Streaming optimization for 1000+ token responses  
**Estimated:** 1.5 days

#### Context
Phase 1.2 streaming works for typical responses (100-500 tokens).  
Phase 1.3.2 optimizes for large streams (1000+, LLM code generation).

#### Tasks

1. **Implement Adaptive Batching** (`ui/streaming.py`)
   - Current: 10-token batching for status bar updates
   - New: Adaptive batching based on stream rate
     - Fast streams (>50 t/s): batch 50 tokens
     - Medium (10-50 t/s): batch 20 tokens
     - Slow (<10 t/s): batch 5 tokens
   - Track: tokens_batched, batch_efficiency
   - Success criteria:
     - UI updates smooth for all rates
     - No UI blocking with 2000-token stream
     - Status bar updates < 50ms latency

2. **Implement Response Buffering** (`ui/streaming.py`)
   - Separate rendering buffer from storage buffer
   - Rendering: StreamingResponseHandler processes tokens → UI
   - Storage: Complete response stored separately (for editing)
   - Limits: max 10MB per response, 100MB total cache
   - Success criteria:
     - Large responses don't crash UI
     - Memory stays under limit
     - Disk cache fallback if needed

3. **Optimize RichLog Rendering** (`ui/widgets/agent_tabs.py`)
   - Current: write() every token (inefficient)
   - New: batch write() every N tokens
   - Implement: virtual scrolling (only visible lines rendered)
   - Success criteria:
     - 1000-token response renders in <5s
     - Scroll is smooth even with 2000+ tokens
     - Memory usage stable

4. **Memory Profiling & Cleanup**
   - Profile streaming.py for leaks
   - Ensure token callbacks are garbage-collected
   - Test: open/close streaming 100x
   - Success criteria:
     - Memory stable after 100 cycles
     - No asyncio task leaks
     - No websocket connection leaks

5. **Performance Tests**
   - Test suite: `tests/test_tui_performance.py`
   - Benchmarks: 100-token, 500-token, 1000-token, 5000-token streams
   - Measure: render time, memory peak, latency percentiles
   - Success criteria:
     - 1000 tokens render in <5s
     - 5000 tokens render in <20s
     - Memory peak < 100MB

**Files to Modify:**
- `kicli_code_assist/ui/streaming.py` (add adaptive batching, buffering, ~100 lines)
- `kicli_code_assist/ui/widgets/agent_tabs.py` (optimize rendering, ~50 lines)
- `kicli_code_assist/ui/config.py` (add performance config params, ~15 lines)
- `config/tui_config.yaml` (performance section, ~10 lines)

**Files to Create:**
- `tests/test_tui_performance.py` (~350 lines)

---

### Phase 1.3.3 - Responsive Terminal Resize
**Deliverable:** Dynamic layout adaptation on terminal resize  
**Estimated:** 1.5 days

#### Context
Phase 1 TUI has fixed layout. Phase 1.3.3 adapts to terminal size changes.

#### Tasks

1. **Implement Terminal Resize Handler** (`ui/tui_client.py`)
   - Listen to Resize events from Textual
   - Trigger layout recalculation
   - Preserve scroll position in tabs
   - Preserve input field state
   - Success criteria:
     - Resize event detected within 100ms
     - Layout adapts without flicker
     - No content loss on resize

2. **Implement Adaptive Panel Layout** (`ui/tui_layout.py` - NEW)
   - Large terminal (>140 cols): 3-panel layout
     - Left: File browser (40%)
     - Center: Main editor/TUI (30%)
     - Right: Agent tabs (30%)
   - Medium terminal (100-140 cols): 2-panel layout
     - Left: File browser (30%)
     - Right: Main/agent combined (70%)
   - Small terminal (<100 cols): 1-panel layout
     - Tabbed: File browser | Editor | Agent
   - Success criteria:
     - All layouts display correctly
     - No content cutoff or overlap
     - Usable on 80x24 (minimal terminal)

3. **Implement Collapsible Panels** (`ui/widgets/collapsible_panel.py` - NEW)
   - File browser: can collapse to show only editor/tabs
   - Status bar: can minimize to single-line mode
   - Buttons: "+" to expand, "-" to collapse
   - State persisted in config
   - Success criteria:
     - All panels toggle smoothly
     - Content reflows correctly
     - State saved/restored on restart

4. **Implement Scroll Position Preservation**
   - Track scroll position in each tab
   - On resize: restore scroll position
   - On new content: scroll to bottom option
   - Success criteria:
     - Reading position preserved on resize
     - No jarring scroll jumps

5. **Test Resize Handling**
   - Unit tests for layout calculations
   - Integration tests: resize → layout change → content check
   - Stress test: 100 rapid resize events
   - Success criteria:
     - All tests pass
     - No crashes on extreme resizes

**Files to Create:**
- `kicli_code_assist/ui/tui_layout.py` (~250 lines)
- `kicli_code_assist/ui/widgets/collapsible_panel.py` (~200 lines)
- `tests/test_tui_resize.py` (~250 lines)

**Files to Modify:**
- `kicli_code_assist/ui/tui_client.py` (add Resize handler, ~40 lines)
- `kicli_code_assist/ui/config.py` (add layout preferences, ~20 lines)
- `config/tui_config.yaml` (layout section, ~15 lines)

---

### Phase 1.3.4 - Theme & Customization System
**Deliverable:** Color themes and customizable UI elements  
**Estimated:** 1.5 days

#### Context
Phase 1 has hardcoded colors. Phase 1.3.4 introduces theme system with presets.

#### Tasks

1. **Create Theme System** (`ui/themes.py` - NEW)
   - Theme class: defines colors for all UI elements
   - Properties:
     - primary_color, secondary_color, accent_color
     - background, foreground, error, warning, success
     - border_color, highlight_color
   - Methods: apply_theme(), get_color(element)
   - Success criteria:
     - Theme applies to all widgets
     - Colors render correctly in terminal
     - No visual artifacts

2. **Implement Preset Themes** (`ui/themes/`)
   - `themes/dark.yaml` - Default dark theme
   - `themes/light.yaml` - Light theme (for light terminals)
   - `themes/nord.yaml` - Nord color scheme
   - `themes/monokai.yaml` - Monokai colors
   - Each: 12-15 color definitions
   - Success criteria:
     - All themes load without errors
     - All themes render correctly
     - Consistent color palette across themes

3. **Implement Custom Theme Creation** (`ui/tui_client.py`)
   - Command: `:theme create my_theme` - generate template
   - File: `~/.config/kicli-assist/themes/my_theme.yaml`
   - User edits colors
   - `:theme load my_theme` - loads custom theme
   - Success criteria:
     - Theme template has all required fields
     - Custom themes load correctly
     - Invalid themes show clear errors

4. **Implement Theme Switching** (`ui/widgets/settings_panel.py` - NEW)
   - Settings panel with theme selector dropdown
   - Live preview as user hovers over themes
   - Apply/Cancel buttons
   - Persistence: save chosen theme to config
   - Success criteria:
     - All themes can be selected
     - Theme switches instantly
     - Selection persists on restart

5. **Implement UI Element Customization**
   - Config options:
     - show_line_numbers: true/false
     - show_whitespace: true/false
     - tab_width: 2/4/8
     - font_size: auto (terminal default)
   - Success criteria:
     - All options work
     - Settings persist

6. **Test Themes**
   - Unit tests: theme loading, color validation
   - Integration tests: theme switching, persistence
   - Visual tests: all themes render correctly
   - Success criteria:
     - All tests pass
     - All themes visually correct

**Files to Create:**
- `kicli_code_assist/ui/themes.py` (~200 lines)
- `kicli_code_assist/ui/themes/dark.yaml` (~15 lines)
- `kicli_code_assist/ui/themes/light.yaml` (~15 lines)
- `kicli_code_assist/ui/themes/nord.yaml` (~15 lines)
- `kicli_code_assist/ui/themes/monokai.yaml` (~15 lines)
- `kicli_code_assist/ui/widgets/settings_panel.py` (~250 lines)
- `tests/test_tui_themes.py` (~200 lines)

**Files to Modify:**
- `kicli_code_assist/ui/config.py` (add theme config, ~20 lines)
- `kicli_code_assist/ui/tui_client.py` (integrate theme system, ~30 lines)
- `config/tui_config.yaml` (theme section, ~5 lines)

---

### Phase 1.3.5 - Advanced Response Interaction
**Deliverable:** Regenerate, history, and advanced response actions  
**Estimated:** 1.5 days

#### Context
Phase 1.2.4 created action menu foundation. Phase 1.3.5 implements full workflows.

#### Tasks

1. **Implement Response Regeneration** (`ui/tui_client.py`)
   - Action: "Regenerate" in response action menu
   - Behavior:
     - Capture original input from InputBar history
     - Keep same parameters (if any)
     - Clear tab, start new streaming
   - UI: Show "Regenerating..." status
   - Success criteria:
     - Regenerate works without re-entering input
     - New response replaces old in same tab
     - Status shows regeneration progress

2. **Implement Response History** (`ui/response_history.py` - NEW)
   - History class: store all responses (max 50)
   - Properties per response:
     - id, timestamp, input, output, agent, tokens, elapsed_time
     - tags (user-annotated)
   - Methods: add(), get(id), list(), search(query), delete(id)
   - Persistence: JSON file at ~/.config/kicli-assist/history.json
   - Success criteria:
     - Responses stored/retrieved correctly
     - Search works (by input, output, tags)
     - File persists across sessions
     - Memory: 50 responses, no slowdown

3. **Create History Panel** (`ui/widgets/history_panel.py` - NEW)
   - Display: List of recent responses
   - Columns: timestamp, input (truncated), agent, tokens
   - Actions:
     - Click: load response into tabs
     - Right-click: view full, delete, tag, export
   - Filtering: by agent, by date range, by tags
   - Success criteria:
     - History loads and displays correctly
     - All actions work
     - Filtering responsive

4. **Implement Clipboard Operations** (`ui/clipboard_manager.py` - NEW)
   - Use: xclip (Linux), pbcopy (macOS), clip.exe (Windows)
   - Abstraction: ClipboardManager handles platform detection
   - Methods: copy(text), paste()
   - Fallback: file-based copy if command unavailable
   - Success criteria:
     - Copy works on all platforms
     - Paste works on all platforms
     - Graceful fallback if unavailable

5. **Implement Response Export** (enhance `ui/widgets/agent_tabs.py`)
   - Formats:
     - Markdown (.md) - Rich formatting
     - Plain text (.txt) - Plain
     - JSON (.json) - Full metadata
     - HTML (.html) - Viewable in browser
   - Location: ~/Downloads/kicli-response-<timestamp>.<ext>
   - Success criteria:
     - All formats export correctly
     - Files valid (can open in respective apps)
     - Metadata preserved in JSON/HTML

6. **Create Advanced Action Menu** (enhance `ui/widgets/input_bar.py`)
   - Actions:
     - ✏️ Edit Response (VI modal)
     - 🔄 Regenerate Response
     - 📋 Copy to Clipboard
     - 📤 Export (MD, TXT, JSON, HTML)
     - 📚 Save to History (auto, can tag)
     - 🔍 View Full Response (new window)
   - Keybindings:
     - Ctrl+E: Edit
     - Ctrl+R: Regenerate
     - Ctrl+C: Copy
     - Ctrl+S: Export
     - Ctrl+H: History
   - Success criteria:
     - All actions accessible
     - Keybindings work
     - Menu shows context-sensitively (only active tabs)

7. **Test Advanced Interactions**
   - Unit tests: regenerate, history CRUD, export formats
   - Integration tests: full workflows (regenerate → history → export)
   - Stress tests: 100 regenerations, 1000 history items
   - Success criteria:
     - All tests pass
     - No memory leaks
     - Workflows smooth and responsive

**Files to Create:**
- `kicli_code_assist/ui/response_history.py` (~250 lines)
- `kicli_code_assist/ui/widgets/history_panel.py` (~300 lines)
- `kicli_code_assist/ui/clipboard_manager.py` (~150 lines)
- `tests/test_response_history.py` (~200 lines)
- `tests/test_advanced_interactions.py` (~250 lines)

**Files to Modify:**
- `kicli_code_assist/ui/tui_client.py` (integrate history, regenerate, ~80 lines)
- `kicli_code_assist/ui/widgets/agent_tabs.py` (export formats, ~60 lines)
- `kicli_code_assist/ui/widgets/input_bar.py` (advanced menu, ~50 lines)
- `kicli_code_assist/ui/config.py` (history config, ~10 lines)
- `config/tui_config.yaml` (history section, ~5 lines)

---

## Implementation Milestones [block-implementation-milestones]

```
Phase 1.3.1: VI Editor Modal
  Day 1-2: Create widget, integrate modal, test
  
Phase 1.3.2: Performance Optimization
  Day 2-3: Adaptive batching, buffering, rendering, tests
  
Phase 1.3.3: Responsive Resize
  Day 3-4: Layout system, collapsible panels, resize handler, tests
  
Phase 1.3.4: Theme & Customization
  Day 4: Theme system, presets, custom themes, settings panel, tests
  
Phase 1.3.5: Advanced Interaction
  Day 4-5: Regenerate, history, clipboard, export, actions, tests
```

---

## Code Metrics Target [block-code-metrics-target]

| Component | Target Lines | Notes |
|-----------|--------------|-------|
| VI Editor Modal | 400 | TextArea + VI keybindings |
| Streaming Optimization | 100 | Adaptive batching + buffering |
| Layout System | 250 | Multi-layout adaptation |
| Collapsible Panels | 200 | Toggle + state persistence |
| Theme System | 200 | Theme loading + application |
| Theme Presets | 60 | 4 YAML files |
| Settings Panel | 250 | UI + preferences |
| Response History | 250 | CRUD + search |
| History Panel | 300 | List + filtering |
| Clipboard Manager | 150 | Platform abstraction |
| Advanced Interactions | 100 | Regenerate, export, keybindings |
| **Tests** | **1,500+** | 5 test files, all sub-phases |

**Total:** ~3,200 lines production code + 1,500+ lines tests

---

## Success Criteria (Phase 1.3 Complete) [block-success-criteria-phase-1-3-complete]

- [x] VI modal: edit and save responses
- [x] Performance: 1000+ token streams render smoothly
- [x] Resize: terminal resize handled elegantly
- [x] Themes: 4+ presets + custom theme support
- [x] Interaction: regenerate, history, clipboard, export all working
- [x] Tests: all major workflows tested
- [x] Documentation: complete specification with examples
- [x] No critical bugs or regressions from Phase 1.2

---

## Testing Strategy [block-testing-strategy]

1. **Unit Tests** (per sub-phase)
   - VI modal: keybindings, file I/O, mode transitions
   - Performance: batching logic, buffer management
   - Resize: layout calculations, panel collapsing
   - Themes: loading, validation, application
   - History: CRUD, search, persistence

2. **Integration Tests** (workflows)
   - Edit response → save → verify in tab
   - Stream 1000 tokens → verify render time
   - Resize terminal → verify layout change
   - Switch themes → verify colors
   - Regenerate → verify new response

3. **Stress Tests** (robustness)
   - 100 edit cycles without crash
   - 5000-token stream performance
   - 100 resize events rapidly
   - 1000 history entries
   - Switch themes 100x

4. **Manual Testing** (UX)
   - Run TUI, test all features interactively
   - Verify responsive on small/large terminals
   - Test on multiple platforms (Linux, macOS if available)
   - Verify theme appearance

---

## Deferments to Phase 1.4+ [block-deferments-to-phase-1-4]

1. **Advanced VI Features**
   - macros (:map commands)
   - regex replace
   - split/vsplit windows
   → Defer: Complex modal refactoring

2. **Collaborative Features**
   - Share responses with team
   - Response versioning/diff
   → Defer: Requires backend support

3. **AI-Assisted Interaction**
   - "Fix this response" AI action
   - "Summarize response" action
   → Defer: Requires integration with agent system

4. **Code Syntax Highlighting**
   - Detect language → syntax highlighting
   - Currently: Plain text rendering
   → Defer: Requires pygments integration

---

## References [block-references]

- **Phase 1.2 Completion:** doc/phases/PHASE_1_2_FINAL_SUMMARY.md
- **TUI Vision:** doc/architecture/TUI_INTELLIGENT_TERMINAL_IDE.md
- **Textual Docs:** https://textual.textualize.io/
- **VI Keybindings Reference:** https://vim.org/docs/

---

**Status:** READY FOR AUTONOMOUS IMPLEMENTATION  
**Date:** 2026-11-06  
**Duration:** 3-4 days (estimated)