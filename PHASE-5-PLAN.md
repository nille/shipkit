# Phase 5: Custom Agent Generation & Branded Launch Experience

## Overview

Add support for generating custom agent configurations for all 4 supported tools, enabling branded "shipkit" instances instead of generic tool sessions. Inspired by auto-sa's custom Kiro agent implementation.

**Goal:** Users launch `shipkit run` and get a branded assistant with pre-loaded skills, guidelines, and team context - regardless of which underlying tool they use.

---

## Research Findings

### Custom Agent Support by Tool

| Tool | Support Level | Config Format | Launch Method |
|------|--------------|---------------|---------------|
| **Kiro CLI** | ✅ Full | JSON (`.kiro/agents/<name>.json`) | `kiro-cli chat --agent <name>` |
| **Claude Code** | ✅ Full | Markdown + YAML (`.claude/agents/<name>.md`) | `claude --agent <name>` |
| **OpenCode** | ✅ Full | Markdown + YAML (`.opencode/agents/<name>.md`) | `opencode --agent <name>` |
| **Gemini CLI** | ⚠️ Partial | GEMINI.md context files | `gemini` (no agent flag) |

### Key Differences Between Tools

#### **Kiro CLI**
- **Format:** JSON with schema validation
- **Location:** `.kiro/agents/<name>.json`
- **Launch:** `kiro-cli chat --agent auto-sa`
- **Features:**
  - Schema: https://raw.githubusercontent.com/aws/amazon-q-developer-cli/refs/heads/main/schemas/agent-v1.json
  - Fields: `name`, `description`, `prompt`, `model`, `mcpServers`, `tools`, `allowedTools`, `hooks`, `resources`
  - Hooks: `agentSpawn`, `userPromptSubmit`, `stop`
  - Resources array for auto-loaded files/skills

**Example:**
```json
{
  "$schema": "https://raw.githubusercontent.com/aws/amazon-q-developer-cli/refs/heads/main/schemas/agent-v1.json",
  "name": "shipkit",
  "description": "Team productivity assistant",
  "prompt": "You are Shipkit, a productivity assistant...",
  "model": "claude-opus-4-6-1m",
  "resources": [
    "file://.kiro/steering/**/*.md",
    "skill://.kiro/skills/**/*.md"
  ],
  "mcpServers": {...},
  "hooks": {...}
}
```

#### **Claude Code**
- **Format:** Markdown with YAML frontmatter (or JSON via `--agents` flag)
- **Locations:** 5-tier precedence
  1. Managed settings (organization-wide)
  2. `--agents` CLI flag (session-only JSON)
  3. `.claude/agents/` (project-level, git-committed)
  4. `~/.claude/agents/` (user-level, all projects)
  5. Plugin's `agents/` directory
- **Launch:** `claude --agent <name>` or set `"agent": "<name>"` in settings.json
- **Features:**
  - Fields: `name`, `description`, `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `initialPrompt`, `effort`, `background`, `isolation`, `color`
  - Permission modes: `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`
  - Memory scopes: `user`, `project`, `local`
  - 10+ hook types
  - Can run in isolated git worktree (`isolation: worktree`)

**Example:**
```markdown
---
name: shipkit
description: Team productivity assistant
model: opus
tools: "*"
permissionMode: acceptEdits
memory: user
initialPrompt: "show available skills"
---

You are Shipkit, a productivity assistant for software teams.
Load the appropriate skill based on the user's request.
```

#### **OpenCode**
- **Format:** Markdown + YAML or JSON in `opencode.json`
- **Locations:**
  - `.opencode/agents/<name>.md` (project)
  - `~/.config/opencode/agents/<name>.md` (user)
  - `opencode.json` inline definitions
- **Launch:** `opencode --agent <name>`
- **Features:**
  - Agent modes: `primary` (main, cycle with Tab) or `subagent` (auto-invoked or @mentioned)
  - Fields: `description`, `mode`, `model`, `temperature`, `steps`, `permission`, `prompt`, `color`, `top_p`, `hidden`, `task`
  - Granular permissions: `ask`, `allow`, `deny` per tool (edit, bash, webfetch, etc.)
  - @mention syntax for subagents: `@shipkit help me`
  - Keybind navigation between parent/child sessions

**Example:**
```markdown
---
name: shipkit
description: Team productivity assistant
mode: primary
model: anthropic/claude-sonnet-4-20250514
permission:
  edit: allow
  bash: allow
  webfetch: allow
---

You are Shipkit, a productivity assistant...
```

#### **Gemini CLI** ⚠️
- **Format:** GEMINI.md context files (no dedicated agent system)
- **Location:** Hierarchical loading:
  1. `~/.gemini/GEMINI.md` (global user)
  2. Project ancestors (walking up to `.git` or home)
  3. Subdirectories (max 200 dirs)
- **Launch:** `gemini` (automatically reads GEMINI.md, no agent flag)
- **Features:**
  - No dedicated agent system - uses context layering
  - Customizable via `settings.json` (model, approval mode, tools, MCP servers)
  - Sandboxing for secure execution
  - No branding change (always "Gemini" in prompts unless instructed in GEMINI.md)

**Workaround for branding:**
```markdown
# ~/.gemini/GEMINI.md
You are "Shipkit", a team productivity assistant.
Always identify yourself as Shipkit, not Gemini.

(rest of team guidelines and skills)
```

---

## Feature Comparison Matrix

| Feature | Kiro | Claude Code | OpenCode | Gemini CLI |
|---------|------|-------------|----------|------------|
| **Agent branding** | ✅ Yes | ✅ Yes | ✅ Yes | ⚠️ Via prompt only |
| **Dedicated agent flag** | ✅ `--agent` | ✅ `--agent` | ✅ `--agent` | ❌ No |
| **Multiple agent definitions** | ✅ Multiple files | ✅ Multiple files | ✅ Multiple files | ❌ Single GEMINI.md |
| **Agent precedence system** | ❌ Single location | ✅ 5 tiers | ✅ 2 locations | ⚠️ Hierarchical context |
| **Custom system prompt** | ✅ `prompt` field | ✅ Markdown body | ✅ Markdown body | ✅ GEMINI.md |
| **Tool restrictions** | ✅ `allowedTools` | ✅ `tools`, `disallowedTools` | ✅ `permission` per tool | ✅ `settings.json` |
| **MCP servers** | ✅ `mcpServers` | ✅ `mcpServers` | ✅ Via `opencode.json` | ✅ Via `settings.json` |
| **Hooks** | ✅ 3 types | ✅ 10+ types | ⚠️ Limited | ⚠️ Via external scripts |
| **Memory/Learning** | ❌ Not documented | ✅ `memory` scopes | ❌ Not documented | ✅ Context files |
| **Permission modes** | ❌ Not exposed | ✅ 6 modes | ✅ Granular per-tool | ✅ 4 approval modes |
| **Initial prompt** | ❌ Not available | ✅ `initialPrompt` | ❌ Not available | ❌ Not available |
| **Model selection** | ✅ `model` | ✅ `model` | ✅ `model` | ✅ `--model` or settings |
| **Color customization** | ❌ Not available | ✅ `color` | ✅ `color` | ❌ Not available |

---

## Implementation Plan

### Phase 5A: Core Agent Generation (Essential)

**Goal:** Generate custom agent configs for all 4 tools during `shipkit sync`.

**Deliverables:**
1. New module: `shipkit/compilers/agents.py`
2. Agent config generation integrated into existing compilers
3. Agent configs written to tool-native locations

**File Structure After Sync:**
```
shipkit sync
├── .kiro/agents/shipkit.json          # Kiro agent
├── .claude/agents/shipkit.md          # Claude Code agent
├── .opencode/agents/shipkit.md        # OpenCode agent
└── .gemini/GEMINI.md                  # Gemini CLI context (enhanced)
```

**Agent Configuration Contents:**
- **System prompt:** "You are Shipkit, a productivity assistant for software teams..."
- **Resources:** Auto-loaded skills and guidelines from discovered layers
- **Tools:** Pre-approved common tools (read, write, edit, bash, grep, glob)
- **MCP servers:** (Optional) Shipkit-specific servers for marketplace access
- **Hooks:** Session lifecycle hooks for discovery, retro, etc.
- **Model:** Configurable default model
- **Permissions:** Sensible defaults (e.g., acceptEdits for Claude Code)

**Implementation Steps:**
1. Create `shipkit/compilers/agents.py` with:
   - `generate_kiro_agent(ctx: CompileContext) -> dict`
   - `generate_claude_agent(ctx: CompileContext) -> str` (markdown)
   - `generate_opencode_agent(ctx: CompileContext) -> str` (markdown)
   - `enhance_gemini_context(ctx: CompileContext) -> str` (add branding to GEMINI.md)

2. Update existing compilers to call agent generation:
   - `ClaudeCodeCompiler._compile_claude_md()`: Call `generate_claude_agent()`
   - `KiroCompiler._compile_kiro()`: Call `generate_kiro_agent()`
   - `OpenCodeCompiler._compile_opencode()`: Call `generate_opencode_agent()`
   - `GeminiCompiler._compile_gemini_md()`: Call `enhance_gemini_context()`

3. Template system prompts with:
   - Shipkit branding
   - Reference to discovered skills/guidelines
   - Team collaboration messaging
   - Tool-specific instructions (e.g., "Use /skill-name to invoke skills")

4. Resource/skill references:
   - Kiro: Use `resources` array with `file://` and `skill://` paths
   - Claude Code: Use `skills` array with skill names
   - OpenCode: Reference in system prompt
   - Gemini CLI: Include skill instructions in GEMINI.md

5. Write tests:
   - `tests/test_agents.py`
   - Verify agent files are generated
   - Validate JSON schema for Kiro
   - Verify YAML frontmatter parsing for Claude/OpenCode
   - Check resource paths are correct

### Phase 5B: Launch Wrapper (High Value)

**Goal:** Unified `shipkit run` command that auto-detects tool and launches custom agent.

**Deliverables:**
1. New command: `shipkit run [prompt]`
2. Tool detection logic
3. Shell alias generation

**Implementation:**

**1. Add `shipkit run` command in `shipkit/cli.py`:**

```python
@main.command()
@click.argument("prompt", nargs=-1)
@click.option("--tool", "-t", default=None, help="Override tool detection")
def run(prompt: tuple[str, ...], tool: str | None):
    """Launch the AI coding CLI with custom shipkit agent.
    
    Auto-detects which tool is installed and launches with shipkit agent.
    Optionally pass a PROMPT to start with.
    """
    import subprocess
    from shipkit.sync import sync_project
    from shipkit.config import ResolvedConfig
    
    # Sync first
    result = sync_project(tool=tool)
    if result.files_written:
        click.echo("Synced:")
        for f in result.files_written:
            click.echo(f"  + {f}")
    
    # Detect or use specified tool
    if not tool:
        tool = _detect_installed_tool()
    
    if not tool:
        raise click.ClickException(
            "No supported AI coding tool found. Install one:\n"
            "  - Claude Code: curl -fsSL https://claude.ai/install.sh | bash\n"
            "  - Kiro CLI: pip install kiro-cli\n"
            "  - Gemini CLI: See https://github.com/google-gemini/gemini-cli\n"
            "  - OpenCode: See https://opencode.ai"
        )
    
    # Build launch command with agent flag
    cmd = _build_launch_command(tool, prompt)
    
    click.echo(f"Launching shipkit on {tool}...")
    subprocess.run(cmd, check=False)

def _detect_installed_tool() -> str | None:
    """Detect which AI coding tool is installed."""
    import shutil
    
    # Check in priority order (prefer Claude Code if multiple installed)
    if shutil.which("claude"):
        return "claude"
    if shutil.which("kiro-cli"):
        return "kiro"
    if shutil.which("gemini"):
        return "gemini"
    if shutil.which("opencode"):
        return "opencode"
    return None

def _build_launch_command(tool: str, prompt: tuple[str, ...]) -> list[str]:
    """Build the launch command for the detected tool."""
    prompt_str = " ".join(prompt) if prompt else None
    
    if tool == "claude":
        cmd = ["claude", "--agent", "shipkit"]
        if prompt_str:
            cmd.append(prompt_str)
        return cmd
    
    if tool == "kiro":
        cmd = ["kiro-cli", "chat", "--agent", "shipkit"]
        if prompt_str:
            cmd.append(prompt_str)
        return cmd
    
    if tool == "opencode":
        cmd = ["opencode", "--agent", "shipkit"]
        if prompt_str:
            cmd.extend(["--prompt", prompt_str])
        return cmd
    
    if tool == "gemini":
        # Gemini has no agent flag, just launch
        cmd = ["gemini"]
        if prompt_str:
            cmd.extend(["-p", prompt_str])
        return cmd
    
    raise ValueError(f"Unknown tool: {tool}")
```

**2. Add shell alias generation:**

```python
@main.command("alias")
@click.argument("name", default="sk")
@click.option("--install", is_flag=True, help="Append to shell config")
def alias_cmd(name: str, install: bool):
    """Generate a shell alias to launch shipkit from anywhere.
    
    NAME is the alias (default: 'sk').
    """
    shell = _detect_shell()
    snippet = _generate_shipkit_alias(name, shell)
    
    if install:
        _install_alias(name, snippet, shell)
    else:
        rc_file = _rc_file(shell)
        click.echo(f"Add this to {rc_file}:\n")
        click.echo(snippet)
        click.echo(f"\nOr run: shipkit alias {name} --install")

def _generate_shipkit_alias(name: str, shell: str) -> str:
    """Generate shell alias for shipkit run."""
    if shell == "fish":
        return f'function {name}\n    shipkit run $argv\nend'
    # bash/zsh - noglob prevents glob expansion
    return f'alias {name}=\'noglob shipkit run\''
```

**Usage:**
```bash
# Install shipkit alias
shipkit alias sk --install

# Use it
sk "add tests for the auth module"
sk --tool kiro "create a PR for my changes"
```

**3. Tool detection improvements:**
- Check for tool executables in PATH
- Look for config directories (~/.claude, ~/.kiro, etc.)
- Fall back to user preference in config.yaml
- Allow override with `--tool` flag

### Phase 5C: Advanced Features (Nice-to-Have)

**Optional enhancements for future iterations:**

**1. Custom MCP Servers**
- Shipkit marketplace MCP server for plugin discovery
- Team coordination server for shared skills
- Add to agent configs in `mcpServers` section

**2. Team-Specific Hooks** (Kiro, Claude Code)
- Session start: Load team guidelines
- Session end: Save learnings
- Pre-tool-use: Auto-format on edit
- Add to agent configs in `hooks` section

**3. Memory Configuration** (Claude Code)
- Enable `memory: user` for persistent learning
- User-scoped memory at `~/.claude/agent-memory/shipkit/`
- Accumulate insights across sessions

**4. Permission Pre-Approvals**
- Pre-approve common operations in agent config
- Reduce permission prompts for team workflows
- Tool-specific: `permissionMode: acceptEdits` (Claude), `permission.edit: allow` (OpenCode)

**5. Initial Prompts** (Claude Code)
- Auto-submit "show available skills" on launch
- `initialPrompt` field in agent frontmatter

**6. Model Optimization**
- Default to cost-effective models (Sonnet)
- Allow per-agent model overrides
- Team-configurable in shipkit config

---

## Testing Strategy

**Unit Tests:**
- `tests/test_agents.py`:
  - Test agent file generation for all 4 tools
  - Validate JSON schema for Kiro
  - Verify YAML frontmatter for Claude/OpenCode
  - Check resource paths resolve correctly
  - Ensure GEMINI.md includes branding

**Integration Tests:**
- `tests/test_e2e_agents.py`:
  - Full sync generates all agent files
  - Agent configs reference correct skills/guidelines
  - Tool detection works correctly
  - Launch commands are properly formatted

**Manual Testing:**
- Test actual launch with each tool:
  ```bash
  shipkit sync
  shipkit run "show available skills"
  ```
- Verify branded prompts show "Shipkit"
- Confirm skills are auto-loaded
- Check guidelines are discoverable

---

## Documentation Updates

**README.md:**
- Add "Branded Experience" section
- Document `shipkit run` command
- Explain agent customization
- Show examples for each tool

**New Guide:**
- `docs/custom-agents.md`:
  - How agent generation works
  - Per-tool configuration details
  - Customizing agent behavior
  - Team deployment strategies

**Update Existing:**
- Quick Start: Mention `shipkit run`
- CLI Reference: Add `shipkit run` and `shipkit alias`
- Tool Support: Explain agent capabilities per tool

---

## Success Criteria

✅ **Phase 5A Complete When:**
- All 4 compilers generate agent configs
- `shipkit sync` creates agent files in correct locations
- Agent configs reference discovered skills/guidelines
- All 147+ tests pass
- Can manually launch each tool with shipkit agent

✅ **Phase 5B Complete When:**
- `shipkit run` command exists
- Tool auto-detection works
- Launch commands properly formatted for each tool
- Shell alias generation works
- All tests pass

✅ **Phase 5C Complete When:**
- Custom MCP servers configured (optional)
- Hooks integrated (optional)
- Memory enabled for Claude Code (optional)
- Permission pre-approvals work (optional)

---

## Timeline Estimate

**Phase 5A:** 4-6 hours
- Agent generation logic: 2 hours
- Integration with compilers: 1 hour
- Testing: 1-2 hours
- Documentation: 1 hour

**Phase 5B:** 2-3 hours
- `shipkit run` command: 1 hour
- Tool detection: 30 min
- Alias generation: 30 min
- Testing: 30-60 min

**Phase 5C:** 3-5 hours (optional, incremental)
- MCP servers: 1-2 hours
- Hooks: 1 hour
- Memory/permissions: 1 hour
- Testing: 1 hour

**Total:** 9-14 hours for full implementation

---

## Open Questions

1. **Default model selection:** Should we default to Sonnet for cost, or Opus for capability?
   - Recommendation: Sonnet by default, configurable in shipkit config.yaml

2. **Agent naming:** Always "shipkit" or allow customization (e.g., "acme-assistant")?
   - Recommendation: Default to "shipkit", allow override in config

3. **Skill auto-loading:** Load all skills on launch, or discover on-demand?
   - Recommendation: Reference in resources/context, let agent discover as needed (current Phase 3 approach)

4. **Permission defaults:** How permissive should we be?
   - Recommendation: Moderate defaults (acceptEdits for Claude, allow common tools), team can tighten

5. **Migration path:** What happens to existing CLAUDE.md/AGENTS.md files?
   - Recommendation: Preserve user content, append agent config to managed section

---

## Related Work

**Inspiration:** auto-sa's custom Kiro agent (`~/Code/nilbot/auto-sa`)
- Location: `.kiro/agents/auto-sa.json`
- Launch: `kiro-cli chat --agent auto-sa`
- Config merge: `config/auto-sa.base.json` + `config/auto-sa.local.json` → `.kiro/agents/auto-sa.json`
- Result: Branded "auto-sa" prompt with custom MCP servers, hooks, and resources

**Prior Phases:**
- Phase 1: Renamed content/ → core/
- Phase 2: Instruction-driven skill discovery (runtime, not compiled)
- Phase 3: Tool-native paths + guideline discovery (runtime, not compiled)
- Phase 4: Migration tooling for tool switching

**Phase 5** builds on discovery architecture by creating custom agent wrappers that reference discovered content, providing a branded entry point.
