# GitHub Repo Rename Instructions

## Step 1: Rename on GitHub

1. Go to your repo: https://github.com/jsnhff/gmail-ai-unsubscriber
2. Click **Settings** (top right)
3. Scroll down to **Repository name**
4. Change from `gmail-ai-unsubscriber` to `no-thanks`
5. Click **Rename**

GitHub will automatically set up redirects from the old URL to the new one.

## Step 2: Update Your Local Repo

```bash
# Update your remote URL
git remote set-url origin https://github.com/jsnhff/no-thanks.git

# Verify it worked
git remote -v
```

## Step 3: Commit and Push the Name Changes

```bash
# Stage all the changes we made
git add -A

# Commit
git commit -m "Rename to 'No Thanks' - what you actually say to people trying to sell you crap

- New name: No Thanks (from Gmail AI Unsubscriber)
- Updated ASCII banner
- Updated all references in code and docs
- Updated class names and messages
- README reflects new name and tagline

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to the renamed repo
git push origin main
```

## Step 4: Update Releases (Optional)

Since you already have v1.0.0 and v1.0.1 releases, you might want to:

1. Go to Releases on GitHub
2. Edit each release to mention the repo rename
3. Or just leave them as-is - they'll still work with the redirect

## Step 5: Update Any External Links

If you've shared the old URL anywhere:
- LinkedIn posts
- Twitter/X
- Documentation
- Blog posts

GitHub's redirect will handle them, but it's good to update them when you can.

## That's It!

The repo is now officially "No Thanks" 🎉
