import os
import shlex
from pathlib import Path

import google.auth
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.genai import types
from mcp import StdioServerParameters

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

MODEL = os.getenv("CHALLENGE3_MODEL", "gemini-flash-latest")

# Custom NWS MCP server (local Python process).
NWS_MCP_COMMAND = os.getenv("NWS_MCP_COMMAND", "python3")
NWS_MCP_ARGS = shlex.split(
    os.getenv("NWS_MCP_ARGS", "nws_weather_mcp/server.py")
)

# Google Maps MCP server (typically npx-based).
MAPS_MCP_COMMAND = os.getenv("MAPS_MCP_COMMAND", "npx")
MAPS_MCP_ARGS = shlex.split(
    os.getenv("MAPS_MCP_ARGS", "-y @googlemaps/mcp-server")
)

maps_mcp_env = dict(os.environ)
if os.getenv("GOOGLE_MAPS_API_KEY"):
    maps_mcp_env["GOOGLE_MAPS_API_KEY"] = os.getenv("GOOGLE_MAPS_API_KEY", "")

nws_specialist = Agent(
    name="nws_weather_specialist",
    model=Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=3)),
    instruction="""
You are a weather specialist.
Use NWS weather tools to get forecast or hourly forecast for US locations.
If needed, ask for clarification.
""",
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=NWS_MCP_COMMAND,
                    args=NWS_MCP_ARGS,
                )
            )
        )
    ],
)

maps_specialist = Agent(
    name="google_maps_specialist",
    model=Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=3)),
    instruction="""
You are a maps specialist.
Use Google Maps MCP tools for geocoding, place lookup, and routing tasks.
""",
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=MAPS_MCP_COMMAND,
                    args=MAPS_MCP_ARGS,
                    env=maps_mcp_env,
                )
            )
        )
    ],
)


root_agent = Agent(
    name="weather_maps_root_agent",
    model=Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=3)),
    instruction="""
You are a weather and navigation assistant.
Use the Google Maps specialist when a place name, address, route, distance, or coordinates are needed.
Use the NWS specialist for weather forecasts.
For weather-by-place requests, first obtain coordinates with maps, then ask NWS tools for forecast data.
""",
    tools=[AgentTool(agent=maps_specialist), 
           AgentTool(agent=nws_specialist)],
)

app = App(
    root_agent=root_agent,
    name="weather_maps_agent",
)
