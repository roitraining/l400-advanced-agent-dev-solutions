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
    """Minimal session state shared by all workflow nodes."""

    phase: Literal["awaiting_incident", "awaiting_approval", "completed"] = "awaiting_incident"
    last_user_message: str = ""
    incident_report: str = ""
    triage_summary: str = ""
    risk_assessment: str = ""
    action_plan: str = ""
    human_feedback: str = ""
    final_email: str = ""


model = Gemini(
    model="gemini-flash-latest",
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
Keep output very short.
Return exactly 3 bullets: business impact, operational risk, and next-24h urgency.
Each bullet must be <= 14 words.""",
    output_key="risk_assessment",
)

action_plan_agent = Agent(
    name="action_plan_agent",
    model=model,
    instruction="""You are an incident response planner.
Keep output short and practical.
Return exactly 4 numbered steps.
Each step format: 'Owner - action'.
Each step must be <= 12 words.
No tables.""",
    output_key="action_plan",
)

revise_plan_agent = Agent(
    name="revise_plan_agent",
    model=model,
    instruction="""You revise incident action plans using human feedback.
Keep output short.
Return exactly 4 numbered steps.
Each step format: 'Owner - action'.
Each step must be <= 12 words.
No tables.""",
    output_key="action_plan",
)

email_agent = Agent(
    name="email_agent",
    model=model,
    instruction="""You are a communications specialist.
Draft a very short stakeholder update.
Output format: Subject line + 4 bullets (summary, impact, action, next update).
Each bullet must be <= 14 words.""",
    output_key="final_email",
)


def to_model_text(text: str) -> types.Content:
    return types.Content(role="model", parts=[types.Part(text=text)])


def ask_for_incident_details() -> types.Content:
    return to_model_text(
        "Please describe the incident before I run triage. Include: what happened, "
        "impacted systems/users, and urgency."
    )


def route_entry(node_input: str, ctx) -> Event:
    """Single entry router for normal flow, approval flow, and initial gating."""

    message = (node_input or "").strip()
    ctx.state["last_user_message"] = message

    phase = ctx.state.get("phase", "awaiting_incident")

    if phase == "awaiting_approval":
        return Event(actions=EventActions(route="process_approval"))

    if phase == "completed":
        return Event(
            content=to_model_text(
                "Incident workflow is complete for the current case. "
                "To start a new incident, describe it and include 'new incident'."
            )
        )

    return Event(actions=EventActions(route="collect_incident"))


def prepare_triage_prompt(ctx) -> str:
    """Store incident details and build prompt for triage agent."""

    user_message = ctx.state.get("last_user_message", "").strip()

    if not user_message:
        return (
            "No incident details were provided. Ask the user for: what happened, impacted systems, urgency, and timeline."
        )

    if "new incident" in user_message.lower():
        ctx.state["triage_summary"] = ""
        ctx.state["risk_assessment"] = ""
        ctx.state["action_plan"] = ""
        ctx.state["human_feedback"] = ""
        ctx.state["final_email"] = ""

    # Always use the latest user turn as the candidate incident report.
    ctx.state["incident_report"] = user_message
    ctx.state["phase"] = "awaiting_incident"

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


def request_human_approval(ctx) -> types.Content:
    ctx.state["phase"] = "awaiting_approval"
    return to_model_text(
        "Draft action plan ready for review:\n\n"
        f"{ctx.state.get('action_plan', '')}\n\n"
        "Human approval needed: reply with APPROVE to generate the stakeholder email, "
        "or provide feedback to revise the plan."
    )


def route_approval_decision(ctx) -> Event:
    """Branch to approve or revise path from human reply."""

    decision = ctx.state.get("last_user_message", "").strip()
    if decision.lower() == "approve":
        return Event(actions=EventActions(route="approve"))

    ctx.state["human_feedback"] = decision
    return Event(actions=EventActions(route="revise"))


def prepare_email_prompt(ctx) -> str:
    return (
        "Draft a stakeholder update email from the approved incident plan.\n\n"
        f"Incident report:\n{ctx.state.get('incident_report', '')}\n\n"
        f"Approved action plan:\n{ctx.state.get('action_plan', '')}"
    )


def finalize_approved_email(ctx) -> types.Content:
    ctx.state["phase"] = "completed"
    return to_model_text(
        "Approval complete.\n\n"
        "Output 1 - Final Action Plan:\n"
        f"{ctx.state.get('action_plan', '')}\n\n"
        "Output 2 - Stakeholder Email Draft:\n"
        f"{ctx.state.get('final_email', '')}"
    )


def prepare_revision_prompt(ctx) -> str:
    return (
        "Revise the action plan using this feedback.\n\n"
        f"Current action plan:\n{ctx.state.get('action_plan', '')}\n\n"
        f"Human feedback:\n{ctx.state.get('human_feedback', '')}"
    )


root_agent = Workflow(
    name="incident_graph_workflow",
    description="Simple ADK 2 graph workflow with sequential incident processing and human approval branching.",
    state_schema=IncidentState,
    edges=[
        (
            START,
            route_entry,
            {
                "collect_incident": prepare_triage_prompt,
                "process_approval": route_approval_decision,
            },
        ),
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
            request_human_approval,
        ),
        (
            route_approval_decision,
            {
                "approve": prepare_email_prompt,
                "revise": prepare_revision_prompt,
            },
        ),
        (prepare_email_prompt, email_agent, finalize_approved_email),
        (prepare_revision_prompt, revise_plan_agent, request_human_approval),
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
