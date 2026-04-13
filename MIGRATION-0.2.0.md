# Migration Guide: v0.1.0 → v0.2.0

## Breaking Change: "steering" → "guidelines"

Shipkit has renamed "steering rules" to "guidelines" throughout the codebase and documentation.

### What Changed

**Directory names:**
- `~/.config/shipkit/steering/` → `~/.config/shipkit/guidelines/`
- `~/.config/shipkit/projects/<name>/steering/` → `.../guidelines/`
- `shipkit/content/steering/` → `shipkit/content/guidelines/`

**Code references:**
- `steering_layers` → `guidelines_layers`
- `package_steering` → `package_guidelines`
- All internal references updated

**Documentation:**
- "Steering Rules" → "Guidelines"
- All examples updated

### Migration Steps

**Option 1: Automatic (Recommended)**

Run the migration helper:

```bash
python3 -c "
import shutil
from pathlib import Path

shipkit_home = Path.home() / '.config/shipkit'

# Rename user global
old_dir = shipkit_home / 'steering'
new_dir = shipkit_home / 'guidelines'
if old_dir.exists() and not new_dir.exists():
    shutil.move(str(old_dir), str(new_dir))
    print(f'✓ Renamed {old_dir} → {new_dir}')

# Rename project-specific
projects_dir = shipkit_home / 'projects'
if projects_dir.exists():
    for project_dir in projects_dir.iterdir():
        old_proj = project_dir / 'steering'
        new_proj = project_dir / 'guidelines'
        if old_proj.exists() and not new_proj.exists():
            shutil.move(str(old_proj), str(new_proj))
            print(f'✓ Renamed {old_proj} → {new_proj}')

print('Migration complete!')
"
```

**Option 2: Manual**

```bash
# Rename user global
mv ~/.config/shipkit/steering ~/.config/shipkit/guidelines

# Rename project-specific (for each project)
mv ~/.config/shipkit/projects/my-project/steering ~/.config/shipkit/projects/my-project/guidelines
```

**Option 3: Start Fresh**

If you haven't customized steering rules:

```bash
rm -rf ~/.config/shipkit/steering
shipkit sync  # Will create guidelines/ with core rules
```

### If You Have Versioned Config

If you're versioning `~/.config/shipkit/` in git:

```bash
cd ~/.config/shipkit
git mv steering guidelines
git commit -m "Rename steering to guidelines (shipkit v0.2.0)"
git push
```

### Verify Migration

```bash
ls -la ~/.config/shipkit/guidelines/
# Should see your custom guideline files

shipkit sync
# Should compile without errors
```

### Backward Compatibility

Shipkit v0.2.0 **does not** read from `steering/` directories. You must migrate to `guidelines/`.

### Rollback

If you need to rollback to v0.1.x:

```bash
pip install shipkit==0.1.0
mv ~/.config/shipkit/guidelines ~/.config/shipkit/steering
```
