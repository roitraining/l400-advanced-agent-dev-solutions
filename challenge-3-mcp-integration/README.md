# Challenge 3 Solution: External Systems with MCP

This folder contains an independent solution project for Challenge 3.

## Goal
Connect an ADK v2 agent to MCP servers so it can:
- Read from and write to backend systems via tools
- Avoid direct database access
- Run with a custom MCP server for a legacy system

## Scope For This Lab
Keep this project self-contained and runnable on its own.

## Status
Implemented with:
- ADK agent scaffolded via `agents-cli`
- Custom MCP server for NWS weather forecasts
- Google Maps MCP integration

## Architecture
- Root agent: `weather_maps_root_agent`
- Specialist agent tool 1: `google_maps_specialist`
  - Uses the hosted Maps Experience MCP server (`https://mapstools.googleapis.com/mcp`)
- Specialist agent tool 2: `nws_weather_specialist`
  - Uses custom local MCP server (`nws_weather_mcp/server.py`)

Flow:
1. Root routes place/address requests to Maps tools.
2. Root routes forecast retrieval to NWS tools.
3. For place-based weather questions, root can use Maps to get coordinates first, then use NWS.

## Project Layout
- `weather_maps_agent/agent.py` - ADK agent team
- `nws_weather_mcp/server.py` - custom MCP server (NWS-backed)
- `agents-cli-manifest.yaml` - agents-cli project metadata

## Prerequisites
- `agents-cli` installed (`agents-cli --version`)
- Python 3.11+
- ADC configured for Google Cloud
- Google Maps API key sent as the `X-Goog-Api-Key` header
- Maps Experience agent tools API enabled on the project and on that key
- Billing enabled on the GCP project used by your Maps API key

## Environment Variables
- `GOOGLE_MAPS_API_KEY` (required; sent as `X-Goog-Api-Key` to `https://mapstools.googleapis.com/mcp`)
- `NWS_USER_AGENT` (recommended; identify your app/email for NWS)

Optional overrides:
- `CHALLENGE3_MODEL` (default: `gemini-4-hydrogen`)
- `NWS_MCP_COMMAND` (default: `python3`)
- `NWS_MCP_ARGS` (default: `nws_weather_mcp/server.py`)

Use a local `.env` file so secrets are not committed:
```bash
cp .env.example .env
# edit .env with your real values
```

`.env` is ignored by git in this project.

## Install And Run (Local)
```bash
cd ./challenge-3-mcp-integration
source .venv/bin/activate
agents-cli install
cp .env.example .env
# edit .env with your real keys/secrets

agents-cli playground
```

Important:
- Run from the project root (`challenge-3-mcp-integration`), not from `weather_maps_agent`.

## Preflight Checks
```bash
cd ./challenge-3-mcp-integration
source .venv/bin/activate

# Confirm key is loaded from .env in this shell.
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('key-set:', bool(os.getenv('GOOGLE_MAPS_API_KEY')))"

# Optional import smoke test.
python -c "from weather_maps_agent.agent import app, root_agent; print(app.name, root_agent.name)"
```

## Quick Test Prompts
- `What is the weather forecast for Pike Place Market tomorrow?`
- `Give me the next 12 hours forecast for Seattle.`
- `What is the route distance from Space Needle to Sea-Tac Airport, and what weather should I expect at departure?`

## Notes
- NWS coverage is US-focused (api.weather.gov).
- The custom MCP weather server exposes:
  - `forecast_by_point(latitude, longitude)`
  - `hourly_forecast_by_point(latitude, longitude)`
