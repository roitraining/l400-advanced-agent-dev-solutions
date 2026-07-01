# Challenge 2 Solution: RAG + Google Search with ADK

This folder contains an independent solution project for Challenge 2.

## Goal
Extend an ADK v2 agent with grounding tools:
- RAG pipeline over local documents
- Google Search for live information

## Scope For This Lab
Keep this project self-contained and runnable on its own.

## Status
RAG data source created and agent scaffold added.

## Prerequisites
- Python virtual environment created at `.venv`
- `agents-cli` installed (`agents-cli --version`)
- Google Cloud project configured (`l400-adv-agent-dev-solutions`)
- Discovery Engine datastore exists and is populated
- ADC configured for local runs

## Run With agents-cli
From this folder:

```bash
cd ./challenge-2-rag-and-search
source .venv/bin/activate
agents-cli install

export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT=l400-adv-agent-dev-solutions
export GOOGLE_CLOUD_LOCATION=global
export DISCOVERY_ENGINE_DATASTORE_FULL_NAME="projects/l400-adv-agent-dev-solutions/locations/global/collections/default_collection/dataStores/aurora-bay-faqs-ad63b7"

agents-cli playground
```

## Quick CLI Test
```bash
cd ./challenge-2-rag-and-search
source .venv/bin/activate

export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT=l400-adv-agent-dev-solutions
export GOOGLE_CLOUD_LOCATION=global
export DISCOVERY_ENGINE_DATASTORE_FULL_NAME="projects/l400-adv-agent-dev-solutions/locations/global/collections/default_collection/dataStores/aurora-bay-faqs-ad63b7"

agents-cli run "What is Aurora Bay famous for?" --app-name aurora_bay_chat
agents-cli run "What are current Alaska travel advisories this week?" --app-name aurora_bay_chat
```

## Agent: aurora_bay_chat
Added package: `aurora_bay_chat`

Design:
- Root agent: `aurora_bay_chat`
- Specialist agent 1: `aurora_bay_private_docs_subagent`
	- Uses Discovery Engine datastore tool (`VertexAiSearchTool`)
- Specialist agent 2: `aurora_bay_web_search_subagent`
	- Uses Google Search tool (`google_search`)
- Root uses `AgentTool` wrappers for both specialists (instead of `sub_agents`) to avoid built-in tool delegation limits.

Environment variable required:
- `DISCOVERY_ENGINE_DATASTORE_FULL_NAME`
	- Format:
		- `projects/<project>/locations/<location>/collections/default_collection/dataStores/<data_store_id>`

Optional model override:
- `AURORA_BAY_MODEL` (default: `gemini-flash-latest`)
