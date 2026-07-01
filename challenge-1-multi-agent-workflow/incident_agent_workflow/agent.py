from google.adk.agents import Agent
from google.adk.agents import ParallelAgent
from google.adk.agents import SequentialAgent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

import os
import google.auth

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


model = Gemini(
    model="gemini-flash-latest",
    retry_options=types.HttpRetryOptions(attempts=3),
)

triage_agent = Agent(
    name="triage_agent",
    model=model,
    instruction="""You are an incident triage specialist.
If the user did not provide an incident, ask them to describe it briefly.
Otherwise return exactly 3 short bullets: incident type, affected systems, severity.""",
    output_key="triage_summary",
)

business_impact_agent = Agent(
    name="business_impact_agent",
    model=model,
    instruction="""Assess business impact from the incident and triage summary.
Return exactly 2 short bullets.""",
    output_key="business_impact",
)

operational_risk_agent = Agent(
    name="operational_risk_agent",
    model=model,
    instruction="""Assess operational risk and urgency from the incident and triage summary.
Return exactly 2 short bullets.""",
    output_key="operational_risk",
)

risk_parallel = ParallelAgent(
    name="risk_parallel",
    description="Run business impact and operational risk analysis in parallel.",
    sub_agents=[business_impact_agent, operational_risk_agent],
)

action_plan_agent = Agent(
    name="action_plan_agent",
    model=model,
    instruction="""Create a short action plan using triage_summary, business_impact, and operational_risk.
Return exactly 4 numbered steps.
Each step format: 'Owner - action'.""",
    output_key="action_plan",
)

email_agent = Agent(
    name="email_agent",
    model=model,
    instruction="""Draft a short stakeholder email using incident_report and action_plan.
Output a subject line and 4 bullets (summary, impact, action, next update).""",
    output_key="final_email",
)

final_report_agent = Agent(
    name="final_report_agent",
    model=model,
    instruction="""Return final output with two sections:
Output 1 - Action Plan (use action_plan)
Output 2 - Stakeholder Email (use final_email)
Keep it concise.""",
)

root_agent = SequentialAgent(
    name="incident_old_style_workflow",
    description="Old-style workflow using SequentialAgent and ParallelAgent.",
    sub_agents=[
        triage_agent,
        risk_parallel,
        action_plan_agent,
        email_agent,
        final_report_agent,
    ],
)

app = App(
    root_agent=root_agent,
    name="incident_agent_workflow",
)
