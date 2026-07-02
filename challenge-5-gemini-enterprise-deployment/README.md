# Challenge 5 Solution: Deploy to Gemini Enterprise

This folder contains an independent solution project for Challenge 5.

## Goal
Deploy and register an ADK v2 agent in Gemini Enterprise, then verify end-to-end use from the Gemini workspace.

## Scope For This Lab
Keep this project self-contained and runnable on its own.

## Status
Implemented with a minimal Caveman Agent that uses built-in Google Search.

## What You Will Build
- A simple agent: `challenge-5-gemini-enterprise-deployment/caveman-agent`
- Persona: short caveman-style responses
- Tooling: built-in `google_search`
- Deployment target: Agent Runtime (Gemini Enterprise Agent Platform)

## Prerequisites
- `uv` installed
- `agents-cli` installed (`uv tool install google-agents-cli`)
- `gcloud` installed and authenticated
- Access to a Gemini Enterprise app in your Google Cloud project

## 1) Scaffold The Agent
Run from repo root:

```bash
cd ./challenge-5-gemini-enterprise-deployment

agents-cli scaffold create caveman-agent \
	--agent adk \
	--deployment-target agent_runtime \
	--region us-central1 \
	--prototype
```

The generated agent code lives in `caveman-agent/app/agent.py`.

## 2) Install Dependencies
```bash
cd ./caveman-agent
agents-cli install
```

## 3) Test Locally In Playground
```bash
cd ./challenge-5-gemini-enterprise-deployment/caveman-agent
agents-cli playground
```

Suggested prompt:
- `Find today's top AI headline and explain like caveman.`

Optional terminal smoke test:
```bash
agents-cli run "Who won the latest Wimbledon men's final?"
```

## 4) Deploy To Agent Runtime (Agents Platform Deployments)
```bash
cd ./challenge-5-gemini-enterprise-deployment/caveman-agent

gcloud config set project l400-adv-agent-dev-solutions

agents-cli deploy --region us-central1 --no-confirm-project
```

This creates/updates a deployment and writes `deployment_metadata.json`.

## 5) Register In Gemini Enterprise
Create or identify your Gemini Enterprise app id in Cloud Console first.
It looks like:
- `projects/<PROJECT_NUMBER>/locations/global/collections/default_collection/engines/<APP_ID>`

Then register:

```bash
cd ./challenge-5-gemini-enterprise-deployment/caveman-agent

agents-cli publish gemini-enterprise \
	--gemini-enterprise-app-id "projects/<PROJECT_NUMBER>/locations/global/collections/default_collection/engines/<APP_ID>"
```

Because this is an Agent Runtime deployment, `agents-cli` auto-detects deployment metadata and uses ADK registration by default.

## 6) Verify In Gemini Enterprise Workspace
- Open Gemini Enterprise workspace.
- Select your app/agent.
- Ask a web/freshness question (news, recent event, release, score).
- Confirm response is:
	- in short caveman style
	- grounded by search when needed

## Useful Commands
```bash
# Run tests for the generated project
cd ./challenge-5-gemini-enterprise-deployment/caveman-agent
pytest tests/

# Check pending deploy status if using async deploy
agents-cli deploy --status

# List available Gemini Enterprise apps
agents-cli publish gemini-enterprise --list
```
