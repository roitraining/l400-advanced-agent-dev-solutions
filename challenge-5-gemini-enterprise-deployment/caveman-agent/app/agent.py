import os

import google.auth
from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.tools import google_search

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

MODEL = os.getenv("CHALLENGE5_MODEL", "gemini-flash-latest")

root_agent = LlmAgent(
    name="caveman_agent",
    model=MODEL,
    description="Caveman-style assistant that uses Google Search.",
    instruction="""
You are Caveman Agent.
Talk in short, simple caveman style.
Use plain words and brief sentences.

When user asks for facts, current events, or anything time-sensitive,
use Google Search first.

If search is needed, summarize what you found clearly and keep the
caveman tone.
If you do not find a reliable answer, say so plainly.
""",
    tools=[google_search],
)

app = App(
    root_agent=root_agent,
    name="app",
)
