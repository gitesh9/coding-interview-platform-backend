#!/bin/bash

cd /sandboxes/$EXECUTION_ID || exit 1
echo "Running code in $PWD"

START=$(date +%s%3N)

timeout 2s python3 main.py < input.txt > output.txt 2> error.txt
EXIT_CODE=$?

END=$(date +%s%3N)
DURATION=$((END - START))  # Duration in ms

echo "$DURATION" > time.txt

if [ $EXIT_CODE -eq 124 ]; then
    echo "TIME_LIMIT_EXCEEDED" > error.txt
fi