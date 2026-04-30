import json
import os
from typing import Any, List, Dict, Tuple

import httpx

from .builders import builder_map

# Each language runner is now a network service exposing POST /execute on
# port 9000 (see code_runners/<lang>/server.py). The eval service used to
# share a Docker socket + a /sandboxes volume with the runners; now it talks
# to them over HTTP, removing the host-bound coupling.
RUNNER_URLS = {
    "python":     os.getenv("PYTHON_RUNNER_URL",     "http://python_runner:9000"),
    "c":          os.getenv("C_RUNNER_URL",          "http://c_runner:9000"),
    "cpp":        os.getenv("CPP_RUNNER_URL",        "http://cpp_runner:9000"),
    "java":       os.getenv("JAVA_RUNNER_URL",       "http://java_runner:9000"),
    "rust":       os.getenv("RUST_RUNNER_URL",       "http://rust_runner:9000"),
    "go":         os.getenv("GO_RUNNER_URL",         "http://go_runner:9000"),
    "javascript": os.getenv("JAVASCRIPT_RUNNER_URL", "http://javascript_runner:9000"),
}

FILENAME_MAP = {
    "python":     "main.py",
    "c":          "main.c",
    "cpp":        "main.cpp",
    "java":       "Main.java",
    "rust":       "main.rs",
    "go":         "main.go",
    "javascript": "main.js",
}

RUNNER_REQUEST_TIMEOUT = float(os.getenv("RUNNER_REQUEST_TIMEOUT", "15.0"))


def run_code(
    user_code: str,
    input_data: str,
    input_parsing: str,
    function_call: str,
    language: str,
) -> Tuple[str, str, str, str]:
    """Build the executable source for `language` and run it on the language runner.

    Returns (output, error, runtime, results) — same shape as the previous
    docker-exec implementation so callers (sample_tests, app.py) don't change.
    """
    if language not in builder_map or language not in RUNNER_URLS:
        return ("", "Invalid Language", "-1", "")

    builder = builder_map[language]
    source = builder(user_code, input_parsing, function_call)
    filename = FILENAME_MAP[language]
    runner_url = RUNNER_URLS[language]

    try:
        with httpx.Client(timeout=RUNNER_REQUEST_TIMEOUT) as client:
            response = client.post(
                f"{runner_url}/execute",
                json={
                    "filename": filename,
                    "source":   source,
                    "input":    input_data,
                },
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as e:
        return ("", f"Runner unavailable: {e}", "-1", "")
    except Exception as e:
        return ("", f"Runner error: {e}", "-1", "")

    return (
        (data.get("output") or "").strip(),
        (data.get("error") or "").strip(),
        (data.get("runtime") or "").strip(),
        (data.get("results") or "").strip(),
    )


def validate_sample(actual_output_str: str, expected_output_str: str, raw_testcases: str, raw_input_schema: str) -> List[Dict[str, Any]]:
    """Compare two JSON arrays (as strings) and report per-testcase pass/fail."""
    try:
        inputs = raw_testcases.split("\n")
        actual_outputs: List[Any] = json.loads(actual_output_str.strip())
        expected_outputs: List[Any] = json.loads(expected_output_str.strip())
        number_of_inputs = len(json.loads(raw_input_schema)["args"])
        testcases: List[str] = []

        for i in range(0, len(inputs), number_of_inputs):
            for j in range(i, i + number_of_inputs):
                testcases.append(inputs[j])

        if len(actual_outputs) != len(expected_outputs):
            print(f"❌ Mismatch in number of outputs: Expected {len(expected_outputs)}, got {len(actual_outputs)}")
            return [{"Testcases": "", "status": "Failed"}]

        results: List[Dict[str, Any]] = []
        for i, (actual, expected) in enumerate(zip(actual_outputs, expected_outputs)):
            testcase = testcases[i]
            if actual["value"] != expected["value"]:
                results.append({"Testcases": testcase, "output": actual["value"], "expected": expected["value"], "status": "Failed"})
            else:
                results.append({"Testcases": testcase, "output": actual["value"], "expected": expected["value"], "status": "Accepted"})

        return results

    except Exception as e:
        print("❌ Exception during validation:", e)
        return [{"Testcases": "", "status": "Failed"}]
