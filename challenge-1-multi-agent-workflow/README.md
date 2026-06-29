# Challenge 1 Solution: Multi-Agent Workflow with ADK

This folder contains an independent solution project for Challenge 1.

## Goal
Build a multi-agent workflow using Google Agent Development Kit (ADK) v2 with:
- A root routing agent
- Specialized sub-agents
- Bidirectional handoffs
- Shared session state across the conversation

## Scope For This Lab
Keep this project self-contained and runnable on its own.

## Status
Implemented with an ADK 2 Graph Workflow.

## What This Agent Demonstrates
- Root workflow that routes user turns by current phase
- Specialized agents for triage, risk assessment, action planning, plan revision, and email drafting
- Shared workflow state passed across steps
- Human-in-the-loop approval gate before final email generation
- Branching behavior:
  - `APPROVE` -> generate final stakeholder email
  - feedback text -> revise plan and ask for approval again

## Prerequisites
- Python virtual environment created at `.venv`
- `agents-cli` installed (`agents-cli --version`)
- Google Cloud project configured (`l400-adv-agent-dev-solutions`)
- Vertex AI API enabled for the project

## Run The Agent In Playground
From this folder:

```bash
cd /Users/doug/GitHub/l400-advanced-agent-dev-solutions/challenge-1-multi-agent-workflow
source .venv/bin/activate
agents-cli install
agents-cli playground
```

If browser launch does not happen automatically, use the local URL shown in terminal.

## Quick CLI Test (No Playground)
```bash
cd /Users/doug/GitHub/l400-advanced-agent-dev-solutions/challenge-1-multi-agent-workflow
source .venv/bin/activate
agents-cli run "Database outage impacting checkout and payments for 20 minutes"
```

## Manual Test Scenarios

### Scenario 1: Happy Path (Approve)
1. Send incident details:
	`Database outage impacting checkout and payments for 20 minutes; customers cannot complete purchases.`
2. Wait for triage + risk + action plan.
3. Reply:
	`APPROVE`
4. Expected:
	Final stakeholder email is generated.

### Scenario 2: Revision Loop
1. Send incident details:
	`API latency spike in auth service, users seeing login timeouts for 10 minutes.`
2. Wait for draft plan.
3. Reply with feedback:
	`Please make the plan shorter (4 steps max) and include a customer status-page update within 10 minutes.`
4. Expected:
	Revised action plan is returned and approval is requested again.
5. Reply:
	`APPROVE`
6. Expected:
	Final email is generated from revised plan.

### Scenario 3: Start A New Incident After Completion
After a completed flow, send:
`new incident: payment API intermittent 500 errors affecting mobile checkout`

Expected:
- Workflow clears prior draft outputs and starts the sequential triage flow for the new incident.

## Useful Commands
```bash
# Show project metadata
agents-cli info

# One-shot run
agents-cli run "hello"

# Stop a lingering local run server (if needed)
agents-cli run --stop-server
```

## Notes For Learning
- Keep prompts and incident descriptions concise while testing state transitions.
- Use exact `APPROVE` to exercise the approval branch.
- Any non-approve response at the approval step is treated as revision feedback.
