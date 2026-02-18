---
name: bitbucket-pr
description: Creates Bitbucket pull requests. Use when asked to create a PR, open a pull request, or promote code between branches (dev, master, uat, stg, prod).
argument-hint: "[dev|release|<source>-to-<target>] [title]"
user-invocable: true
---

# Bitbucket Pull Request

Create PRs against `finityconsulting` workspace repos via the Bitbucket API.

## Step 1: Gather git context

Run these commands to determine context:

```bash
repo=$(basename "$(git rev-parse --show-toplevel)")
branch=$(git branch --show-current)
last_commit=$(git log -1 --pretty=format:%s)
```

## Step 2: Determine workflow

Parse `$ARGUMENTS` (first word = workflow, rest = optional title override).

| Argument / Context | Source | Target | Close source? |
|--------------------|--------|--------|---------------|
| `dev` or no args + feature branch | current branch | develop | true |
| `release` or no args + on develop | develop | master | false |
| `master-to-prod` | master | prod | false |
| `master-to-uat` | master | uat | false |
| `uat-to-stg` | uat | stg | false |
| `uat-to-prod` | uat | prod | false |
| `stg-to-prod` | stg | prod | false |

**"Feature branch"** = any branch that is not `develop`, `master`, `prod`, `uat`, or `stg`.

If the workflow cannot be determined (e.g. on `master` with no arguments), use `AskUserQuestion` to ask.

**Title**: use the explicit title from arguments if provided, otherwise use `last_commit`.

## Step 3: Confirm with user

Before executing, show a summary and ask for confirmation:

```
Repo:           <repo>
Source branch:  <src>
Target branch:  <target>
Title:          <title>
Close source:   <true/false>
```

Use `AskUserQuestion` with options: **Create PR**, **Change title**, **Cancel**.

## Step 4: Execute

Run the bundled script. The skill directory is at `~/.claude/skills/bitbucket-pr/`.

```bash
python3 ~/.claude/skills/bitbucket-pr/scripts/pull_request \
  --repo "$repo" \
  --user "$(pass bitbucket/login)" \
  --title "$title" \
  --close-source-branch "$close_source_branch" \
  --src-branch "$src_branch" \
  --target-branch "$target_branch"
```

## Step 5: Report

Extract and display the Pull Request URL from the script output. If the script fails, show the error message.
