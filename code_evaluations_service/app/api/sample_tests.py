from typing import Dict, List,Any
import json
from ..judge.judge import run_code

from typing import Dict, List, Any, Union
import json
from ..judge.judge import run_code


def run_sample_code(
    raw_code: str,
    lang: str,
    raw_testcases: str,
    raw_input_schema: Union[str, dict, list],
    raw_official_solution: str,
    execution_template: Dict[str, str],
):
    code = raw_code
    # Do not forcefully decode unicode escapes if raw_code is already a clean string
    if isinstance(raw_code, bytes):
        code = raw_code.decode("utf-8", errors="replace")

    input_parser = execution_template.get("input_parser", "") if isinstance(execution_template, dict) else ""
    function_call = execution_template.get("function_call", "") if isinstance(execution_template, dict) else ""

    # Pass raw_testcases directly to stdin via input_data
    return run_code(code, raw_testcases, input_parser, function_call, lang)


def parse_input(raw_input: str, schema: Any) -> List[Dict[str, Any]]:
    if not raw_input:
        return []

    lines = raw_input.strip().splitlines()

    # Normalize schema
    if isinstance(schema, str):
        try:
            schema = json.loads(schema)
        except Exception:
            schema = []

    if isinstance(schema, dict):
        args = schema.get("args", [])
    elif isinstance(schema, list):
        args = schema
    else:
        args = []

    if not args:
        return []

    step = len(args)
    testcases: List[Dict[str, Any]] = []

    for i in range(0, len(lines), step):
        testcase: Dict[str, Any] = {}
        for j, arg in enumerate(args):
            if i + j >= len(lines):
                break
            raw_value = lines[i + j]
            arg_name = arg.get("name", f"arg_{j}") if isinstance(arg, dict) else f"arg_{j}"
            arg_type = (arg.get("type", "str") if isinstance(arg, dict) else "str").lower()

            try:
                if arg_type in ("int", "integer"):
                    value = int(raw_value)
                elif arg_type in ("float", "double"):
                    value = float(raw_value)
                elif arg_type in ("bool", "boolean"):
                    value = raw_value.strip().lower() in ("true", "1")
                else:
                    try:
                        value = json.loads(raw_value)
                    except Exception:
                        value = raw_value
            except Exception:
                value = raw_value

            testcase[arg_name] = value
        testcases.append(testcase)

    return testcases

