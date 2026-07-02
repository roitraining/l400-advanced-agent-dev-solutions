# agents-cli Quickstart (Scaffolded ADK Project)

Use this when you want the fastest path to a working, structured ADK project.

## 1) Prerequisites

1. Install uv: https://docs.astral.sh/uv/getting-started/installation/
2. Install agents-cli:

```bash
uv tool install google-agents-cli
```

3. Authenticate to Google Cloud:

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

## 2) Create Project With Scaffold

From any workspace location:

```bash
agents-cli scaffold create hello-agents-cli \
  --agent adk \
  --prototype
```

Then enter the project:

```bash
cd hello-agents-cli
```

## 3) Install Dependencies

```bash
agents-cli install
```

## 4) Run Playground

```bash
agents-cli playground
```

Open the local URL printed in terminal.

In the playground:

1. Start a new chat session.
2. Send a basic prompt first.
3. Update `app/agent.py` instructions.
4. Refresh or start a new chat and test again.

## 5) Ask A First Prompt

Try:

- What is the difference between an AI model and an AI agent?

## 6) Edit Agent Behavior

Open app/agent.py and change the instruction text.

Example change:

- Before: "You are a helpful assistant."
- After: "You are a teacher. Answer in 3 concise bullet points."

Save and re-test in playground.

## 7) Optional Terminal Smoke Test

```bash
agents-cli run "Explain Retrieval Augmented Generation in plain language"
```

## 8) Deploy To Agent Platform (Agent Runtime)

If you scaffolded with `--prototype`, add deployment support first:

```bash
agents-cli scaffold enhance . --deployment-target agent_runtime
```

Then deploy:

```bash
gcloud config set project YOUR_PROJECT_ID
agents-cli deploy --project YOUR_PROJECT_ID --region us-central1 --no-confirm-project
```

On success, you will get deployment details and a generated `deployment_metadata.json` file.

## 9) Optional: Register To Gemini Enterprise

```bash
agents-cli publish gemini-enterprise \
  --gemini-enterprise-app-id "projects/<PROJECT_NUMBER>/locations/global/collections/default_collection/engines/<APP_ID>"
```

## Common Fixes

- If agents-cli is not found, reopen terminal after installation.
- If auth errors appear, rerun gcloud auth application-default login.
- If project detection is wrong, run gcloud config set project YOUR_PROJECT_ID again.
