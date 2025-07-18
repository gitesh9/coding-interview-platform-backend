#!/bin/bash
set -e
cd /sandboxes/$EXECUTION_ID || { echo "❌ No such directory"; exit 1; }

START=$(date +%s%3N)

# Run JS with timeout, redirect input/output/error
timeout 2s node main.js < input.txt > output.txt 2> error.txt

EXIT_CODE=$?

END=$(date +%s%3N)
DURATION=$((END - START))  # Duration in ms

echo "$DURATION" > time.txt

if [ $EXIT_CODE -eq 124 ]; then
  echo "TIME_LIMIT_EXCEEDED" > error.txt
fi
