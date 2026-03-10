# Phase 0 Spike — Claude Desktop as Orchestrator

## Goal

Validate a simple question: **Can Claude Desktop coordinate two MCP servers naturally,
without any custom orchestration code?**

## The Scenario

Two agents, one job:

| Agent | Role | Tools |
|---|---|---|
| `monitor-agent` | Detects data anomalies | `check_data_health`, `list_anomalies`, `get_summary` |
| `engineer-agent` | Investigates anomalies | `investigate_anomaly`, `get_details`, `suggest_fix` |

Both servers are configured in Claude Desktop simultaneously. The test prompt:

> *"Check the data health and investigate anything suspicious."*

Claude Desktop should call monitor-agent tools, detect an anomaly, then call
engineer-agent tools to investigate — without us writing any workflow code.

## Status

- [ ] monitor-agent server built
- [ ] engineer-agent server built
- [ ] Both tested individually
- [ ] Both configured in Claude Desktop simultaneously
- [ ] Coordination validated
- [ ] Findings documented in FINDINGS.md

## Running the Spike

```bash
# From repo root — test each server individually first
uv run --directory spike/monitor-agent server.py
uv run --directory spike/engineer-agent server.py
```

### Claude Desktop Config

Copy `claude_desktop_config_example.json` from the repo root to your Claude Desktop
config location, replacing `/absolute/path/to` with your actual repo path.

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

## What We're Watching For

- Does Claude call the right server first?
- Does it pass context from monitor → engineer naturally?
- Does it synthesize a coherent final response?
- Any unexpected behavior or tool call failures?

Results go in [FINDINGS.md](FINDINGS.md) once the spike is complete.
