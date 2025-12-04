#!/bin/bash
# Script to create a new clean branch without secrets in history

echo "🔧 Creating a clean branch for merging with main..."
echo ""

# Step 1: Make sure all current changes are committed
echo "Step 1: Checking git status..."
git status

read -p "Are all your changes committed? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "⚠️  Please commit or stash your changes first!"
    echo "   git add ."
    echo "   git commit -m 'Your commit message'"
    exit 1
fi

# Step 2: Get the current branch name
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

# Step 3: Fetch latest main
echo ""
echo "Step 2: Fetching latest main..."
git fetch origin main

# Step 4: Create new branch from main
NEW_BRANCH_NAME="feature/ui-updates-clean"
echo ""
echo "Step 3: Creating new branch '$NEW_BRANCH_NAME' from main..."
git checkout -b $NEW_BRANCH_NAME origin/main 2>/dev/null || git checkout -b $NEW_BRANCH_NAME main

# Step 5: Cherry-pick or merge changes from current branch (without the secret commit)
echo ""
echo "Step 4: Applying changes from $CURRENT_BRANCH (excluding secret commits)..."
echo "Finding commits to apply..."

# Get list of commits from current branch that aren't in main
COMMITS=$(git log origin/main..$CURRENT_BRANCH --oneline --reverse | grep -v "secret\|Secret\|SECRET\|OAuth\|oauth" | awk '{print $1}')

if [ -z "$COMMITS" ]; then
    echo "No commits found. Trying to apply all changes as a single commit..."
    git checkout $CURRENT_BRANCH
    git diff origin/main...HEAD > /tmp/changes.patch
    git checkout $NEW_BRANCH_NAME
    git apply /tmp/changes.patch
    git add .
    git commit -m "Add UI updates and comprehensive test coverage"
else
    echo "Applying commits: $COMMITS"
    for commit in $COMMITS; do
        echo "  Applying commit: $commit"
        git cherry-pick $commit 2>/dev/null || echo "    (Skipped - may contain secrets or conflicts)"
    done
fi

echo ""
echo "✅ New clean branch '$NEW_BRANCH_NAME' created!"
echo ""
echo "Next steps:"
echo "1. Review the changes: git log"
echo "2. Push the new branch: git push origin $NEW_BRANCH_NAME"
echo "3. Create a pull request from $NEW_BRANCH_NAME to main"
echo ""
echo "To switch back to your old branch: git checkout $CURRENT_BRANCH"

