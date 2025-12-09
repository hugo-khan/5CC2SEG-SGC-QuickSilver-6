# How to Pull from Main

## Basic Pull (if you're on main branch)

```bash
# Make sure you're on main branch
git checkout main

# Pull latest changes
git pull origin main
```

## Pull into Current Branch

If you're on a different branch (like `UpdatingUI`) and want to get the latest changes from main:

```bash
# Option 1: Merge main into your current branch
git fetch origin main
git merge origin/main

# Option 2: Rebase your branch on top of main (cleaner history)
git fetch origin main
git rebase origin/main
```

## Step-by-Step for Your Situation

Since you're working on `UpdatingUI` branch and want to sync with main:

```bash
# 1. Make sure your current changes are committed or stashed
git status

# If you have uncommitted changes, either:
# Option A: Commit them
git add .
git commit -m "Your commit message"

# Option B: Stash them temporarily
git stash

# 2. Fetch the latest from remote
git fetch origin main

# 3. Merge main into your current branch
git merge origin/main

# If you stashed changes, restore them:
git stash pop
```

## If You Get Conflicts

If there are merge conflicts:

```bash
# 1. See which files have conflicts
git status

# 2. Open the conflicted files and resolve them
# Look for <<<<<<< HEAD markers

# 3. After resolving, mark as resolved
git add <resolved-file>

# 4. Complete the merge
git commit
```

## Alternative: Rebase (Recommended for cleaner history)

```bash
# 1. Fetch latest main
git fetch origin main

# 2. Rebase your branch on top of main
git rebase origin/main

# If conflicts occur, resolve them and continue:
git add <resolved-files>
git rebase --continue
```

