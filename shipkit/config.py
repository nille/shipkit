"""Configuration management for shipkit.

Two config layers:
1. Shipkit home: ~/.config/shipkit/ (skills, steering, projects, state — all user data)
2. Project config: <home>/projects/<name>/project.yaml (per-project overrides)

The home directory is configurable via SHIPKIT_HOME env var.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

SHIPKIT_HOME = Path(os.environ.get("SHIPKIT_HOME", "~/.config/shipkit")).expanduser()
CONFIG_PATH = SHIPKIT_HOME / "config.yaml"


@dataclass
class ShipkitConfig:
    cli_tool: str = "claude"

    def save(self) -> None:
        SHIPKIT_HOME.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(yaml.dump({"cli_tool": self.cli_tool}, default_flow_style=False))

    @classmethod
    def load(cls) -> ShipkitConfig:
        if not CONFIG_PATH.exists():
            return cls()
        data = yaml.safe_load(CONFIG_PATH.read_text()) or {}
        return cls(cli_tool=data.get("cli_tool", "claude"))


@dataclass
class ProjectConfig:
    name: str = ""
    repo_path: str = ""
    template: str = "default"
    cli_tool: str = ""

    @classmethod
    def load(cls, project_yaml: Path) -> ProjectConfig:
        if not project_yaml.exists():
            return cls()
        data = yaml.safe_load(project_yaml.read_text()) or {}
        return cls(
            name=data.get("name", ""),
            repo_path=data.get("repo_path", ""),
            template=data.get("template", "default"),
            cli_tool=data.get("cli_tool", ""),
        )

    def save(self, project_yaml: Path) -> None:
        project_yaml.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "name": self.name,
            "repo_path": self.repo_path,
            "template": self.template,
        }
        if self.cli_tool:
            data["cli_tool"] = self.cli_tool
        project_yaml.write_text(yaml.dump(data, default_flow_style=False))


@dataclass
class ResolvedConfig:
    """Fully resolved config: home + project layers merged."""

    home_path: Path
    cli_tool: str
    project_name: str = ""
    repo_path: Path = field(default_factory=lambda: Path.cwd())
    template: str = "default"

    @classmethod
    def resolve(cls, project_name: str = "") -> ResolvedConfig:
        home_path = SHIPKIT_HOME
        if not home_path.exists():
            raise ConfigError("Shipkit not initialized. Run 'shipkit init' in a project first.")

        cfg = ShipkitConfig.load()
        cli_tool = cfg.cli_tool or "claude"

        if project_name:
            project_yaml = home_path / "projects" / project_name / "project.yaml"
            proj_cfg = ProjectConfig.load(project_yaml)
            if proj_cfg.cli_tool:
                cli_tool = proj_cfg.cli_tool
            return cls(
                home_path=home_path,
                cli_tool=cli_tool,
                project_name=proj_cfg.name,
                repo_path=Path(proj_cfg.repo_path).expanduser().resolve() if proj_cfg.repo_path else Path.cwd(),
                template=proj_cfg.template,
            )

        return cls(home_path=home_path, cli_tool=cli_tool)


class ConfigError(Exception):
    pass
