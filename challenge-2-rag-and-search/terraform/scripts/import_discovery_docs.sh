#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "Usage: $0 <project_id> <location> <data_store_id> <bucket_name>"
  exit 1
fi

PROJECT_ID="$1"
LOCATION="$2"
DATA_STORE_ID="$3"
BUCKET_NAME="$4"

IMPORT_URI="gs://${BUCKET_NAME}/aurora-bay-alaska-faqs/*.txt"
ENDPOINT="https://discoveryengine.googleapis.com/v1/projects/${PROJECT_ID}/locations/${LOCATION}/collections/default_collection/dataStores/${DATA_STORE_ID}/branches/0/documents:import"

TOKEN="$(gcloud auth application-default print-access-token)"

echo "Starting Discovery Engine import from ${IMPORT_URI}"
RESPONSE="$(curl -sS -X POST \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  "${ENDPOINT}" \
  -d "$(cat <<JSON
{
  "gcsSource": {
    "inputUris": ["${IMPORT_URI}"],
    "dataSchema": "content"
  },
  "reconciliationMode": "FULL"
}
JSON
)")"

OP_NAME="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("name", ""))' <<< "${RESPONSE}")"
if [[ -z "${OP_NAME}" ]]; then
  echo "Import request did not return an operation name. Response was:"
  echo "${RESPONSE}"
  exit 1
fi

echo "Import operation: ${OP_NAME}"
STATUS_URL="https://discoveryengine.googleapis.com/v1/${OP_NAME}"

for _ in $(seq 1 120); do
  sleep 5
  TOKEN="$(gcloud auth application-default print-access-token)"
  STATUS="$(curl -sS -H "Authorization: Bearer ${TOKEN}" "${STATUS_URL}")"

  DONE="$(python3 -c 'import json,sys; print(str(json.loads(sys.stdin.read()).get("done", False)).lower())' <<< "${STATUS}")"
  if [[ "${DONE}" == "true" ]]; then
    ERR_CODE="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("error", {}).get("code", ""))' <<< "${STATUS}")"
    if [[ -n "${ERR_CODE}" ]]; then
      echo "Import failed. Operation response:"
      echo "${STATUS}"
      exit 1
    fi

    echo "Import completed successfully."
    exit 0
  fi
done

echo "Timed out waiting for import operation to complete."
exit 1
