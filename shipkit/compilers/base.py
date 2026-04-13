"""Base compiler interface for shipkit.

Each target CLI tool (Claude Code, Kiro, Gemini CLI, etc.) implements this
interface to compile shipkit content into tool-native configuration.

Content layering (lowest to highest precedence):
1. Package core — shipped with shipkit (guidelines, skills, MCP defaults)
2. User global — personal additions/overrides in shipkit home
3. Plugins — from marketplace or local installs
4. Repo — team-shared content committed to the repo

Note: project_dir is kept for storing project metadata (project.yaml) but
no longer used as a content layer. Use the repo itself for project-specific content.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

# Core content shipped with the shipkit package
PACKAGE_CORE_DIR = Path(__file__).parent.parent / "core"
PACKAGE_HOOKS_DIR = PACKAGE_CORE_DIR / "hooks"


@dataclass
class CompileContext:
    """Everything a compiler needs to generate tool-native output."""

    home_path: Path
    repo_path: Path
    project_name: str

    # --- Layer 1: Package core (shipped with shipkit) ---

    @property
    def package_guidelines(self) -> Path:
        return PACKAGE_CORE_DIR / "guidelines"

    @property
    def package_skills(self) -> Path:
        return PACKAGE_CORE_DIR / "skills"

    @property
    def package_mcp(self) -> Path:
        return PACKAGE_CORE_DIR / "mcp.json"

    # --- Layer 2: User global (personal additions/overrides) ---

    @property
    def user_guidelines(self) -> Path:
        return self.home_path / "guidelines"

    @property
    def user_skills(self) -> Path:
        return self.home_path / "skills"

    @property
    def user_mcp(self) -> Path:
        return self.home_path / "mcp.json"

    # --- Subagents ---

    @property
    def package_subagents(self) -> Path:
        return PACKAGE_CORE_DIR / "subagents"

    @property
    def user_subagents(self) -> Path:
        return self.home_path / "subagents"

    # --- Hooks ---

    @property
    def package_hooks(self) -> Path:
        return PACKAGE_HOOKS_DIR

    @property
    def user_hooks(self) -> Path:
        return self.home_path / "hooks"

    # --- Plugins ---

    @property
    def plugin_dirs(self) -> list[Path]:
        """All installed plugin directories."""
        plugins_dir = self.home_path / "plugins"
        if not plugins_dir.exists():
            return []
        return sorted(d for d in plugins_dir.iterdir() if d.is_dir() and (d / "plugin.yaml").exists())

    # --- Convenience: ordered layer lists for iteration ---

    @property
    def guidelines_layers(self) -> list[Path]:
        """Guidelines dirs in precedence order (lowest first)."""
        layers = [self.package_guidelines, self.user_guidelines]
        for pd in self.plugin_dirs:
            layers.append(pd / "guidelines")
        return layers

    @property
    def skills_layers(self) -> list[Path]:
        """Skills dirs in precedence order (lowest first)."""
        layers = [self.package_skills, self.user_skills]
        for pd in self.plugin_dirs:
            layers.append(pd / "skills")
        return layers

    @property
    def mcp_layers(self) -> list[Path]:
        """MCP config files in precedence order (lowest first)."""
        layers: list[Path] = [self.package_mcp, self.user_mcp]
        for pd in self.plugin_dirs:
            layers.append(pd / "mcp.json")
        return layers

    @property
    def hooks_layers(self) -> list[Path]:
        """Hook dirs in precedence order (lowest first)."""
        layers = [self.package_hooks, self.user_hooks]
        for pd in self.plugin_dirs:
            layers.append(pd / "hooks")
        return layers

    @property
    def subagents_layers(self) -> list[Path]:
        """Subagent dirs in precedence order (lowest first)."""
        layers = [self.package_subagents, self.user_subagents]
        for pd in self.plugin_dirs:
            layers.append(pd / "subagents")
        return layers


@dataclass
class CompileResult:
    """Summary of what the compiler did."""

    files_written: list[str]
    files_skipped: list[str]
    warnings: list[str]


class Compiler(ABC):
    """Base class for tool-specific compilers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the target tool."""
        ...

    @abstractmethod
    def compile(self, ctx: CompileContext, dry_run: bool = False) -> CompileResult:
        """Compile shipkit content into tool-native configuration.

        If dry_run is True, report what would change without writing files.
        """
        ...


COMPILERS: dict[str, type[Compiler]] = {}


def register_compiler(tool_name: str):
    """Decorator to register a compiler for a tool name."""
    def decorator(cls: type[Compiler]):
        COMPILERS[tool_name] = cls
        return cls
    return decorator


def get_compiler(tool_name: str) -> Compiler:
    """Get a compiler instance for the given tool name."""
    if tool_name not in COMPILERS:
        available = ", ".join(sorted(COMPILERS.keys()))
        raise ValueError(f"No compiler for '{tool_name}'. Available: {available}")
    return COMPILERS[tool_name]()
