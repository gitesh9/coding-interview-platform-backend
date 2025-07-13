import subprocess
import uuid
from pathlib import Path
from typing import Dict, Union

def run_sample_code(code: str, lang:str) -> Dict[str, Union[str, Dict[str, str]]]:
    if lang == "c":
        return compile_c_to_wasm(code)
    elif lang == "python":
        return {"hint": "Use Pyodide client-side for Python WASM"}
    else:
        return {"error": f"Language {lang} is not yet supported"}

def compile_c_to_wasm(code: str) -> Dict[str, Union[str, Dict[str, str]]]:
    temp_dir = Path(f"/tmp/eval/{uuid.uuid4()}")
    temp_dir.mkdir(parents=True, exist_ok=True)

    source_path = temp_dir / "main.c"
    output_js = temp_dir / "output.js"
    output_wasm = temp_dir / "output.wasm"
    source_path.write_text(code)

    try:
        result = subprocess.run(
            [
                "docker", "run", "--rm", "-i",
                "--network", "none",
                "-v", f"{temp_dir}:/src",
                "emscripten/emsdk",
                "emcc", "/src/main.c",
                "-o", "/src/output.js",
                "-s", "EXPORTED_RUNTIME_METHODS=['cwrap','ccall']",
                "-s", "MODULARIZE=1",
                "-s", "ENVIRONMENT=web"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15
        )

        if result.returncode != 0:
            return {"error": result.stderr.decode()}

        return {
            "js": output_js.read_text(),
            "wasm_base64": output_wasm.read_bytes().hex()
        }

    except subprocess.TimeoutExpired:
        return {"error": "Compilation timed out"}

    finally:
        for f in temp_dir.glob("*"):
            f.unlink()
        temp_dir.rmdir()