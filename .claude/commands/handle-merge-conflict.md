---
allowed-tools: Bash(git fetch:*), Bash(git merge:*), Bash(git rebase:*), Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git branch:*), Bash(git checkout:*), Bash(git add:*), Bash(git commit:*), Bash(git remote:*), Bash(git rev-parse:*), Bash(git stash:*), Bash(make:*), Read, Edit, Grep, Glob
description: Handle merge conflicts by merging from origin main (with rebase fallback) and running verification
---

## Pre-computed Context

- Current branch: !`git branch --show-current`
- Default branch: !`git remote show origin | grep 'HEAD branch' | cut -d' ' -f5`
- Fetch status: !`git fetch origin 2>&1`
- Commits behind default: !`git rev-list --count HEAD..origin/$(git remote show origin | grep 'HEAD branch' | cut -d' ' -f5) 2>/dev/null || echo "0"`
- Commits ahead of default: !`git rev-list --count origin/$(git remote show origin | grep 'HEAD branch' | cut -d' ' -f5)..HEAD 2>/dev/null || echo "0"`
- Files changed on default branch: !`git diff --name-only HEAD...origin/$(git remote show origin | grep 'HEAD branch' | cut -d' ' -f5) 2>/dev/null || echo "none"`
- Local uncommitted changes: !`git status --short`
- Available make targets: !`make -qp 2>/dev/null | awk -F':' '/^[a-zA-Z0-9][^$#\/\t=]*:([^=]|$)/ {split($1,A,/ /);print A[1]}' | sort -u | head -20 || echo "no makefile"`

## Your Task

Based on the context above:

1. **Check prerequisites**
   - If there are uncommitted changes, stash them with `git stash push -m "auto-stash before merge"`
   - If current branch is the default branch, report that no merge is needed

2. **Attempt merge first**
   - Run `git merge origin/{default-branch}`
   - If merge completes cleanly, proceed to step 5 (verification)

3. **Handle merge conflicts** (if merge has conflicts)
   - List conflicting files with `git status`
   - For each conflicting file:
     - Read the file to understand both versions
     - Analyze the conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
     - Resolve intelligently: preserve functionality from both sides where possible
     - Remove all conflict markers
     - Stage resolved file with `git add {file}`
   - Complete merge with `git commit` (use default merge message)

4. **Fallback to rebase** (only if merge fails catastrophically)
   - Abort the failed merge: `git merge --abort`
   - Attempt rebase: `git rebase origin/{default-branch}`
   - Handle conflicts during rebase similarly to step 3
   - After each file resolution, run `git add {file}` then `git rebase --continue`

5. **Run verification**
   - Check available make targets from pre-computed context
   - Run `make test` if available
   - Run `make lint` if available
   - Run `make type-check` if available
   - Report any failures - do NOT automatically fix them

6. **Restore and report**
   - If changes were stashed in step 1, run `git stash pop`
   - Show summary: `git log --oneline -5`
   - Report final status and any verification failures
