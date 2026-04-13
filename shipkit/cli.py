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
def init(name: str | None, template: str):
    """Register the current directory as a shipkit project."""
    from shipkit.project import init_project, ProjectError

    try:
        project_name = init_project(Path.cwd(), name=name, template=template)
        click.echo(f"Project '{project_name}' registered.")
        click.echo(f"  Marker: .shipkit")
        click.echo(f"  Run 'shipkit sync' to generate tool-native config.")
    except ProjectError as e:
        raise click.ClickException(str(e))


# --- sync command ---

@main.command()
@click.option("--tool", "-t", default=None, help="Target CLI tool (claude, kiro, gemini)")
@click.option("--dry-run", is_flag=True, help="Show what would change without writing")
@click.option("--all", "sync_all_flag", is_flag=True, help="Sync all registered projects")
def sync(tool: str | None, dry_run: bool, sync_all_flag: bool):
    """Compile shipkit content into tool-native configuration."""
    from shipkit.sync import sync_project, sync_all
    from shipkit.project import ProjectError
    from shipkit.datadir import DataDirError

    try:
        if sync_all_flag:
            results = sync_all(tool=tool, dry_run=dry_run)
            for project_name, result in results.items():
                _print_result(project_name, result, dry_run)
        else:
            result = sync_project(tool=tool, dry_run=dry_run)
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
        if cfg.cli_tool:
            click.echo(f"  CLI tool: {cfg.cli_tool}")

        # Check what's in the home for this project
        steering_count = len(list((project_dir / "steering").glob("*.md"))) if (project_dir / "steering").exists() else 0
        skills_count = len([d for d in (project_dir / "skills").iterdir() if d.is_dir()]) if (project_dir / "skills").exists() else 0
        knowledge_count = len(list((project_dir / "knowledge").glob("*"))) if (project_dir / "knowledge").exists() else 0
        click.echo(f"  Project steering: {steering_count} files")
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
        cfg = ShipkitConfig.load()
        click.echo(f"  CLI tool: {cfg.cli_tool}")
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
    for subdir in ["steering", "skills"]:
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
    """Install a plugin from a Git repo URL or local path."""
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


# --- run command ---

@main.command()
@click.argument("prompt", nargs=-1)
@click.option("--tool", "-t", default=None, help="Override CLI tool")
def run(prompt: tuple[str, ...], tool: str | None):
    """Sync config then launch the AI coding CLI.

    Optionally pass a PROMPT to start with.
    """
    import subprocess
    import sys
    from shipkit.sync import sync_project
    from shipkit.config import ResolvedConfig, ConfigError
    from shipkit.project import resolve_project, ProjectError
    from shipkit.datadir import DataDirError

    # Sync first
    try:
        result = sync_project(tool=tool)
        if result.files_written:
            click.echo("Synced:")
            for f in result.files_written:
                click.echo(f"  + {f}")
    except (ProjectError, DataDirError, ValueError) as e:
        raise click.ClickException(str(e))

    # Resolve which tool to launch
    try:
        project_name, _ = resolve_project()
        cfg = ResolvedConfig.resolve(project_name)
        cli_tool = tool or cfg.cli_tool
    except (ConfigError, ProjectError) as e:
        raise click.ClickException(str(e))

    # Map tool name to CLI command
    tool_commands = {
        "claude": ["claude"],
        "kiro": ["kiro-cli", "chat"],
        "gemini": ["gemini"],
        "opencode": ["opencode"],
    }

    cmd = tool_commands.get(cli_tool)
    if cmd is None:
        raise click.ClickException(f"Unknown CLI tool: {cli_tool}. Configure in config.yaml.")

    if prompt:
        cmd.append(" ".join(prompt))

    click.echo(f"Launching {cli_tool}...")
    try:
        subprocess.run(cmd, check=False)
    except FileNotFoundError:
        raise click.ClickException(f"'{cmd[0]}' not found. Is {cli_tool} installed?")
