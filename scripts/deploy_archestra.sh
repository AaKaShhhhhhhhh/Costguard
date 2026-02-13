#!/bin/bash
# Template script to deploy workflows to Archestra.AI

# Ensure ARCHESTRA_API_URL and ARCHESTRA_API_KEY are set
if [ -z "$ARCHESTRA_API_URL" ]; then
    echo "Error: ARCHESTRA_API_URL is not set."
    exit 1
fi

if [ -z "$ARCHESTRA_API_KEY" ]; then
    echo "Error: ARCHESTRA_API_KEY is not set."
    exit 1
fi

echo "Deploying workflows to $ARCHESTRA_API_URL..."

# Example: Loop through workflow files and upload them
# for flow in workflows/*.yaml; do
#     echo "Uploading $flow..."
#     curl -X POST "$ARCHESTRA_API_URL/api/v1/workflows" \
#          -H "Authorization: Bearer $ARCHESTRA_API_KEY" \
#          -H "Content-Type: application/yaml" \
#          --data-binary "@$flow"
# done

echo "Deployment complete (Template - Uncomment lines to enable actual deployment)."
