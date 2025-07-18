def build_python_main(user_code: str, input_parsing: str, function_call: str) -> str:
    test_wrapper = f"""
{input_parsing}
{function_call}
"""
    return user_code + "\n" + test_wrapper

def build_c_main(user_code: str, input_parsing: str, function_call: str) -> str:
    return f"""
#include <stdio.h>

{user_code}

int main() {{
    {input_parsing}
    printf("%d\\n", {function_call});
    return 0;
}}
"""

def build_cpp_main(user_code: str, input_parsing: str, function_call: str) -> str:
    return f"""
{input_parsing}

{user_code}

{function_call}
""".strip()

def build_java_main(user_code: str, input_parsing: str, function_call: str) -> str:
    return f"""
{user_code}

public class Main {{
    public static void main(String[] args) {{
        Solution s = new Solution();
        {input_parsing}
        System.out.println({function_call});
    }}
}}
"""

def build_rust_main(user_code: str, input_parsing: str, function_call: str) -> str:
    return f"""
{user_code}

fn main() {{
    let s = Solution{{}};
    {input_parsing}
    println!("{{}}", {function_call});
}}
"""

def build_go_main(user_code: str, input_parsing: str, function_call: str) -> str:
    return f"""
package main
import (
    "fmt"
)

{user_code}

func main() {{
    s := Solution{{}}
    {input_parsing}
    fmt.Println({function_call})
}}
"""

def build_javascript_main(user_code: str, input_parsing: str, function_call: str) -> str:
    return f"""
{user_code}

function main() {{
    const s = new Solution();
    {input_parsing}
    console.log({function_call});
}}

main();
"""

builder_map = {
    "python": build_python_main,
    "c": build_c_main,
    "cpp": build_cpp_main,
    "java": build_java_main,
    "rust": build_rust_main,
    "go": build_go_main,
    "javascript": build_javascript_main,
}