---
name: pro-diagram
description: "Generate professional flowcharts, sequence diagrams, and visual diagrams for client presentations, internal docs, or Obsidian notes. Use when the user asks for a diagram, flowchart, process map, sequence diagram, ERPNext workflow visualization, or any Mermaid-renderable diagram. Triggers: 'วาด diagram', 'flowchart', 'draw a workflow', 'process map', 'ER diagram', 'sequence diagram', 'visualize this process'."
user-invocable: true
---

# Pro-Diagram

Generate CTO-grade visual diagrams using Mermaid.js with professional styling, multiple themes, and easy export.

## Supported Diagram Types

| Type | Mermaid Syntax | Best For |
|---|---|---|
| Flowchart | `flowchart TD/LR` | Processes, approval workflows, decision trees |
| Sequence | `sequenceDiagram` | API flows, user interactions, system calls |
| Gantt | `gantt` | Timelines, project phases |
| ER Diagram | `erDiagram` | Database models, doctype relationships |
| State | `stateDiagram-v2` | Document states, lifecycle |
| Class | `classDiagram` | System architecture, object models |
| Pie | `pie` | Distribution, breakdown |
| Mindmap | `mindmap` | Brainstorming, feature mapping |

## Layout Modes

| Mode | Use case | `{{BACKGROUND}}` | `{{CARD_STYLES}}` | `{{BODY_PADDING}}` |
|---|---|---|---|---|
| **clean** (default) | Export, embed in slides/docs/Obsidian | `transparent` | `padding: 20px;` | `20px` |
| **card** | Standalone screenshot, social share | Theme bg color | `background: #fff; border: 1px solid #e2e8f0; border-radius: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.03); padding: 40px;` | `48px 40px` |

- **Default is always `clean`** — no card, no border, transparent bg
- Use `card` only when the user explicitly wants a framed/standalone look
- For `clean` mode: `{{EDGE_LABEL_BG}}` = `transparent`; for `card` mode: `#ffffff`
- For `clean` mode: `{{HEADER_COLOR}}` = `#0f172a`, `{{SUBTITLE_COLOR}}` = `#64748b`, `{{FOOTER_COLOR}}` = `#94a3b8`

## Color Themes

Use these preset palettes. Default is `slate-indigo` if the user doesn't specify.

### slate-indigo (default — professional/corporate)
- Background: `#f8fafc`
- Primary: `#eef2ff` / text `#312e81` / border `#a5b4fc`
- Secondary: `#e0e7ff` / text `#3730a3` / border `#818cf8`
- Tertiary: `#f1f5f9`

### emerald-teal (positive/growth)
- Background: `#f0fdf4`
- Primary: `#d1fae5` / text `#064e3b` / border `#6ee7b7`
- Secondary: `#ccfbf1` / text `#134e4a` / border `#5eead4`
- Tertiary: `#f0fdfa`

### amber-warm (attention/urgency)
- Background: `#fffbeb`
- Primary: `#fef3c7` / text `#78350f` / border `#fbbf24`
- Secondary: `#ffedd5` / text `#7c2d12` / border `#fb923c`
- Tertiary: `#fefce8`

### rose-critical (risk/blockers)
- Background: `#fff1f2`
- Primary: `#ffe4e6` / text `#881337` / border `#fda4af`
- Secondary: `#fce7f3` / text `#831843` / border `#f9a8d4`
- Tertiary: `#fdf2f8`

### neutral-clean (minimal/white)
- Background: `#ffffff`
- Primary: `#f9fafb` / text `#111827` / border `#d1d5db`
- Secondary: `#f3f4f6` / text `#1f2937` / border `#9ca3af`
- Tertiary: `#f9fafb`

### dark-pro (dark mode presentation)
- Background: `#0f172a`
- Primary: `#1e293b` / text `#e2e8f0` / border `#475569`
- Secondary: `#334155` / text `#f1f5f9` / border `#64748b`
- Tertiary: `#1e293b`
- Card bg override: `#1e293b`, card border: `#334155`
- Header h1 color: `#f1f5f9`, header p color: `#94a3b8`
- Footer color: `#475569`

## Workflow

### 1. Understand the request
- What type of diagram? (flowchart, sequence, etc.)
- What theme? (default: slate-indigo)
- Title and subtitle? (optional — adds header)
- Direction? (TD = top-down default, LR = left-right for wide flows)

### 2. Draft Mermaid code
Write clean Mermaid.js syntax. Rules:
- **Node IDs**: use short meaningful IDs (`start`, `approve`, `reject`)
- **Labels**: human-readable, concise (max ~25 chars per label)
- **Styling**: use `classDef` + `class` for color-coded node groups (e.g., success nodes green, error nodes red)
- **Subgraphs**: group related steps logically
- **Thai labels**: fully supported — wrap in quotes if needed

### 3. Build HTML from template
Read `assets/template.html` and replace these placeholders:

| Placeholder | Value |
|---|---|
| `{{MERMAID_CODE}}` | The Mermaid diagram code |
| `{{BACKGROUND}}` | Background color from theme |
| `{{PRIMARY_COLOR}}` | Primary node fill |
| `{{PRIMARY_TEXT}}` | Primary node text color |
| `{{PRIMARY_BORDER}}` | Primary node border |
| `{{SECONDARY_COLOR}}` | Secondary node fill |
| `{{SECONDARY_TEXT}}` | Secondary node text color |
| `{{SECONDARY_BORDER}}` | Secondary node border |
| `{{TERTIARY_COLOR}}` | Tertiary fill |
| `{{HEADER_HTML}}` | See below (or empty string) |
| `{{FOOTER_HTML}}` | See below (or empty string) |

**Header HTML** (if title provided):
```html
<div class="diagram-header">
  <h1>Title Here</h1>
  <p>Subtitle here</p>
</div>
```
If no title: replace `{{HEADER_HTML}}` with empty string.

**Footer HTML** (if attribution wanted):
```html
<div class="diagram-footer">ExampleCo Digital</div>
```
If no footer: replace `{{FOOTER_HTML}}` with empty string.

**Dark mode card override**: for `dark-pro` theme, inject additional style:
```css
.diagram-card { background: #1e293b; border-color: #334155; }
.diagram-header h1 { color: #f1f5f9; }
.diagram-header p { color: #94a3b8; }
.diagram-footer { color: #475569; }
```

### 4. Render & capture

```
1. Write the final HTML to a temp file: media/tmp/diagram.html
2. browser(action="open", targetUrl="file://<workspace>/media/tmp/diagram.html")
3. Wait 2s for fonts + Mermaid render
4. browser(action="screenshot", fullPage=true, type="png")
5. Save screenshot to media/out/diagrams/YYYY-MM-DD_<slug>.png
```

### 5. Export options
Offer these after rendering:
- **PNG** (already done) — ready for Slack/Telegram/presentation
- **HTML** — save to Obsidian vault for interactive viewing: `<vault>/20_Artifacts/diagrams/`
- **Mermaid source** — raw `.mmd` file for editing in Mermaid Live Editor or Obsidian Mermaid plugin

### 6. Reply
- Send the screenshot in chat
- Mention saved file paths
- If the diagram might need iteration, ask "ปรับอะไรอีกไหมครับ?"

## Quality Checklist
Before rendering, verify:
- [ ] All nodes connected (no orphans)
- [ ] Labels readable (not too long)
- [ ] Direction makes sense for the content
- [ ] Decision nodes use diamond shape (rhombus `{}`)
- [ ] Start/end nodes use rounded/circle shape `([])` or `((()))`
- [ ] Color-coded groups if >8 nodes (use classDef)
- [ ] Subgraphs for logical grouping if >10 nodes
- [ ] No Mermaid syntax errors (test mentally)

## Tips
- For ERPNext workflows: show document states as nodes, transitions as arrows, conditions on edges
- For approval flows: put happy path vertical, exception paths horizontal
- For Thai audiences: Thai labels are fine, but keep technical terms in English
- `flowchart LR` works better for sequential processes; `flowchart TD` for hierarchical/decision trees
- If diagram is complex (>20 nodes), consider splitting into multiple diagrams
