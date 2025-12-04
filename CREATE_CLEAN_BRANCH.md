# Create Clean Branch for Merging with Main

This guide helps you create a new branch without secrets in the commit history, so you can merge with main.

## Option 1: Simple Approach (Recommended)

Create a new branch from main and apply all current changes as a single commit:

```bash
# 1. Make sure all changes are committed
git add .
git commit -m "Add UI updates, test coverage, and remove hardcoded secrets"

# 2. Fetch latest main
git fetch origin main

# 3. Create new branch from main
git checkout -b feature/ui-updates-clean origin/main

# 4. Apply all changes from your current branch
git checkout UpdatingUI -- .
git add .
git commit -m "Add UI updates, comprehensive test coverage, and security improvements

- Added 1,046+ lines of test coverage
- Improved UI with modern design
- Removed hardcoded secrets, using environment variables
- Added recipe sharing, delete, and search features
- Fixed OAuth account deletion handling"

# 5. Push the new branch
git push origin feature/ui-updates-clean

# 6. Create pull request from feature/ui-updates-clean to main
```

## Option 2: Using the Script

```bash
chmod +x create_clean_branch.sh
./create_clean_branch.sh
```

## Option 3: Manual Cherry-Pick (Selective)

If you want to be more selective about which commits to include:

```bash
# 1. Create new branch from main
git fetch origin main
git checkout -b feature/ui-updates-clean origin/main

# 2. See commits in your current branch
git log origin/main..UpdatingUI --oneline

# 3. Cherry-pick specific commits (avoid the one with secrets: a72ce88)
git cherry-pick <commit-hash-1> <commit-hash-2> ...

# 4. Push
git push origin feature/ui-updates-clean
```

## Option 4: Fresh Start (Orphan Branch)

Create a completely new branch with no history:

```bash
# 1. Create orphan branch (no parent)
git checkout --orphan feature/ui-updates-clean

# 2. Remove all files (they'll be re-added)
git rm -rf .

# 3. Copy files from your current branch
git checkout UpdatingUI -- .

# 4. Add and commit everything
git add .
git commit -m "Add UI updates, test coverage, and security improvements"

# 5. Push (force push needed for orphan branch)
git push origin feature/ui-updates-clean
```

## Verify No Secrets

Before pushing, verify no secrets are in the code:

```bash
# Check for exposed secrets
grep -r "374477879508-imqs4bh9ec6rqvh3eusmnp0sbof4jvko" . --exclude-dir=venv --exclude-dir=.git
grep -r "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" . --exclude-dir=venv --exclude-dir=.git

# Should return no results (or only in .env which is gitignored)
```

## Recommended: Option 1

Option 1 is the simplest and safest. It creates a clean branch with all your changes in a single commit, avoiding any secret history.

