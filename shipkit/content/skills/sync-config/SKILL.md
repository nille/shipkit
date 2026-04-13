# Sync Config

**Trigger:** User says "sync config", "push config", "backup shipkit", "commit shipkit config", or similar

**Purpose:** Version and push personal shipkit content (~/.config/shipkit/) to a git remote for backup and cross-machine sync.

## Prerequisites Check

Before starting, verify:
- `~/.config/shipkit/` exists
- User wants to version their personal content (skills, steering, learned preferences)

## Process

### 1. Check Git Status

```bash
cd ~/.config/shipkit

# Check if it's a git repo
if [ ! -d .git ]; then
    echo "~/.config/shipkit/ is not a git repository yet."
    # Offer to initialize (see step 2)
else
    git status
fi
```

### 2. Initialize Git if Needed

If not yet a git repo, offer to initialize:

**Ask the user:**
```
~/.config/shipkit/ is not a git repository yet.

Want me to initialize it so you can version your personal content?
  - skills/
  - steering/ (including auto-learned.md)
  - config.yaml, mcp.json
  - templates/

Will exclude: .state/, plugins/, projects/

Initialize git? (y/n)
```

If yes:
```bash
cd ~/.config/shipkit
git init
echo "✓ Git repository initialized"
```

The `.gitignore` should already exist (created during `shipkit init`). Verify it's there and excludes `.state/`, `plugins/`, `projects/`.

If no:
```
Okay, skipping. To version your config later:
  cd ~/.config/shipkit && git init
```

Exit if user declines.

### 3. Stage Changes

```bash
cd ~/.config/shipkit

# Show what's changed
git status --short

# Stage versionable content
git add skills/ steering/ config.yaml mcp.json templates/ .gitignore 2>/dev/null || true
```

### 4. Check if There Are Changes

```bash
if git diff --staged --quiet; then
    echo "No changes to commit. Config is up to date."
    exit 0
fi
```

### 5. Create Commit

Generate a meaningful commit message based on what changed:

```bash
# Get summary of changes
summary=$(git diff --staged --stat | tail -1)

git commit -m "Update shipkit config

$(git diff --staged --name-only | head -10)

$summary
"
```

### 6. Set Up Remote if Needed

Check if remote is configured:
```bash
if ! git remote get-url origin &>/dev/null; then
    # No remote configured
fi
```

**Ask the user:**
```
No git remote configured. Want me to create a private GitHub repo for you?

Option 1: Auto-create (requires gh CLI)
  - I'll run: gh repo create shipkit-config --private --source=.
  - Sets up remote automatically
  
Option 2: Manual setup
  - You create the repo on GitHub
  - Add remote: git remote add origin git@github.com:you/repo.git
  - Run /sync-config again

Choose: auto / manual / skip
```

**If auto:**
```bash
# Check gh CLI is available
if ! command -v gh &>/dev/null; then
    echo "Error: gh CLI not found. Install from https://cli.github.com"
    echo "Or choose 'manual' to set up remote yourself."
    exit 1
fi

# Check gh auth
if ! gh auth status &>/dev/null; then
    echo "Error: gh CLI not authenticated. Run: gh auth login"
    exit 1
fi

# Create private repo and set up remote
cd ~/.config/shipkit
gh repo create shipkit-config --private --source=. --remote=origin

echo "✓ Created private repo and configured remote"
```

**If manual:**
```
Create a private GitHub repo: https://github.com/new

Then add the remote:
  cd ~/.config/shipkit
  git remote add origin git@github.com:YOU/REPO.git
  
Run /sync-config again when ready.
```

**If skip:**
```
Okay, config committed locally but not pushed.
To add remote later: git remote add origin <url>
```

Exit if user chooses manual or skip.

### 7. Push to Remote

```bash
# Get current branch
branch=$(git branch --show-current)

# Push
git push -u origin "$branch"

echo "✓ Config backed up to remote"
echo "✓ Branch: $branch"
```

### 8. Summary

Tell the user:
- ✅ Config committed and pushed
- Remote URL: `git remote get-url origin`
- To restore on another machine: `git clone <url> ~/.config/shipkit`

## Error Handling

**Not a git repo and user doesn't want to initialize:**
```
Okay, skipping. Your config is not being versioned.
To version later, run: cd ~/.config/shipkit && git init
```

**No changes to commit:**
```
No changes to commit. Your config is up to date.
Last commit: <commit message>
```

**Remote not configured:**
```
No git remote configured. Create a private GitHub repo and add it:
  git remote add origin git@github.com:you/my-shipkit-config.git
```

**Push fails (auth issue):**
```
Failed to push. Check your git authentication:
  gh auth refresh
  ssh -T git@github.com
```

## Example Interaction

```
User: sync my config