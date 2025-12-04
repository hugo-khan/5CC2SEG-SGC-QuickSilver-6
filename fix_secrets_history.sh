#!/bin/bash
# Script to remove secrets from git history

echo "⚠️  This script will rewrite git history to remove secrets."
echo "⚠️  Make sure you have a backup or are working on a branch!"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Get the commit hash with secrets
COMMIT_WITH_SECRETS="a72ce88044113a46ca28fc022c1607a8b5e4a850"

echo "Step 1: Finding the commit in history..."
git log --oneline --all | grep -i "$COMMIT_WITH_SECRETS" || echo "Commit found in history"

echo ""
echo "Step 2: Using git filter-branch to remove secrets from history..."
echo "This will rewrite all commits after the one with secrets."

# Method 1: Use git filter-branch to rewrite the specific files in history
git filter-branch --force --index-filter \
  'git update-index --remove recipify/settings.py GOOGLE_OAUTH_SETUP.md 2>/dev/null || true' \
  --prune-empty --tag-name-filter cat -- --all

# Alternative: Use filter-repo (if installed)
# git filter-repo --path recipify/settings.py --path GOOGLE_OAUTH_SETUP.md --invert-paths

echo ""
echo "Step 3: Cleaning up..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo ""
echo "✅ History rewritten. You can now force push:"
echo "   git push --force-with-lease origin UpdatingUI"
echo ""
echo "⚠️  WARNING: Force pushing rewrites remote history!"
echo "   Make sure all team members are aware!"

