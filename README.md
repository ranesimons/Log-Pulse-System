# Log Pulse

A log ingestion and observability system that stores high-volume structured log data and surfaces real-time insights through a dashboard.

---

## Architecture

```
┌──────────────────┐     HTTP/REST      ┌──────────────┐     asyncpg      ┌─────────────┐
│  Svelte 5 + TS   │ ◄────────────────► │  FastAPI API  │ ◄──────────────► │  PostgreSQL  │
│   (Vite SPA)     │                    │  (Python 3.12)│                  │  (16-alpine) │
└──────────────────┘                    └──────────────┘                  └─────────────┘
       :3000                                  :8000                             :5432
```

### Components

| Layer | Tech | Role |
|-------|------|------|
| Frontend | Svelte 5 + TypeScript + Vite + Chart.js | Dashboard SPA with charts, filters, log table |
| Backend | FastAPI + asyncpg | REST API for ingest and query |
| Database | PostgreSQL 16 | Persistent log storage with optimized indexes |
| Infra | Docker Compose + K8s | Local dev and cluster deployment |

---

## Database Schema

```sql
CREATE TABLE logs (
    id          UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    timestamp   TIMESTAMPTZ NOT NULL,
    level       VARCHAR(10) NOT NULL,   -- DEBUG INFO WARN ERROR FATAL
    service     VARCHAR(100) NOT NULL,
    message     TEXT        NOT NULL,
    host        VARCHAR(255),
    environment VARCHAR(20) NOT NULL DEFAULT 'production',
    trace_id    VARCHAR(64),
    span_id     VARCHAR(32),
    metadata    JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Indexes (all targeting < 100ms at 100K rows):**

| Index | Type | Why |
|-------|------|-----|
| `(timestamp DESC)` | BTree | Primary time-range scans |
| `(level, timestamp DESC)` | BTree | Level + time filter combos |
| `(service, timestamp DESC)` | BTree | Service + time filter combos |
| `(trace_id)` WHERE NOT NULL | BTree | Trace correlation lookups |
| `to_tsvector(message)` | GIN | Full-text search on log messages |
| `metadata` | GIN | Arbitrary JSON metadata filtering |

---

## API Endpoints

### Ingest
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/logs` | Ingest a single log entry |
| `POST` | `/api/v1/logs/batch` | Batch ingest up to 1,000 logs |

### Query
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/logs` | Paginated log query with filters |
| `GET` | `/api/v1/logs/{id}` | Fetch single log by UUID |

**Query params:** `level[]`, `service[]`, `start`, `end`, `q` (full-text), `limit`, `cursor`

### Stats
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/stats/overview` | Total, error count, error rate, unique services |
| `GET` | `/api/v1/stats/by-level` | Log count per level |
| `GET` | `/api/v1/stats/by-service` | Top N services by volume + errors |
| `GET` | `/api/v1/stats/timeline` | Time-bucketed log volume (all levels) |
| `GET` | `/api/v1/stats/services` | Distinct service names |

All stat endpoints accept a `?hours=24` window parameter.

### System
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |

---

## Setup

### Prerequisites
- Docker + Docker Compose v2

### Run locally

```bash
# Start all services
docker compose up --build

# In a separate terminal, seed 100K rows
docker compose --profile seed run --rm seed
```

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

### Run without Docker

```bash
# Start PostgreSQL (requires psql locally or a running instance)
createdb logpulse

# Backend
cd backend
pip install -r requirements.txt
DATABASE_URL=postgresql://localhost/logpulse uvicorn app.main:app --reload

# Seed
DATABASE_URL=postgresql://localhost/logpulse python scripts/seed.py

# Frontend
cd frontend
npm install && npm run dev
```

---

## Kubernetes Deployment

```bash
# Apply secret (edit k8s/secret-example.yaml first)
kubectl apply -f k8s/secret-example.yaml

# Deploy backend
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml
```

The Deployment runs 2 replicas with CPU/memory limits and HTTP liveness/readiness probes.

---

## Trade-offs & What I'd Improve

### Decisions made
- **Cursor pagination over offset** — `OFFSET N` degrades linearly; cursor-based pagination stays constant-time at any depth.
- **asyncpg over SQLAlchemy ORM** — lower abstraction = faster async queries, no ORM overhead on 100K row aggregations.
- **GIN index on `metadata` JSONB** — keeps arbitrary metadata filterable without schema changes, at the cost of slightly slower writes.
- **FastAPI over Flask/Django** — native async + automatic OpenAPI docs is a better fit for a high-throughput ingest API.
- **Svelte 5 + TypeScript over React** — Svelte's compiled output is smaller and faster with no virtual DOM; runes (`$state`, `$effect`, `$derived`) make reactivity explicit and easy to follow; Chart.js bound directly to canvas elements keeps the charting layer thin.

### Given more time
- **Ingest queue** — put Kafka or Redis Streams in front of the DB write so spikes don't block the ingest endpoint.
- **Materialized views** — pre-aggregate hourly buckets so stats queries are sub-millisecond even at 100M rows.
- **Authentication** — API key or JWT auth on the ingest endpoint; dashboard login.
- **Alerting** — threshold-based rules that fire webhooks when error rate exceeds a configured %, stored in a separate `alert_rules` table.
- **Log retention policy** — `pg_partman` table partitioning by month + automatic partition drop for cost control.
- **Structured filtering on metadata** — expose a query DSL for metadata fields in the UI (e.g. `metadata.request_id = "abc"`).
- **WebSocket push** — replace 15s polling with a server-sent events or WebSocket stream for true real-time updates.
- **OpenTelemetry collector** — add an OTLP endpoint so any OTel-instrumented service can ship traces + logs without SDK changes.
