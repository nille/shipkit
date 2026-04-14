"""Shipkit CLI — built with Click."""

from __future__ import annotations

from pathlib import Path

import click

from shipkit import __version__


@click.group()
@click.version_option(__version__, prog_name="shipkit")
def main():
    """Shipkit — Production-grade Claude Code setup. Stop configuring, start shipping."""


# --- init command ---

@main.command()
def install():
    """Install Shipkit into your Claude Code setup (interactive).

    Copies package core to ~/.config/shipkit/ and creates symlinks to ~/.claude/
    Then launches an intelligent installer agent that configures everything.

    Safe for existing setups - your personal skills/guidelines/hooks are preserved.
    """
    import subprocess
    import shutil
    from shipkit.datadir import ensure_home
    from shipkit.config import CLAUDE_HOME, SHIPKIT_HOME
    from shipkit.install import sync_package_core_to_user_space, create_symlinks_to_claude

    # Check Claude Code is installed
    if not shutil.which("claude"):
        raise click.ClickException(
            "Claude Code not found. Install it first:\n"
            "  curl -fsSL https://claude.ai/install.sh | bash\n"
            "\nThen run: shipkit install"
        )

    # Step 1: Create shipkit metadata directory
    shipkit_home = ensure_home()

    # Step 2: Copy package core to user space
    click.echo("📦 Copying shipkit core to ~/.config/shipkit/...")
    copy_result = sync_package_core_to_user_space(shipkit_home, force=False)

    for item in copy_result["copied"]:
        click.echo(f"  ✓ {item}")
    for item in copy_result["skipped"]:
        click.echo(f"  - {item}")
    for item in copy_result["errors"]:
        click.echo(f"  ! {item}")

    # Step 3: Create symlinks to ~/.claude/
    click.echo()
    click.echo("🔗 Creating symlinks to ~/.claude/skills/...")
    link_result = create_symlinks_to_claude(shipkit_home, CLAUDE_HOME)

    for item in link_result["created"]:
        click.echo(f"  ✓ {item}")
    for item in link_result["skipped"]:
        click.echo(f"  - {item}")
    for item in link_result["errors"]:
        click.echo(f"  ! {item}")

    # Step 4: Launch LLM installer for configuration
    click.echo()
    click.echo("🚀 Launching interactive installer...")
    click.echo()
    click.echo("The installer agent will:")
    click.echo("  1. Scan your existing Claude Code setup")
    click.echo("  2. Configure layer preferences")
    click.echo("  3. Set up MCP servers")
    click.echo("  4. Merge hooks (preserves your config)")
    click.echo("  5. Verify installation worked")
    click.echo()
    click.echo("Note: Using installer agent with broader permissions for smooth setup")
    click.echo()

    # Get path to the install skill (now in user space)
    install_skill = shipkit_home / "core" / "skills" / "install" / "SKILL.md"

    # Check if installer agent exists
    installer_agent_path = shipkit_home / "core" / "agents" / "installer.md"

    # Launch Claude Code with installer agent (has permissionMode: auto for smooth setup)
    initial_prompt = (
        f"Read the installation instructions at {install_skill} and execute them to install Shipkit. "
        f"Follow the skill's workflow exactly: Phase 1 (diagnose), Phase 2 (report), Phase 3 (preferences), "
        f"Phase 4 (install), Phase 5 (next steps). Be methodical and safe."
    )

    try:
        if installer_agent_path.exists():
            # Use dedicated installer agent with broader permissions
            subprocess.run(["claude", "--agent", "shipkit-installer", initial_prompt], check=False)
        else:
            # Fallback to regular claude if installer agent not found
            subprocess.run(["claude", initial_prompt], check=False)
    except KeyboardInterrupt:
        click.echo("\n\nInstallation cancelled.")
        raise SystemExit(0)


@main.command()
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def uninstall(yes: bool):
    """Completely remove shipkit from your system.

    Removes:
    - ~/.config/shipkit/ (all shipkit metadata and core content)
    - ~/.claude/skills/core-*, experimental-*, advanced-* (symlinks)
    - Shipkit hooks from ~/.claude/settings.json
    - ~/.claude/agents/shipkit.md

    Your personal skills in ~/.claude/skills/ are preserved (only shipkit symlinks removed).
    """
    import json
    from shipkit.config import CLAUDE_HOME, SHIPKIT_HOME

    click.echo("⚠️  This will remove all shipkit installation:")
    click.echo()
    click.echo("  Will remove:")
    click.echo(f"    - {SHIPKIT_HOME} (all shipkit content)")
    click.echo("    - ~/.claude/skills/core-*, experimental-*, advanced-* (symlinks)")
    click.echo("    - Shipkit hooks from ~/.claude/settings.json")
    click.echo("    - ~/.claude/agents/shipkit.md")
    click.echo()
    click.echo("  Will preserve:")
    click.echo("    - Your personal skills in ~/.claude/skills/")
    click.echo("    - Your personal guidelines in ~/.claude/guidelines/")
    click.echo("    - Your other hooks and Claude Code settings")
    click.echo()

    if not yes:
        if not click.confirm("Are you sure you want to uninstall shipkit?"):
            click.echo("Cancelled.")
            return

    click.echo()
    click.echo("Uninstalling shipkit...")
    click.echo()

    # 1. Remove symlinks from ~/.claude/skills/
    removed_links = 0
    if (CLAUDE_HOME / "skills").exists():
        for skill_link in (CLAUDE_HOME / "skills").iterdir():
            if skill_link.is_symlink():
                # Only remove shipkit symlinks (core-*, experimental-*, advanced-*)
                if skill_link.name.startswith(("core-", "experimental-", "advanced-")):
                    skill_link.unlink()
                    removed_links += 1
    if removed_links:
        click.echo(f"  ✓ Removed {removed_links} shipkit skill symlinks from ~/.claude/skills/")

    # 2. Remove shipkit agent
    shipkit_agent = CLAUDE_HOME / "agents" / "shipkit.md"
    if shipkit_agent.exists():
        shipkit_agent.unlink()
        click.echo("  ✓ Removed ~/.claude/agents/shipkit.md")

    # 2b. Remove installer agent
    installer_agent = CLAUDE_HOME / "agents" / "shipkit-installer.md"
    if installer_agent.exists():
        installer_agent.unlink()
        click.echo("  ✓ Removed ~/.claude/agents/shipkit-installer.md")

    # 2c. Remove MCP config
    mcp_config = CLAUDE_HOME / "mcp.json"
    if mcp_config.exists():
        # Backup before removing
        import shutil
        from datetime import datetime
        backup_name = f"mcp.json.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        shutil.copy2(mcp_config, CLAUDE_HOME / backup_name)
        mcp_config.unlink()
        click.echo(f"  ✓ Removed ~/.claude/mcp.json (backed up to {backup_name})")

    # 3. Remove shipkit hooks from settings.json
    settings_path = CLAUDE_HOME / "settings.json"
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text())
            hooks = settings.get("hooks", {})
            removed_hooks = 0

            # Remove hooks that point to shipkit
            for event_name, hook_list in hooks.items():
                if not isinstance(hook_list, list):
                    continue

                filtered = []
                for hook_group in hook_list:
                    if not isinstance(hook_group, dict):
                        filtered.append(hook_group)
                        continue

                    group_hooks = hook_group.get("hooks", [])
                    if isinstance(group_hooks, list):
                        # Filter out shipkit hooks
                        non_shipkit = [
                            h for h in group_hooks
                            if isinstance(h, dict) and "shipkit" not in h.get("command", "")
                        ]

                        if non_shipkit:
                            hook_group["hooks"] = non_shipkit
                            filtered.append(hook_group)
                        else:
                            removed_hooks += 1
                    else:
                        filtered.append(hook_group)

                hooks[event_name] = filtered

            settings["hooks"] = hooks
            settings_path.write_text(json.dumps(settings, indent=2) + "\n")

            if removed_hooks:
                click.echo(f"  ✓ Removed shipkit hooks from ~/.claude/settings.json")

        except Exception as e:
            click.echo(f"  ! Could not clean hooks from settings.json: {e}")

    # 4. Remove ~/.config/shipkit/
    if SHIPKIT_HOME.exists():
        import shutil
        shutil.rmtree(SHIPKIT_HOME)
        click.echo(f"  ✓ Removed {SHIPKIT_HOME}")

    click.echo()
    click.echo("✅ Shipkit uninstalled successfully.")
    click.echo()
    click.echo("To reinstall later: pip install shipkit && shipkit install")


@main.command()
def upgrade():
    """Upgrade shipkit core content to latest version.

    Refreshes core/experimental/advanced content from the pip package to
    ~/.config/shipkit/, updating skills, guidelines, and hooks to latest versions.

    Your personal customizations in ~/.claude/skills/ are preserved.
    """
    from shipkit.datadir import resolve_home
    from shipkit.config import CLAUDE_HOME, SHIPKIT_HOME
    from shipkit.install import sync_package_core_to_user_space, create_symlinks_to_claude, remove_broken_symlinks

    try:
        shipkit_home = resolve_home()
    except Exception:
        raise click.ClickException(
            "Shipkit not installed. Run 'shipkit install' first."
        )

    click.echo("⬆️  Upgrading shipkit core content...")
    click.echo()

    # Force refresh core content from package
    copy_result = sync_package_core_to_user_space(shipkit_home, force=True)

    for item in copy_result["copied"]:
        click.echo(f"  ✓ {item}")
    for item in copy_result["errors"]:
        click.echo(f"  ! {item}")

    # Recreate symlinks (in case new skills added)
    click.echo()
    click.echo("🔗 Updating symlinks...")
    link_result = create_symlinks_to_claude(shipkit_home, CLAUDE_HOME)

    for item in link_result["created"]:
        click.echo(f"  ✓ {item}")

    # Clean up broken symlinks
    removed = remove_broken_symlinks(CLAUDE_HOME)
    if removed:
        click.echo()
        click.echo("🧹 Cleaned up broken symlinks:")
        for item in removed:
            click.echo(f"  - {item}")

    click.echo()
    click.echo("✅ Upgrade complete!")
    click.echo()
    click.echo("Next steps:")
    click.echo("  1. Restart Claude Code")
    click.echo("  2. Run: shipkit sync (in any project)")
    click.echo()
    click.echo("New skills and updates are now available.")


def _offer_alias_installation():
    """Offer to install a shell alias for shipkit run."""
    import sys

    click.echo()
    click.echo("🚀 Quick access: Install a shell alias?")
    click.echo()
    click.echo("  Creates: alias sk='noglob shipkit run'")
    click.echo("  Usage:   sk \"add tests for auth module\"")
    click.echo()

    if not sys.stdin.isatty():
        # Non-interactive, skip
        click.echo("  Run 'shipkit alias sk --install' to add it later.")
        return

    if click.confirm("  Install 'sk' alias?", default=True):
        shell = _detect_shell()
        snippet = _generate_shipkit_alias("sk", shell)
        _install_alias("sk", snippet, shell)
        click.echo()
        click.echo(f"✓ Alias installed! Restart your shell or run: source {_rc_file(shell)}")
    else:
        click.echo()
        click.echo("  Skipped. Install later with: shipkit alias sk --install")


# --- sync command ---

@main.command()
@click.option("--dry-run", is_flag=True, help="Show what would change without writing")
def sync(dry_run: bool):
    """Compile shipkit content into Claude Code configuration for current directory."""
    from shipkit.sync import sync_project
    from shipkit.project import ProjectError
    from shipkit.datadir import DataDirError

    try:
        result = sync_project(dry_run=dry_run)
        _print_result(None, result, dry_run)
    except (ProjectError, DataDirError, ValueError) as e:
        raise click.ClickException(str(e))


def _print_result(project_name: str | None, result, dry_run: bool):
    prefix = f"[{project_name}] " if project_name else ""
    mode = " (dry-run)" if dry_run else ""

    if result.files_written:
        click.echo(f"{prefix}Written{mode}:")
        for f in result.files_written:
            click.echo(f"  + {f}")
    if result.files_skipped:
        click.echo(f"{prefix}Skipped:")
        for f in result.files_skipped:
            click.echo(f"  - {f}")
    if result.warnings:
        click.echo(f"{prefix}Warnings:")
        for w in result.warnings:
            click.echo(f"  ! {w}")
    if not result.files_written and not result.warnings:
        click.echo(f"{prefix}Nothing to do.")


# --- status command ---

@main.command()
def status():
    """Show shipkit configuration and current directory status."""
    from shipkit.datadir import resolve_home, DataDirError
    from shipkit.config import ShipkitConfig, CLAUDE_HOME
    from shipkit.project import is_claude_project

    try:
        home_path = resolve_home()
        click.echo(f"Shipkit metadata: {home_path}")

        cfg = ShipkitConfig.load()
        click.echo()
        click.echo("Enabled layers:")
        click.echo("  [x] Core")
        if cfg.layers_experimental:
            click.echo("  [x] Experimental")
        if cfg.layers_advanced:
            click.echo("  [x] Advanced")

        click.echo()
        click.echo(f"Claude Code home: {CLAUDE_HOME}")
        if CLAUDE_HOME.exists():
            skills_count = len(list((CLAUDE_HOME / "skills").glob("*"))) if (CLAUDE_HOME / "skills").exists() else 0
            guidelines_count = len(list((CLAUDE_HOME / "guidelines").glob("*.md"))) if (CLAUDE_HOME / "guidelines").exists() else 0
            click.echo(f"  Personal skills: {skills_count}")
            click.echo(f"  Personal guidelines: {guidelines_count}")
        else:
            click.echo("  (not yet created)")

    except DataDirError as e:
        click.echo(f"Shipkit not initialized: {e}")
        click.echo("Run 'shipkit init' to get started.")
        return

    click.echo()
    click.echo(f"Current directory: {Path.cwd()}")
    if is_claude_project():
        click.echo("  Status: Claude Code project ✓")
        if (Path.cwd() / ".claude").exists():
            team_skills = len(list((Path.cwd() / ".claude" / "skills").glob("*"))) if (Path.cwd() / ".claude" / "skills").exists() else 0
            team_guidelines = len(list((Path.cwd() / ".claude" / "guidelines").glob("*.md"))) if (Path.cwd() / ".claude" / "guidelines").exists() else 0
            click.echo(f"  Team skills: {team_skills}")
            click.echo(f"  Team guidelines: {team_guidelines}")
    else:
        click.echo("  Status: Not a git repository")
        click.echo("  Run 'git init' to use shipkit here")


# --- doctor command ---

@main.command()
@click.option("--lint", is_flag=True, help="Run content validation checks")
@click.option("--check", "check_name", default=None, help="Run a specific lint check")
def doctor(lint: bool, check_name: str | None):
    """Check shipkit configuration health."""
    from shipkit.config import ShipkitConfig, SHIPKIT_HOME, CONFIG_PATH
    from shipkit.datadir import resolve_home, validate_home, DataDirError

    # If --lint or --check, run content validation
    if lint or check_name:
        from shipkit.lint import run_all, run_check
        if check_name:
            ok = run_check(check_name)
        else:
            ok = run_all()
        raise SystemExit(0 if ok else 1)

    ok = True

    # Check home directory
    if SHIPKIT_HOME.exists():
        click.echo(f"+ Home: {SHIPKIT_HOME}")
        warnings = validate_home(SHIPKIT_HOME)
        for w in warnings:
            click.echo(f"  ! {w}")
            ok = False
    else:
        click.echo(f"! Home not initialized: {SHIPKIT_HOME}")
        ok = False

    # Check current project
    try:
        from shipkit.project import resolve_project
        name, _ = resolve_project()
        click.echo(f"+ Current project: {name}")
    except Exception:
        click.echo("  (not in a registered project)")

    if ok:
        click.echo("\nAll checks passed.")
    else:
        click.echo("\nSome issues found. Run 'shipkit init' in a project to get started.")


# --- template commands ---

@main.group()
def template():
    """Manage project templates."""


@template.command("list")
def template_list():
    """List available project templates."""
    from shipkit.datadir import resolve_home, SEED_DIR, DataDirError

    templates = {}

    # Seed templates (shipped with package)
    seed_templates = SEED_DIR / "templates"
    if seed_templates.exists():
        for t in sorted(seed_templates.iterdir()):
            if t.is_dir():
                templates[t.name] = "built-in"

    # Home templates (user-created, override built-in)
    try:
        home = resolve_home()
        home_templates = home / "templates"
        if home_templates.exists():
            for t in sorted(home_templates.iterdir()):
                if t.is_dir():
                    templates[t.name] = "home" if t.name not in templates else "home (override)"
    except DataDirError:
        pass

    if not templates:
        click.echo("No templates found.")
        return

    for name, source in sorted(templates.items()):
        click.echo(f"  {name:<20} ({source})")


@template.command("create")
@click.argument("name")
def template_create(name: str):
    """Create a new template from the current project's config."""
    from shipkit.project import resolve_project, ProjectError
    from shipkit.datadir import resolve_home, DataDirError
    import shutil

    try:
        home_path = resolve_home()
        _, project_dir = resolve_project()
    except (DataDirError, ProjectError) as e:
        raise click.ClickException(str(e))

    template_dir = home_path / "templates" / name
    if template_dir.exists():
        raise click.ClickException(f"Template '{name}' already exists.")

    template_dir.mkdir(parents=True)
    for subdir in ["guidelines", "skills"]:
        src = project_dir / subdir
        if src.exists() and any(src.iterdir()):
            shutil.copytree(src, template_dir / subdir)
        else:
            (template_dir / subdir).mkdir()

    click.echo(f"Template '{name}' created from current project.")
    click.echo(f"  Location: {template_dir}")


# --- plugin commands ---

@main.group()
def plugin():
    """Manage shipkit plugins."""


@plugin.command("install")
@click.argument("source")
@click.option("--name", "-n", default=None, help="Override plugin name")
def plugin_install(source: str, name: str | None):
    """Install a plugin from marketplace short name, Git URL, or local path.

    Examples:
      shipkit plugin install review-plus          # from marketplace
      shipkit plugin install https://github.com/user/plugin  # full URL
      shipkit plugin install ~/Code/my-plugin     # local path
    """
    from shipkit.plugin import install_plugin, PluginError

    try:
        plugin_name = install_plugin(source, name=name)
        click.echo(f"Plugin '{plugin_name}' installed.")
        click.echo(f"  Run 'shipkit sync' to compile plugin content.")
    except PluginError as e:
        raise click.ClickException(str(e))


@plugin.command("uninstall")
@click.argument("name")
def plugin_uninstall(name: str):
    """Uninstall a plugin."""
    from shipkit.plugin import uninstall_plugin, PluginError

    try:
        uninstall_plugin(name)
        click.echo(f"Plugin '{name}' uninstalled.")
    except PluginError as e:
        raise click.ClickException(str(e))


@plugin.command("list")
def plugin_list():
    """List installed plugins."""
    from shipkit.plugin import list_plugins

    plugins = list_plugins()
    if not plugins:
        click.echo("No plugins installed.")
        return

    for p in plugins:
        skills = f"{p['skills']} skills" if p['skills'] else ""
        hooks = f"{p['hooks']} hooks" if p['hooks'] else ""
        extras = ", ".join(filter(None, [skills, hooks]))
        extras_str = f" ({extras})" if extras else ""
        click.echo(f"  {p['name']:<20} {p['description']}{extras_str}")


@plugin.command("update")
@click.argument("name")
def plugin_update(name: str):
    """Update an installed plugin from its git remote."""
    from shipkit.plugin import update_plugin, PluginError

    try:
        update_plugin(name)
        click.echo(f"Plugin '{name}' updated.")
        click.echo(f"  Run 'shipkit sync' to recompile.")
    except PluginError as e:
        raise click.ClickException(str(e))


# --- alias command ---

@main.command("alias")
@click.argument("name", default="sk")
@click.option("--install", is_flag=True, help="Append the alias to your shell config")
def alias_cmd(name: str, install: bool):
    """Generate a shell alias to launch shipkit in current directory.

    NAME is the alias you want to use (default: 'sk').

    Creates a project-specific alias if in a git repo, otherwise global.
    """
    shell = _detect_shell()

    # Project-specific alias if in a git repo
    if _is_in_git_repo():
        repo_path = Path.cwd()
        snippet = _generate_alias(name, str(repo_path), shell)
    else:
        # Global alias (shipkit run from anywhere)
        snippet = _generate_shipkit_alias(name, shell)

    if install:
        _install_alias(name, snippet, shell)
    else:
        rc_file = _rc_file(shell)
        click.echo(f"Add this to {rc_file}:\n")
        click.echo(snippet)
        click.echo(f"\nOr run: shipkit alias {name} --install")


def _is_in_git_repo() -> bool:
    """Check if current directory is a git repository."""
    return (Path.cwd() / ".git").exists()


def _detect_shell() -> str:
    """Detect the user's shell."""
    import os
    shell = os.environ.get("SHELL", "")
    if "fish" in shell:
        return "fish"
    if "zsh" in shell:
        return "zsh"
    return "bash"


def _rc_file(shell: str) -> Path:
    """Return the config file path for the given shell."""
    if shell == "fish":
        return Path.home() / ".config" / "fish" / "config.fish"
    if shell == "zsh":
        return Path.home() / ".zshrc"
    return Path.home() / ".bashrc"


def _generate_alias(name: str, repo_path: str, shell: str) -> str:
    """Generate the shell alias snippet for project-specific launches."""
    if shell == "fish":
        return (
            f'function {name}\n'
            f'    cd "{repo_path}"; and shipkit run $argv\n'
            f'end'
        )
    # bash/zsh — noglob wrapper prevents glob expansion of ?, *, ! in prompts
    return (
        f'_{name}_shipkit() {{ cd "{repo_path}" && shipkit run "$@"; }}\n'
        f'alias {name}=\'noglob _{name}_shipkit\''
    )


def _generate_shipkit_alias(name: str, shell: str) -> str:
    """Generate the shell alias snippet for global shipkit run."""
    if shell == "fish":
        return f'alias {name}="shipkit run"'
    # bash/zsh — noglob wrapper prevents glob expansion
    return f'alias {name}=\'noglob shipkit run\''


def _install_alias(name: str, snippet: str, shell: str):
    """Append alias to the user's shell config."""
    rc = _rc_file(shell)

    # For fish, ensure config dir exists
    if shell == "fish":
        rc.parent.mkdir(parents=True, exist_ok=True)

    # Check if alias already exists
    func_marker = f"function {name}" if shell == "fish" else f"_{name}_shipkit"
    if rc.exists():
        content = rc.read_text()
        if func_marker in content:
            click.echo(f"Alias '{name}' already exists in {rc}")
            return

    marker = f"# shipkit alias: {name}"
    with open(rc, "a") as f:
        f.write(f"\n{marker}\n{snippet}\n")

    click.echo(f"Alias '{name}' added to {rc}")
    click.echo(f"Run 'source {rc}' or open a new terminal to use it.")


# --- run command ---

@main.command()
@click.argument("prompt", nargs=-1)
@click.option("--no-agent", is_flag=True, help="Launch without custom shipkit agent")
def run(prompt: tuple[str, ...], no_agent: bool):
    """Sync config then launch Claude Code with custom shipkit agent.

    Optionally pass a PROMPT to start with.
    """
    import subprocess
    import shutil
    from shipkit.sync import sync_project
    from shipkit.project import ProjectError
    from shipkit.datadir import DataDirError

    # Sync first
    try:
        result = sync_project()
        if result.files_written:
            click.echo("Synced:")
            for f in result.files_written:
                click.echo(f"  + {f}")
    except (ProjectError, DataDirError, ValueError) as e:
        raise click.ClickException(str(e))

    # Check if Claude Code is installed
    if not shutil.which("claude"):
        raise click.ClickException(
            "Claude Code not found. Install it with:\n"
            "  curl -fsSL https://claude.ai/install.sh | bash"
        )

    # Build launch command with shipkit agent (unless --no-agent)
    cmd = ["claude"]
    if not no_agent:
        cmd.extend(["--agent", "shipkit"])
    if prompt:
        cmd.append(" ".join(prompt))

    click.echo("Launching shipkit on Claude Code...")
    subprocess.run(cmd, check=False)


