from typing import Dict, List,Any
import json
from ..judge.judge import run_code

def run_sample_code(raw_code: str, lang:str,raw_testcases:str, raw_input_schema:str,raw_official_solution: str, execution_template:Dict[str,str]):
    code = raw_code.encode('utf-8').decode('unicode_escape')
    
    input_schema = json.loads(raw_input_schema)
    # execution_template = json.loads(raw_execution_template)
    
    testcases2 = parse_input(raw_testcases,input_schema)
    
    print(execution_template["input_parser"])
    
    input_parser = execution_template['input_parser']
    function_call = execution_template['function_call']
    
    return run_code(code,json.dumps(testcases2),input_parser,function_call,lang) # type: ignore
    return [{"error": error, "runtime":runtime,"status":"Accepted","stdout":output,"results":results}]

def parse_input(raw_input: str, schema: Dict[str,Any])->List[Dict[str,Any]]:
    lines = raw_input.strip().splitlines()
    args = schema["args"]
    step = len(args)

    testcases: List[Dict[str,Any]] = []
    for i in range(0, len(lines), step):
        testcase:Dict[str,Any] = {}
        for j, arg in enumerate(args):
            raw_value = lines[i + j]
            arg_type = arg["type"]
            arg_name = arg["name"]

            if arg_type == "str":
                # Parse quoted strings safely
                value = json.loads(raw_value)
            elif arg_type == "int":
                value = int(raw_value)
            elif arg_type == "float":
                value = float(raw_value)
            else:
                raise ValueError(f"Unsupported type: {arg_type}")
            
            testcase[arg_name] = value
        testcases.append(testcase)
    print(testcases,schema,raw_input)
    return testcases
