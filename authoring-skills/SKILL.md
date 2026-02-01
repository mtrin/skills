---
name: authoring-skills
description: Creates and structures Claude Code skills with proper YAML frontmatter, progressive disclosure, and file organization. Use when creating new skills, refactoring existing skills, or helping users author skills for Claude Code.
---

# Skill Authoring Guide

Create effective Claude Code skills that are concise, well-structured, and easy for Claude to discover and use.

## Critical Rule: Keep SKILL.md Under 500 Lines

Split content when approaching this limit:

```
my-skill/
├── SKILL.md           # Required: overview and navigation (<500 lines)
├── reference.md       # Detailed API docs (loaded when needed)
├── examples.md        # Usage examples (loaded when needed)
└── scripts/
    └── helper.py      # Utility script (executed, not loaded)
```

## SKILL.md Structure

Every skill needs a `SKILL.md` file with YAML frontmatter and markdown instructions:

```yaml
---
name: my-skill-name
description: What it does and when to use it. Include trigger keywords.
user-invocable: false
---

# Skill Title

## Quick Start
[Essential instructions here]

## Additional Resources
- For details, see [reference.md](reference.md)
- For examples, see [examples.md](examples.md)
```

## Required Fields

| Field | Rules |
|-------|-------|
| `name` | Lowercase, numbers, hyphens only. Max 64 chars. Must match directory name. |
| `description` | Non-empty. Max 1024 chars. Describe what + when to use. |
| `user-invocable` | `false` |

## Optional Fields

| Field | Purpose |
|-------|---------|
| `allowed-tools` | Restrict tools: `Read, Grep, Glob` |
| `model` | Override model: `claude-sonnet-4-20250514` |
| `context` | Set to `fork` for isolated subagent context |
| `agent` | Agent type when `context: fork` (e.g., `Explore`, `Plan`) |
| `hooks` | Skill-scoped hooks: `PreToolUse`, `PostToolUse`, `Stop` |

For complete field reference, see [reference.md](reference.md).

## Writing Effective Descriptions

The description is critical for skill discovery. Include:
1. **What it does**: Specific capabilities
2. **When to use it**: Trigger keywords users would say

**Always write in third person** (description is injected into system prompt):

```yaml
# Good
description: Processes Excel files and generates reports. Use when analyzing spreadsheets, .xlsx files, or tabular data.

# Bad - inconsistent POV causes discovery issues
description: I can help you process Excel files
description: You can use this to process Excel files
```

## Naming Convention

Use gerund form (verb + -ing) with lowercase-hyphens:

- `processing-pdfs`
- `analyzing-data`
- `reviewing-code`

## Progressive Disclosure Pattern

Put essential info in SKILL.md, details in separate files:

```markdown
# SKILL.md

## Quick Start
[Essential instructions - what 80% of users need]

## Resources
- **API Reference**: See [reference.md](reference.md)
- **Examples**: See [examples.md](examples.md)
- **Advanced**: See [advanced.md](advanced.md)
```

**Keep references ONE level deep.** Claude may partially read deeply nested files.

## Conciseness Principles

Claude is already very smart. Only add context Claude doesn't have:

```markdown
# Good (~50 tokens)
## Extract PDF text
Use pdfplumber:
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()

# Bad (~150 tokens) - explains what Claude already knows
## Extract PDF text
PDF (Portable Document Format) files are a common file format...
```

## Degrees of Freedom

Match specificity to task fragility:

| Freedom | When to Use | Example |
|---------|-------------|---------|
| **High** | Multiple valid approaches | "Analyze code structure and suggest improvements" |
| **Medium** | Preferred pattern exists | Provide template with parameters |
| **Low** | Fragile/critical operations | "Run exactly: `python scripts/migrate.py --verify`" |

## Utility Scripts

Bundle scripts for reliable, token-efficient execution:

```markdown
## Validate Input
Run the validation script:
python scripts/validate.py input.txt

Do NOT read the script - just execute it.
```

Scripts should handle errors explicitly, not punt to Claude.

## Workflow Pattern

For complex tasks, provide checkable steps:

```markdown
## Form Processing Workflow

Progress checklist:
- [ ] Step 1: Analyze form
- [ ] Step 2: Create mapping
- [ ] Step 3: Validate
- [ ] Step 4: Execute
- [ ] Step 5: Verify

**Step 1: Analyze form**
Run: `python scripts/analyze.py input.pdf`
...
```

## Common Patterns

For templates, examples, and conditional workflows, see [examples.md](examples.md).

## Anti-Patterns to Avoid

1. **Windows paths**: Use `scripts/helper.py`, not `scripts\helper.py`
2. **Too many options**: Provide a default, mention alternatives only when needed
3. **Time-sensitive info**: Use "old patterns" section instead of dates
4. **Inconsistent terminology**: Pick one term and use it throughout
5. **Deeply nested references**: Keep file references one level deep
6. **Assuming tools installed**: List required packages explicitly

## Checklist Before Sharing

- [ ] Description is specific with trigger keywords
- [ ] Description in third person
- [ ] SKILL.md under 500 lines
- [ ] Large content split into reference files
- [ ] References are one level deep
- [ ] Consistent terminology
- [ ] No time-sensitive information
- [ ] Scripts have error handling
- [ ] Required packages listed
