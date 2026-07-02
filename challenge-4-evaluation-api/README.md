# Challenge 4 Solution: Agent Evaluation API

This folder contains an independent solution project for Challenge 4.

## Goal
Use the ADK Agent Evaluation API to:
- Author an evaluation dataset
- Run evaluations for accuracy and safety
- Improve prompts and re-run to verify gains

## Scope For This Lab
Keep this project self-contained and runnable on its own.

## Status
Implemented with:
- A simple customer-service agent for fictional company Cymbal Retail.
- A built-in evaluation workflow using `agents-cli eval` commands.
- A 20-case evaluation dataset focused on policy-grounded factual responses.
- Two prompt modes for before/after comparison:
  - `simple` baseline
  - `detailed` improved instructions with explicit negative guidance

## Use Case
The agent answers customer-service questions using an embedded Cymbal Retail policy document (US only, online + brick-and-mortar).

This challenge is intentionally simple:
- No external tools.
- No complex orchestration.
- Focus on evaluation loop quality.

## Files You Will Use
- `cymbal_support_agent/agent.py`
- `tests/eval/datasets/basic-dataset.json`
- `tests/eval/eval_config.yaml`

## Prompt Modes
The agent reads `CYMBAL_PROMPT_STYLE`:
- `simple` = lightweight, friendly instructions.
- `detailed` = stricter grounded behavior + explicit "what not to do" rules.

Default is `simple`.

## Setup
```bash
cd ./challenge-4-evaluation-api
source .venv/bin/activate
agents-cli install
```

## Running Tests
Run tests from `challenge-4-evaluation-api` with the virtual environment activated.

### Run All Tests
```bash
source .venv/bin/activate
pytest tests/
```

### Run Unit Tests Only
```bash
source .venv/bin/activate
pytest tests/unit
```

### Run Integration Tests Only
```bash
source .venv/bin/activate
pytest tests/integration
```

## Optional Playground Smoke Test
```bash
agents-cli playground
```

## Evaluation Workflow

This repo supports two paths:
- Local path: `eval generate` + `eval grade` (great for quick iteration)
- Cloud path: `eval submit` + `eval results` (shows up in Cloud Console Evaluation Experiments)

### 1) Baseline Run (Simple Instructions)
```bash
cd ./challenge-4-evaluation-api
source .venv/bin/activate

export CYMBAL_PROMPT_STYLE=simple

agents-cli eval generate \
	--dataset tests/eval/datasets/basic-dataset.json \
	--output artifacts/traces_simple

agents-cli eval grade \
	--traces artifacts/traces_simple \
	--config tests/eval/eval_config.yaml \
	--output artifacts/grade_results_simple
```

### 2) Improved Run (Detailed Instructions)
```bash
cd ./challenge-4-evaluation-api
source .venv/bin/activate

export CYMBAL_PROMPT_STYLE=detailed

agents-cli eval generate \
	--dataset tests/eval/datasets/basic-dataset.json \
	--output artifacts/traces_detailed

agents-cli eval grade \
	--traces artifacts/traces_detailed \
	--config tests/eval/eval_config.yaml \
	--output artifacts/grade_results_detailed
```

### 3) Compare Results
Pick the most recent `results_*.json` file from each output folder:
```bash
agents-cli eval compare \
	artifacts/grade_results_simple/results_<timestamp>.json \
	artifacts/grade_results_detailed/results_<timestamp>.json
```

## Cloud Console Workflow (Evaluation Experiments)

Use this flow when you want evaluation runs visible in Google Cloud Console.

### 1) Set Environment
```bash
cd ./challenge-4-evaluation-api
source .venv/bin/activate

export GOOGLE_CLOUD_PROJECT="l400-adv-agent-dev-solutions"
export EVAL_REGION="global"
export EVAL_BUCKET="gs://<your-existing-bucket>/challenge-4-evals"
```

### 2) Submit Baseline (Simple Prompt)
```bash
export CYMBAL_PROMPT_STYLE=simple

agents-cli eval submit \
	--dataset tests/eval/datasets/basic-dataset.json \
	--config tests/eval/eval_config.yaml \
	--dest "$EVAL_BUCKET" \
	--project "$GOOGLE_CLOUD_PROJECT" \
	--region "$EVAL_REGION"
```

Save the returned run id.

### 3) Fetch Baseline Results
```bash
agents-cli eval results \
	--run-id "projects/<project>/locations/global/evaluationRuns/<run_id>" \
	--output artifacts/cloud_results_simple \
	--project "$GOOGLE_CLOUD_PROJECT" \
	--region "$EVAL_REGION"
```

### 4) Submit Improved (Detailed Prompt)
```bash
export CYMBAL_PROMPT_STYLE=detailed

agents-cli eval submit \
	--dataset tests/eval/datasets/basic-dataset.json \
	--config tests/eval/eval_config.yaml \
	--dest "$EVAL_BUCKET" \
	--project "$GOOGLE_CLOUD_PROJECT" \
	--region "$EVAL_REGION"
```

Save the returned run id.

### 5) Fetch Improved Results
```bash
agents-cli eval results \
	--run-id "projects/<project>/locations/global/evaluationRuns/<run_id>" \
	--output artifacts/cloud_results_detailed \
	--project "$GOOGLE_CLOUD_PROJECT" \
	--region "$EVAL_REGION"
```

### 6) Compare Downloaded Cloud Results
```bash
agents-cli eval compare \
	artifacts/cloud_results_simple/results_<timestamp>.json \
	artifacts/cloud_results_detailed/results_<timestamp>.json
```

### Important Notes
- The bucket in `EVAL_BUCKET` must already exist.
- Use a real bucket path. Do not leave placeholder text like `YOUR_BUCKET_NAME`.
- If using multi-line commands, keep the trailing `\` on each continued line.
- Check Console project and region filters. This challenge uses `global`.

## Metrics
Configured in `tests/eval/eval_config.yaml`:
- `FINAL_RESPONSE_QUALITY` (built-in)
- `SAFETY` (built-in)
- `policy_grounded_factuality` (custom judge metric)

The grading focus for this challenge is factual, policy-grounded responses.

## Notes
- Responses should stay in plain language.
- The detailed prompt includes explicit negative instructions for what not to do.
- No human escalation path is used in this scenario.
