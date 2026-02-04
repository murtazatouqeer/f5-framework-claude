---
name: database-types
description: Comparison of database paradigms and their use cases
category: database/fundamentals
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Database Types

## Overview

Understanding different database paradigms is essential for choosing
the right tool for your data storage needs.

## Relational Databases (RDBMS)

### Characteristics
- Structured data in tables (rows and columns)
- Schema-on-write (predefined structure)
- ACID transactions
- SQL query language
- Strong consistency guarantees

### When to Use
- Complex queries with joins
- Financial transactions
- Data integrity is critical
- Well-defined, stable schema
- Reporting and analytics

### Popular Options

| Database | Strengths | Best For |
|----------|-----------|----------|
| PostgreSQL | Extensions, JSON, full-featured | General purpose, complex apps |
| MySQL | Simplicity, wide support | Web applications, WordPress |
| SQL Server | Enterprise features, BI | Microsoft ecosystem |
| Oracle | Enterprise, high performance | Large enterprises |
| SQLite | Embedded, zero-config | Mobile, desktop apps |

### Example Schema

```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(100) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  total DECIMAL(10, 2) NOT NULL,
  status VARCHAR(20) DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT NOW()
);

-- Relational query
SELECT u.name, COUNT(o.id) as order_count, SUM(o.total) as total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.name
ORDER BY total_spent DESC;
```

## Document Databases

### Characteristics
- Flexible schema (schema-on-read)
- JSON/BSON documents
- Nested data structures
- Horizontal scaling
- Eventually consistent (configurable)

### When to Use
- Evolving schema requirements
- Hierarchical data
- Content management
- Real-time analytics
- Rapid prototyping

### Popular Options

| Database | Strengths | Best For |
|----------|-----------|----------|
| MongoDB | Flexibility, aggregation | General document storage |
| CouchDB | Sync, offline-first | Mobile sync |
| Firestore | Real-time, serverless | Firebase apps |
| RethinkDB | Real-time queries | Live dashboards |

### Example Document

```javascript
// MongoDB document
{
  _id: ObjectId("507f1f77bcf86cd799439011"),
  email: "user@example.com",
  name: "John Doe",
  profile: {
    avatar: "https://...",
    bio: "Software developer",
    social: {
      twitter: "@johndoe",
      github: "johndoe"
    }
  },
  orders: [
    {
      id: "ord-001",
      items: [
        { product: "Widget", qty: 2, price: 29.99 }
      ],
      total: 59.98,
      status: "delivered"
    }
  ],
  tags: ["premium", "early-adopter"],
  created_at: ISODate("2024-01-15T10:30:00Z")
}

// Query with aggregation
db.users.aggregate([
  { $unwind: "$orders" },
  { $group: {
      _id: "$_id",
      name: { $first: "$name" },
      total_spent: { $sum: "$orders.total" },
      order_count: { $sum: 1 }
  }},
  { $sort: { total_spent: -1 } }
]);
```

## Key-Value Stores

### Characteristics
- Simple get/set operations
- Extremely fast (O(1) access)
- In-memory or persistent
- Limited query capabilities
- Horizontal scaling

### When to Use
- Session storage
- Caching layer
- Real-time data
- Rate limiting
- Leaderboards, counters

### Popular Options

| Database | Strengths | Best For |
|----------|-----------|----------|
| Redis | Data structures, persistence | Caching, real-time |
| Memcached | Simplicity, multi-threaded | Simple caching |
| DynamoDB | Managed, scalable | AWS serverless |
| etcd | Distributed, consistent | Service discovery |

### Example Usage

```python
import redis

r = redis.Redis()

# Simple key-value
r.set("user:1001:name", "John Doe")
r.get("user:1001:name")  # b'John Doe'

# Hash (object-like)
r.hset("user:1001", mapping={
    "name": "John Doe",
    "email": "john@example.com",
    "visits": 42
})
r.hgetall("user:1001")

# Sorted set (leaderboard)
r.zadd("leaderboard", {"player1": 100, "player2": 85, "player3": 92})
r.zrevrange("leaderboard", 0, 9, withscores=True)  # Top 10

# List (queue)
r.lpush("task_queue", "task1", "task2")
r.rpop("task_queue")  # Process FIFO

# Set operations
r.sadd("user:1001:interests", "coding", "music", "travel")
r.sinter("user:1001:interests", "user:1002:interests")  # Common interests
```

## Wide-Column Stores

### Characteristics
- Column families (not tables)
- Sparse data friendly
- Designed for write-heavy loads
- Linear horizontal scaling
- Eventual consistency

### When to Use
- Time-series data
- IoT sensor data
- Write-heavy workloads
- Petabyte-scale data
- Geographic distribution

### Popular Options

| Database | Strengths | Best For |
|----------|-----------|----------|
| Cassandra | Write performance, HA | Time-series, IoT |
| HBase | Hadoop integration | Big data analytics |
| ScyllaDB | Performance (C++) | High-throughput |

### Example Schema

```cql
-- Cassandra CQL
CREATE KEYSPACE analytics WITH replication = {
  'class': 'NetworkTopologyStrategy',
  'dc1': 3, 'dc2': 3
};

CREATE TABLE analytics.events (
  event_date date,
  event_time timestamp,
  user_id uuid,
  event_type text,
  properties map<text, text>,
  PRIMARY KEY ((event_date), event_time, user_id)
) WITH CLUSTERING ORDER BY (event_time DESC);

-- Write (fast)
INSERT INTO analytics.events (event_date, event_time, user_id, event_type, properties)
VALUES ('2024-01-15', now(), uuid(), 'page_view', {'page': '/home', 'duration': '45'});

-- Query by partition key (fast)
SELECT * FROM analytics.events
WHERE event_date = '2024-01-15'
AND event_time > '2024-01-15 00:00:00';
```

## Graph Databases

### Characteristics
- Nodes and relationships as first-class citizens
- Traversal queries
- Pattern matching
- Flexible schema
- Relationship-centric

### When to Use
- Social networks
- Recommendation engines
- Fraud detection
- Knowledge graphs
- Network/dependency analysis

### Popular Options

| Database | Strengths | Best For |
|----------|-----------|----------|
| Neo4j | Mature, Cypher query | General graph |
| Neptune | Managed, AWS | AWS ecosystem |
| ArangoDB | Multi-model | Hybrid needs |
| JanusGraph | Distributed | Large-scale graphs |

### Example Graph

```cypher
// Neo4j Cypher
// Create nodes
CREATE (john:Person {name: 'John', age: 30})
CREATE (jane:Person {name: 'Jane', age: 28})
CREATE (acme:Company {name: 'Acme Corp'})
CREATE (tech:Skill {name: 'Python'})

// Create relationships
CREATE (john)-[:KNOWS {since: 2020}]->(jane)
CREATE (john)-[:WORKS_AT {role: 'Engineer'}]->(acme)
CREATE (jane)-[:WORKS_AT {role: 'Manager'}]->(acme)
CREATE (john)-[:HAS_SKILL {level: 'Expert'}]->(tech)
CREATE (jane)-[:HAS_SKILL {level: 'Intermediate'}]->(tech)

// Find friends of friends
MATCH (john:Person {name: 'John'})-[:KNOWS*2..3]-(fof:Person)
WHERE john <> fof
RETURN DISTINCT fof.name;

// Shortest path
MATCH path = shortestPath(
  (john:Person {name: 'John'})-[*]-(jane:Person {name: 'Jane'})
)
RETURN path;

// Recommendation: People with similar skills
MATCH (john:Person {name: 'John'})-[:HAS_SKILL]->(skill)<-[:HAS_SKILL]-(other:Person)
WHERE john <> other
RETURN other.name, collect(skill.name) as common_skills, count(*) as match_count
ORDER BY match_count DESC;
```

## Time-Series Databases

### Characteristics
- Optimized for time-stamped data
- High write throughput
- Automatic data retention
- Built-in aggregation functions
- Time-based partitioning

### When to Use
- Metrics and monitoring
- IoT sensor data
- Financial tick data
- Log analysis
- Real-time analytics

### Popular Options

| Database | Strengths | Best For |
|----------|-----------|----------|
| TimescaleDB | PostgreSQL extension | SQL + time-series |
| InfluxDB | Purpose-built, InfluxQL | Metrics, monitoring |
| Prometheus | Pull-based, alerting | Kubernetes metrics |
| QuestDB | Performance, SQL | High-frequency data |

### Example Usage

```sql
-- TimescaleDB (PostgreSQL extension)
CREATE TABLE metrics (
  time TIMESTAMPTZ NOT NULL,
  device_id TEXT NOT NULL,
  temperature DOUBLE PRECISION,
  humidity DOUBLE PRECISION
);

SELECT create_hypertable('metrics', 'time');

-- Insert data
INSERT INTO metrics (time, device_id, temperature, humidity)
VALUES (NOW(), 'sensor-001', 23.5, 65.2);

-- Time-bucket aggregation
SELECT
  time_bucket('1 hour', time) AS hour,
  device_id,
  AVG(temperature) as avg_temp,
  MAX(temperature) as max_temp,
  MIN(temperature) as min_temp
FROM metrics
WHERE time > NOW() - INTERVAL '24 hours'
GROUP BY hour, device_id
ORDER BY hour DESC;

-- Continuous aggregates (materialized)
CREATE MATERIALIZED VIEW hourly_metrics
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 hour', time) AS hour,
  device_id,
  AVG(temperature) as avg_temp,
  COUNT(*) as readings
FROM metrics
GROUP BY hour, device_id;
```

## Comparison Summary

| Type | Data Model | Scaling | Consistency | Query Power |
|------|------------|---------|-------------|-------------|
| Relational | Tables | Vertical | Strong | High (SQL) |
| Document | JSON docs | Horizontal | Configurable | Medium |
| Key-Value | Key→Value | Horizontal | Eventual | Low |
| Wide-Column | Column families | Horizontal | Eventual | Medium |
| Graph | Nodes/Edges | Limited | Configurable | High (traversal) |
| Time-Series | Time+metrics | Horizontal | Configurable | Medium |

## Decision Guide

```
┌──────────────────────────────────────────────────────────────┐
│                  Database Selection Guide                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. What's your data structure?                              │
│     ├─ Tables with relationships → RDBMS (PostgreSQL)        │
│     ├─ Hierarchical/nested → Document (MongoDB)              │
│     ├─ Simple key lookups → Key-Value (Redis)                │
│     ├─ Time-stamped events → Time-Series (TimescaleDB)       │
│     └─ Connected entities → Graph (Neo4j)                    │
│                                                              │
│  2. What's your scale requirement?                           │
│     ├─ Single server OK → RDBMS                              │
│     ├─ Need horizontal scale → NoSQL                         │
│     └─ Petabyte scale → Wide-Column (Cassandra)              │
│                                                              │
│  3. What's your consistency need?                            │
│     ├─ Strong consistency → RDBMS, some NoSQL configs        │
│     ├─ Eventual OK → Most NoSQL                              │
│     └─ Tunable → MongoDB, Cassandra                          │
│                                                              │
│  4. What's your query pattern?                               │
│     ├─ Complex joins → RDBMS                                 │
│     ├─ Key access → Key-Value                                │
│     ├─ Full-text search → Elasticsearch                      │
│     └─ Graph traversal → Graph DB                            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Polyglot Persistence

Modern applications often use multiple database types:

```
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
    ▼                     ▼                     ▼
┌─────────┐         ┌─────────┐         ┌─────────────┐
│PostgreSQL│        │  Redis  │         │Elasticsearch│
│ Primary  │        │  Cache  │         │   Search    │
│   Data   │        │Sessions │         │  Full-text  │
└─────────┘         └─────────┘         └─────────────┘
    │
    ▼
┌─────────────┐
│  TimescaleDB │
│   Metrics    │
└─────────────┘
```

### Example Architecture

```yaml
# Polyglot persistence example
databases:
  primary:
    type: postgresql
    purpose: Users, orders, transactions

  cache:
    type: redis
    purpose: Sessions, rate limiting, hot data

  search:
    type: elasticsearch
    purpose: Product search, logs

  analytics:
    type: clickhouse
    purpose: Event analytics, reporting

  graph:
    type: neo4j
    purpose: Recommendations, social features
```
