#!/usr/bin/env bash
set -euo pipefail

trap 'echo "Error: command failed at line $LINENO: $BASH_COMMAND" >&2' ERR

if [[ "${DEBUG_SCRIPT:-0}" == "1" ]]; then
  set -x
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-l400-adv-agent-dev-solutions}"
EVAL_REGION="${EVAL_REGION:-global}"
BUCKET_LOCATION="${BUCKET_LOCATION:-US}"
DATASET_PATH="$PROJECT_ROOT/tests/eval/datasets/basic-dataset.json"
EVAL_CONFIG_PATH="$PROJECT_ROOT/tests/eval/eval_config.yaml"
TRACES_SIMPLE_PATH="$PROJECT_ROOT/artifacts/traces_simple"
TRACES_DETAILED_PATH="$PROJECT_ROOT/artifacts/traces_detailed"
SIMPLE_OUTPUT_DIR="$PROJECT_ROOT/artifacts/cloud_results_simple"
DETAILED_OUTPUT_DIR="$PROJECT_ROOT/artifacts/cloud_results_detailed"
COMPARE_OUTPUT_FILE="$PROJECT_ROOT/artifacts/cloud_results_compare.json"

if [[ "${1:-}" == "--check-paths" ]]; then
  echo "PROJECT_ROOT=$PROJECT_ROOT"
  echo "DATASET_PATH=$DATASET_PATH"
  echo "EVAL_CONFIG_PATH=$EVAL_CONFIG_PATH"
  [[ -f "$DATASET_PATH" ]] && echo "dataset: ok" || echo "dataset: missing"
  [[ -f "$EVAL_CONFIG_PATH" ]] && echo "eval_config: ok" || echo "eval_config: missing"
  exit 0
fi

if [[ ! -f "$DATASET_PATH" ]]; then
  echo "Dataset not found: $DATASET_PATH"
  exit 1
fi

if [[ ! -f "$EVAL_CONFIG_PATH" ]]; then
  echo "Eval config not found: $EVAL_CONFIG_PATH"
  exit 1
fi

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud CLI is required but was not found in PATH."
  exit 1
fi

if ! command -v agents-cli >/dev/null 2>&1; then
  echo "agents-cli is required but was not found in PATH."
  exit 1
fi

random_suffix() {
  python3 - <<'PY'
import random
import string

alphabet = string.ascii_lowercase + string.digits
print(''.join(random.choice(alphabet) for _ in range(10)))
PY
}

create_bucket() {
  local tries=0
  while [[ "$tries" -lt 6 ]]; do
    local suffix
    suffix="$(random_suffix)"
    BUCKET_NAME="adk-evaluations-${suffix}"
    BUCKET_URI="gs://${BUCKET_NAME}"

    if gcloud storage buckets describe "$BUCKET_URI" --project "$PROJECT_ID" >/dev/null 2>&1; then
      tries=$((tries + 1))
      continue
    fi

    echo "Creating bucket: $BUCKET_URI"
    gcloud storage buckets create "$BUCKET_URI" \
      --project "$PROJECT_ID" \
      --location "$BUCKET_LOCATION" \
      --uniform-bucket-level-access

    export EVAL_BUCKET="${BUCKET_URI}/challenge-4-evals"
    export EVAL_BUCKET_NAME="$BUCKET_NAME"
    return 0
  done

  echo "Failed to create a unique bucket name after multiple attempts."
  exit 1
}

extract_run_id() {
  local submit_output="$1"
  local run_id
  run_id="$(echo "$submit_output" | grep -Eo 'projects/[^[:space:]]+/locations/[^[:space:]]+/evaluationRuns/[^[:space:]]+' | tail -n 1 | sed 's/[",]$//')"

  if [[ -z "$run_id" ]]; then
    echo "Could not parse run id from submit output."
    echo "Submit output was:"
    echo "$submit_output"
    exit 1
  fi

  echo "$run_id"
}

run_submit() {
  local style="$1"
  local traces_path="$2"
  echo "Submitting cloud evaluation for prompt style: $style"
  CYMBAL_PROMPT_STYLE="$style" agents-cli eval submit \
    --dataset "$traces_path" \
    --config "$EVAL_CONFIG_PATH" \
    --dest "$EVAL_BUCKET" \
    --project "$PROJECT_ID" \
    --region "$EVAL_REGION"
}

run_generate() {
  local style="$1"
  local output_path="$2"
  echo "Generating local traces for prompt style: $style"
  CYMBAL_PROMPT_STYLE="$style" agents-cli eval generate \
    --dataset "$DATASET_PATH" \
    --output "$output_path"
}

fetch_results() {
  local run_id="$1"
  local output_dir="$2"

  echo "Fetching results for run: $run_id"
  agents-cli eval results \
    --run-id "$run_id" \
    --output "$output_dir" \
    --project "$PROJECT_ID" \
    --region "$EVAL_REGION"
}

latest_result_file_in_dir() {
  local dir="$1"
  ls -t "$dir"/results_*.json 2>/dev/null | head -n 1
}

extract_state_from_result_json() {
  local json_file="$1"
  python3 - <<'PY' "$json_file"
import json
import sys

path = sys.argv[1]
state = "UNKNOWN"
try:
    data = json.load(open(path))
except Exception:
    print(state)
    raise SystemExit(0)

meta = data.get("metadata") or {}
if isinstance(meta, dict):
    state = (meta.get("run_state") or meta.get("state") or state)

if state == "UNKNOWN":
    # If metrics are present, treat as succeeded even if state is absent.
    if data.get("summary_metrics"):
        state = "SUCCEEDED"

print(str(state))
PY
}

wait_for_run_completion() {
  local run_id="$1"
  local output_dir="$2"
  local max_attempts=12
  local attempt=1
  local fetch_retries=3

  while [[ "$attempt" -le "$max_attempts" ]]; do
    echo "Polling run state ($attempt/$max_attempts): $run_id"

    local fetch_ok=0
    local fetch_try=1
    while [[ "$fetch_try" -le "$fetch_retries" ]]; do
      if fetch_results "$run_id" "$output_dir"; then
        fetch_ok=1
        break
      fi
      echo "Result retrieval failed (try $fetch_try/$fetch_retries) for run: $run_id"
      fetch_try=$((fetch_try + 1))
    done

    if [[ "$fetch_ok" -ne 1 ]]; then
      echo "Result retrieval still failing after retries; will continue polling."
      attempt=$((attempt + 1))
      continue
    fi

    local latest_json
    latest_json="$(latest_result_file_in_dir "$output_dir")"
    if [[ -z "$latest_json" ]]; then
      echo "No results JSON found yet for run: $run_id"
      attempt=$((attempt + 1))
      continue
    fi

    local state
    state="$(extract_state_from_result_json "$latest_json")"
    echo "Run state from JSON: $state"

    case "$state" in
      SUCCEEDED|EvaluationRunState.SUCCEEDED)
        return 0
        ;;
      FAILED|CANCELLED|EvaluationRunState.FAILED|EvaluationRunState.CANCELLED)
        echo "Run reached terminal non-success state: $state"
        return 1
        ;;
      *)
        attempt=$((attempt + 1))
        ;;
    esac
  done

  echo "Run did not reach terminal success state within polling limit: $run_id"
  return 1
}

main() {
  cd "$PROJECT_ROOT"

  echo "Project root: $PROJECT_ROOT"
  echo "Project: $PROJECT_ID"
  echo "Eval region: $EVAL_REGION"
  echo "Bucket location: $BUCKET_LOCATION"

  create_bucket

  echo "Using bucket prefix: $EVAL_BUCKET"

  run_generate simple "$TRACES_SIMPLE_PATH"
  run_generate detailed "$TRACES_DETAILED_PATH"

  mkdir -p "$SIMPLE_OUTPUT_DIR" "$DETAILED_OUTPUT_DIR"

  simple_submit_output="$(run_submit simple "$TRACES_SIMPLE_PATH")"
  simple_run_id="$(extract_run_id "$simple_submit_output")"
  echo "Simple run id: $simple_run_id"

  detailed_submit_output="$(run_submit detailed "$TRACES_DETAILED_PATH")"
  detailed_run_id="$(extract_run_id "$detailed_submit_output")"
  echo "Detailed run id: $detailed_run_id"

  wait_for_run_completion "$simple_run_id" "$SIMPLE_OUTPUT_DIR"
  wait_for_run_completion "$detailed_run_id" "$DETAILED_OUTPUT_DIR"

  simple_result_file="$(latest_result_file_in_dir "$SIMPLE_OUTPUT_DIR")"
  detailed_result_file="$(latest_result_file_in_dir "$DETAILED_OUTPUT_DIR")"

  if [[ -z "$simple_result_file" || -z "$detailed_result_file" ]]; then
    echo "Could not find results_*.json files in one or both output directories."
    exit 1
  fi

  echo "Comparing:"
  echo "  $simple_result_file"
  echo "  $detailed_result_file"

  agents-cli eval compare "$simple_result_file" "$detailed_result_file" > "$COMPARE_OUTPUT_FILE"

  echo
  echo "Done."
  echo "Bucket created: gs://${EVAL_BUCKET_NAME}"
  echo "Eval staging prefix: ${EVAL_BUCKET}"
  echo "Simple run id: $simple_run_id"
  echo "Detailed run id: $detailed_run_id"
  echo "Compare output: $COMPARE_OUTPUT_FILE"
}

main "$@"
