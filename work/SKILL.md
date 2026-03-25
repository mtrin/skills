---
name: work
description: Manage ticket workspaces — create tickets, check status, add repos, close tickets. Does NOT switch contexts (use the external `w` shell function for that).
argument-hint: "start|status|add-repo|close [args...]"
user-invocable: true
disable-model-invocation: true
allowed-tools:
  - Bash(bash ~/.claude/skills/work/scripts/setup-repo.sh *)
  - Bash(bash ~/.claude/skills/work/scripts/ws)
  - Bash(mkdir *)
  - Bash(yq *)
  - Bash(git -C * status *)
  - Bash(git -C * log *)
  - Bash(git -C * branch *)
  - Bash(git -C * remote *)
  - Bash(git -C * fetch *)
  - Bash(git -C * worktree *)
  - Bash(git -C * rev-parse *)
  - Bash(git -C * diff *)
  - Bash(date *)
  - mcp__mcp-atlassian__jira_get_issue
  - mcp__bitbucket__bb_get
---

# Workspace Ticket Manager

The user may invoke this skill with explicit subcommands OR conversationally. Interpret intent from `$ARGUMENTS`:
- `start ...` or "start a ticket for PLAT-1400" → **start**
- `status` or "what's the state of my tickets" → **status**
- `add-repo ...` or "add the punt terraform repo" or "I also need shared services" → **add-repo**
- `close ...` or "close this ticket" → **close**

When the user speaks conversationally, extract the repo name (fuzzy is fine — search Bitbucket MCP to resolve), ticket ID, and intent. Don't require exact syntax.

The workspace root is `~/workspace`. Ticket dirs are at `~/workspace/<TICKET-ID-description>/`.
Clone cache is at `~/clones/`. Scripts are at `~/.claude/skills/work/scripts/`.

CWD context: this skill runs from inside a ticket dir (e.g. `~/workspace/PLAT-1344-desc/`) or `~/workspace/main/`. The current ticket is the CWD basename.

## Permission Rules — READ CAREFULLY

**You CAN freely do (no confirmation needed):**
- Read any file (git log, git status, git diff, git branch, manifest.yaml, CLAUDE.md, etc.)
- git fetch, git worktree add/list, git remote, git rev-parse
- Create directories, write CLAUDE.md, manifest.yaml, .gitignore template
- Run `bash ~/.claude/skills/work/scripts/setup-repo.sh`
- Run `bash ~/.claude/skills/work/scripts/ws`
- Run yq to parse/update manifest.yaml
- Append to `~/workspace/.changelog`

**You MUST ASK the user before:**
- git add (show what will be staged)
- git commit (show the proposed message, let user edit)
- git checkout/switch (show current state first)
- Any file deletion

**You CANNOT do (denied, will be blocked):**
- git push (user does this themselves)
- git reset --hard
- git clean -f
- git checkout -- (destructive restore)
- git restore (destructive)

## Auth Handling

If setup-repo.sh exits with code 2 (AUTH_URL in output), tell the user to run the same command with `!` prefix so the terminal handles the OAuth link directly:

```
Run this to authenticate (the link will be clickable):
! bash ~/.claude/skills/work/scripts/setup-repo.sh <same args>
```

After user confirms success, continue with remaining ticket setup steps.

---

## start

Create a new ticket workspace.

### Usage
```
/work start PLAT-1400-some-description
/work start PLAT-1400-some-description platform_argocd_lower plt_tf_platform
```

### Steps

1. **Parse arguments**: Extract ticket key (e.g. `PLAT-1400`) from the first argument (match `[A-Z]+-\d+` prefix). Remaining arguments are repo names. If the user only provided the ticket key (no description suffix), you MUST construct the dir name as `PLAT-1400-kebab-description` using the JIRA title after fetching it in step 3. Always use kebab-case, lowercase, short (3-5 words max). Example: `PLAT-1347-cleanup-jam-dashboards`.

2. **Check ticket dir doesn't already exist**: If `~/workspace/<TICKET-ID-description>/` exists, stop and tell the user. Don't overwrite.

3. **Fetch JIRA issue**: Use `mcp__mcp-atlassian__jira_get_issue` with the ticket key. Present a brief summary: title, description, status, priority.

4. **Determine repos**: If repos were specified in the command, use those. Otherwise, ask the user which repos are needed. Suggest from the known repos list:
   - `platform_argocd_lower` — ArgoCD config, ApplicationSets, bootstrap
   - `plt_tf_platform` — Terraform IaC
   - `shared_services_deploy` — Platform shared apps (Grafana, etc.)
   - `pipeline_build_image` — CI build image (Gitlab)
   - Other — user provides name and URL

   Also check `~/workspace/.ref/argocd/apps/` for app-specific deploy repos if relevant.

5. **Resolve URLs — ALWAYS use SSH, never HTTPS**:
   - Bitbucket: `git@bitbucket.org:finityconsulting/<name>.git`
   - Gitlab ISA repos: `git@gitlab.com:finity-consulting/isa/<name>.git`
   - Gitlab platform repos: `git@gitlab.com:finity-consulting/platform/<name>.git`

   If unsure about a repo name, use `mcp__bitbucket__bb_get` to search, but ALWAYS construct the SSH URL yourself — never use the HTTPS URL returned by the API.

6. **Create ticket directory**:
   ```bash
   mkdir -p ~/workspace/<TICKET-ID-description>
   ```

7. **Write .gitignore template** (always the same content):
   ```
   *
   !.gitignore
   !CLAUDE.md
   !manifest.yaml
   ```

8. **Write manifest.yaml**: For each repo, the branch name is `<TICKET-ID-description>` (same as the dir name). Source branch is usually `develop`.
   ```yaml
   repos:
     <name>:
       url: <url>
       branch: <TICKET-ID-description>
       source: develop
   ```

9. **Setup repos**: For each repo in the manifest, run:
   ```bash
   bash ~/.claude/skills/work/scripts/setup-repo.sh ~/workspace/<TICKET-ID-description> <name> <url> <branch> --source <source>
   ```

10. **Write CLAUDE.md**: Create ticket context with:
    - `# <TICKET-KEY>: <title from JIRA>`
    - Summary from JIRA description
    - Active repos list with branches and purpose
    - Steps/goals derived from JIRA description

11. **Log to changelog**:
    Append to `~/workspace/.changelog`:
    ```
    <ISO-timestamp> [ticket-start] <TICKET-ID-description>
    ```

12. **Tell the user**: "Ticket ready. Run `w` to switch to it, or `cd ~/workspace/<TICKET-ID-description>`."

---

## status

Show all tickets and their state. Runs `bash ~/.claude/skills/work/scripts/ws` and shows recent changelog.

### Steps

1. Run `bash ~/.claude/skills/work/scripts/ws` to show ticket/repo state.

2. Show last 10 lines of `~/workspace/.changelog`.

---

## add-repo

Add a repo to the current ticket.

### Usage
```
/work add-repo punt_tf_platform
/work add-repo shared_services_deploy git@bitbucket.org:finityconsulting/shared_services_deploy.git
```

### Steps

1. **Determine current ticket dir**: From CWD. Must be inside a ticket dir (not workspace root or main).

2. **Resolve repo name and URL**:
   - If the user gave a full name, use it directly.
   - If the user gave a partial/fuzzy name, search Bitbucket MCP first:
     ```
     mcp__bitbucket__bb_get path=/repositories/finityconsulting queryParams={"q":"name~\"<search>\"","pagelen":"5"}
     ```
     Do NOT use Explore agents or crawl argocd files to find repos. Use the Bitbucket API.
   - Construct the SSH URL: `git@bitbucket.org:finityconsulting/<name>.git` (NEVER use HTTPS URLs from the API).
   - For Gitlab repos: `git@gitlab.com:finity-consulting/<group>/<name>.git`
   - Branch defaults to the ticket dir basename. Source defaults to `develop`.

3. **Run setup-repo.sh** — ALWAYS pass `--source`:
   ```bash
   bash ~/.claude/skills/work/scripts/setup-repo.sh <ticket-dir> <name> <url> <branch> --source develop
   ```

4. **Show result**: Display the updated manifest.yaml.

---

## close

Archive a ticket. Removes worktrees but keeps tracked state (CLAUDE.md, manifest.yaml).

### Usage
```
/work close PLAT-1344-deactivate-log-analytics
```

### Steps

1. **Check state**: Run `bash ~/.claude/skills/work/scripts/ws` to show current state. For the target ticket:
   - Any uncommitted changes? → BLOCK, tell user to commit or discard first
   - Any unpushed commits? → WARN, ask user to push first

2. **Ask for confirmation**: Show what will be removed (worktrees only, context files stay).

3. **Remove worktrees**: For each repo in the ticket's manifest:
   ```bash
   git -C ~/clones/<name>.git worktree remove ~/workspace/<ticket>/<name>
   ```
   No `--force` — git will refuse if dirty.

4. **Log to changelog**:
   Append to `~/workspace/.changelog`:
   ```
   <ISO-timestamp> [ticket-close] <TICKET-ID-description>
   ```
