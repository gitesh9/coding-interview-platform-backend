def build_python_main(user_code: str, input_parsing: str, function_call: str) -> str:
    ip = (input_parsing or "").strip()
    fc = (function_call or "").strip()

    if ip and fc:
        if not (fc.startswith("print(") or fc.startswith("print ")):
            fc_code = f"""__res = {fc}
if __res is not None:
    import json
    if isinstance(__res, (list, dict, bool)):
        print(json.dumps(__res, separators=(',', ':')))
    else:
        print(__res)"""
        else:
            fc_code = fc

        test_wrapper = f"""
{ip}
{fc_code}
"""
        return user_code + "\n" + test_wrapper

    # Intelligent auto-harness supporting JSON, LeetCode assignments, tuples, and multiline inputs
    harness = '''
import sys
import json
import inspect
import ast
import re

def _run_harness():
    raw_input = sys.stdin.read().strip()
    if 'Solution' not in globals():
        return
    sol = Solution()
    methods = [
        m for m in dir(sol)
        if not m.startswith('_') and callable(getattr(sol, m))
    ]
    if not methods:
        return
    method_name = methods[0]
    method = getattr(sol, method_name)
    try:
        sig = inspect.signature(method)
        param_names = [p.name for p in sig.parameters.values() if p.name != 'self']
    except Exception:
        param_names = []

    args = []
    kwargs = {}

    if raw_input:
        # 1. Standard JSON parse
        try:
            parsed = json.loads(raw_input)
            if isinstance(parsed, dict) and any(p in parsed for p in param_names):
                for p in param_names:
                    if p in parsed:
                        kwargs[p] = parsed[p]
            elif isinstance(parsed, list) and len(parsed) == len(param_names) and len(param_names) > 1:
                args = parsed
            elif isinstance(parsed, dict):
                args = list(parsed.values())
            elif len(param_names) == 1:
                args = [parsed]
        except Exception:
            pass

        # 2. Pseudo-JSON with unquoted keys: e.g. '{nums: [2,7,11,15], target: 9}' or 'nums: [2,7,11,15], target: 9'
        if not kwargs and not args and ':' in raw_input:
            try:
                pseudo = raw_input
                if not pseudo.startswith('{'):
                    pseudo = '{' + pseudo + '}'
                pseudo = re.sub(r'([a-zA-Z_]\\w*)\\s*:', r'"\\1":', pseudo)
                parsed = json.loads(pseudo)
                if isinstance(parsed, dict) and any(p in parsed for p in param_names):
                    for p in param_names:
                        if p in parsed:
                            kwargs[p] = parsed[p]
            except Exception:
                pass

        # 3. Variable assignments: e.g. 'nums = [2,7,11,15], target = 9' or multiline
        if not kwargs and not args and '=' in raw_input:
            norm = raw_input
            for p in param_names:
                norm = re.sub(r',\\s*(?=' + re.escape(p) + r'\\s*=)', chr(10), norm)
            norm = re.sub(r',\\s*(?=[a-zA-Z_]\\w*\\s*=)', chr(10), norm)

            env = {}
            try:
                tree = ast.parse(norm)
                for stmt in tree.body:
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Name):
                                try:
                                    env[target.id] = ast.literal_eval(stmt.value)
                                except Exception:
                                    pass
                if any(p in env for p in param_names):
                    for p in param_names:
                        if p in env:
                            kwargs[p] = env[p]
            except Exception:
                pass

        # 4. Comma-separated Python literal values or tuple: e.g. '[2,7,11,15], 9'
        if not kwargs and not args:
            try:
                val = ast.literal_eval(raw_input)
                if isinstance(val, tuple) and len(val) == len(param_names):
                    args = list(val)
                elif len(param_names) == 1:
                    args = [val]
            except Exception:
                pass

        # 5. Line-by-line fallback
        if not kwargs and not args:
            lines = raw_input.splitlines()
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    args.append(json.loads(line))
                except Exception:
                    try:
                        args.append(ast.literal_eval(line))
                    except Exception:
                        args.append(line)

    try:
        if kwargs and len(kwargs) == len(param_names):
            res = method(**kwargs)
        elif kwargs and not args:
            res = method(**kwargs)
        elif len(args) == len(param_names):
            res = method(*args)
        elif args:
            res = method(*args)
        else:
            res = method()
    except Exception as e:
        sys.stderr.write(str(e) + chr(10))
        sys.exit(1)

    if res is not None:
        if isinstance(res, (list, dict, bool)):
            print(json.dumps(res, separators=(',', ':')))
        else:
            print(res)

if __name__ == '__main__':
    _run_harness()
'''
    return user_code + "\n" + harness

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
    ip = (input_parsing or "").strip()
    fc = (function_call or "").strip()

    if ip and fc:
        return f"""
{user_code}

function main() {{
    const s = new Solution();
    {ip}
    console.log({fc});
}}

main();
"""

    harness = """
const fs = require('fs');

function _runHarness() {
    if (typeof Solution === 'undefined') return;
    const s = new Solution();
    const rawInput = fs.readFileSync(0, 'utf-8').trim();
    const proto = Object.getPrototypeOf(s);
    const methods = Object.getOwnPropertyNames(proto).filter(m => m !== 'constructor' && typeof s[m] === 'function');
    if (methods.length === 0) return;
    const methodName = methods[0];

    let args = [];
    if (rawInput) {
        try {
            const parsed = JSON.parse(rawInput);
            if (typeof parsed === 'object' && parsed !== null && !Array.isArray(parsed)) {
                args = Object.values(parsed);
            } else if (Array.isArray(parsed)) {
                args = parsed;
            } else {
                args = [parsed];
            }
        } catch (e) {
            if (rawInput.includes('=')) {
                try {
                    const normalized = rawInput.replace(/,\s*(?=[a-zA-Z_]\w*\s*=)/g, '; ');
                    const fn = new Function('let ' + normalized + '; return [' + normalized.split(';').map(s => s.split('=')[0].trim()).filter(Boolean).join(', ') + '];');
                    args = fn();
                } catch (_) {}
            }
            if (!args || args.length === 0) {
                args = rawInput.split('\\n').map(l => {
                    try { return JSON.parse(l); } catch (_) { return l.trim(); }
                });
            }
        }
    }

    try {
        const res = s[methodName](...args);
        if (res !== undefined) {
            console.log(typeof res === 'object' ? JSON.stringify(res) : res);
        }
    } catch (err) {
        process.stderr.write(String(err));
        process.exit(1);
    }
}

_runHarness();
"""
    return user_code + "\n" + harness


builder_map = {
    "python": build_python_main,
    "python3": build_python_main,
    "py": build_python_main,
    "c": build_c_main,
    "cpp": build_cpp_main,
    "c++": build_cpp_main,
    "java": build_java_main,
    "rust": build_rust_main,
    "go": build_go_main,
    "golang": build_go_main,
    "javascript": build_javascript_main,
    "js": build_javascript_main,
}