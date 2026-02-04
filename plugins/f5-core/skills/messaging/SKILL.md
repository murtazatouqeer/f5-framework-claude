---
name: messaging
description: Message queues, events, and async communication patterns
category: skill
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: true
context: inject
version: 1.0.0
---

# Messaging Skills

## Overview

Asynchronous communication patterns for building scalable, decoupled distributed systems. Messaging enables services to communicate without direct coupling, improving reliability and scalability.

## Messaging Types

| Type | Description | Use Case | Examples |
|------|-------------|----------|----------|
| **Point-to-Point** | One sender, one receiver | Task distribution | RabbitMQ, SQS |
| **Pub/Sub** | One sender, many receivers | Event broadcasting | Kafka, Redis Pub/Sub |
| **Request/Reply** | Synchronous over async | RPC-style calls | RabbitMQ RPC |
| **Event Streaming** | Ordered, replayable log | Event sourcing | Kafka, Kinesis |

## Delivery Guarantees

| Guarantee | Description | Trade-off |
|-----------|-------------|-----------|
| **At-most-once** | Fire and forget | May lose messages |
| **At-least-once** | Retry until acknowledged | May have duplicates |
| **Exactly-once** | Deduplicated delivery | Complex, higher latency |

## When to Use Messaging

### Use Messaging For

- Decoupling services
- Async task processing
- Event-driven architectures
- Load leveling and buffering
- Cross-service communication

### Avoid Messaging When

- Simple request/response is sufficient
- Strong consistency is required
- Real-time response is critical
- System complexity isn't justified

## Categories

### Fundamentals
Core messaging concepts:
- **Messaging Patterns** - Common communication patterns
- **Sync vs Async** - When to use each approach
- **Message Types** - Commands, events, and queries

### Queues
Message queue implementations:
- **RabbitMQ** - Feature-rich message broker
- **Redis Queues** - Simple Redis-based queues
- **AWS SQS** - Managed queue service
- **BullMQ** - Node.js job queue

### Events
Event-driven patterns:
- **Event-Driven Architecture** - EDA fundamentals
- **Apache Kafka** - Event streaming platform
- **Event Sourcing** - State as event log
- **Pub/Sub** - Publish-subscribe patterns

### Patterns
Distributed system patterns:
- **Saga Pattern** - Distributed transactions
- **Outbox Pattern** - Reliable event publishing
- **Retry Strategies** - Handling failures
- **Dead Letter Queue** - Failed message handling

### Reliability
Ensuring message delivery:
- **Delivery Guarantees** - At-most/least/exactly-once
- **Idempotency** - Safe message reprocessing
- **Message Ordering** - Maintaining sequence

### Best Practices
Production considerations:
- **Message Design** - Schema and versioning
- **Error Handling** - Failure management
- **Monitoring** - Observability and alerting

## Quick Reference

### Message Broker Comparison

| Feature | RabbitMQ | Kafka | SQS | Redis |
|---------|----------|-------|-----|-------|
| Model | Queue | Log | Queue | Queue/Pub-Sub |
| Ordering | Per-queue | Per-partition | FIFO option | Per-queue |
| Persistence | Durable | Always | Always | Optional |
| Replay | No | Yes | No | No |
| Throughput | High | Very High | High | Very High |
| Latency | Low | Low | Medium | Very Low |

### Common Patterns

```
Producer → Queue → Consumer (Point-to-Point)
Producer → Exchange → Queue → Consumer (RabbitMQ)
Producer → Topic → Partition → Consumer Group (Kafka)
Publisher → Channel → Subscribers (Pub/Sub)
```

## Integration with F5

```yaml
# In f5-config.yaml
messaging:
  broker: rabbitmq
  queues:
    - name: orders
      durable: true
      dlq: orders-dlq
  events:
    - topic: order.placed
      retention: 7d
```

## Related Skills

- [Architecture](/skills/architecture/) - System design patterns
- [Database](/skills/database/) - Transactional outbox
- [DevOps](/skills/devops/) - Message broker deployment
