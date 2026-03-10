# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

`mcp-multi-agent` is the second repository in a two-repo learning series:

1. **[mcp-agentic-starter](https://github.com/billzGH/mcp-agentic-starter)** — Learn to build individual MCP servers *(start here)*
2. **mcp-multi-agent** (this repo) — Learn to coordinate multiple MCP servers as a multi-agent system

**Prerequisites**: Familiarity with individual MCP server development. Complete mcp-agentic-starter first.

## Commands

```bash
# Install dependencies (uses UV)
uv sync

# Install optional dependency groups
uv sync --extra api        # Mock API support (fastapi, uvicorn)
uv sync --extra dev        # Dev tools (pytest, pytest-asyncio, black, ruff)
uv sync --all-extras       # All of the above

# Run spike servers (for testing or Claude Desktop integration)
uv run --directory spike/monitor-agent server.py
uv run --directory spike/engineer-agent server.py

# Lint and format
uv run ruff check .
uv run black .

# Run tests (requires dev extras)
uv sync --extra dev
uv run pytest tests/ -v
```

## Current Phase: Phase 0 — Spike

**Status**: In progress — servers not yet built.

**Goal**: Validate that Claude Desktop can coordinate two MCP servers naturally, without
any custom orchestration code.

**The spike scenario**:

- `spike/monitor-agent/server.py` — detects anomalies in a dataset
- `spike/engineer-agent/server.py` — investigates anomalies in detail
- Both are configured in Claude Desktop simultaneously
- Test prompt: *"Check the data health and investigate anything suspicious."*
- Success = Claude calls monitor tools, detects an anomaly, then calls engineer tools
  to investigate — no orchestration code written by us

**What to build next**:

1. `spike/monitor-agent/server.py` — minimal MCP server, 2-3 tools
2. `spike/engineer-agent/server.py` — minimal MCP server, 2-3 tools
3. Small sample dataset for the spike scenario
4. Test both servers individually, then together in Claude Desktop
5. Document findings in `spike/FINDINGS.md`

## Architecture

### MCP Server Pattern

All servers follow the same pattern as mcp-agentic-starter:

1. Create a `Server` instance: `server = Server("name")`
2. Register a tool list handler: `@server.list_tools()` returning `List[Tool]` with JSON schemas
3. Register a tool call handler: `@server.call_tool()` dispatching on tool name, returning `List[TextContent]`
4. Run via stdio transport in `main()`:

   ```python
   async with stdio_server() as (read_stream, write_stream):
       await server.run(read_stream, write_stream, server.create_initialization_options())
   ```

All tool calls return `List[TextContent]` and handle exceptions internally, returning
error messages as text rather than raising.

### Planned Structure

```filetree
mcp-multi-agent/
├── spike/                        # Phase 0: validate Claude Desktop as orchestrator
│   ├── monitor-agent/server.py   # Anomaly detection MCP server
│   ├── engineer-agent/server.py  # Anomaly investigation MCP server
│   ├── FINDINGS.md               # Spike results and learnings
│   └── README.md
├── examples/                     # Phase 1+: polished coordination examples (planned)
├── docs/                         # Architecture guides and patterns
├── tests/                        # Test suite (mirrors mcp-agentic-starter pattern)
└── claude_desktop_config_example.json
```

### Architecture Decision Log

| Decision | Choice | Rationale |
| --- | --- | --- |
| Phase 0 orchestration | Claude Desktop as orchestrator | Validate simplest approach before adding complexity |
| Repo separation | Separate from mcp-agentic-starter | Different audiences, different complexity levels |
| Starting scenario | Monitor + Engineer | Clear roles, testable handoff, realistic use case |
| Future Phase 1 | Claude Desktop coordination examples | Build on validated spike pattern |
| Future Phase 2 | Custom orchestrator MCP server | Programmatic control when Claude Desktop isn't enough |

## Code Style

- Line length: 100 characters (black + ruff)
- Target: Python 3.10+
- Ruff rules: E, F, I, N, W
- Tests use pytest-asyncio with `asyncio_mode = "auto"`

## Contributing

### Pull Requests

Always use the template at `.github/pull_request_template.md` when opening PRs. Use
feature branches (`feature/...`) for new functionality and `fix/...` for bug fixes —
never commit directly to `main`.

### Claude Desktop Config

`claude_desktop_config_example.json` at the repo root shows how to wire up the spike
servers. Copy it to the Claude Desktop config location and replace `/absolute/path/to`
with the actual repo path.

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
