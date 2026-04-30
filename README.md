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

## Getting Started

### Prerequisites
- Docker + Docker Compose v2

### 1. Start the stack

```bash
docker compose up --build
```

### 2. Seed 100K rows

```bash
docker compose --profile seed run --rm seed
```

> **Note:** The seed script distributes logs realistically — 70% within the last 24 hours and 30% spread randomly across the last 30 days. The default dashboard window is 24 hours, so switching to the 7-day view will show ~77K logs and the full 100K only appears at the 30-day window.

### 3. Open the dashboard

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

### Tear down

```bash
docker compose down
```

---

## Kubernetes (Alternative)

K8s is supported as an alternative to Docker Compose using [kind](https://kind.sigs.k8s.io/) (Kubernetes inside Docker). Docker Compose and the kind cluster cannot run at the same time as they share ports — stop one before starting the other.

### Prerequisites

```bash
brew install kind kubectl
```

### Start

```bash
bash k8s/setup-kind.sh
```

Builds both images, loads them into the cluster, applies all manifests, and waits for readiness.

### Seed 100K rows

```bash
kubectl run seed --image=logpulse-backend:latest --image-pull-policy=IfNotPresent --restart=Never \
  --overrides='{"spec":{"hostNetwork":true}}' \
  --env=DATABASE_URL=postgresql://logpulse:logpulse@localhost:5432/logpulse \
  -- python scripts/seed.py
```

### Redeploy after code changes

```bash
bash k8s/redeploy.sh
```

### Tear down

```bash
kind delete cluster --name logpulse
```

### Production readiness gaps

The K8s manifests are tuned for kind and would need the following changes before a production deployment:

- **`hostNetwork: true`** — used to bypass iptables latency in kind. Remove it in production (real clusters have fast CNI) and revert `DATABASE_URL` to `postgres:5432`.
- **Credentials** — `secret-local.yaml` contains plaintext dev credentials. Production should use a secrets manager (AWS Secrets Manager, Vault, Sealed Secrets).
- **`strategy: Recreate` + `replicas: 1`** — required in kind because `hostNetwork` causes port conflicts on a single node. Production should use `RollingUpdate` with multiple replicas and `PodDisruptionBudgets`.
- **No Ingress** — services are exposed via NodePort. Production needs an `Ingress` resource with TLS termination (nginx-ingress, ALB, etc.).
- **PostgreSQL as a Deployment** — fine for dev but production should use a managed database (RDS, Cloud SQL) or a `StatefulSet` with backup configuration.

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
- **WebSocket push** — replace 15s polling with a server-sent events for true real-time updates.
- **OpenTelemetry collector** — add an OTLP endpoint so any OTel-instrumented service can ship traces + logs without SDK changes.
