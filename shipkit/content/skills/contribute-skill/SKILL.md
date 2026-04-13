# Contribute Skill to Marketplace

**Trigger:** User wants to publish/contribute a local skill to the marketplace, or says "contribute skill", "publish skill", "submit to marketplace"

**Purpose:** Convert a local skill into a plugin and submit a PR to the shipkit-marketplace repository.

## Prerequisites Check

Before starting, verify:
- `gh` CLI is installed and authenticated: `gh auth status`
- User has a skill in `~/.config/shipkit/skills/<name>/` they want to contribute
- The skill has a `SKILL.md` file

If `gh` is not installed or authenticated:
```bash
# Check status
gh auth status

# If not authenticated
gh auth login
```

## Process

### 1. Identify the Skill

List available local skills:
```bash
ls -1 ~/.config/shipkit/skills/
```

Ask the user which skill they want to contribute and verify it exists.

### 2. Gather Plugin Metadata

Ask the user for:
- **Plugin name** (default: same as skill name, suggest kebab-case)
- **Description** (one-line summary of what the skill does - read from SKILL.md if available)
- **Author** (default: fetch from `gh api user -q .login`)
- **Version** (default: `1.0.0`)

### 3. Create Plugin Structure

Create a temporary directory with the plugin structure:

```bash
tmpdir=$(mktemp -d)
plugin_dir="$tmpdir/<plugin-name>"
mkdir -p "$plugin_dir/skills"

# Copy the skill
cp -r ~/.config/shipkit/skills/<skill-name> "$plugin_dir/skills/"
```

Create `$plugin_dir/plugin.yaml`:
```yaml
name: <plugin-name>
description: <description>
author: <author>
version: <version>
```

Create `$plugin_dir/README.md`:
````markdown
# <Plugin Name>

<description>

## Installation

```bash
shipkit plugin install <plugin-name>
```

## What's included

- **/<skill-name>** - <brief description from SKILL.md>

## Usage

After installation, run `shipkit sync` then use the skill:

```
> /<skill-name>
```

<Add any usage notes or examples>

## Author

@<author>
````

### 4. Select Target Registry

Read configured registries from `~/.config/shipkit/config.yaml`:

```bash
# Read plugin_registries from config.yaml
registries=$(python3 -c "import yaml; print('\n'.join(yaml.safe_load(open('$HOME/.config/shipkit/config.yaml')).get('plugin_registries', ['github.com/nille/shipkit-marketplace'])))")
```

**If multiple registries configured, ask user:**
```
Which marketplace should I contribute to?

1. github.com/nille/shipkit-marketplace (public)
2. github.com/yourcompany/private-plugins (private)

Choose (1-2): 
```

**If only one registry:**
- Use it automatically
- Show: "Contributing to: <registry>"

Store the selected registry as `$target_registry` (e.g., "github.com/nille/shipkit-marketplace")

Extract owner/repo from registry:
```bash
# Parse "github.com/owner/repo" to "owner/repo"
repo_path=$(echo "$target_registry" | sed 's|github.com/||')
```

### 5. Fork and Clone Marketplace

```bash
# Get username
username=$(gh api user -q .login)

# Fork if not already forked
gh repo fork "$repo_path" --clone=false 2>/dev/null || echo "Fork already exists"

# Clone the fork
cd "$tmpdir"
gh repo clone "$username/$(basename $repo_path)" marketplace
cd marketplace
```

### 6. Create Branch and Add Plugin

```bash
# Create branch
git checkout -b add-<plugin-name>

# Copy plugin
cp -r "$plugin_dir" ./<plugin-name>

# Stage and commit
git add <plugin-name>/
git commit -m "Add <plugin-name> plugin

<description>

Includes:
- <skill-name> skill
"

# Push
git push -u origin add-<plugin-name>
```

### 7. Create Pull Request

```bash
gh pr create \
  --repo "$repo_path" \
  --title "Add <plugin-name> plugin" \
  --body "## Plugin: <plugin-name>

<description>

## What's included

- **/<skill-name>** skill

## Author

@<author>

## Checklist

- [x] Plugin has plugin.yaml manifest
- [x] Plugin has README.md with usage instructions  
- [x] Skills follow shipkit conventions
- [ ] Tested installation with \`shipkit plugin install <plugin-name>\`
"
```

### 8. Report Results

Tell the user:

1. **PR created**: <pr-url>
2. **Test your plugin** (before it's merged):
   ```bash
   shipkit plugin install https://github.com/<username>/shipkit-marketplace/<plugin-name>
   shipkit sync
   ```
3. **Next steps**:
   - Maintainers will review the PR
   - Once merged, anyone can install with: `shipkit plugin install <plugin-name>`

### 9. Cleanup

```bash
rm -rf "$tmpdir"
```

## Error Handling

**gh not installed or not authenticated:**
```
Error: GitHub CLI (gh) is required but not found or not authenticated.

Install: https://cli.github.com
Authenticate: gh auth login
```

**Skill not found:**
```
Skill '<skill-name>' not found in ~/.config/shipkit/skills/

Available skills:
<list available skills>
```

**Fork fails (network error):**
```
Failed to fork repository. Check your network connection and GitHub authentication.
Try: gh auth refresh
```

**Push fails (auth error):**
```
Failed to push to your fork. Check git authentication.
Try: gh auth refresh
```

## Example Interaction

```
User: contribute my deploy skill to the marketplace