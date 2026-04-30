"""Generic HTTP runner: accepts source + input, runs the existing run.sh, returns output.

This file is copied into every code_runners/<lang>/ directory so each runner
becomes a self-contained network service.
"""
import os
import shutil
import subprocess
import uuid
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Each runner image keeps run.sh in its WORKDIR. We resolve to an absolute
# path at startup so the working directory of subprocess.run doesn't matter.
RUN_SCRIPT = os.path.abspath(os.getenv("RUN_SCRIPT", "run.sh"))
SANDBOX_ROOT = "/sandboxes"
EXEC_TIMEOUT_SECONDS = int(os.getenv("EXEC_TIMEOUT", "10"))


class ExecuteRequest(BaseModel):
    filename: str          # e.g. "main.py", "Main.java", "main.cpp"
    source: str            # full source code to compile/run
    input: str = ""        # stdin content


class ExecuteResponse(BaseModel):
    output: str
    error: str
    runtime: str
    results: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/execute", response_model=ExecuteResponse)
def execute(req: ExecuteRequest) -> ExecuteResponse:
    execution_id = str(uuid.uuid4())
    workspace = os.path.join(SANDBOX_ROOT, execution_id)
    os.makedirs(workspace, exist_ok=True)

    try:
        # Write source + stdin
        with open(os.path.join(workspace, req.filename), "w") as f:
            f.write(req.source)
        with open(os.path.join(workspace, "input.txt"), "w") as f:
            f.write(req.input or "")

        # Invoke the language-specific run.sh — same script that previously
        # ran via `docker exec`. It expects EXECUTION_ID and reads/writes
        # files in /sandboxes/$EXECUTION_ID/.
        env = os.environ.copy()
        env["EXECUTION_ID"] = execution_id
        try:
            subprocess.run(
                ["bash", RUN_SCRIPT],
                env=env,
                timeout=EXEC_TIMEOUT_SECONDS,
                check=False,
                capture_output=True,
            )
        except subprocess.TimeoutExpired:
            return ExecuteResponse(
                output="",
                error="TIME_LIMIT_EXCEEDED",
                runtime=str(EXEC_TIMEOUT_SECONDS * 1000),
                results="",
            )

        return ExecuteResponse(
            output=_read(workspace, "output.txt"),
            error=_read(workspace, "error.txt"),
            runtime=_read(workspace, "time.txt"),
            results=_read(workspace, "results.txt"),
        )
    finally:
        # Best-effort cleanup so the runner doesn't accumulate disk usage.
        try:
            shutil.rmtree(workspace, ignore_errors=True)
        except Exception:
            pass


def _read(workspace: str, name: str) -> str:
    path = os.path.join(workspace, name)
    if not os.path.exists(path):
        return ""
    try:
        with open(path) as f:
            return f.read().strip()
    except Exception:
        return ""
