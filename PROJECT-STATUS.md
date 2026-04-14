# Shipkit Development Context

## Current State (2026-04-14)

Shipkit has completed a major architectural transformation to **instruction-driven discovery** - moving from compile-time skill/guideline aggregation to runtime agent discovery.

### Architecture Status

**Completed Phases:**
- ✅ **Phase 1:** Foundation - Renamed `content/` → `core/`
- ✅ **Phase 2:** Skill Discovery - Skills discovered at runtime, not compiled
- ✅ **Phase 3:** Tool-Native Paths + Guideline Discovery - Guidelines also runtime-discovered
- ✅ **Phase 4:** Migration Tooling - Seamless tool switching with `shipkit migrate`
- ✅ **Phase 5A:** Custom Agent Generation - Branded "shipkit" agents for all 4 tools

**In Progress:**
- 🚧 **Phase 5B:** Launch Wrapper - Unified `shipkit run` command

See [PHASE-5-PLAN.md](PHASE-5-PLAN.md) for detailed implementation plan.

### How Discovery Works Now

**Skills:**
- Agents discover from tool-native locations (`.claude/skills/`, `~/.kiro/skills/`, etc.)
- No compilation - agents read SKILL.md files directly at runtime
- Cascading logic applied by agent following guideline instructions

**Guidelines:**
- Agents discover from tool-native locations (`.claude/guidelines/`, `~/.kiro/steering/`, etc.)
- No compilation - agents read guideline .md files directly at runtime
- Cascading logic applied by agent

**What's Still Compiled:**
- Discovery instructions (CLAUDE.md, AGENTS.md, GEMINI.md) - ~12k chars each
- Hooks (tool-specific formats)
- MCP servers (tool-specific locations)

### Directory Structure

```
~/.config/shipkit/
├── core/                      ← Package core content (shipped with shipkit)
│   ├── guidelines/            ← 8 core guidelines
│   ├── skills/                ← 21 core skills
│   ├── hooks/                 ← 5 hooks + lib
│   ├── subagents/             ← 3 subagent definitions
│   └── mcp.json               ← Default MCP servers
└── plugins/                   ← Marketplace plugins (tool-agnostic)
    └── <plugin-name>/
        ├── plugin.yaml
        ├── skills/
        ├── guidelines/
        └── hooks/

# Tool-native user content (example for Claude Code)
~/.claude/
├── skills/                    ← User personal skills
└── guidelines/                ← User personal guidelines

# Tool-native project content
.claude/
├── skills/                    ← Team-shared skills (committed to git)
└── guidelines/                ← Team-shared guidelines (committed to git)
```

### Supported Tools (4)

1. **Claude Code** - CLAUDE.md, .claude/skills/, ~/.claude/skills/
2. **Kiro** - .kiro/steering/, ~/.kiro/steering/ (uses "steering" not "guidelines")
3. **Gemini CLI** - GEMINI.md, .gemini/skills/, ~/.gemini/skills/
4. **OpenCode** - AGENTS.md, .opencode/skills/, ~/.opencode/skills/

### Key Principles

**1. Tool-Native Conventions**
- Respect each tool's native paths and terminology
- Kiro: uses "steering" not "guidelines"
- OpenCode: uses AGENTS.md not OPENCODE.md
- Each tool gets what it expects

**2. Runtime Discovery**
- Skills: Discovered on-demand when invoked
- Guidelines: Discovered at session start
- Agent applies cascading logic (extends: true/false)
- No compilation overhead

**3. Plugins = Complex Infrastructure**
- Plugins: MCP servers, hooks, dependencies (complex)
- Skills: Just SKILL.md (can share directly without "plugin" wrapper)
- Marketplace can have both

**4. No Backward Compatibility**
- 0.1.0 not published yet (only 0.0.1 placeholder on PyPI)
- No users to migrate
- Clean break, simplified architecture

### What Changed from auto-sa

Shipkit was inspired by auto-sa but differentiated:
- Removed "steering" terminology → "guidelines" (more developer-friendly)
- CLI-agnostic (works with Claude Code, Kiro, Gemini, OpenCode)
- Discovery architecture (not compilation)
- Agent Skills standard compliance
- Public marketplace (not internal-only)

### Recent Major Changes

**Discovery Architecture (Phases 1-3):**
- Skills and guidelines discovered at runtime by agents
- Tool-specific discovery instructions generated per tool
- Agents apply cascading logic (not Python)
- Compilers simplified by ~70 lines
- Output files contain only discovery instructions (~12k chars)

**Self-Learning:**
- Interactive and visible (not hidden background)
- Works on all tools (uses whatever LLM provider you have)
- Agent analyzes sessions in-conversation when you say "retro"
- No separate API keys needed

**Terminology:**
- "steering" → "guidelines" (except Kiro uses native "steering")
- "content/" → "core/" (package core only)
- Project-specific layer removed (use repo instead)

### Test Coverage

- 140 tests passing
- 4 compilers fully tested
- E2e tests for discovery mode
- Cross-tool compatibility validated

### Known Issues / TODO

**Future Considerations:**
- Permission check in `shipkit init` for ~/.config/shipkit/ access
- Performance benchmarking of runtime discovery
- Improve tool detection in `detect_tool_mismatch.py` hook (currently relies on env vars/parent process)
- Consider adding psutil as optional dependency for better process detection

### Development Notes

**Always use feature branches** - Never push directly to main.

**Testing:**
```bash
pytest tests/ -v          # Run all tests
pytest tests/ -k e2e      # E2e tests only
python -m shipkit.lint    # Content validation
```

**Architecture Decision Log:**
- Discovery > Compilation (less code, more flexible)
- Tool-native > Abstraction (respect conventions)
- Interactive > Background (transparency, trust)
- Simplicity > Features (ship small, iterate)

### Quick Reference

**Core locations:**
- Skills: `shipkit/core/skills/`
- Guidelines: `shipkit/core/guidelines/`
- Hooks: `shipkit/core/hooks/`

**Discovery templates:**
- Skills: `shipkit/compilers/discovery_template.py`
- Guidelines: `shipkit/compilers/guideline_discovery_template.py`

**Compilers:**
- `shipkit/compilers/claude.py` (226 lines)
- `shipkit/compilers/kiro.py` (359 lines)
- `shipkit/compilers/gemini.py` (310 lines)
- `shipkit/compilers/opencode.py` (338 lines)

### Session Summary (2026-04-13 to 2026-04-14)

**Total work:** 31 PRs (planned), ~9 hours
**Code changes:** +4300 lines, -592 lines removed
**Major features:** Discovery architecture (Phases 1-4), 4 tool compilers, marketplace, self-learning, migration tooling

**Key achievement:** Transformed from compilation-based to instruction-driven discovery architecture. Skills and guidelines now discovered at runtime. Migration tooling enables seamless switching between AI coding tools.

**Phase 4 deliverables:**
- `shipkit migrate --to <tool>` command with dry-run support
- `/migrate-tool` skill for interactive migration
- `detect_tool_mismatch.py` hook for auto-detection
- 7 migration test cases (all passing)
- README and CHANGELOG updates documenting migration features
