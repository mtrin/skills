---
name: aligning-md-tables
description: Aligns markdown tables and box-drawing diagrams so all edges line up vertically. Use when fixing tables, aligning markdown tables, formatting .md files, aligning diagrams, fixing boxes, or when pipes/edges look misaligned.
user-invocable: false
---

# Align Markdown Tables & Diagrams

Detects and fixes misaligned markdown tables and box-drawing diagrams in any `.md` file using `scripts/fix-md-tables.py`.

## Usage

### Check for misalignment (dry run)

```bash
python ~/.claude/skills/aligning-md-tables/scripts/fix-md-tables.py --check <file.md>
```

Exit code 0 = all aligned, 1 = misaligned tables found.

### Fix tables in-place

```bash
python ~/.claude/skills/aligning-md-tables/scripts/fix-md-tables.py --fix <file.md>
```

Rewrites the file with all edges padded to equal width.

## Workflow

1. Run `--check` first to see what needs fixing
2. Run `--fix` to align in-place
3. Run `--check` again to confirm

## What It Handles

### Markdown tables (`|` pipes)
- Finds consecutive lines starting with `|`
- Pads each column to the widest cell
- Rebuilds separator rows (`---`) to match

### Box-drawing diagrams (`┌┐└┘│─`)
- Finds `┌...┐` through `└...┘` blocks
- Normalizes left edges to the `┌` column
- Pads content so right `│` aligns with `┐`/`┘`
- Extends `─` borders to match new width
- Preserves mid-connectors (`┬`, `┴`, `┼`) at their absolute column
- Handles `├...┤` divider rows
