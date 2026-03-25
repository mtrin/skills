#!/bin/bash
# Add a repo to a ticket working directory.
# Usage: setup-repo.sh <ticket-dir> <name> <url> <branch> [--source <source-branch>]
# Ensures bare clone, creates worktree, sets remote+upstream, updates manifest.
set -eo pipefail

CLONES="$HOME/clones"
HOOKS="$HOME/workspace/.hooks"

ticket_dir="$1" name="$2" url="$3" branch="$4"
shift 4 || { echo "Usage: setup-repo.sh <ticket-dir> <name> <url> <branch> [--source <source-branch>]"; exit 1; }

source_branch=""
if [ "$1" = "--source" ] && [ -n "$2" ]; then
    source_branch="$2"
fi

[ -d "$ticket_dir" ] || { echo "Ticket dir does not exist: $ticket_dir"; exit 1; }

MANIFEST="$ticket_dir/manifest.yaml"
cache="$CLONES/$name.git"
dir="$ticket_dir/$name"

# Track what this run creates for cleanup on failure
created_cache=false
created_worktree=false

cleanup() {
    if [ $? -ne 0 ]; then
        echo "  Cleaning up after failure..."
        if $created_worktree && [ -d "$dir" ]; then
            git -C "$cache" worktree remove "$dir" 2>/dev/null || true
        fi
        if $created_cache && [ -d "$cache" ]; then
            rm -rf "$cache"
        fi
    fi
}
trap cleanup EXIT

# --- Phase 1: Ensure bare clone ---

if [ ! -d "$cache" ]; then
    echo "  Cloning $name (first time)..."
    git clone --bare "$url" "$cache"
    created_cache=true
fi

# Ensure bare clone remote matches the URL we were given (fixes HTTPS→SSH migration)
current_url=$(git -C "$cache" remote get-url origin 2>/dev/null)
if [ "$current_url" != "$url" ]; then
    git -C "$cache" remote set-url origin "$url"
fi

# Ensure fetch refspec exists (bare clones from git clone --bare don't have one)
if ! git -C "$cache" config remote.origin.fetch >/dev/null 2>&1; then
    git -C "$cache" config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
fi

# --- Phase 2: Fetch and discover remote state ---

echo "  Fetching $name..."
fetch_output=$(timeout 15 git -C "$cache" fetch origin 2>&1) || {
    if echo "$fetch_output" | grep -q "oauth2/authorize\|authentication\|login"; then
        auth_url=$(echo "$fetch_output" | grep -oE 'https://[^ ]+')
        printf '\e]8;;%s\e\\Click to authenticate\e]8;;\e\\\n' "$auth_url"
        echo "  AUTH_URL=$auth_url"
        exit 2
    fi
    echo "  ERROR: fetch failed for $name (timeout or network issue)"
    echo "$fetch_output"
    exit 1
}

# Discover: does the target branch exist?
branch_ref=""
if git -C "$cache" rev-parse --verify "$branch" >/dev/null 2>&1; then
    branch_ref="$branch"
elif git -C "$cache" rev-parse --verify "origin/$branch" >/dev/null 2>&1; then
    branch_ref="origin/$branch"
fi

# Discover: does the source branch exist?
source_ref=""
if [ -n "$source_branch" ]; then
    if git -C "$cache" rev-parse --verify "$source_branch" >/dev/null 2>&1; then
        source_ref="$source_branch"
    elif git -C "$cache" rev-parse --verify "origin/$source_branch" >/dev/null 2>&1; then
        source_ref="origin/$source_branch"
    fi
fi

# --- Phase 3: Remove stale worktree if exists ---

if [ -d "$dir" ]; then
    if ! git -C "$cache" worktree remove "$dir" 2>&1; then
        echo "  ERROR: could not remove worktree at $dir (dirty or locked?)"
        exit 1
    fi
fi

# --- Phase 4: Create worktree ---

if [ -n "$branch_ref" ]; then
    # Branch exists — check it out
    git -C "$cache" worktree add "$dir" "$branch" 2>&1
    echo "  $name → $branch (existing)"
elif [ -n "$source_ref" ]; then
    # Branch doesn't exist — create from source
    git -C "$cache" worktree add -b "$branch" "$dir" "$source_ref" 2>&1
    echo "  $name → $branch (new from $source_ref)"
else
    echo "  ERROR: neither branch '$branch' nor source '${source_branch:-<none>}' found"
    echo "  Available branches:"
    git -C "$cache" branch -a 2>&1 | head -20
    exit 1
fi
created_worktree=true

# --- Phase 5: Configure worktree ---

# Shared hooks
git -C "$dir" config core.hooksPath "$HOOKS"

# Set remote URL directly on worktree (independent of bare clone for push)
if ! git -C "$dir" remote set-url origin "$url" 2>/dev/null; then
    git -C "$dir" remote add origin "$url"
fi

# Fetch in worktree to populate origin/* refs for tracking
git -C "$dir" fetch origin 2>&1 || echo "  WARNING: worktree fetch failed"

# Push config: always push to same-named remote branch (handles new branches)
git -C "$dir" config push.default current

# Set upstream tracking if remote branch exists, otherwise unset any inherited upstream
if git -C "$dir" rev-parse --verify "origin/$branch" >/dev/null 2>&1; then
    git -C "$dir" branch --set-upstream-to="origin/$branch" 2>&1 || true
else
    git -C "$dir" branch --unset-upstream 2>/dev/null || true
fi

# --- Phase 6: Update manifest (last — only on full success) ---

if [ ! -f "$MANIFEST" ]; then
    echo "repos: {}" > "$MANIFEST"
fi
yq -i ".repos[\"$name\"].url = \"$url\" | .repos[\"$name\"].branch = \"$branch\"" "$MANIFEST"
if [ -n "$source_branch" ]; then
    yq -i ".repos[\"$name\"].source = \"$source_branch\"" "$MANIFEST"
fi

echo "  OK: $name → $branch"
