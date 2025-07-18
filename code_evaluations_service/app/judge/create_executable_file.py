import os
from .builders import builder_map

def create_file(lang: str, user_code: str, input_parsing: str, function_call: str, workspace: str) -> None:
    if lang not in builder_map:
        raise ValueError(f"Unsupported language: {lang}")

    filename_map = {
        "python": "main.py",
        "c": "main.c",
        "cpp": "main.cpp",
        "java": "Main.java",
        "rust": "main.rs",
        "go": "main.go",
        "javascript": "main.js",
    }

    filename = filename_map[lang]
    builder = builder_map[lang]
    main_code = builder(user_code, input_parsing, function_call)
    print()
    print()
    print("final code: ", main_code)
    print()
    print()
    os.makedirs(workspace, exist_ok=True)
    with open(os.path.join(workspace, filename), "w") as f:
        f.write(main_code)