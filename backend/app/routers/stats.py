from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, Query

from ..database import get_pool
from ..schemas import LevelBucket, OverviewStats, ServiceBucket, TimelineBucket

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


@router.get("/overview", response_model=OverviewStats)
async def overview(
    hours: int = Query(24, ge=1, le=720),
    pool: asyncpg.Pool = Depends(get_pool),
):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                COUNT(*)                                        AS total_logs,
                COUNT(*) FILTER (WHERE level = 'ERROR')        AS error_count,
                COUNT(*) FILTER (WHERE level = 'FATAL')        AS fatal_count,
                COUNT(*) FILTER (WHERE level = 'WARN')         AS warn_count,
                COUNT(DISTINCT service)                        AS unique_services
            FROM logs
            WHERE timestamp >= $1
            """,
            since,
        )

    total = row["total_logs"] or 0
    errors = (row["error_count"] or 0) + (row["fatal_count"] or 0)
    return OverviewStats(
        total_logs=total,
        error_count=row["error_count"] or 0,
        fatal_count=row["fatal_count"] or 0,
        warn_count=row["warn_count"] or 0,
        error_rate=round(errors / total * 100, 2) if total else 0.0,
        unique_services=row["unique_services"] or 0,
        window_hours=hours,
    )


@router.get("/by-level", response_model=list[LevelBucket])
async def by_level(
    hours: int = Query(24, ge=1, le=720),
    pool: asyncpg.Pool = Depends(get_pool),
):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT level, COUNT(*) AS count
            FROM logs
            WHERE timestamp >= $1
            GROUP BY level
            ORDER BY count DESC
            """,
            since,
        )
    return [LevelBucket(level=r["level"], count=r["count"]) for r in rows]


@router.get("/by-service", response_model=list[ServiceBucket])
async def by_service(
    hours: int = Query(24, ge=1, le=720),
    top: int = Query(10, ge=1, le=50),
    pool: asyncpg.Pool = Depends(get_pool),
):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                service,
                COUNT(*)                                  AS count,
                COUNT(*) FILTER (WHERE level IN ('ERROR','FATAL')) AS error_count
            FROM logs
            WHERE timestamp >= $1
            GROUP BY service
            ORDER BY count DESC
            LIMIT $2
            """,
            since,
            top,
        )
    return [
        ServiceBucket(service=r["service"], count=r["count"], error_count=r["error_count"])
        for r in rows
    ]


@router.get("/timeline", response_model=list[TimelineBucket])
async def timeline(
    hours: int = Query(24, ge=1, le=720),
    buckets: int = Query(24, ge=4, le=168),
    pool: asyncpg.Pool = Depends(get_pool),
):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    interval_secs = (hours * 3600) // buckets
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                to_timestamp(
                    floor(EXTRACT(EPOCH FROM timestamp) / $2) * $2
                ) AT TIME ZONE 'UTC' AS bucket,
                COUNT(*)                                         AS total,
                COUNT(*) FILTER (WHERE level = 'DEBUG')         AS debug,
                COUNT(*) FILTER (WHERE level = 'INFO')          AS info,
                COUNT(*) FILTER (WHERE level = 'WARN')          AS warn,
                COUNT(*) FILTER (WHERE level = 'ERROR')         AS error,
                COUNT(*) FILTER (WHERE level = 'FATAL')         AS fatal
            FROM logs
            WHERE timestamp >= $1
            GROUP BY bucket
            ORDER BY bucket ASC
            """,
            since,
            interval_secs,
        )
    return [
        TimelineBucket(
            bucket=r["bucket"],
            total=r["total"],
            debug=r["debug"],
            info=r["info"],
            warn=r["warn"],
            error=r["error"],
            fatal=r["fatal"],
        )
        for r in rows
    ]


@router.get("/services", response_model=list[str])
async def list_services(pool: asyncpg.Pool = Depends(get_pool)):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT DISTINCT service FROM logs ORDER BY service"
        )
    return [r["service"] for r in rows]
