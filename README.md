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
   │  │  │  └────────► Collaboration Service    :8004  (WebSocket) ──► Redis :6379 (pub/sub)
   │  │  └───────────► Code Evaluations Svc     :8003  ──HTTP──► Language Runners (FastAPI :9000)
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
- **Code Sandboxing:** Each language runner is an isolated FastAPI HTTP service (`:9000`) running in its own container with an ephemeral per-request workspace
- **Real-time Fanout:** Redis Pub/Sub (collaboration_service is horizontally scalable)

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

   Copy the example file and fill in values:
   ```bash
   cp .env.example .env
   ```

   Required variables:
   | Variable | Purpose |
   |---|---|
   | `OPENAI_API_KEY` | AI interview, hints, Weaviate semantic search |
   | `OPENAI_MODEL` | LLM to use (default: `gpt-4o-mini`) |
   | `JWT_SECRET_KEY` | Auth token signing — generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
   | `REDIS_URL` | Defaults to `redis://redis:6379` (Compose-managed) |

   All database URLs and inter-service URLs are pre-configured in `docker-compose.yml`.

3. **Start all services**
   ```bash
   docker compose up --build -d
   ```
   First build takes 5–10 minutes (7 language runner images + 7 backend services).

4. **Verify**
   ```bash
   curl http://localhost:8000/get/problems-set/
   docker compose ps
   ```

5. **Stop and clean up**
   ```bash
   docker compose down       # keep data volumes
   docker compose down -v    # also wipe Postgres + Redis data
   ```

6. **Rebuild without cache** (if needed)
   ```bash
   docker compose build --no-cache
   docker compose up -d
   ```

---

## Deployment — Single AWS EC2 Instance

This section walks through deploying the entire stack to **one EC2 instance** using Docker Compose. Suitable for personal projects, demos, and small-scale use. For production-grade multi-instance deployment, see the AWS deployment section below.

### 1. Launch an EC2 instance

- **AMI:** Ubuntu Server 22.04 LTS
- **Instance type:** `t3.medium` minimum (2 vCPU, 4 GiB) — recommended `t3.large` (8 GiB) because Weaviate + 7 runners + 7 services is memory-hungry on first boot
- **Storage:** 30 GiB gp3 (Docker images alone consume ~8 GiB)
- **Key pair:** create or use an existing SSH key
- **Security group inbound rules:**
  - SSH (22) — your IP only
  - HTTP (80) — `0.0.0.0/0`
  - HTTPS (443) — `0.0.0.0/0`
  - Custom TCP (8000) — `0.0.0.0/0` (temporary, for testing before HTTPS)

### 2. Connect and install Docker

```bash
ssh -i your-key.pem ubuntu@<ec2-public-ip>

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker Engine + Compose plugin
sudo apt-get install -y ca-certificates curl gnupg git
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Allow current user to run docker without sudo
sudo usermod -aG docker $USER
newgrp docker  # apply group membership now

# Verify
docker version && docker compose version
```

### 3. Clone the repo and configure

```bash
git clone https://github.com/gitesh9/coding-interview-platform-backend.git
cd coding-interview-platform-backend

# Make sure the FAISS index is present
ls data/faiss/problems.index   # should print the file

# Copy and edit env file
cp .env.example .env
nano .env   # fill in OPENAI_API_KEY and a strong JWT_SECRET_KEY
```

If `data/faiss/problems.index` is **not** in the repo, copy it from your local machine:
```bash
# from your local machine
scp -i your-key.pem data/faiss/problems.index \
    ubuntu@<ec2-public-ip>:~/coding-interview-platform-backend/data/faiss/
```

### 4. Build and start

```bash
docker compose up -d --build
```

This takes 8–15 minutes on first build. Monitor:
```bash
docker compose logs -f api_gateway
docker compose ps   # all should show "running" or "healthy"
```

### 5. Smoke-test

```bash
curl http://localhost:8000/get/problems-set/
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"test","email":"t@t.com","password":"pass","role":"candidate"}'
```

From your laptop:
```bash
curl http://<ec2-public-ip>:8000/get/problems-set/
```

### 6. (Recommended) Put Caddy in front for HTTPS

Caddy auto-provisions Let's Encrypt certificates. Install on the host:

```bash
sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | \
  sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | \
  sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt-get update && sudo apt-get install -y caddy
```

Point a domain (Route 53 A-record, or any DNS) to the EC2 public IP. Then edit `/etc/caddy/Caddyfile`:

```
api.yourdomain.com {
    # WebSocket-aware reverse proxy to the API gateway
    reverse_proxy localhost:8000
}
```

```bash
sudo systemctl reload caddy
```

Caddy will auto-issue an HTTPS certificate. Now `https://api.yourdomain.com/get/problems-set/` works. You can remove port `8000` from the EC2 security group inbound rules.

### 7. Updating the deployment

```bash
cd ~/coding-interview-platform-backend
git pull
docker compose up -d --build
```

For a clean rebuild:
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

### 8. Operational notes

- **Logs:** `docker compose logs -f <service_name>`
- **Restart one service:** `docker compose restart api_gateway`
- **Check resource usage:** `docker stats`
- **Disk cleanup:** `docker system prune -af` (removes unused images/containers)
- **Backup Postgres:**
  ```bash
  docker compose exec db pg_dump -U postgres postgres > backup-$(date +%F).sql
  ```

### 9. Frontend

The Angular frontend (`coding-interview-platform-frontend`) builds to a static bundle. Deploy it separately to **S3 + CloudFront** (recommended) or to the same EC2 via Caddy:

```
app.yourdomain.com {
    root * /var/www/frontend
    file_server
    try_files {path} /index.html
}
```

Update `src/environments/environment.prod.ts` so the API base URL is `https://api.yourdomain.com` before building.

---

## Scaling Path: Single Instance → Multi-Instance AWS

When you outgrow a single EC2:

1. **Migrate Postgres** → Amazon RDS (change `DATABASE_URL` in `.env`)
2. **Migrate Redis** → Amazon ElastiCache (change `REDIS_URL` in `.env`)
3. **Push images** to ECR and run each service as an ECS Fargate Service (2+ tasks)
4. **Use AWS Cloud Map** for service discovery (replaces Compose DNS)
5. **Put an ALB** in front of `api_gateway` and `collaboration_service`
6. **Move FAISS index** to S3 and lazy-load on `get_service` startup

All services in this codebase are stateless after the recent refactor (Redis pub/sub for collab, HTTP-based runners for code execution), so this scaling path requires no code changes — only infrastructure changes.

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

Each runner is a standalone FastAPI HTTP service (port `9000`) running in its own container. Code execution follows:

1. `code_evaluations_service` builds the full source from the user's code + the problem's `execution_template`
2. POSTs `{ filename, source, input }` to `http://{lang}_runner:9000/execute` (httpx)
3. The runner creates a fresh workspace at `/sandboxes/{UUID}/`, writes source + `input.txt`, and invokes `run.sh` via `subprocess`
4. `run.sh` compiles (if needed) and runs the code with a 2-second `timeout` guard
5. The runner reads `output.txt`, `error.txt`, `time.txt`, `results.txt` and returns them as JSON
6. Workspace is deleted after every request (no shared volume, no Docker socket)

> This HTTP-based design lets the eval service and runners run on separate hosts (e.g., separate ECS tasks).

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