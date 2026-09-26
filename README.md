# Agentic Automation Platform

[![CI](https://github.com/Lonfea/agentic-automation-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/Lonfea/agentic-automation-platform/actions/workflows/ci.yml)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)
![Celery](https://img.shields.io/badge/Workers-Celery-37814A)
![Redis](https://img.shields.io/badge/Broker-Redis-DC382D)
![Reliability](https://img.shields.io/badge/Pattern-Idempotent%20Async%20Jobs-blue)

A webhook-driven asynchronous execution service designed around the failure modes that matter in production automation: duplicate delivery, worker crashes, transient dependency failures, retry storms and permanently failed jobs.

## System architecture

```text
flowchart LR
EXT[External System] -->|Webhook| API[FastAPI]
API --> ID{Idempotency Store}
ID -->|duplicate| DUP[Return existing acceptance]
ID -->|new| Q[(Redis / Celery Queue)]
Q --> W[Automation Worker]
W -->|success| DONE[Completed]
W -->|transient failure| RETRY[Exponential Backoff]
RETRY --> W
W -->|retries exhausted| DLQ[(Dead-Letter Queue)]
DLQ --> DW[DLQ Worker / Inspection] 
```

## Retry lifecycle

```text
stateDiagram-v2
[*] --> Accepted
Accepted --> Queued
Queued --> Processing
Processing --> Completed: success
Processing --> Retrying: transient failure
Retrying --> Processing: backoff elapsed
Retrying --> DeadLettered: retry budget exhausted
Completed --> [*]
DeadLettered --> [*] 
```

## Reliability guarantees demonstrated

- **Idempotency:** same key + same payload does not enqueue duplicate work.
- **Conflict detection:** same key + different payload is rejected.
- **Late acknowledgement:** unfinished work is not silently acknowledged when a worker dies.
- **Bounded exponential backoff:** transient errors retry without immediate hammering.
- **Dead-letter handling:** permanently failing jobs move to a dedicated queue.
- **Separate workers:** normal automation and dead-letter processing are operationally distinct.

## Run locally

```bash
git clone https://github.com/Lonfea/agentic-automation-platform.git
cd agentic-automation-platform
docker compose up --build
```

Then send an event:

```bash
curl -X POST http://localhost:8000/webhooks/events \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: order-123" \
  -d '{"event_id":"evt-123","event_type":"report.generate","payload":{"report_id":"r-42"}}'
```

## What this demonstrates

Async API design, Celery worker architecture, webhook semantics, idempotency, failure recovery and explicit dead-letter behavior—the infrastructure needed to make agentic workflows dependable outside a notebook.

## Production roadmap

- signed webhook verification;
- transactional outbox;
- persistent DLQ replay/inspection UI;
- OpenTelemetry trace propagation;
- managed/clustered broker;
- workflow compensation logic;
- per-workflow concurrency controls.

> No throughput or reliability percentage is claimed until the system is load-tested under a defined workload.
