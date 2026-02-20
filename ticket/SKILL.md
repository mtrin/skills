---
name: ticket
description: Manages JIRA ticket lifecycle - creates task folders with worktrees and MCP config, checks status, and cleans up when done. Use when starting, closing, or checking status of work tickets.
argument-hint: "start|close|status [PLAT-1234-description]"
user-invocable: true
---

# Ticket Lifecycle Manager

Parse `$ARGUMENTS` to determine the subcommand and task identifier:
- First word is the subcommand: `start`, `close`, or `status`
- Remaining words are the task ID (e.g. `PLAT-1234-dashboard-fix`)
- The JIRA key is the prefix matching `[A-Z]+-\d+` (e.g. `PLAT-1234`)

Task folder path: `~/llm/stories/<task-id>`

---

## start

Set up a new task folder with worktrees and configuration.

### Step 1: Fetch JIRA issue

Use `mt-jira-mcp` to get issue details. Present a brief summary: title, description, acceptance criteria, status.

### Step 2: Ask which repos are needed

Use `AskUserQuestion` (multi-select) with common choices:

- **platform_argocd_lower** — ArgoCD config, ApplicationSets, bootstrap
- **plt_tf_platform** — Terraform IaC
- **shared_services_deploy** — Platform shared apps (Grafana, etc.)
- Other — user types the repo name

Worktree source locations:
- `/home/mano/llm/platform/platform_argocd_lower/`
- `/home/mano/llm/platform/plt_tf_platform/`
- `/home/mano/llm/platform/shared_services_deploy/`
- `/home/mano/llm/platform/deployments/<repo_name>/` — deploy repos
- `/home/mano/llm/platform/apps/<repo_name>/` — app source repos
- `/home/mano/llm/punt-platform/<repo_name>/` — Punt-specific repos (punt_argocd, punt_tf_platform, punt_deploy, punt_api)

### Step 3: Ask which MCPs are needed

Use `AskUserQuestion` (multi-select):

- **Grafana** — Dashboard, Prometheus, Loki queries
- **Azure MCP** — Azure resource and monitoring queries
- **None** — No extra MCPs

### Step 4: Create task folder and worktrees

```bash
mkdir -p ~/llm/stories/<task-id>
```

For each selected repo, create a worktree using `git -C` (never use `cd`):

```bash
# 1. Fetch latest
git -C <source-repo-path> fetch --all

# 2. Ensure develop branch exists locally
git -C <source-repo-path> switch develop 2>/dev/null || git -C <source-repo-path> checkout -b develop origin/develop

# 3. Create worktree
git -C <source-repo-path> worktree add ~/llm/stories/<task-id>/<repo-name> -b <task-id> origin/develop

# 4. Set tracking
git -C ~/llm/stories/<task-id>/<repo-name> config branch.<task-id>.remote origin
git -C ~/llm/stories/<task-id>/<repo-name> config branch.<task-id>.merge refs/heads/<task-id>
```

Where `<repo-name>` is the basename of the source repo (e.g. `punt_argocd`, `plt_tf_platform`).

Run all independent repo worktree creations in parallel.

#### Read-only reference copies

If the user needs files from a repo for reference only (no changes needed), offer to extract a read-only copy instead of a full worktree:

```bash
mkdir -p ~/llm/stories/<task-id>/reference
git -C <source-repo-path> archive origin/develop <path-within-repo>/ | tar -x -C ~/llm/stories/<task-id>/reference --strip-components=<N>
```

Where `<N>` strips leading path components to keep the directory structure clean. This avoids creating unnecessary worktrees when only reading is needed.

### Step 5: Write .mcp.json (if MCPs selected)

Write `~/llm/stories/<task-id>/.mcp.json` with selected MCPs:

**Grafana:**
```json
{
  "grafana": {
    "type": "stdio",
    "command": "docker",
    "args": ["run","--rm","-i","-e","GRAFANA_URL","-e","GRAFANA_API_KEY","mcp/grafana:local","-t","stdio","--enabled-tools=datasource,prometheus,loki,dashboard,alerting,search,folder,admin,navigation"],
    "env": {"GRAFANA_URL": "${GRAFANA_URL}", "GRAFANA_API_KEY": "${GRAFANA_API_KEY}"}
  }
}
```

**Azure MCP:**

When Azure MCP is selected, ask which Azure namespaces are relevant using `AskUserQuestion` (multi-select). Suggest namespaces based on the ticket context. Common namespaces:

- **monitor** — Azure Monitor logs and metrics
- **eventhubs** — EventHub management
- **storage** — Storage accounts
- **subscription** — Subscription listing
- **group** — Resource group listing
- **keyvault** — Key Vault secrets/keys
- **aks** — AKS cluster info
- **compute** — VMs, VMSS, disks
- **cosmos** — CosmosDB
- **postgres** — PostgreSQL
- **servicebus** — Service Bus
- **extension cli generate** — Generates `az` CLI commands; useful for topics Azure MCP doesn't cover natively (e.g. networking, vnet peering, VPN gateways, resource graph queries)

Full list available via: `npx -y @azure/mcp@latest tools list --namespace-mode --name-only`

Each selected namespace is added as a `--namespace` arg:
```json
{
  "Azure MCP Server": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@azure/mcp@latest", "server", "start", "--namespace", "monitor", "--namespace", "storage"]
  }
}
```

**Note:** Azure MCP has no networking/vnet/peering namespace. For network queries, use `az graph query` via Bash or include `extension cli generate` to help build the right `az` commands.

Combine selected into `{"mcpServers": { ... }}`.

### Step 6: Write task CLAUDE.md

Write `~/llm/stories/<task-id>/CLAUDE.md`:

```markdown
# <JIRA-KEY>: <Issue Summary>

## Goal
<Brief description from JIRA>

## Directories
<List each worktree subdirectory and what it's for>

## Progress
<!-- Keep this section updated as you work. The coordinator reads it via /ticket status. -->
- **Status**: Not started
- **Current focus**: —
- **Blockers**: None
- **Key decisions**: None yet

## Decisions
<Empty — fill in as you work>
```

**Important:** Instruct the ticket session to keep the `## Progress` section updated as it works. This section is read by `/ticket status` from the stories level to give the user an overview across all active tickets.

### Step 7: Summary

Print what was created: task folder path, worktrees, MCPs configured.
Suggest: `cd ~/llm/stories/<task-id> && claude`

---

## close

Clean up a task folder, remove worktrees, and capture learnings.

### Step 1: Inventory the task folder

List `~/llm/stories/<task-id>/`. For each git worktree subdirectory (has `.git` file, not directory), show:

| Worktree | Branch | Uncommitted | Unpushed |
|----------|--------|-------------|----------|


### Step 2: Handle dirty worktrees

For each worktree with uncommitted changes or unpushed commits, use `AskUserQuestion`:

- **Push and clean** — commit and push remaining work
- **Discard** — user confirms changes are not needed
- **Skip** — leave this worktree alone

### Step 3: Capture learnings

Use `AskUserQuestion`:

- **Yes, capture learnings** — ask what patterns/knowledge to save
- **No** — skip to cleanup

If yes, determine scope:
- Universal patterns → update relevant `~/.claude/rules/` file or `~/.claude/CLAUDE.md`
- Project-specific → update `~/.claude/projects/-home-mano-llm-stories/memory/`

### Step 4: Remove worktrees

For each worktree (not skipped), find the source repo by reading the `.git` file's `gitdir:` pointer, then:

```bash
# Extract source repo from the worktree's .git file
# The gitdir line points to <source-repo>/.git/worktrees/<name>
git -C <source-repo-path> worktree remove ~/llm/stories/<task-id>/<worktree-name>
```

Never use `cd` — always use `git -C`.

### Step 5: Confirm folder removal

Use `AskUserQuestion`:

- **Delete task folder** — remove `~/llm/stories/<task-id>/` entirely
- **Keep folder** — leave it (may have notes or non-git files)

If deleting, list any non-worktree files first and confirm before removing.

### Step 6: Summary

Print: worktrees removed, learnings captured, folder status.

---

## status

Overview of active task folders in `~/llm/stories/`.

List all directories matching `*-*` pattern. For each:
- Read `CLAUDE.md` and extract the `## Progress` section (status, current focus, blockers)
- Check worktree subdirectories for branch names and dirty state
- Note if `.mcp.json` exists

Present as a summary table:

| Ticket | Status | Current Focus | Blockers | Dirty Worktrees |
|--------|--------|---------------|----------|-----------------|

If a ticket has no `## Progress` section in its CLAUDE.md, show status as "Unknown (no progress tracking)".
