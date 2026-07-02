# google-agents-cli Quickstart (uvx Invocation)

Use this when you want a predictable, low-friction setup across Cloud Shell, macOS, and Windows.

## 1) Prerequisites

1. Install uv: https://docs.astral.sh/uv/getting-started/installation/
2. Authenticate to Google Cloud:

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

## 2) Initialize CLI Skills and Environment

```bash
uvx google-agents-cli setup
```

This runs the setup flow without depending on a globally available `agents-cli` binary in PATH.

## 3) Create Project With Scaffold

From any workspace location:

```bash
uvx google-agents-cli scaffold create hello-google-agents-cli \
  --agent adk \
  --prototype
```

Then enter the project:

```bash
cd hello-google-agents-cli
```

## 4) Install Dependencies

```bash
uvx google-agents-cli install
```

## 5) Run Playground

```bash
uvx google-agents-cli playground
```

Open the local URL printed in terminal.

In the playground:

1. Start a new chat session.
2. Send a basic prompt first.
3. Update `app/agent.py` instructions.
4. Refresh or start a new chat and test again.

## 6) Ask A First Prompt

Try:

- What is the difference between an AI model and an AI agent?

## 7) Edit Agent Behavior

Open app/agent.py and change the instruction text.

Example change:

- Before: "You are a helpful assistant."
- After: "You are a teacher. Answer in 3 concise bullet points."

Save and re-test in playground.

## 8) Optional Terminal Smoke Test

```bash
uvx google-agents-cli run "Explain Retrieval Augmented Generation in plain language"
```

## 9) Deploy To Agent Platform (Agent Runtime)

If you scaffolded with `--prototype`, add deployment support first:

```bash
uvx google-agents-cli scaffold enhance . --deployment-target agent_runtime
```

Then deploy:

```bash
gcloud config set project YOUR_PROJECT_ID
uvx google-agents-cli deploy --project YOUR_PROJECT_ID --region us-central1 --no-confirm-project
```

On success, you will get deployment details and a generated `deployment_metadata.json` file.

## 10) Optional: Register To Gemini Enterprise

```bash
uvx google-agents-cli publish gemini-enterprise \
  --gemini-enterprise-app-id "projects/<PROJECT_NUMBER>/locations/global/collections/default_collection/engines/<APP_ID>"
```

## Common Fixes

- If `uvx` is not found, install uv and open a new terminal.
- If auth errors appear, rerun gcloud auth application-default login.
- If project detection is wrong, run gcloud config set project YOUR_PROJECT_ID again.
