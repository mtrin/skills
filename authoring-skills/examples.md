# Skill Examples and Patterns

Common patterns and complete example skills.

## Example 1: Simple Single-File Skill

Minimal skill with just SKILL.md:

```
commit-helper/
└── SKILL.md
```

```yaml
---
name: generating-commit-messages
description: Generates clear commit messages from git diffs. Use when writing commit messages or reviewing staged changes.
---

# Generating Commit Messages

## Instructions

1. Run `git diff --staged` to see changes
2. Generate commit message with:
   - Summary under 50 characters
   - Detailed description
   - Affected components

## Format

- Use present tense
- Explain what and why, not how
```

## Example 2: Multi-File Skill with Progressive Disclosure

```
pdf-processing/
├── SKILL.md
├── FORMS.md
├── REFERENCE.md
└── scripts/
    ├── fill_form.py
    └── validate.py
```

**SKILL.md**:
```yaml
---
name: pdf-processing
description: Extract text, fill forms, merge PDFs. Use when working with PDF files, forms, or document extraction.
allowed-tools: Read, Bash(python:*)
---

# PDF Processing

## Quick Start

Extract text:
import pdfplumber
with pdfplumber.open("doc.pdf") as pdf:
    text = pdf.pages[0].extract_text()

## Resources
- Form filling: [FORMS.md](FORMS.md)
- API reference: [REFERENCE.md](REFERENCE.md)

## Requirements
pip install pypdf pdfplumber
```

## Example 3: Read-Only Analysis Skill

```yaml
---
name: code-analysis
description: Analyzes code quality without making changes. Use for code review, security audit, or understanding codebases.
allowed-tools: Read, Grep, Glob
---

# Code Analysis

This skill can only read files, not modify them.

## Analysis Types

1. **Security**: Check for common vulnerabilities
2. **Quality**: Review structure and patterns
3. **Dependencies**: Analyze import graphs
```

## Example 4: Skill with Forked Context

```yaml
---
name: deep-research
description: Performs extensive codebase research in isolated context. Use for complex investigations that need their own conversation history.
context: fork
agent: Explore
---

# Deep Research

Runs in isolated context to avoid polluting main conversation.

## Process
1. Gather all relevant files
2. Build understanding incrementally
3. Return synthesized findings
```

## Pattern: Template Output

For consistent output format:

```markdown
## Report Structure

Use this exact template:

# [Title]

## Summary
[One paragraph]

## Findings
- Finding 1
- Finding 2

## Recommendations
1. Action item
2. Action item
```

## Pattern: Examples for Style

Show input/output pairs:

```markdown
## Commit Message Format

**Example 1:**
Input: Added user auth with JWT
Output:
feat(auth): implement JWT authentication

Add login endpoint and token validation

**Example 2:**
Input: Fixed date display bug
Output:
fix(reports): correct date formatting

Use UTC timestamps consistently
```

## Pattern: Conditional Workflow

Guide through decision points:

```markdown
## Document Workflow

1. Determine type:
   - **Creating new?** → Use docx-js library
   - **Editing existing?** → Modify XML directly

2. For editing:
   - Unpack document
   - Edit XML
   - Validate changes
   - Repack
```

## Pattern: Feedback Loop

Validate before proceeding:

```markdown
## Edit Process

1. Make edits to document.xml
2. **Validate immediately**: python scripts/validate.py
3. If validation fails:
   - Review error message
   - Fix the issue
   - Validate again
4. **Only proceed when validation passes**
5. Rebuild document
```

## Pattern: Checklist Workflow

Track multi-step progress:

```markdown
## Processing Workflow

Copy and track progress:

- [ ] Step 1: Analyze input
- [ ] Step 2: Create plan
- [ ] Step 3: Validate plan
- [ ] Step 4: Execute
- [ ] Step 5: Verify output

**Step 1: Analyze input**
Run: python scripts/analyze.py input.pdf
...
```

## Pattern: Domain-Specific Organization

For skills covering multiple domains:

```
data-analysis/
├── SKILL.md
└── reference/
    ├── finance.md
    ├── sales.md
    └── product.md
```

**SKILL.md**:
```markdown
# Data Analysis

## Datasets

- **Finance**: Revenue, billing → [reference/finance.md](reference/finance.md)
- **Sales**: Pipeline, accounts → [reference/sales.md](reference/sales.md)
- **Product**: Usage, features → [reference/product.md](reference/product.md)
```

## Pattern: Utility Script Documentation

Document scripts for execution:

```markdown
## Scripts

**analyze.py**: Extract form fields
python scripts/analyze.py input.pdf > fields.json

Output:
{"field_name": {"type": "text", "x": 100, "y": 200}}

**validate.py**: Check for errors
python scripts/validate.py fields.json
Returns "OK" or lists errors

**fill.py**: Apply values
python scripts/fill.py input.pdf fields.json output.pdf
```

## Anti-Pattern Examples

### Too Verbose

```markdown
# Bad
## Extract PDF text
PDF (Portable Document Format) files are a common file format
that contains text, images, and other content. To extract text
from a PDF, you'll need to use a library. There are many libraries...

# Good
## Extract PDF text
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

### Too Many Options

```markdown
# Bad
You can use pypdf, or pdfplumber, or PyMuPDF, or pdf2image...

# Good
Use pdfplumber for text extraction.
For scanned PDFs requiring OCR, use pdf2image with pytesseract.
```

### Deeply Nested References

```markdown
# Bad
SKILL.md → advanced.md → details.md → actual info

# Good
SKILL.md → advanced.md (contains actual info)
SKILL.md → details.md (contains actual info)
```
