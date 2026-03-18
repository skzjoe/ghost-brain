# OpenClaw Integration

Complete setup and usage guide for integrating the self-improvement skill with OpenClaw.

## Overview

OpenClaw uses workspace-based prompt injection combined with event-driven hooks. Context is injected from workspace files at session start, and hooks can trigger on lifecycle events.

## Workspace Structure

```
~/.openclaw/                      
├── workspace/                   # Working directory
│   ├── AGENTS.md               # Multi-agent coordination patterns
│   ├── SOUL.md                 # Behavioral guidelines and personality
│   ├── TOOLS.md                # Tool capabilities and gotchas
│   ├── MEMORY.md               # Long-term memory (main session only)
│   └── memory/                 # Daily memory files
│       └── YYYY-MM-DD.md
├── skills/                      # Installed skills
│   └── <skill-name>/
│       └── SKILL.md
└── hooks/                       # Custom hooks
    └── <hook-name>/
        ├── HOOK.md
        └── handler.ts
```

## Quick Setup

### 1. Install the Skill

```bash
clawdhub install self-improving-agent
```

Or copy manually:

```bash
cp -r self-improving-agent ~/.openclaw/skills/
```

### 2. Install the Hook (Optional)

Copy the hook to OpenClaw's hooks directory:

```bash
cp -r hooks/openclaw ~/.openclaw/hooks/self-improvement
```

Enable the hook:

```bash
openclaw hooks enable self-improvement
```

### 3. Create Learning Files

Create the `.learnings/` directory in your workspace:

```bash
mkdir -p ~/.openclaw/workspace/.learnings
```

Or in the skill directory:

```bash
mkdir -p ~/.openclaw/skills/self-improving-agent/.learnings
```

## Injected Prompt Files

### AGENTS.md

Purpose: Multi-agent workflows and delegation patterns.

```markdown
# Agent Coordination

## Delegation Rules
- Use explore agent for open-ended codebase questions
- Spawn sub-agents for long-running tasks
- Use sessions_send for cross-session communication

## Session Handoff
When delegating to another session:
1. Provide full context in the handoff message
2. Include relevant file paths
3. Specify expected output format
```

### SOUL.md

Purpose: Behavioral guidelines and communication style.

```markdown
# Behavioral Guidelines

## Communication Style
- Be direct and concise
- Avoid unnecessary caveats and disclaimers
- Use technical language appropriate to context

## Error Handling
- Admit mistakes promptly
- Provide corrected information immediately
- Log significant errors to learnings
```

### TOOLS.md

Purpose: Tool capabilities, integration gotchas, local configuration.

```markdown
# Tool Knowledge

## Self-Improvement Skill
Log learnings to `.learnings/` for continuous improvement.

## Local Tools
- Document tool-specific gotchas here
- Note authentication requirements
- Track integration quirks
```

## Learning Workflow

### Capturing Learnings

1. **In-session**: Log to `.learnings/` as usual
2. **Cross-session**: Promote to workspace files

### Promotion Decision Tree

```
Is the learning project-specific?
├── Yes → Keep in .learnings/
└── No → Is it behavioral/style-related?
    ├── Yes → Promote to SOUL.md
    └── No → Is it tool-related?
        ├── Yes → Promote to TOOLS.md
        └── No → Promote to AGENTS.md (workflow)
```

### Promotion Format Examples

**From learning:**
> Git push to GitHub fails without auth configured - triggers desktop prompt

**To TOOLS.md:**
```markdown
## Git
- Don't push without confirming auth is configured
- Use `gh auth status` to check GitHub CLI auth
```

## Inter-Agent Communication

OpenClaw provides tools for cross-session communication:

### sessions_list

View active and recent sessions:
```
sessions_list(activeMinutes=30, messageLimit=3)
```

### sessions_history

Read transcript from another session:
```
sessions_history(sessionKey="session-id", limit=50)
```

### sessions_send

Send message to another session:
```
sessions_send(sessionKey="session-id", message="Learning: API requires X-Custom-Header")
```

### sessions_spawn

Spawn a background sub-agent:
```
sessions_spawn(task="Research X and report back", label="research")
```

## Available Hook Events

| Event | When It Fires |
|-------|---------------|
| `agent:bootstrap` | Before workspace files inject |
| `command:new` | When `/new` command issued |
| `command:reset` | When `/reset` command issued |
| `command:stop` | When `/stop` command issued |
| `gateway:startup` | When gateway starts |

## Coding workflow integration

For non-trivial coding work in older or unfamiliar repos, combine Ghost Brain with OpenClaw's agent/session features like this:

### Recommended operating model
1. **Research first**
   - Use the main session or a sub-agent to locate the real system slice.
   - Save findings using `memory/reference/CODING-QUICKSTART.md` and the templates in `skills/assets/` as guidance.
2. **Use sub-agents for context isolation**
   - Spawn sub-agents for repo scanning, tracing flows, and summarizing read-heavy exploration.
   - Return only concise, high-signal findings to the parent session.
3. **Create a plan before major edits**
   - Treat the plan as a review artifact, not just a prompt.
4. **Implement from the plan**
   - Keep validation explicit.
5. **Compact and restart when the thread degrades**
   - If the session becomes noisy or correction-heavy, create a compaction handoff and resume from a fresh session.

### Suggested artifact flow
- Research → `skills/assets/coding-research-template.md`
- Plan → `skills/assets/coding-plan-template.md`
- Compaction → `skills/assets/coding-compaction-handoff-template.md`
- Implementation summary → `skills/assets/coding-implementation-summary-template.md`

### When NOT to use the heavy workflow
Skip the full process for tiny, obvious, low-risk edits.

## Detection Triggers

### Standard Triggers
- User corrections ("No, that's wrong...")
- Command failures (non-zero exit codes)
- API errors
- Knowledge gaps

### OpenClaw-Specific Triggers

| Trigger | Action |
|---------|--------|
| Tool call error | Log to TOOLS.md with tool name |
| Session handoff confusion | Log to AGENTS.md with delegation pattern |
| Model behavior surprise | Log to SOUL.md with expected vs actual |
| Skill issue | Log to .learnings/ or report upstream |

## Verification

Check hook is registered:

```bash
openclaw hooks list
```

Check skill is loaded:

```bash
openclaw status
```

## Troubleshooting

### Hook not firing

1. Ensure hooks enabled in config
2. Restart gateway after config changes
3. Check gateway logs for errors

### Learnings not persisting

1. Verify `.learnings/` directory exists
2. Check file permissions
3. Ensure workspace path is configured correctly

### Skill not loading

1. Check skill is in skills directory
2. Verify SKILL.md has correct frontmatter
3. Run `openclaw status` to see loaded skills
