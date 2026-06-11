---
scope: global
applies-to: all projects
---

# MCP — Global Connections

Source of truth: `~/.studio/mcp/global.json`  
Activation: `python3 ~/.studio/scripts/activate.py --mcp-only`

---

## Active global connections

| Server       | Type   | Use                                                       |
|--------------|--------|-----------------------------------------------------------|
| higgsfield   | plugin | Generazione immagini e video AI                           |
| obsidian     | server | Leggi/scrivi note vault Obsidian (specs, decision log)    |

### Disabled (riattivabile con `mowgli mcp on <name>`)

| Server     | Use                                               |
|------------|---------------------------------------------------|
| notebooklm | Ricerca documenti su Google NotebookLM            |

### Skills (non MCP — invocabili come slash command)

| Skill    | Use                                                         |
|----------|-------------------------------------------------------------|
| graphify | Knowledge graph del codebase — build, query, PR impact      |

---

## Architecture

Two scopes:

| Scope  | Source of truth                  | Writes to                         |
|--------|----------------------------------|-----------------------------------|
| Global | `~/.studio/mcp/global.json`      | `~/.claude/settings.json`         |
| Local  | `.studio/mcp/local.json`         | `.claude/settings.json` (project) |

Two connection types:

| Type    | Key in settings.json  | When to use                              |
|---------|-----------------------|------------------------------------------|
| plugin  | `enabledPlugins`      | claude.ai integrated plugins (Higgsfield, Figma, Gmail…) |
| server  | `mcpServers`          | Custom MCP servers with a command/args   |

---

## Adding a new global connection

**Plugin** (claude.ai integrated):
```json
// ~/.studio/mcp/global.json → "plugins"
"figma@claude-plugins-official": true
```

**Custom MCP server**:
```json
// ~/.studio/mcp/global.json → "servers"
"my-server": {
  "command": "npx",
  "args": ["@my/mcp-server", "--arg"]
}
```

Then: `python3 ~/.studio/scripts/activate.py --mcp-only`

---

## Adding a local connection (project-specific)

Create `.studio/mcp/local.json` in the project:
```json
{
  "plugins": {},
  "servers": {
    "supabase": {
      "command": "npx",
      "args": ["@supabase/mcp-server-supabase@latest", "--project-ref", "YOUR_REF"]
    }
  }
}
```

Document it in the project's `.studio/mcp.md`.

---

## Commands

```bash
# Sync all (hooks + MCP)
python3 ~/.studio/scripts/activate.py

# Sync only MCP
python3 ~/.studio/scripts/activate.py --mcp-only

# Check status
python3 ~/.studio/scripts/activate.py --status

# Preview without writing
python3 ~/.studio/scripts/activate.py --mcp-only --dry-run

# Remove studio-managed config
python3 ~/.studio/scripts/activate.py --off
```
