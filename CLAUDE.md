# RescueTime MCP Server

## Overview
A FastMCP server that exposes RescueTime productivity data to Claude Desktop via the Model Context Protocol.

## Architecture

```
rescuetime-mcp/
├── src/rescuetime_mcp/
│   ├── server.py      # FastMCP server with 5 tools
│   ├── client.py      # Async RescueTime API client
│   └── models.py      # Pydantic models for API responses
├── .env               # Non-secret settings only (gitignored)
├── .env.example       # Template showing required variables
└── pyproject.toml     # Dependencies managed by uv
```

## Key Components

### server.py - MCP Tools
- `get_today_summary()` - Daily productivity metrics
- `get_productivity_trend(days=7)` - Weekly/monthly productivity trends
- `get_activity_data(date_str, limit)` - Top apps/websites by time
- `get_category_breakdown(date_str)` - Time by category
- `get_hourly_productivity(date_str)` - Hourly productivity breakdown

### client.py - API Client
- Base URL: `https://www.rescuetime.com/anapi`
- API key passed as query parameter
- Methods: `get_daily_summary()`, `get_analytic_data()`, `get_hourly_data()`

### models.py - Data Models
- `DailySummary` - 36 fields from daily API
- `AnalyticDataRow` - Activity/category rows with productivity scores
- `HourlyData` - Hour-level productivity data

## Secrets Management
- `RESCUETIME_API_KEY` comes from the Keychain via `~/.local/bin/secrets get RESCUETIME_API_KEY` (master copy in 1Password), filled in `client.py` when not already in the environment; it is not kept in `.env`
- Required variable: `RESCUETIME_API_KEY`
- Get your key from: https://www.rescuetime.com/anapi/manage

## Running
```bash
# Run server
uv run rescuetime-mcp
```

## Dependencies
- `fastmcp>=2.0.0` - MCP framework
- `httpx` - Async HTTP client
- `pydantic>=2.0` - Data validation
- `python-dotenv` - Environment variable loading
