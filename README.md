# Agentic Automation Pipeline

A webhook-driven asynchronous execution service with idempotency, Celery workers, bounded exponential backoff, late acknowledgements, and a dead-letter queue.

## Delivery path

Webhook -> idempotency claim -> Celery queue -> worker -> success or retry -> dead-letter queue after retry exhaustion.

## Reliability properties

- duplicate webhook deliveries with the same key and payload are accepted without creating another task;
- reusing the same idempotency key for a different payload returns a conflict;
- tasks acknowledge late so a worker crash does not silently mark unfinished work complete;
- transient dependency errors use bounded exponential backoff;
- exhausted tasks are handed to a dedicated dead-letter queue.

## Run

    docker compose up --build

Then POST an event with an `Idempotency-Key` header to `/webhooks/events`.

## Production upgrades

- signed webhook verification;
- transactional outbox for downstream effects;
- persistent DLQ inspection/replay UI;
- OpenTelemetry trace propagation from webhook to worker;
- Redis Cluster or managed broker;
- workflow-specific compensation logic.
