from typing import Literal

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions
from google.adk.models import Gemini
from google.adk.workflow import START
from google.adk.workflow import Workflow
from google.genai import types
from pydantic import BaseModel

import os
import google.auth

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


class IncidentState(BaseModel):
    """State for the simple graph workflow version."""

    incident_report: str = ""
    triage_summary: str = ""
    risk_assessment: str = ""
    action_plan: str = ""
    final_email: str = ""
    last_user_message: str = ""
    phase: Literal["awaiting_incident", "completed"] = "awaiting_incident"


model = Gemini(
    model="gemini-4-hydrogen",
    retry_options=types.HttpRetryOptions(attempts=3),
)

triage_agent = Agent(
    name="triage_agent",
    model=model,
    instruction="""You are an incident triage specialist.
If the message is not a real incident report, output exactly:
ASK_FOR_INCIDENT: Please describe the incident (what happened, impacted systems/users, urgency).

If it is a real incident report, keep output very short and return exactly 3 bullets:
- incident type
- affected systems
- severity (Low/Medium/High/Critical)
Each bullet must be <= 12 words.""",
    output_key="triage_summary",
)

risk_agent = Agent(
    name="risk_agent",
    model=model,
    instruction="""You are a risk analyst.
Return exactly 3 short bullets: business impact, operational risk, next-24h urgency.
Each bullet <= 14 words.""",
    output_key="risk_assessment",
)

action_plan_agent = Agent(
    name="action_plan_agent",
    model=model,
    instruction="""You are an incident response planner.
Return exactly 4 numbered steps.
Each step format: 'Owner - action'.
Each step <= 12 words.""",
    output_key="action_plan",
)

email_agent = Agent(
    name="email_agent",
    model=model,
    instruction="""Draft a very short stakeholder update.
Output: Subject line + 4 bullets (summary, impact, action, next update).
Each bullet <= 14 words.""",
    output_key="final_email",
)


def to_model_text(text: str) -> types.Content:
    return types.Content(role="model", parts=[types.Part(text=text)])


def capture_input(node_input: str, ctx) -> Event:
    message = (node_input or "").strip()
    ctx.state["last_user_message"] = message
    if ctx.state.get("phase", "awaiting_incident") == "completed":
        ctx.state["phase"] = "awaiting_incident"
    return Event(actions=EventActions(route="collect_incident"))


def prepare_triage_prompt(ctx) -> str:
    user_message = ctx.state.get("last_user_message", "").strip()
    ctx.state["incident_report"] = user_message
    return f"Incident report:\n{ctx.state['incident_report']}"


def route_after_triage(ctx) -> Event | types.Content:
    triage_summary = (ctx.state.get("triage_summary", "") or "").strip()
    if triage_summary.startswith("ASK_FOR_INCIDENT:"):
        message = triage_summary.split(":", 1)[1].strip() or "Please describe the incident."
        return to_model_text(message)
    return Event(actions=EventActions(route="continue"))


def prepare_risk_prompt(ctx) -> str:
    return (
        "Evaluate risk for this incident.\n\n"
        f"Incident report:\n{ctx.state.get('incident_report', '')}\n\n"
        f"Triage summary:\n{ctx.state.get('triage_summary', '')}"
    )


def prepare_action_plan_prompt(ctx) -> str:
    return (
        "Create an actionable response plan.\n\n"
        f"Incident report:\n{ctx.state.get('incident_report', '')}\n\n"
        f"Triage summary:\n{ctx.state.get('triage_summary', '')}\n\n"
        f"Risk assessment:\n{ctx.state.get('risk_assessment', '')}"
    )


def prepare_email_prompt(ctx) -> str:
    return (
        "Draft a stakeholder update email from this plan.\n\n"
        f"Incident report:\n{ctx.state.get('incident_report', '')}\n\n"
        f"Action plan:\n{ctx.state.get('action_plan', '')}"
    )


def finalize_outputs(ctx) -> types.Content:
    ctx.state["phase"] = "completed"
    return to_model_text(
        "Workflow complete.\n\n"
        "Output 1 - Action Plan:\n"
        f"{ctx.state.get('action_plan', '')}\n\n"
        "Output 2 - Stakeholder Email:\n"
        f"{ctx.state.get('final_email', '')}"
    )


root_agent = Workflow(
    name="incident_graph_workflow_simple",
    description="Simple graph workflow: triage -> risk -> action plan -> email.",
    state_schema=IncidentState,
    edges=[
        (START, capture_input, {"collect_incident": prepare_triage_prompt}),
        (
            prepare_triage_prompt,
            triage_agent,
            route_after_triage,
            {
                "continue": prepare_risk_prompt,
            },
        ),
        (
            prepare_risk_prompt,
            risk_agent,
            prepare_action_plan_prompt,
            action_plan_agent,
            prepare_email_prompt,
            email_agent,
            finalize_outputs,
        ),
    ],
)

app = App(
    root_agent=root_agent,
    name="incident_agent_graph_workflow",
)
