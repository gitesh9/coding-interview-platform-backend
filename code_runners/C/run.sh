#!/bin/bash
cd /sandboxes/$EXECUTION_ID

START=$(date +%s%3N)

gcc main.c -o main.out 2> error.txt || exit 1

timeout 2s ./main.out < input.txt > output.txt 2>> error.txt
EXIT_CODE=$?

END=$(date +%s%3N)
DURATION=$((END - START))  # Duration in ms

echo "$DURATION" > time.txt

if [ $EXIT_CODE -eq 124 ]; then
  echo "TIME_LIMIT_EXCEEDED" > error.txt
fi
