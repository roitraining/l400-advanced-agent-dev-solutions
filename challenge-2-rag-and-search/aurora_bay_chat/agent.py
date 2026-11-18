import os

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools import VertexAiSearchTool, google_search

import google.auth

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

MODEL = os.getenv("AURORA_BAY_MODEL", "gemini-4-hydrogen")
DISCOVERY_ENGINE_DATASTORE_FULL_NAME = os.getenv(
    "DISCOVERY_ENGINE_DATASTORE_FULL_NAME",
    f"projects/{os.environ['GOOGLE_CLOUD_PROJECT']}/locations/global/collections/default_collection/dataStores/aurora-bay-faqs-ad63b7",
)

private_docs_subagent = LlmAgent(
    name="aurora_bay_private_docs_subagent",
    model=MODEL,
    description="Answers questions using the Aurora Bay private datastore.",
    instruction="""
Use the datastore search tool to answer questions from Aurora Bay private content.
If the datastore does not contain the answer, say you could not find it in private docs.
""",
    tools=[VertexAiSearchTool(data_store_id=DISCOVERY_ENGINE_DATASTORE_FULL_NAME)],
)

web_search_subagent = LlmAgent(
    name="aurora_bay_web_search_subagent",
    model=MODEL,
    description="Answers questions using live Google Search.",
    instruction="""
Use Google Search for up-to-date public information and cite what you found succinctly.
""",
    tools=[google_search],
)

root_agent = LlmAgent(
    name="aurora_bay_chat",
    model=MODEL,
    description="Routes Aurora Bay questions to private datastore or live web search using specialist agent tools.",
    instruction="""
You are the Aurora Bay assistant.
Use aurora_bay_private_docs_subagent for questions about internal or local Aurora Bay knowledge.
Use aurora_bay_web_search_subagent for current events or when private docs likely do not contain the answer.
If unsure, try private docs first, then web search.
""",
    tools=[
        AgentTool(agent=private_docs_subagent),
        AgentTool(agent=web_search_subagent),
    ],
)
