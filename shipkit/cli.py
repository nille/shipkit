"""Shipkit CLI — built with Click."""

from __future__ import annotations

from pathlib import Path

import click

from shipkit import __version__


@click.group()
@click.version_option(__version__, prog_name="shipkit")
def main():
    """Shipkit — CLI-agnostic AI dev productivity kit."""


# --- init command ---

@main.command()
@click.option("--name", "-n", default=None, help="Project name (defaults to directory name)")
@click.option("--template", "-t", default="default", help="Project template to use")
@click.option("--skip-alias", is_flag=True, help="Skip alias installation prompt")
def init(name: str | None, template: str, skip_alias: bool):
    """Register the current directory as a shipkit project."""
    from shipkit.project import init_project, ProjectError
    from shipkit.datadir import resolve_home
    import sys

    try:
        project_name = init_project(Path.cwd(), name=name, template=template)
        click.echo(f"Project '{project_name}' registered.")
        click.echo(f"  Marker: .shipkit")
        click.echo(f"  Run 'shipkit sync' to generate tool-native config.")

        # Check if this is the first project (offer alias installation)
        if not skip_alias:
            try:
                home_path = resolve_home()
                projects_dir = home_path / "projects"
                project_count = len([d for d in projects_dir.iterdir() if d.is_dir()]) if projects_dir.exists() else 0

                # If this is the first project, offer alias installation
                if project_count == 1:
                    _offer_alias_installation()
            except Exception:
                # Don't fail init if alias offer fails
                pass

    except ProjectError as e:
        raise click.ClickException(str(e))


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
@click.option("--all", "sync_all_flag", is_flag=True, help="Sync all registered projects")
def sync(dry_run: bool, sync_all_flag: bool):
    """Compile shipkit content into Claude Code configuration."""
    from shipkit.sync import sync_project, sync_all
    from shipkit.project import ProjectError
    from shipkit.datadir import DataDirError

    try:
        if sync_all_flag:
            results = sync_all(dry_run=dry_run)
            for project_name, result in results.items():
                _print_result(project_name, result, dry_run)
        else:
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
    """Show project info and sync status."""
    from shipkit.project import resolve_project, ProjectError
    from shipkit.datadir import resolve_home, DataDirError
    from shipkit.config import ProjectConfig

    try:
        home_path = resolve_home()
        click.echo(f"Home: {home_path}")
    except DataDirError as e:
        click.echo(f"Home: not initialized ({e})")
        return

    try:
        name, project_dir = resolve_project()
        cfg = ProjectConfig.load(project_dir / "project.yaml")
        click.echo(f"Project: {name}")
        click.echo(f"  Repo: {cfg.repo_path}")
        click.echo(f"  Template: {cfg.template}")

        # Check what's in the home for this project
        guidelines_count = len(list((project_dir / "guidelines").glob("*.md"))) if (project_dir / "guidelines").exists() else 0
        skills_count = len([d for d in (project_dir / "skills").iterdir() if d.is_dir()]) if (project_dir / "skills").exists() else 0
        knowledge_count = len(list((project_dir / "knowledge").glob("*"))) if (project_dir / "knowledge").exists() else 0
        click.echo(f"  Project guidelines: {guidelines_count} files")
        click.echo(f"  Project skills: {skills_count}")
        click.echo(f"  Knowledge: {knowledge_count} files")
    except ProjectError:
        click.echo("Project: not registered (run 'shipkit init')")


# --- projects command ---

@main.group()
def projects():
    """Manage registered projects."""


@projects.command("list")
def projects_list():
    """List all registered projects."""
    from shipkit.project import list_projects

    projs = list_projects()
    if not projs:
        click.echo("No projects registered.")
        return

    for p in projs:
        status_icon = "+" if p["repo_exists"] else "!"
        click.echo(f"  {status_icon} {p['name']:<20} {p['repo_path']}")


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
@click.option("--project", "-p", default=None, help="Project name (creates project-specific alias)")
@click.option("--install", is_flag=True, help="Append the alias to your shell config")
def alias_cmd(name: str, project: str | None, install: bool):
    """Generate a shell alias to launch shipkit.

    NAME is the alias you want to use (default: 'sk').

    Without --project: creates global alias (shipkit run anywhere)
    With --project: creates project-specific alias (cd to project first)
    """
    from shipkit.project import resolve_project, ProjectError
    from shipkit.config import ProjectConfig
    from shipkit.datadir import resolve_home, DataDirError

    shell = _detect_shell()

    # Project-specific alias (cd to project first)
    if project or _is_in_project():
        try:
            if project:
                home_path = resolve_home()
                project_dir = home_path / "projects" / project
                cfg = ProjectConfig.load(project_dir / "project.yaml")
                repo_path = cfg.repo_path
            else:
                _, project_dir = resolve_project()
                cfg = ProjectConfig.load(project_dir / "project.yaml")
                repo_path = cfg.repo_path
        except (ProjectError, DataDirError) as e:
            raise click.ClickException(str(e))

        snippet = _generate_alias(name, repo_path, shell)
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


def _is_in_project() -> bool:
    """Check if current directory is a shipkit project."""
    return (Path.cwd() / ".shipkit").exists()


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


