---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*), Bash(git push:*), Bash(git diff:*), Bash(git log:*), Bash(git branch:*), Bash(git rev-parse:*), Bash(gh pr:*)
description: Commit staged changes, push to remote, and create a PR
---

## Pre-computed Context

- Current branch: !`git branch --show-current`
- Default branch: !`git remote show origin | grep 'HEAD branch' | cut -d' ' -f5`
- Git status: !`git status --short`
- Staged changes: !`git diff --cached --stat`
- Unstaged changes: !`git diff --stat`
- Recent commits on this branch: !`git log --oneline -5`
- Commits ahead of origin: !`git log --oneline @{upstream}..HEAD 2>/dev/null || echo "(no upstream set)"`

## Your Task

Based on the context above:

1. **Stage changes** (if needed): Add any relevant untracked/modified files
2. **Create a commit**: Write a clear, concise commit message based on the changes
3. **Push to remote**: Push the current branch (set upstream if needed)
4. **Create a PR**: Use `gh pr create` with:
   - A descriptive title summarizing the changes
   - A body with a brief summary and test plan
   - Target the default branch

If a PR already exists for this branch, skip PR creation and report the existing PR URL.

End the commit message with:
Co-Authored-By: Claude <noreply@anthropic.com>
