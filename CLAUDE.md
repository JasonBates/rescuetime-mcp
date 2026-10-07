# RescueTime MCP Server

A FastMCP server exposing RescueTime productivity data to Claude Desktop. The tools are the `@mcp.tool` functions in `src/rescuetime_mcp/server.py`; the API client (`https://www.rescuetime.com/anapi`, key as a query parameter) is `client.py`, response models are `models.py`.

## Commands

```bash
uv run rescuetime-mcp      # run the server (stdio)
```

## Secrets

`RESCUETIME_API_KEY` comes from the Keychain via `~/.local/bin/secrets get RESCUETIME_API_KEY` (master copy in 1Password), filled in `client.py` when not already in the environment. It is not kept in `.env`, which holds non-secret settings only (template: `.env.example`). Keys are issued at https://www.rescuetime.com/anapi/manage.
