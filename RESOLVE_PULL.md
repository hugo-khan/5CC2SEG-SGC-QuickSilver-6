# Resolve Pull Issue - Step by Step

## Quick Fix (Recommended)

```bash
# 1. Make sure all your changes are committed
git status
# If you have uncommitted changes:
git add .
git commit -m "Save current work"

# 2. Pull from main using merge
git pull origin main --no-rebase
```

## If You Get Merge Conflicts

```bash
# 1. See which files have conflicts
git status

# 2. Open conflicted files and look for:
# <<<<<<< HEAD
# (your changes)
# (main's changes separator)
# (main's changes)
# >>>>>>> origin/main

# 3. Edit the files to resolve conflicts (keep what you need)

# 4. Mark conflicts as resolved
git add <resolved-file>

# 5. Complete the merge
git commit
```

## Alternative: Rebase (Cleaner History)

```bash
# 1. Commit your changes first
git add .
git commit -m "Save current work"

# 2. Rebase on main
git pull origin main --rebase

# If conflicts during rebase:
# - Resolve them
# - git add <file>
# - git rebase --continue
```

## If You Want to See What's Different First

```bash
# See what's in main that you don't have
git log HEAD..origin/main --oneline

# See what you have that main doesn't
git log origin/main..HEAD --oneline
```

