#!/bin/bash

# Helper script to encode a file to base64 for Action 2B workflow
# Usage: ./tools/encode-file-for-workflow.sh path/to/your/file.xlsx

if [ $# -eq 0 ]; then
    echo "Usage: $0 <file-path>"
    echo "Example: $0 data/input.xlsx"
    exit 1
fi

FILE_PATH="$1"

if [ ! -f "$FILE_PATH" ]; then
    echo "Error: File not found: $FILE_PATH"
    exit 1
fi

echo "Encoding file: $FILE_PATH"
echo "---"
echo ""

# Encode the file to base64
BASE64_CONTENT=$(base64 < "$FILE_PATH")

echo "Base64 encoded content (copy this for the workflow):"
echo ""
echo "$BASE64_CONTENT"
echo ""
echo "---"
echo ""
echo "Instructions:"
echo "1. Copy the base64 content above"
echo "2. Go to: https://github.com/NachaiCapco/combination-engine/actions/workflows/action-2-combination-with-upload.yml"
echo "3. Click 'Run workflow'"
echo "4. Paste the base64 content into the 'file_base64' field"
echo "5. Optionally provide a test_id"
echo "6. Click 'Run workflow'"
