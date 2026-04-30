#!/usr/bin/env python3
"""Seed the database with 100K realistic log rows."""
import asyncio
import json
import os
import random
import uuid
from datetime import datetime, timedelta, timezone

import asyncpg

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://logpulse:logpulse@localhost:5432/logpulse")

SERVICES = [
    "api-gateway", "auth-service", "user-service", "payment-service",
    "notification-service", "search-service", "recommendation-engine",
    "order-service", "inventory-service", "analytics-service",
]
LEVELS = ["DEBUG", "INFO", "INFO", "INFO", "WARN", "WARN", "ERROR", "ERROR", "FATAL"]
ENVIRONMENTS = ["production", "staging", "development"]
HOSTS = [f"host-{i:03d}" for i in range(1, 21)]

MESSAGES = {
    "DEBUG": [
        "Cache lookup for key {key}",
        "SQL query executed in {ms}ms: SELECT * FROM {table}",
        "Processing item {id} from queue",
        "Connection pool size: {n}",
        "Feature flag '{flag}' evaluated to {val}",
    ],
    "INFO": [
        "Request {method} {path} completed in {ms}ms",
        "User {user_id} authenticated successfully",
        "Order {order_id} created for customer {customer_id}",
        "Payment processed: ${amount} for order {order_id}",
        "Email notification sent to {email}",
        "Service started on port {port}",
        "Background job '{job}' completed successfully",
        "Cache warmed for {n} items",
        "Webhook delivered to {url} (status={status})",
        "Config reloaded: {n} keys updated",
    ],
    "WARN": [
        "Slow query detected: {ms}ms for {query}",
        "Retry attempt {n}/3 for {service}",
        "High memory usage: {pct}% of limit",
        "Rate limit approaching for client {client_id}: {req}/min",
        "Deprecated endpoint {path} called by {client_id}",
        "Circuit breaker half-open for {service}",
        "Cache miss rate elevated: {pct}%",
        "Disk usage at {pct}% on {host}",
    ],
    "ERROR": [
        "Failed to connect to {service}: {error}",
        "Unhandled exception in {handler}: {error}",
        "Payment declined for order {order_id}: {reason}",
        "Database query timed out after {ms}ms",
        "Invalid JWT token for user {user_id}",
        "Third-party API {api} returned {status}",
        "Queue consumer died, restarting",
        "File upload failed: {error}",
    ],
    "FATAL": [
        "Out of memory, process killed",
        "Database connection pool exhausted",
        "Unrecoverable error in core service: {error}",
        "Disk full on {host}",
        "SSL certificate expired for {domain}",
    ],
}

def _render(template: str) -> str:
    replacements = {
        "{key}": f"cache:{uuid.uuid4().hex[:8]}",
        "{ms}": str(random.randint(1, 5000)),
        "{table}": random.choice(["users", "orders", "products", "sessions"]),
        "{id}": str(random.randint(1000, 9999)),
        "{n}": str(random.randint(1, 100)),
        "{flag}": random.choice(["new-checkout", "dark-mode", "beta-search"]),
        "{val}": random.choice(["true", "false"]),
        "{method}": random.choice(["GET", "POST", "PUT", "DELETE"]),
        "{path}": random.choice(["/api/users", "/api/orders", "/api/products", "/api/search", "/api/auth"]),
        "{user_id}": str(random.randint(10000, 99999)),
        "{order_id}": f"ORD-{random.randint(10000, 99999)}",
        "{customer_id}": str(random.randint(10000, 99999)),
        "{amount}": f"{random.uniform(10, 500):.2f}",
        "{email}": f"user{random.randint(1,9999)}@example.com",
        "{port}": str(random.choice([8000, 8080, 3000, 5000])),
        "{job}": random.choice(["daily-report", "cleanup", "index-rebuild", "cache-warm"]),
        "{url}": f"https://hooks.example.com/{uuid.uuid4().hex[:6]}",
        "{status}": str(random.choice([200, 201, 400, 404, 500, 502, 503])),
        "{pct}": str(random.randint(50, 99)),
        "{query}": "SELECT * FROM orders WHERE status = 'pending'",
        "{service}": random.choice(SERVICES),
        "{client_id}": f"client-{random.randint(1, 50)}",
        "{req}": str(random.randint(80, 120)),
        "{handler}": random.choice(["handle_request", "process_event", "consume_message"]),
        "{error}": random.choice(["Connection refused", "Timeout", "EOF", "Permission denied"]),
        "{reason}": random.choice(["Insufficient funds", "Card expired", "Invalid CVV"]),
        "{api}": random.choice(["stripe", "sendgrid", "twilio", "google-maps"]),
        "{domain}": random.choice(["api.example.com", "app.example.com", "cdn.example.com"]),
        "{host}": random.choice(HOSTS),
    }
    result = template
    for k, v in replacements.items():
        result = result.replace(k, v)
    return result


def make_row(now: datetime, idx: int):
    level = random.choice(LEVELS)
    service = random.choice(SERVICES)
    # Skew timestamps: 70% in last 24h, 30% spread over last 30 days
    if random.random() < 0.7:
        delta = timedelta(seconds=random.uniform(0, 86400))
    else:
        delta = timedelta(seconds=random.uniform(0, 86400 * 30))
    ts = now - delta

    trace_id = uuid.uuid4().hex if random.random() > 0.4 else None
    span_id  = uuid.uuid4().hex[:16] if trace_id else None

    metadata = {}
    if random.random() > 0.5:
        metadata["request_id"] = uuid.uuid4().hex
    if level in ("ERROR", "FATAL"):
        metadata["stack_trace"] = f"Traceback (most recent call last):\n  File 'app.py', line {random.randint(10,500)}"
    if random.random() > 0.7:
        metadata["duration_ms"] = random.randint(1, 3000)

    message = _render(random.choice(MESSAGES[level]))

    return (
        ts,
        level,
        service,
        message,
        random.choice(HOSTS),
        random.choice(ENVIRONMENTS),
        trace_id,
        span_id,
        json.dumps(metadata),
    )


async def seed(total: int = 100_000, batch: int = 2000):
    conn = await asyncpg.connect(DATABASE_URL)
    now = datetime.now(timezone.utc)

    print(f"Seeding {total:,} rows in batches of {batch}...")
    inserted = 0
    while inserted < total:
        chunk = min(batch, total - inserted)
        rows = [make_row(now, inserted + i) for i in range(chunk)]
        await conn.executemany(
            """
            INSERT INTO logs
                (timestamp, level, service, message, host, environment, trace_id, span_id, metadata)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
            """,
            rows,
        )
        inserted += chunk
        print(f"  {inserted:,}/{total:,}")

    await conn.close()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(seed())
