# Quick Fix: Remove Secrets from Git History

GitHub is blocking the push because secrets are in commit `a72ce88044113a46ca28fc022c1607a8b5e4a850`.

## Option 1: Interactive Rebase (Recommended - if commit is recent)

If the commit with secrets is one of the last few commits:

```bash
# Find how many commits back the secret commit is
git log --oneline | grep -n "a72ce88"

# Start interactive rebase (replace N with the number from above)
git rebase -i HEAD~N

# In the editor, change 'pick' to 'edit' for the commit with secrets
# Save and close

# The commit will be checked out, now fix the files
# (Files are already fixed, so just amend)
git add recipify/settings.py GOOGLE_OAUTH_SETUP.md
git commit --amend --no-edit
git rebase --continue

# Force push
git push --force-with-lease origin UpdatingUI
```

## Option 2: Filter-Branch (For any commit in history)

```bash
# Rewrite history to remove secrets from those files
git filter-branch --force --index-filter \
  'git update-index --remove recipify/settings.py GOOGLE_OAUTH_SETUP.md 2>/dev/null || true' \
  --prune-empty --tag-name-filter cat -- --all

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push --force-with-lease origin UpdatingUI
```

## Option 3: Create New Branch (Easiest - if you can start fresh)

If you can afford to lose the commit history:

```bash
# Create a new branch from current state (without the secrets)
git checkout -b UpdatingUI-clean
git push origin UpdatingUI-clean

# Then delete the old branch and rename
git push origin --delete UpdatingUI
git branch -m UpdatingUI-clean UpdatingUI
git push origin UpdatingUI
```

## Option 4: Use GitHub's Secret Scanning Override (Temporary)

If you need to push immediately and will fix history later:

1. Visit the URLs provided in the error:
   - https://github.com/hugo-khan/5CC2SEG-SGC-QuickSilver-6/security/secret-scanning/unblock-secret/36MJgPHUvR1rzoUSFZcwZCOcrgx
   - https://github.com/hugo-khan/5CC2SEG-SGC-QuickSilver-6/security/secret-scanning/unblock-secret/36MJgQBY84TZjuWHgetZ2VRLAES

2. Click "Allow secret" (not recommended for production secrets)

3. Push normally

**⚠️ IMPORTANT**: After allowing, you MUST still remove secrets from history and rotate them!

## Recommended: Rotate Secrets

Since the secrets are exposed in git history, **rotate them immediately**:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Delete the old OAuth 2.0 Client ID
3. Create a new one
4. Update your `.env` file with new credentials

