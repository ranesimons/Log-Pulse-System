from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


LogLevel = Literal["DEBUG", "INFO", "WARN", "ERROR", "FATAL"]


# ── Ingest ────────────────────────────────────────────────────────────────────

class LogIngest(BaseModel):
    timestamp: datetime | None = None
    level: LogLevel
    service: str = Field(..., max_length=100)
    message: str
    host: str | None = Field(None, max_length=255)
    environment: str = Field("production", max_length=20)
    trace_id: str | None = Field(None, max_length=64)
    span_id: str | None = Field(None, max_length=32)
    metadata: dict[str, Any] = {}


class BatchIngest(BaseModel):
    logs: list[LogIngest] = Field(..., max_length=1000)


# ── Responses ─────────────────────────────────────────────────────────────────

class LogRecord(BaseModel):
    id: UUID
    timestamp: datetime
    level: str
    service: str
    message: str
    host: str | None
    environment: str
    trace_id: str | None
    span_id: str | None
    metadata: dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class LogPage(BaseModel):
    items: list[LogRecord]
    next_cursor: str | None
    total_hint: int | None


class IngestResponse(BaseModel):
    inserted: int


# ── Stats ─────────────────────────────────────────────────────────────────────

class OverviewStats(BaseModel):
    total_logs: int
    error_count: int
    fatal_count: int
    warn_count: int
    error_rate: float
    unique_services: int
    window_hours: int


class LevelBucket(BaseModel):
    level: str
    count: int


class ServiceBucket(BaseModel):
    service: str
    count: int
    error_count: int


class TimelineBucket(BaseModel):
    bucket: datetime
    total: int
    debug: int
    info: int
    warn: int
    error: int
    fatal: int
