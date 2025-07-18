import json
import os
import subprocess
from typing import Any, List,Dict
import uuid
from .create_executable_file import create_file

SANDBOX = "/sandboxes"
def run_code(user_code: str, input_data: str, input_parsing: str, function_call: str, language:str):
    execution_id = str(uuid.uuid4())
    workspace = os.path.join(SANDBOX, execution_id)
    os.makedirs(workspace, exist_ok=True)

    container_map = {
        "python": "python_runner",
        "c": "c_runner",
        "cpp": "cpp_runner",
        "java": "java_runner",
        "rust": "rust_runner",
        "go": "go_runner",
        "javascript": "javascript_runner",
    }
    path_map = {
        "python": "/python/run.sh",
        "c": "/C/run.sh",
        "cpp": "/C++/run.sh",
        "java": "/Java/run.sh",
        "rust": "/Rust/run.sh",
        "go": "/Go/run.sh",
        "javascript": "/javascript/run.sh",
    }

    create_file(language,user_code,input_parsing,function_call, workspace)
    with open(os.path.join(workspace, "input.txt"), "w") as f:
        f.write(input_data)
    
    if language not in container_map:
        return ("Invalid Language","Invalid Language","-1")
    
    container = container_map[language]
    path = path_map[language]
    
    subprocess.run([
        "docker", "exec",
        "-e", f"EXECUTION_ID={execution_id}",
        f"{container}",
        f"{path}"
    ], timeout=5)

    output_path = os.path.join(workspace, "output.txt")
    error_path = os.path.join(workspace, "error.txt")
    time_path = os.path.join(workspace, "time.txt")
    results_path = os.path.join(workspace, "results.txt")
    
    output:str = open(output_path).read() if os.path.exists(output_path) else ""
    error:str = open(error_path).read() if os.path.exists(error_path) else ""
    runtime:str = open(time_path).read() if os.path.exists(time_path) else ""
    results:str = open(results_path).read() if os.path.exists(results_path) else ""
    # if results and language=='cpp':
    #     parsed_once:List[Dict[str,Any]] = json.loads(results)
    #     validate("",results)
    # else:
    #     parsed_once = []
    return output.strip(), error.strip(), runtime.strip(),results.strip()

def validate_sample(actual_output_str: str, expected_output_str: str, raw_testcases:str, raw_input_schema:str) -> List[Dict[str,Any]]:
    # actual = json.loads(actual_output)
    # expected = json.loads(expected_output)
    # return actual == expected
    """
    Compare two JSON arrays (as strings) and log mismatches.
    
    Returns:
        True if all match, False otherwise.
    """
    try:
        inputs = raw_testcases.split("\n")
        actual_outputs: List[Any] = json.loads(actual_output_str.strip())
        expected_outputs: List[Any] = json.loads(expected_output_str.strip())
        number_of_inputs = len(json.loads(raw_input_schema)["args"])
        testcases:List[str] = []
        
        for i in range(0,len(inputs),number_of_inputs):
            for j in range(i,i+number_of_inputs):
                testcases.append(inputs[j])
        
        if len(actual_outputs) != len(expected_outputs):
            print(f"❌ Mismatch in number of outputs: Expected {len(expected_outputs)}, got {len(actual_outputs)}")
            return [{"Testcases":"","status":"Failed"}]

        results:List[Dict[str,Any]] = []
        for i, (actual, expected) in enumerate(zip(actual_outputs, expected_outputs)):
            testcase = testcases[i]
            print("I: ",actual,expected)
            if actual["value"] != expected["value"]:
                print(f"❌ Testcase {i} failed:")
                print(f"   Expected: {expected}")
                print(f"   Got     : {actual}")
                results.append({"Testcases":testcase, "output":actual["value"], "expected":expected["value"], "status":"Failed"})
            else:
                print(f"✅ Testcase {i} passed")
                results.append({"Testcases":testcase, "output":actual["value"], "expected":expected["value"], "status":"Accepted"})
                
        return results


    except Exception as e:
        print("❌ Exception during validation:", e)
        return [{"Testcases":"","status":"Failed"}]

if __name__ == "__main__":
    user_code = """
class Solution:
    def calculate_LIS(self, arr):
        n = len(arr)
        dp = [1]*n
        for i in range(n):
            for j in range(i):
                if arr[j] < arr[i]:
                    dp[i] = max(dp[i], dp[j]+1)
        return max(dp)
"""
    input_data = "10 20 10 30 20 50"
    input_parsing = "arr = list(map(int, input().split()))"
    function_call = "calculate_LIS(arr)"

    # output, error = run_python_code(user_code, input_data, input_parsing, function_call)
    # print("OUTPUT:", output)
    # print("ERROR:", error)