from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from ..database import get_pool
from ..schemas import BatchIngest, IngestResponse, LogIngest, LogPage, LogRecord

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])


# ── helpers ───────────────────────────────────────────────────────────────────

def _row_to_record(row: asyncpg.Record) -> LogRecord:
    return LogRecord(
        id=row["id"],
        timestamp=row["timestamp"],
        level=row["level"],
        service=row["service"],
        message=row["message"],
        host=row["host"],
        environment=row["environment"],
        trace_id=row["trace_id"],
        span_id=row["span_id"],
        metadata=json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"],
        created_at=row["created_at"],
    )


# ── ingest ────────────────────────────────────────────────────────────────────

@router.post("", response_model=IngestResponse, status_code=201)
async def ingest_single(body: LogIngest, pool: asyncpg.Pool = Depends(get_pool)):
    ts = body.timestamp or datetime.now(timezone.utc)
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO logs (timestamp, level, service, message, host, environment,
                              trace_id, span_id, metadata)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
            """,
            ts, body.level, body.service, body.message,
            body.host, body.environment, body.trace_id, body.span_id,
            json.dumps(body.metadata),
        )
    return IngestResponse(inserted=1)


@router.post("/batch", response_model=IngestResponse, status_code=201)
async def ingest_batch(body: BatchIngest, pool: asyncpg.Pool = Depends(get_pool)):
    now = datetime.now(timezone.utc)
    rows = [
        (
            log.timestamp or now,
            log.level, log.service, log.message,
            log.host, log.environment, log.trace_id, log.span_id,
            json.dumps(log.metadata),
        )
        for log in body.logs
    ]
    async with pool.acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO logs (timestamp, level, service, message, host, environment,
                              trace_id, span_id, metadata)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
            """,
            rows,
        )
    return IngestResponse(inserted=len(rows))


# ── query ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=LogPage)
async def query_logs(
    level: Annotated[list[str] | None, Query()] = None,
    service: Annotated[list[str] | None, Query()] = None,
    start: datetime | None = None,
    end: datetime | None = None,
    q: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    cursor: str | None = None,          # opaque: ISO timestamp|uuid
    pool: asyncpg.Pool = Depends(get_pool),
):
    conditions: list[str] = []
    params: list = []
    idx = 1

    # cursor-based pagination: page after (timestamp, id)
    if cursor:
        try:
            cur_ts_str, cur_id = cursor.split("|", 1)
            cur_ts = datetime.fromisoformat(cur_ts_str)
            conditions.append(
                f"(timestamp < ${idx} OR (timestamp = ${idx} AND id::text < ${idx+1}))"
            )
            params += [cur_ts, cur_id]
            idx += 2
        except (ValueError, AttributeError):
            raise HTTPException(status_code=400, detail="Invalid cursor")

    if level:
        placeholders = ",".join(f"${i}" for i in range(idx, idx + len(level)))
        conditions.append(f"level IN ({placeholders})")
        params += level
        idx += len(level)

    if service:
        placeholders = ",".join(f"${i}" for i in range(idx, idx + len(service)))
        conditions.append(f"service IN ({placeholders})")
        params += service
        idx += len(service)

    if start:
        conditions.append(f"timestamp >= ${idx}::timestamptz")
        params.append(start)
        idx += 1

    if end:
        conditions.append(f"timestamp <= ${idx}::timestamptz")
        params.append(end)
        idx += 1

    if q:
        conditions.append(f"to_tsvector('english', message) @@ plainto_tsquery('english', ${idx})")
        params.append(q)
        idx += 1

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"""
        SELECT id, timestamp, level, service, message, host, environment,
               trace_id, span_id, metadata, created_at
        FROM logs
        {where}
        ORDER BY timestamp DESC, id DESC
        LIMIT ${idx}
    """
    params.append(limit + 1)

    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, *params)

    has_more = len(rows) > limit
    items = [_row_to_record(r) for r in rows[:limit]]
    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = f"{last.timestamp.isoformat()}|{last.id}"

    return LogPage(items=items, next_cursor=next_cursor, total_hint=None)


@router.get("/{log_id}", response_model=LogRecord)
async def get_log(log_id: str, pool: asyncpg.Pool = Depends(get_pool)):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, timestamp, level, service, message, host, environment,
                   trace_id, span_id, metadata, created_at
            FROM logs WHERE id = $1::uuid
            """,
            log_id,
        )
    if not row:
        raise HTTPException(status_code=404, detail="Log not found")
    return _row_to_record(row)
