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
Implemented with three runnable solutions.

## Solution Modules
- `incident_agent_with_human_approval`
	- ADK 2 Graph Workflow with human approval/revision loop.
- `incident_agent_graph_workflow`
	- ADK 2 Graph Workflow (simpler) with no human feedback loop.
- `incident_agent_workflow`
	- Older-style workflow using `SequentialAgent` + `ParallelAgent`.

## What Each Solution Demonstrates
- `incident_agent_with_human_approval`
	- Graph workflow routing + shared state + human-in-the-loop approval/revision.
- `incident_agent_graph_workflow`
	- Minimal graph workflow routing + shared state + two final outputs (plan + email).
- `incident_agent_workflow`
	- Older workflow style orchestration with `SequentialAgent` and `ParallelAgent`.

## Prerequisites
- Python virtual environment created at `.venv`
- `agents-cli` installed (`agents-cli --version`)
- Google Cloud project configured (`l400-adv-agent-dev-solutions`)
- Vertex AI API enabled for the project

## Run The Agent In Playground
From this folder:

```bash
cd ./challenge-1-multi-agent-workflow
source .venv/bin/activate
agents-cli install
agents-cli playground
```

If browser launch does not happen automatically, use the local URL shown in terminal.

In Playground, use the app selector to choose one of:
- `incident_agent_with_human_approval`
- `incident_agent_graph_workflow`
- `incident_agent_workflow`

## Quick CLI Tests (No Playground)
```bash
cd ./challenge-1-multi-agent-workflow
source .venv/bin/activate

# 1) Graph workflow with human approval/revision
agents-cli run "Database outage impacting checkout and payments for 20 minutes" --app-name incident_agent_with_human_approval

# 2) Simple graph workflow (no human approval loop)
agents-cli run "Database outage impacting checkout and payments for 20 minutes" --app-name incident_agent_graph_workflow

# 3) Old-style Sequential/Parallel workflow
agents-cli run "Database outage impacting checkout and payments for 20 minutes" --app-name incident_agent_workflow
```

## Manual Test Scenarios

### Scenario 1: Human Approval Workflow
App: `incident_agent_with_human_approval`

1. Send incident details:
	`Database outage impacting checkout and payments for 20 minutes; customers cannot complete purchases.`
2. Wait for triage + risk + action plan.
3. Reply: `APPROVE`
4. Expected:
	Final stakeholder email is generated.

### Scenario 2: Human Revision Loop
App: `incident_agent_with_human_approval`

1. Send incident details:
	`API latency spike in auth service, users seeing login timeouts for 10 minutes.`
2. Wait for draft plan.
3. Reply with feedback: `Please make the plan shorter (4 steps max) and include a customer status-page update within 10 minutes.`
4. Expected:
	Revised action plan is returned and approval is requested again.
5. Reply: `APPROVE`
6. Expected:
	Final email is generated from revised plan.

### Scenario 3: Simple Graph Workflow
App: `incident_agent_graph_workflow`

1. Send incident details:
	`Checkout outage: payment API returns 500, customers cannot complete purchases.`
2. Expected:
	Triage -> risk -> action plan -> stakeholder email -> final combined output.

### Scenario 4: Old-Style Workflow
App: `incident_agent_workflow`

1. Send incident details:
	`Checkout outage: payment API returns 500, customers cannot complete purchases.`
2. Expected:
	Sequential + parallel sub-agent orchestration and final combined output.

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
- Keep prompts concise while comparing behavior across workflow styles.
- Use exact `APPROVE` in `incident_agent_with_human_approval` to finalize.
- In the human-approval app, any non-`APPROVE` reply at approval time is treated as revision feedback.
