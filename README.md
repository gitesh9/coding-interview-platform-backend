# Coding Interview Platform — Backend

A microservices-based backend for a coding interview platform supporting multi-language code execution, AI-powered interviews, semantic problem search, and real-time collaboration. Built with **FastAPI**, **gRPC**, **Docker**, and **PostgreSQL**.

---

## Architecture Overview

```
┌────────────┐
│   Client   │
└─────┬──────┘
      │ HTTP / WebSocket
┌─────▼──────────┐
│  API Gateway   │ :8000
└──┬──┬──┬──┬──┬──┬──┘
   │  │  │  │  │  │
   │  │  │  │  │  └──► AI Service              :8006  ──► OpenAI API
   │  │  │  │  └─────► Interview Service        :8005
   │  │  │  └────────► Collaboration Service    :8004  (WebSocket)
   │  │  └───────────► Code Evaluations Svc     :8003  ──► Language Runners (Docker)
   │  └──────────────► Get Service              :8002  ──► Weaviate / FAISS
   └─────────────────► Auth Service             :8001
                            │
                      ┌─────▼─────┐
                      │ PostgreSQL│ :5432
                      └───────────┘
```

### Services

| Service | Port | Purpose |
|---|---|---|
| **API Gateway** | 8000 | Central HTTP/WebSocket reverse proxy routing requests to microservices |
| **Auth Service** | 8001 | User registration, login, JWT authentication |
| **Get Service** | 8002 (HTTP), 50051 (gRPC) | Problem retrieval, semantic search, similar problem recommendations |
| **Code Evaluations Service** | 8003 | Code execution, test validation, multi-language judging |
| **Collaboration Service** | 8004 | Real-time collaborative coding sessions (WebSocket) |
| **Interview Service** | 8005 | Interview session CRUD, join codes, candidate/interviewer management |
| **AI Service** | 8006 | AI-powered interview questions, follow-ups, and code hints (OpenAI) |

---

## Tech Stack

- **Language:** Python 3.11
- **Framework:** FastAPI + Uvicorn
- **Database:** PostgreSQL 15 (SQLAlchemy ORM)
- **Inter-service Communication:** gRPC (protobuf), HTTP (httpx)
- **AI / LLM:** OpenAI API (gpt-4o-mini) for interview questions and code hints
- **Vector Search:** FAISS (sentence-transformers `all-MiniLM-L6-v2`), Weaviate (OpenAI embeddings)
- **Real-time:** WebSocket (FastAPI + websockets)
- **Containerization:** Docker + Docker Compose
- **Code Sandboxing:** Isolated Docker containers per language with shared volumes

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- OpenAI API key (for AI interview features and Weaviate semantic search)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/gitesh9/coding-interview-platform-backend.git
   cd coding-interview-platform-backend
   ```

2. **Configure environment variables**

   Create a `.env` file in the project root:

   ```env
   OPENAI_API_KEY=sk-your-openai-api-key
   OPENAI_MODEL=gpt-4o-mini
   ```

   All database URLs and inter-service URLs are pre-configured in `docker-compose.yml`.

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

### API Gateway (`:8000`)

| Method | Endpoint | Description | Proxies To |
|---|---|---|---|
| `POST` | `/auth/login` | Authenticate user | Auth Service |
| `POST` | `/auth/register` | Register new user | Auth Service |
| `GET` | `/get/problems-set/` | List all problems | Get Service |
| `GET` | `/get/problems?value={query}` | Semantic search | Get Service |
| `GET` | `/get/problems/{id}` | Problem details | Get Service |
| `POST` | `/problems/{id}/run` | Run code against sample tests | Code Evaluations Service |
| `POST` | `/problems/{id}/submit` | Submit code for evaluation | Code Evaluations Service |
| `GET` | `/interviews/sessions` | List interviewer's sessions | Interview Service |
| `POST` | `/interviews/sessions` | Create interview session | Interview Service |
| `POST` | `/interviews/sessions/join` | Join session by code | Interview Service |
| `PATCH` | `/interviews/sessions/{id}/end` | End interview session | Interview Service |
| `GET` | `/interviews/sessions/{id}` | Get session details | Interview Service |
| `POST` | `/collab/` | Create collaboration session | Collaboration Service |
| `WS` | `/collab/{sessionId}?userId=` | Real-time code sync | Collaboration Service |
| `POST` | `/ai/interview/question` | Get AI interview question | AI Service |
| `POST` | `/ai/interview/respond` | AI follow-up to answer | AI Service |
| `POST` | `/ai/hint` | Get AI code hint | AI Service |

### Auth Service (`:8001`)

| Method | Endpoint | Body | Response |
|---|---|---|---|
| `POST` | `/login` | `{ email, password }` | `{ token, user: { id, name, email, role, avatarUrl } }` |
| `POST` | `/register` | `{ name, email, password, role }` | Same as login |

### Interview Service (`:8005`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/sessions` | Required | List sessions for current interviewer |
| `POST` | `/sessions` | Required | Create session with `{ problemIds, timeLimit }` |
| `POST` | `/sessions/join` | Required | Join with `{ joinCode }`, sets status to active |
| `GET` | `/sessions/{id}` | — | Get session details |
| `PATCH` | `/sessions/{id}/end` | Required | End session (interviewer only) |

### AI Service (`:8006`)

| Method | Endpoint | Body | Description |
|---|---|---|---|
| `POST` | `/interview/question` | `{ problemContext, conversationHistory[] }` | Generate opening interview question |
| `POST` | `/interview/respond` | `{ userAnswer, problemContext, conversationHistory[] }` | Generate follow-up response |
| `POST` | `/hint` | `{ code, problemDescription, language }` | Generate targeted code hint |

### Get Service (`:8002`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/problems-set/` | List all problems with isSolved status |
| `GET` | `/problems?value={query}` | Semantic search for problems (Weaviate + OpenAI) |
| `GET` | `/problems/{id\|slug}` | Get problem details (examples, constraints, starterCode, testCases) |

### Code Evaluations Service (`:8003`)

| Method | Endpoint | Body | Description |
|---|---|---|---|
| `POST` | `/{problemId}/sample` | `{ code, language }` | Run sample test cases |
| `POST` | `/{problemId}/evaluate` | `{ code, language }` | Full submission (persists result) |

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
| `users` | id, name, email, hashed_password, role (interviewer/candidate) |
| `problems` | id, slug, title, description, difficulty, tags, constraints, input_schema (JSONB), code_templates (JSONB), official_solution, execution_template (JSONB) |
| `sample_testcases` | id, problem_id, input_data, expected_output, explanation |
| `hints` | id, problem_id, text |
| `discussions` | id, problem_id, user_id, comment, created_at |
| `user_problem_status` | id, user_id, problem_id, status (solved/attempted/not_attempted) |
| `submissions` | id, problem_id, user_id, code, language, status, runtime, test_cases_passed, total_test_cases, submitted_at |
| `interview_sessions` | id, interviewer_id, candidate_id, candidate_name, problem_ids, problem_titles, time_limit, status (waiting/active/completed), join_code, created_at |

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
├── api_gateway/             # HTTP/WebSocket reverse proxy (FastAPI)
├── auth_service/            # Authentication & user management (JWT, bcrypt)
├── get_service/             # Problem retrieval, search, gRPC server
├── code_evaluations_service/# Code execution & judging engine
├── collaboration_service/   # Real-time collaboration (WebSocket)
├── interview_service/       # Interview session management (CRUD, join codes)
├── ai_results_service/      # AI-powered interviews & hints (OpenAI)
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
    → Return problem details (examples, constraints, starterCode, testCases)
```

### Semantic Search

```
Client → API Gateway → Get Service
    → Weaviate (OpenAI text2vec embeddings)
    → Return top matching problems
```

### Live Interview Flow

```
Interviewer creates session → POST /interviews/sessions → returns joinCode
Candidate joins → POST /interviews/sessions/join → status becomes "active"
Candidate opens problem → connects WebSocket at /collab/{sessionId}
Interviewer observes → connects same WebSocket → receives real-time code updates
AI interview mode → POST /ai/interview/question → LLM generates questions
```