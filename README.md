# mcp-multi-agent

A hands-on guide to building multi-agent systems with Model Context Protocol (MCP).
Learn how to coordinate multiple MCP servers — from simple Claude Desktop orchestration
to advanced custom orchestration patterns.

> **Prerequisites**: Familiarity with individual MCP server development.
> New to MCP? Start with [mcp-agentic-starter](https://github.com/billzGH/mcp-agentic-starter) first.

## 🎯 What You'll Learn

- How Claude Desktop can orchestrate multiple MCP servers without custom code
- Patterns for designing agents with clear, complementary responsibilities
- How to build custom orchestration logic when you need more control
- State management and shared memory between agents
- Real-world multi-agent workflow design

## 🗺️ Learning Path

### Phase 0: Spike — Does It Work? *(current)*

Validate that Claude Desktop can naturally coordinate two MCP servers without any
orchestration code written by us.

**Monitor Agent** detects anomalies → **Engineer Agent** investigates them →
Claude Desktop figures out how to use them together.

```filetree
spike/
├── monitor-agent/    # Detects data anomalies
├── engineer-agent/   # Investigates anomalies
└── FINDINGS.md       # What we learned
```

### Phase 1: Claude Desktop as Orchestrator *(planned)*

Polished examples using Claude Desktop to coordinate specialized agents.
No custom orchestration code — Claude IS the orchestrator.

### Phase 2: Custom Orchestrator *(planned)*

An MCP server that programmatically manages workflows between other servers.
More control, closer to production patterns.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/billzGH/mcp-multi-agent.git
cd mcp-multi-agent

# Install UV (if not already installed)
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install dependencies
uv sync

# Run a spike server
uv run --directory spike/monitor-agent server.py
uv run --directory spike/engineer-agent server.py
```

### Claude Desktop Config

Copy `claude_desktop_config_example.json` to:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Replace `/absolute/path/to` with your actual repo path.

## 📚 Repository Structure

```filetree
mcp-multi-agent/
├── CLAUDE.md                          # Context file for Claude instances (read first)
├── claude_desktop_config_example.json # Claude Desktop config for spike servers
├── spike/                             # Phase 0: validation spike
│   ├── monitor-agent/server.py        # Anomaly detection MCP server
│   ├── engineer-agent/server.py       # Anomaly investigation MCP server
│   ├── FINDINGS.md                    # Spike results and learnings
│   └── README.md
├── examples/                          # Phase 1+: polished examples (planned)
├── docs/                              # Architecture guides and patterns
└── .github/                           # Issue templates, PR template
```

## 🔗 Related

- [mcp-agentic-starter](https://github.com/billzGH/mcp-agentic-starter) — Learn individual MCP server development first
- [MCP Documentation](https://modelcontextprotocol.io/docs)
- [Anthropic MCP Guide](https://docs.anthropic.com/en/docs/build-with-claude/mcp)

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📝 License

MIT License — free to use for learning and commercial projects.
