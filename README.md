# Coding Interview Platform — Backend

A microservices-based backend for a coding interview platform supporting multi-language code execution, semantic problem search, and real-time collaboration. Built with **FastAPI**, **gRPC**, **Docker**, and **PostgreSQL**.

---

## Architecture Overview

```
┌────────────┐
│   Client   │
└─────┬──────┘
      │ HTTP
┌─────▼──────────┐
│  API Gateway   │ :8080
└──┬──┬──┬──┬────┘
   │  │  │  │
   │  │  │  └──► Collaboration Service  :8004
   │  │  └─────► Code Evaluations Svc   :8003  ──► Language Runners (Docker)
   │  └────────► Get Service            :8002  ──► Weaviate / FAISS
   └───────────► Auth Service           :8001
                        │
                  ┌─────▼─────┐
                  │ PostgreSQL│ :5432
                  └───────────┘
```

### Services

| Service | Port | Purpose |
|---|---|---|
| **API Gateway** | 8080 | Central HTTP reverse proxy routing requests to microservices |
| **Auth Service** | 8001 | User registration, login, JWT authentication |
| **Get Service** | 8002 (HTTP), 50051 (gRPC) | Problem retrieval, semantic search, similar problem recommendations |
| **Code Evaluations Service** | 8003 | Code execution, test validation, multi-language judging |
| **Collaboration Service** | 8004 | Real-time collaborative coding sessions |

---

## Tech Stack

- **Language:** Python 3.11
- **Framework:** FastAPI + Uvicorn
- **Database:** PostgreSQL 15 (SQLAlchemy ORM)
- **Inter-service Communication:** gRPC (protobuf), HTTP (httpx)
- **Vector Search:** FAISS (sentence-transformers `all-MiniLM-L6-v2`), Weaviate (OpenAI embeddings)
- **Containerization:** Docker + Docker Compose
- **Code Sandboxing:** Isolated Docker containers per language with shared volumes

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- OpenAI API key (for Weaviate semantic search)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/gitesh9/coding-interview-platform-backend.git
   cd coding-interview-platform-backend
   ```

2. **Configure environment variables**

   Set the following in your environment or a `.env` file:

   | Variable | Description | Default |
   |---|---|---|
   | `GET_SERVICE_URL` | PostgreSQL connection string for get_service | — |
   | `GET_SERVICE` | Get service base URL | `http://get_service:8002` |
   | `CODE_EVAL_SERVICE_URL` | PostgreSQL connection string for code_evaluations_service | — |
   | `CODE_EVAL_SERVICE` | Code evaluations service base URL | `http://code_evaluations_service:8003` |
   | `DATABASE_URL` | PostgreSQL connection string for auth_service | `postgresql://postgres:postgres@db:5432/postgres` |
   | `OPENAI_APIKEY` | OpenAI API key (Weaviate embeddings) | — |

3. **Start all services**
   ```bash
   docker compose up --build
   ```

4. **Stop and clean up**
   ```bash
   docker compose down -v
   ```

5. **Rebuild without cache** (if needed)
   ```bash
   docker compose build --no-cache
   docker compose up
   ```

---

## API Endpoints

### API Gateway (`:8080`)

| Method | Endpoint | Description | Proxies To |
|---|---|---|---|
| `GET` | `/api/get/{path}` | Fetch problem data | Get Service |
| `POST` | `/api/problems/{problemId}/run` | Run code against sample tests | Code Evaluations Service |
| `POST` | `/api/problems/{problemId}/submit` | Submit code for evaluation | Code Evaluations Service |
| `POST` | `/api/collab/` | Create collaboration session | Collaboration Service |

### Auth Service (`:8001`)

| Method | Endpoint | Body | Description |
|---|---|---|---|
| `POST` | `/login` | `{ username, password }` | Authenticate user, returns JWT |
| `POST` | `/register` | `{ username, user_email, password }` | Register new user |

### Get Service (`:8002`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/problems-set/` | List all problems |
| `GET` | `/problems?value={query}` | Semantic search for problems (Weaviate + OpenAI) |
| `GET` | `/problems/{id\|slug}` | Get problem details + similar problems (FAISS) |
| `GET` | `/user/{id}` | Get user details |

### Code Evaluations Service (`:8003`)

| Method | Endpoint | Body | Description |
|---|---|---|---|
| `POST` | `/{problemId}/sample` | `{ code, input, language }` | Run sample test cases |
| `POST` | `/{problemId}/evaluate` | `{ code, input, input_parsing, function_call, language }` | Full code submission |

---

## Supported Languages

| Language | Container | Compiler/Runtime | Timeout |
|---|---|---|---|
| Python | `python_runner` | Python 3.11 | 2s |
| C | `c_runner` | GCC | 2s |
| C++ | `cpp_runner` | G++ | 2s |
| Java | `java_runner` | JDK (javac) | 2s |
| Rust | `rust_runner` | rustc | 2s |
| Go | `go_runner` | go build | 2s |
| JavaScript | `javascript_runner` | Node.js | 2s |

Each runner is an always-on Docker container with a shared sandbox volume. Code execution follows:

1. Create workspace at `/sandboxes/{UUID}`
2. Generate language-specific main file with execution template
3. Write input to `input.txt`
4. Execute via `docker exec` with a 2-second timeout
5. Capture stdout, stderr, and runtime (ms)

---

## Database Schema

**PostgreSQL 15** with the following tables:

| Table | Key Columns |
|---|---|
| `users` | id, username, user_email, hashed_password |
| `problems` | id, slug, title, description, difficulty, tags, constraints, input_schema (JSONB), code_templates (JSONB), official_solution, execution_template (JSONB) |
| `sample_testcases` | id, problem_id, input_data, expected_output, explanation |
| `hints` | id, problem_id, text |
| `discussions` | id, problem_id, user_id, comment, created_at |
| `user_problem_status` | id, user_id, problem_id, status (solved/attempted/not_attempted) |
| `submissions` | id, problem_id, user_id, code, language, status (Accepted/Wrong), submitted_at |

---

## gRPC

The `get_service` exposes a gRPC server on port `50051` used by the code evaluations service to fetch problem execution templates.

**Proto definition** — `proto/problem.proto`:
```protobuf
service ProblemService {
  rpc GetProblemById (GetProblemRequest) returns (GetProblemResponse);
}
```

**Regenerate gRPC stubs:**
```bash
python -m grpc_tools.protoc -I=./proto --python_out=. --grpc_python_out=. proto/problem.proto
```

---

## Project Structure

```
├── api_gateway/             # HTTP reverse proxy (FastAPI)
├── auth_service/            # Authentication & user management
├── get_service/             # Problem retrieval, search, gRPC server
├── code_evaluations_service/# Code execution & judging engine
├── collaboration_service/   # Real-time collaboration (stub)
├── code_runners/            # Dockerized language execution environments
│   ├── C/
│   ├── C++/
│   ├── Go/
│   ├── Java/
│   ├── javascript/
│   ├── python/
│   └── Rust/
├── proto/                   # Protobuf definitions
├── data/faiss/              # FAISS vector index
└── docker-compose.yml       # Service orchestration
```

---

## Data Flow

### Running Sample Tests

```
Client → API Gateway → Code Evaluations Service
    → gRPC call to Get Service (fetch execution template)
    → Build main file from template + user code
    → docker exec {language}_runner run.sh
    → Compare output with official solution
    → Return per-testcase pass/fail results
```

### Fetching a Problem

```
Client → API Gateway → Get Service
    → PostgreSQL (problem details, hints, sample tests)
    → FAISS index (similar problem IDs)
    → Return problem + similar problems
```

### Semantic Search

```
Client → API Gateway → Get Service
    → Weaviate (OpenAI text2vec embeddings)
    → Return top 5 matching problems
```