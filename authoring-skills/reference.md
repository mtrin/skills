# Skill Field Reference

Complete reference for SKILL.md YAML frontmatter fields.

## Required Fields

### name

**Type**: string
**Max length**: 64 characters
**Validation**:
- Lowercase letters, numbers, and hyphens only
- Cannot contain XML tags
- Cannot contain reserved words: "anthropic", "claude"
- Should match the directory name

```yaml
# Valid
name: pdf-processing
name: code-review-v2
name: my-tool-123

# Invalid
name: PDF_Processing    # uppercase, underscores
name: claude-helper     # reserved word
name: my skill          # spaces
```

### description

**Type**: string
**Max length**: 1024 characters
**Validation**:
- Must be non-empty
- Cannot contain XML tags

**Purpose**: Claude uses this to decide when to apply the skill. Include:
1. What the skill does (specific capabilities)
2. When to use it (trigger keywords)

```yaml
# Good - specific with triggers
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.

# Good - clear scope and triggers
description: Generate commit messages by analyzing git diffs. Use when writing commit messages or reviewing staged changes.

# Bad - vague
description: Helps with documents
description: Processes data
```

## Optional Fields

### allowed-tools

**Type**: string (comma-separated) or array
**Default**: No restriction (standard permission model)

Restrict which tools Claude can use when the skill is active:

```yaml
# Comma-separated string
allowed-tools: Read, Grep, Glob

# YAML array
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(python:*)
```

**Use cases**:
- Read-only skills that shouldn't modify files
- Security-sensitive workflows
- Limited-scope analysis tasks

### model

**Type**: string
**Default**: Conversation's model

Override the model when this skill is active:

```yaml
model: claude-sonnet-4-20250514
model: claude-opus-4-20250514
```

### context

**Type**: string
**Values**: `fork`

Run the skill in an isolated subagent context:

```yaml
context: fork
```

When set, the skill runs with its own conversation history, useful for complex multi-step operations.

### agent

**Type**: string
**Default**: `general-purpose`
**Requires**: `context: fork`

Specify the agent type for forked context:

```yaml
context: fork
agent: Explore
```

**Built-in agents**: `Explore`, `Plan`, `general-purpose`
**Custom agents**: Reference by name from `.claude/agents/`

### hooks

**Type**: object
**Events**: `PreToolUse`, `PostToolUse`, `Stop`

Define hooks scoped to the skill's lifecycle:

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/security-check.sh $TOOL_INPUT"
          once: true
```

The `once: true` option runs the hook only once per session.

### user-invocable

**Type**: boolean
**Default**: `true`

Control visibility in the slash command menu:

```yaml
user-invocable: false  # Hide from menu, Claude can still use it
```

| Setting | Slash Menu | Skill Tool | Auto-discovery |
|---------|------------|------------|----------------|
| `true` (default) | Visible | Allowed | Yes |
| `false` | Hidden | Allowed | Yes |

## File Path Conventions

Always use forward slashes (Unix-style):

```markdown
# Good
See [reference.md](reference.md)
Run: python scripts/validate.py

# Bad - Windows paths cause cross-platform issues
See [reference.md](reference.md)
Run: python scripts\validate.py
```

## MCP Tool References

When referencing MCP tools, use fully qualified names:

```markdown
# Format: ServerName:tool_name
Use the BigQuery:bigquery_schema tool to retrieve schemas.
Use the GitHub:create_issue tool to create issues.
```

## Skill Locations

| Location | Path | Scope |
|----------|------|-------|
| Enterprise | Managed settings | All org users |
| Personal | `~/.claude/skills/` | You, all projects |
| Project | `.claude/skills/` | Anyone in repo |
| Plugin | Plugin's `skills/` | Plugin users |

Higher rows override lower rows when names conflict.
