---
name: multi-repo
description: Applies the same change across multiple repositories with a pilot-first workflow. Use when rolling out kustomize components, config changes, or patches across deploy or app repos.
argument-hint: "PLAT-1234-description"
user-invocable: true
---

# Multi-Repo Change

Apply a change across multiple repositories using a pilot-then-bulk workflow. The argument is used for branch naming across all repos.

Branch name: `$ARGUMENTS` (e.g. `PLAT-974-spot-affinity`)

---

## Step 1: Define the change

Use `AskUserQuestion`:

- **Reference an existing change** — user points to a file, diff, or existing branch/repo where the change is already done
- **Describe a new change** — user describes what needs to be added/modified

If referencing an existing change, read it and confirm understanding with the user before proceeding.

If describing a new change, draft it and show the user for approval before applying anywhere.

## Step 2: Discover target repos

Use `AskUserQuestion`:

- **All deploy repos** — scan `/home/mano/llm/platform/deployments/` for all repos
- **All app repos** — scan `/home/mano/llm/platform/apps/` for all repos
- **Specific repos** — user lists which ones

If scanning, list discovered repos and let the user confirm or exclude any.

## Step 3: Pilot — apply to one repo first

Use `AskUserQuestion` to let user pick which repo to pilot with.

In the pilot repo:
1. Create branch: `git checkout -b $ARGUMENTS`
2. Apply the change
3. Show the diff to the user
4. Wait for explicit approval before committing

If the user wants adjustments, iterate on the change in the pilot repo until approved.

Once approved:
1. Commit and push
2. Create PR using `gh pr create`
3. Present the PR URL

**Stop here and wait.** Tell the user:
> Pilot PR created. Review it, then tell me to proceed with the remaining repos when ready.

## Step 4: Bulk — apply to remaining repos

Only proceed when the user explicitly says to continue.

For each remaining repo:
1. Create branch: `git checkout -b $ARGUMENTS`
2. Apply the same change (use the approved version from the pilot)
3. Commit and push
4. Create PR using `gh pr create`

Present a summary table as you go:

| Repo | Branch | PR | Status |
|------|--------|----|--------|

## Step 5: Summary

Print final table of all repos, branches, and PR URLs.

---

## Notes

- Work directly in the source repos under `/home/mano/llm/platform/deployments/` or `/home/mano/llm/platform/apps/` — no worktrees needed for bulk changes
- If a repo already has the branch, warn the user and ask how to proceed
- If a change fails to apply cleanly in a repo, skip it, note the failure, and continue with the rest
