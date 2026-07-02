# ADK Quickstart (Direct SDK)

Use this when you want a minimal project with very little scaffolding.

Note: for the full official guide and additional options, see https://adk.dev/get-started/python/

## 1) Prerequisites

1. Install Python 3.11-3.13.
2. Install uv: https://docs.astral.sh/uv/getting-started/installation/
3. Authenticate to Google Cloud (Vertex AI path):

```bash
gcloud auth login
gcloud auth application-default login
```

## 2) Create Project Folder

```bash
mkdir my-adk-hello
cd my-adk-hello
```

## 3) Create Virtual Environment and Install ADK

```bash
uv venv
source .venv/bin/activate
uv pip install "google-adk[gcp]>=2.0.0,<3.0.0"
```

## 4) Create Agent File

Create app/agent.py:

```python
from google.adk.agents import LlmAgent

root_agent = LlmAgent(
    name="hello_agent",
    model="gemini-flash-latest",
    instruction="You are a helpful assistant. Keep answers short and clear.",
)
```

## 5) Set Environment Variables

```bash
export GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID"
export GOOGLE_CLOUD_LOCATION="global"
export GOOGLE_GENAI_USE_VERTEXAI="True"
```

## 6) Run In ADK Web Playground

From the project root:

```bash
uv run adk web
```

Then open the local URL shown in the terminal.

## 7) Quick Smoke Test Prompt

Use this prompt in the playground:

- Explain what an AI agent is in 2 sentences.

## 8) Make One Change (Required)

Edit instruction text in app/agent.py, save, and ask again:

- Original instruction: helpful and short
- New instruction: explain with one analogy

You now have a working baseline ADK project.

## Common Fixes

- Auth error: run gcloud auth application-default login again.
- Project error: confirm GOOGLE_CLOUD_PROJECT matches your GCP project.
- Model/region error: use GOOGLE_CLOUD_LOCATION=global.
