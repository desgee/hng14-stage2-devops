# hng14-stage2-devops

# Job Processor Platform

A distributed, containerised job processing system. Users submit background jobs through a browser dashboard, track progress in real time, and see the final result when processing completes.

```
Browser → Express (frontend :3000) → FastAPI (api :8000) → Redis → Worker
```

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Step-by-Step Setup](#step-by-step-setup)
- [What a Successful Startup Looks Like](#what-a-successful-startup-looks-like)
- [Verifying the Stack](#verifying-the-stack)
- [Stopping the Stack](#stopping-the-stack)
- [Running Tests Locally](#running-tests-locally)
- [Project Structure](#project-structure)
- [Environment Variables Reference](#environment-variables-reference)
- [CI/CD Pipeline](#cicd-pipeline)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

You need three things installed on the machine. Nothing else.

| Tool | Minimum version | Check | Install |
|---|---|---|---|
| **Docker** | 24.0 | `docker --version` | https://docs.docker.com/get-docker |
| **Docker Compose** | v2.20 (bundled with Docker Desktop) | `docker compose version` | Included with Docker Desktop; or `apt install docker-compose-plugin` on Linux |
| **Git** | any | `git --version` | https://git-scm.com |

> **Note:** Docker Compose v2 is required — commands use `docker compose` (with a space), not the legacy `docker-compose` (with a hyphen). Run `docker compose version` to confirm you have v2.

You do **not** need Python, Node.js, or Redis installed locally. Everything runs inside containers.

---

## Quick Start

If you just want it running as fast as possible:

```bash
git clone <your-repo-url> job-processor && cd job-processor
cp .env.example .env
docker compose up -d --build
```

Then open **http://localhost:3000** in your browser.

---

## Step-by-Step Setup

### 1 — Clone the repository

```bash
git clone <your-repo-url> job-processor
cd job-processor
```

### 2 — Create your environment file

The stack is configured entirely through environment variables. A template is provided:

```bash
cp .env.example .env
```

Open `.env` and set a strong Redis password before continuing:

```bash
# .env
REDIS_PASSWORD=replace-this-with-a-strong-random-password
REDIS_MAX_MEMORY=128mb
APP_ENV=production
ALLOWED_ORIGIN=http://localhost:3000
FRONTEND_PORT=3000
```

> **Security:** `.env` is listed in `.gitignore` and must never be committed to version control. It contains the only credential in the system — the Redis password.

You can generate a strong password with:

```bash
openssl rand -base64 32
```

### 3 — Build the images

This step compiles all three service images from source. It only needs to run once (or after any code change):

```bash
docker compose build
```

Expect this to take 2–4 minutes on the first run while base layers are pulled and dependencies are installed. Subsequent builds are fast thanks to layer caching.

### 4 — Start the stack

```bash
docker compose up -d
```

The `-d` flag runs all containers in the background. Docker Compose starts services in dependency order:

1. **Redis** starts first and must pass its healthcheck before anything else begins.
2. **API** and **Worker** start together once Redis is healthy.
3. **Frontend** starts last, once the API is healthy.

---

## What a Successful Startup Looks Like

### During startup

Run this command to watch services come up:

```bash
docker compose ps
```

You will see health states transition from `starting` → `healthy`. A fully running stack looks like this:

```
NAME                IMAGE               STATUS                    PORTS
jobprocessor-redis-1      redis:7-alpine      Up 12 seconds (healthy)
jobprocessor-api-1        jobprocessor-api    Up 8 seconds (healthy)    8000/tcp
jobprocessor-worker-1     jobprocessor-worker Up 8 seconds (healthy)
jobprocessor-frontend-1   jobprocessor-frontend Up 4 seconds (healthy)  0.0.0.0:3000->3000/tcp
```

Every service should show `(healthy)` in the STATUS column. If any service shows `(health: starting)`, wait a few seconds and re-run `docker compose ps` — the full startup takes up to 30 seconds.

### In the logs

```bash
docker compose logs -f
```

A clean startup produces output similar to:

```
redis-1     | 1:M * Ready to accept connections
api-1       | INFO:     Started server process
api-1       | INFO:     Uvicorn running on http://0.0.0.0:8000
worker-1    | 2026-04-22 10:00:01 INFO Processing started, waiting for jobs...
frontend-1  | Frontend running on port 3000
```

No `ERROR` or `WARN` lines should appear during a clean startup.

### In the browser

Open **http://localhost:3000**

You should see:

```
Job Processor Dashboard

[ Submit New Job ]
```

Click **Submit New Job**. Within 3–4 seconds the status should change from `queued` → `completed`.

---

## Verifying the Stack

### Check all containers are healthy

```bash
docker compose ps
```

All four services must show `(healthy)`.

### Hit the API directly

```bash
# Create a job
curl -s -X POST http://localhost:8000/jobs | python3 -m json.tool

# Expected response:
# {
#     "job_id": "xxxxxxxx-xxxx-4xxx-xxxx-xxxxxxxxxxxx"
# }

# Check its status (replace the UUID)
curl -s http://localhost:8000/jobs/<job_id> | python3 -m json.tool

# Expected response after ~2 seconds:
# {
#     "job_id": "xxxxxxxx-xxxx-4xxx-xxxx-xxxxxxxxxxxx",
#     "status": "completed"
# }
```

### Run the integration test

This submits a job through the frontend and polls until it completes, exactly as a user would:

```bash
python3 scripts/integration_test.py
```

Expected output:

```
[integration] Submitting job to http://localhost:3000/submit …
[integration] Job submitted: xxxxxxxx-xxxx-4xxx-xxxx-xxxxxxxxxxxx
[integration] status=queued
[integration] status=queued
[integration] status=completed
[integration] PASS ✓ — job completed successfully.
```

---

## Stopping the Stack

### Stop all containers (preserves data volume)

```bash
docker compose down
```

### Stop and remove all data (full reset)

```bash
docker compose down -v
```

The `-v` flag removes the named `redis_data` volume, wiping all stored job state.

---

## Running Tests Locally

Unit tests run against a mocked Redis instance — no running stack is needed.

### Install test dependencies

```bash
pip install -r app/tests/requirements-test.txt
```

### Run pytest with coverage

```bash
PYTHONPATH=app pytest --cov=app --cov-report=term-missing -v
```

Expected output:

```
app/tests/test_api.py::TestCreateJob::test_create_job_returns_201 PASSED
app/tests/test_api.py::TestCreateJob::test_create_job_response_contains_job_id PASSED
...
app/tests/test_api.py::TestCors::test_cors_header_present_for_allowed_origin PASSED

---------- coverage: platform linux ----------
TOTAL    92%

10 passed in 0.43s
```

---

## Project Structure

```
.
├── app/
│   ├── main.py                   # FastAPI API service
│   ├── Dockerfile                # Multi-stage production image
│   └── tests/
│       ├── test_api.py           # pytest unit tests (Redis mocked)
│       └── requirements-test.txt
├── worker/
│   ├── worker.py                 # Redis queue consumer
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app.js                    # Express proxy server
│   ├── Dockerfile
│   ├── package.json
│   ├── eslint.config.js
│   └── views/
│       └── index.html            # Browser dashboard
├── api/
│   └── requirements.txt
├── scripts/
│   ├── integration_test.py       # End-to-end test script
│   └── rolling_deploy.sh         # Zero-downtime deploy script
├── .github/
│   └── workflows/
│       └── ci.yml                # GitHub Actions CI/CD pipeline
├── docker-compose.yml
├── .env.example                  # Template — copy to .env and fill in
├── .gitignore
├── .hadolint.yaml
└── pytest.ini
```

---

## Environment Variables Reference

All variables are set in your `.env` file. None have defaults that are safe for production — always set them explicitly.

| Variable | Required | Description | Example |
|---|---|---|---|
| `REDIS_PASSWORD` | Yes | Password for the Redis server | `s3cur3-r4nd0m-str1ng` |
| `REDIS_MAX_MEMORY` | No | Redis memory cap | `128mb` |
| `APP_ENV` | No | Environment name used in logs | `production` |
| `ALLOWED_ORIGIN` | No | CORS allowed origin for the API | `http://localhost:3000` |
| `FRONTEND_PORT` | No | Host port the frontend binds to | `3000` |

---

## CI/CD Pipeline

The pipeline lives in `.github/workflows/ci.yml` and runs automatically on GitHub Actions using `ubuntu-latest` free-tier runners — no self-hosted infrastructure required.

### When it runs

| Trigger | Stages that run |
|---|---|
| Push to **any branch** | Lint → Test → Build → Security Scan → Integration Test |
| Push to **`main`** | All of the above **+** Deploy |
| Pull request targeting `main` | Lint → Test → Build → Security Scan → Integration Test |

A failure in any stage immediately stops all subsequent stages. The `needs:` chain in the workflow enforces this strictly.

---

### Pipeline Stages

#### Stage 1 — Lint

Three linters run in a single job:

| Tool | Target | What it checks |
|---|---|---|
| `flake8` | `app/main.py`, `worker/worker.py` | PEP 8 style, unused imports, syntax errors |
| `eslint` (v9 flat config) | `frontend/app.js` | JS style, `no-var`, `prefer-const`, unused variables |
| `hadolint` | All three `Dockerfile`s | Dockerfile best practices (pinned bases, no-root, layer hygiene) |

Linter configuration files: `frontend/eslint.config.js`, `.hadolint.yaml`.

#### Stage 2 — Test

Runs the pytest suite in `app/tests/test_api.py` with Redis fully mocked — no live services needed.

- **10 unit tests** covering job creation, job lookup, 404/400 error paths, UUID validation, Redis key correctness, and CORS headers.
- Coverage is collected with `pytest-cov` and must reach **80%** or the stage fails.
- Two artifacts are uploaded and retained for 14 days:
  - `coverage-report` — XML report (machine-readable) + HTML report (human-readable)

To reproduce locally:

```bash
pip install -r app/tests/requirements-test.txt
PYTHONPATH=app pytest --cov=app --cov-report=term-missing -v
```

#### Stage 3 — Build

Builds all three Docker images and pushes them to a **local ephemeral registry** (`localhost:5000`) running as a service container inside the job. No external registry credentials are needed at this stage.

Each image is tagged twice:

```
localhost:5000/api:<git-sha>
localhost:5000/api:latest
```

GitHub Actions layer cache (`type=gha`) is used so unchanged layers are never re-built. The git SHA is written to an artifact (`image-sha`) and passed to downstream jobs.

#### Stage 4 — Security Scan

Scans all three images with **Trivy**. The pipeline **fails immediately** if any `CRITICAL` severity CVE is found. `ignore-unfixed: true` suppresses CVEs that have no available fix, keeping noise low.

Results are published in two places:
- **GitHub Security → Code Scanning tab** (SARIF format, visible in the repository UI)
- **`trivy-sarif` artifact** (downloadable `.sarif` files, retained 14 days)

Because images must exist in the local Docker daemon for Trivy to scan them, this stage rebuilds from the GitHub Actions layer cache — which makes the rebuild near-instant.

#### Stage 5 — Integration Test

Brings the **full four-service stack** up inside the GitHub Actions runner using `docker compose`, then runs `scripts/integration_test.py` against it.

The test script:
1. `POST /submit` — submits a job through the Express frontend
2. Polls `GET /status/:id` every second until status is `completed`
3. Asserts the final status is exactly `"completed"`
4. Exits non-zero on any error, network failure, or timeout (30 s)

The stack is torn down with `docker compose down -v` in an `if: always()` step — it is removed regardless of whether the test passed or failed. Compose logs are captured and uploaded as the `compose-logs` artifact for debugging failures.

#### Stage 6 — Deploy *(main branch only)*

Runs only on a push to `main`. Performs a **zero-downtime rolling update** across all three services using `scripts/rolling_deploy.sh` over SSH.

**How the rolling deploy works:**

```
1. Pull new image on the production host
2. Start NEW container alongside the existing one (different name)
3. Poll `docker inspect .State.Health.Status` every 2 seconds
4. If healthy within 60 seconds  →  stop and remove the OLD container ✓
5. If not healthy within 60 seconds  →  stop and remove the NEW container,
                                         OLD container keeps running (no downtime) ✗
```

This means a bad deploy never causes an outage — the old container stays up if the new one fails its healthcheck.

A `concurrency` block prevents two deploys running simultaneously. A newer push queues behind an in-progress deploy rather than cancelling it.

---

### Required GitHub Actions Secrets

Go to **Settings → Secrets and variables → Actions** in your repository and add:

#### Needed for all branches (stages 1–5)

| Secret | Description |
|---|---|
| `REDIS_PASSWORD` | Redis password used during integration tests |

#### Needed for deploy (stage 6, `main` only)

| Secret | Description |
|---|---|
| `REGISTRY_HOST` | Hostname of your production container registry |
| `REGISTRY_USER` | Registry login username |
| `REGISTRY_PASSWORD` | Registry login password or token |
| `DEPLOY_HOST` | IP or hostname of the production server |
| `DEPLOY_USER` | SSH username on the production server |
| `DEPLOY_SSH_KEY` | Private SSH key (production server must have the matching public key in `authorized_keys`) |
| `PRODUCTION_URL` | Public URL shown in the GitHub Environments UI |

Generate a dedicated deploy key pair with:

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f deploy_key -N ""
# Add deploy_key.pub to the server's ~/.ssh/authorized_keys
# Paste the contents of deploy_key as the DEPLOY_SSH_KEY secret
```

---

### Reading a Pipeline Run

In your repository, click **Actions** → select the most recent workflow run. You will see six jobs listed in order:

```
✅ 1 · Lint
✅ 2 · Unit Tests + Coverage
✅ 3 · Build & Push Images
✅ 4 · Security Scan (Trivy)
✅ 5 · Integration Test
✅ 6 · Deploy (rolling)       ← only appears on pushes to main
```

A green tick on all six means the commit is live in production. A red cross on any stage means all subsequent stages were skipped — click the failed job to see the exact step and error.

**Downloading artifacts** — click any completed run, scroll to the **Artifacts** section at the bottom, and download:
- `coverage-report` — HTML test coverage report
- `trivy-sarif` — Trivy security scan results
- `compose-logs` — Full Docker Compose logs from the integration test

---

## Troubleshooting

### A service is stuck in `(health: starting)`

Wait up to 60 seconds — services with `depends_on: condition: service_healthy` wait for upstream healthchecks before they start. If a service never becomes healthy, check its logs:

```bash
docker compose logs <service-name>
# e.g.:
docker compose logs api
docker compose logs worker
```

### Redis authentication error in API or Worker logs

The `REDIS_PASSWORD` in your `.env` does not match what Redis was started with. Run a full reset:

```bash
docker compose down -v
docker compose up -d
```

### Port 3000 is already in use

Change the host port in `.env`:

```bash
FRONTEND_PORT=3001
```

Then restart: `docker compose down && docker compose up -d`

### `docker compose` command not found

You have the legacy `docker-compose` (v1) instead of the v2 plugin. Either install Docker Desktop (which includes v2), or on Linux:

```bash
sudo apt install docker-compose-plugin   # Debian/Ubuntu
sudo yum install docker-compose-plugin   # RHEL/CentOS
```

### Images are stale after a code change

Rebuild before restarting:

```bash
docker compose up -d --build
```

### Resetting everything to a clean state

```bash
docker compose down -v --remove-orphans
docker compose build --no-cache
docker compose up -d
```
