"""Base compiler interface for shipkit.

Compiles shipkit content into Claude Code native configuration.

Content layering (lowest to highest precedence):
1. Package core — shipped with shipkit (always included)
2. Package experimental — opt-in cutting-edge features
3. Package advanced — opt-in specialized/niche tools
4. Marketplace plugins — installed from shipkit-marketplace
5. User personal — ~/.claude/skills/, ~/.claude/guidelines/
6. Team — .claude/ in repo (highest precedence)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from shipkit.config import ShipkitConfig, CLAUDE_HOME, SHIPKIT_HOME

# Package content layers (source - in pip package)
PACKAGE_ROOT = Path(__file__).parent.parent
PACKAGE_CORE_SOURCE = PACKAGE_ROOT / "core"
PACKAGE_EXPERIMENTAL_SOURCE = PACKAGE_ROOT / "experimental"
PACKAGE_ADVANCED_SOURCE = PACKAGE_ROOT / "advanced"

# User-space content (installed to ~/.config/shipkit/)
# Core content is copied here during 'shipkit install' for user-friendly access
USER_CORE_DIR = SHIPKIT_HOME / "core"
USER_EXPERIMENTAL_DIR = SHIPKIT_HOME / "experimental"
USER_ADVANCED_DIR = SHIPKIT_HOME / "advanced"

# Backwards compatibility export for hooks
PACKAGE_HOOKS_DIR = USER_CORE_DIR / "hooks"


@dataclass
class CompileContext:
    """Everything a compiler needs to generate tool-native output."""

    shipkit_home: Path  # ~/.config/shipkit/ (metadata only)
    repo_path: Path     # Current project directory

    # --- Package layers (read from config which are enabled) ---

    @property
    def config(self) -> ShipkitConfig:
        """Load shipkit config to see which layers are enabled."""
        return ShipkitConfig.load()

    @property
    def package_core_guidelines(self) -> Path:
        """Core guidelines in user space (copied during install)."""
        return USER_CORE_DIR / "guidelines"

    @property
    def package_core_skills(self) -> Path:
        """Core skills in user space (copied during install)."""
        return USER_CORE_DIR / "skills"

    @property
    def package_experimental_guidelines(self) -> Path:
        """Experimental guidelines in user space (copied during install)."""
        return USER_EXPERIMENTAL_DIR / "guidelines"

    @property
    def package_experimental_skills(self) -> Path:
        """Experimental skills in user space (copied during install)."""
        return USER_EXPERIMENTAL_DIR / "skills"

    @property
    def package_advanced_guidelines(self) -> Path:
        """Advanced guidelines in user space (copied during install)."""
        return USER_ADVANCED_DIR / "guidelines"

    @property
    def package_advanced_skills(self) -> Path:
        """Advanced skills in user space (copied during install)."""
        return USER_ADVANCED_DIR / "skills"

    @property
    def package_mcp(self) -> Path:
        """Package MCP config in user space."""
        return USER_CORE_DIR / "mcp.json"

    # --- User personal (Claude Code native location) ---

    @property
    def user_guidelines(self) -> Path:
        return CLAUDE_HOME / "guidelines"

    @property
    def user_skills(self) -> Path:
        return CLAUDE_HOME / "skills"

    @property
    def user_mcp(self) -> Path:
        """User MCP config in shipkit home (agent-scoped, not global Claude config)."""
        return SHIPKIT_HOME / "mcp.json"

    # --- Team (project-specific, git-committed) ---

    @property
    def team_guidelines(self) -> Path:
        return self.repo_path / ".claude" / "guidelines"

    @property
    def team_skills(self) -> Path:
        return self.repo_path / ".claude" / "skills"

    @property
    def team_mcp(self) -> Path:
        """Project MCP config (git-committed, team-shared)."""
        return self.repo_path / ".claude" / "mcp.json"

    # --- Subagents ---

    @property
    def package_subagents(self) -> Path:
        """Package subagents in user space."""
        return USER_CORE_DIR / "subagents"

    @property
    def user_subagents(self) -> Path:
        return CLAUDE_HOME / "subagents"

    # --- Hooks ---

    @property
    def package_hooks(self) -> Path:
        """Package hooks in user space (copied during install)."""
        return USER_CORE_DIR / "hooks"

    @property
    def user_hooks(self) -> Path:
        return CLAUDE_HOME / "hooks"

    # --- Plugins ---

    @property
    def plugin_dirs(self) -> list[Path]:
        """All installed marketplace plugin directories."""
        plugins_dir = self.shipkit_home / "plugins"
        if not plugins_dir.exists():
            return []
        return sorted(d for d in plugins_dir.iterdir() if d.is_dir() and (d / "plugin.yaml").exists())

    # --- Convenience: ordered layer lists for iteration ---

    @property
    def guidelines_layers(self) -> list[Path]:
        """Guidelines dirs in precedence order (lowest first).

        Respects config to include/exclude experimental and advanced layers.
        """
        cfg = self.config
        layers = [self.package_core_guidelines]

        if cfg.layers_experimental:
            layers.append(self.package_experimental_guidelines)

        if cfg.layers_advanced:
            layers.append(self.package_advanced_guidelines)

        # Marketplace plugins
        for pd in self.plugin_dirs:
            layers.append(pd / "guidelines")

        # User personal (Claude Code native)
        layers.append(self.user_guidelines)

        # Team (highest precedence)
        layers.append(self.team_guidelines)

        return layers

    @property
    def skills_layers(self) -> list[Path]:
        """Skills dirs in precedence order (lowest first).

        Respects config to include/exclude experimental and advanced layers.
        """
        cfg = self.config
        layers = [self.package_core_skills]

        if cfg.layers_experimental:
            layers.append(self.package_experimental_skills)

        if cfg.layers_advanced:
            layers.append(self.package_advanced_skills)

        # Marketplace plugins
        for pd in self.plugin_dirs:
            layers.append(pd / "skills")

        # User personal (Claude Code native)
        layers.append(self.user_skills)

        # Team (highest precedence)
        layers.append(self.team_skills)

        return layers

    @property
    def mcp_layers(self) -> list[Path]:
        """MCP config files in precedence order (lowest first)."""
        layers: list[Path] = [self.package_mcp]

        for pd in self.plugin_dirs:
            layers.append(pd / "mcp.json")

        layers.append(self.user_mcp)

        # Project-level (highest precedence, team-shared)
        layers.append(self.team_mcp)
        return layers

    @property
    def hooks_layers(self) -> list[Path]:
        """Hook directories in precedence order (lowest first)."""
        layers = [self.package_hooks]

        for pd in self.plugin_dirs:
            layers.append(pd / "hooks")

        layers.append(self.user_hooks)
        return layers


@dataclass
class CompileResult:
    """Result of a compilation pass."""

    files_written: list[str]
    files_skipped: list[str]
    warnings: list[str]


class Compiler(ABC):
    """Base compiler interface for generating tool-native configs."""

    name: str = "BaseCompiler"

    @abstractmethod
    def compile(self, ctx: CompileContext, dry_run: bool = False) -> CompileResult:
        """Compile shipkit content to tool-native configuration."""
        pass


# --- Compiler registry ---

COMPILERS: dict[str, type[Compiler]] = {}


def register_compiler(name: str):
    """Decorator to register a compiler class."""
    def decorator(cls: type[Compiler]) -> type[Compiler]:
        COMPILERS[name] = cls
        return cls
    return decorator


def get_compiler(tool_name: str) -> Compiler:
    """Get a compiler instance for the given tool name."""
    if tool_name not in COMPILERS:
        available = ", ".join(sorted(COMPILERS.keys()))
        raise ValueError(f"No compiler for '{tool_name}'. Available: {available}")
    return COMPILERS[tool_name]()
