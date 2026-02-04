---
name: database
description: Database design, SQL, NoSQL, and data management
category: skill
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: true
context: inject
version: 1.0.0
---

# Database Skills

## Overview

Comprehensive database knowledge for designing, querying, optimizing,
and managing data storage systems effectively across relational and
non-relational paradigms.

## Database Landscape

```
┌─────────────────────────────────────────────────────────┐
│                    Relational (SQL)                      │
│  PostgreSQL │ MySQL │ SQL Server │ Oracle │ SQLite      │
├─────────────────────────────────────────────────────────┤
│                    Document (NoSQL)                      │
│  MongoDB │ CouchDB │ Firestore │ RethinkDB              │
├─────────────────────────────────────────────────────────┤
│                    Key-Value                             │
│  Redis │ DynamoDB │ Memcached │ etcd │ Riak            │
├─────────────────────────────────────────────────────────┤
│                    Wide-Column                           │
│  Cassandra │ HBase │ ScyllaDB │ BigTable               │
├─────────────────────────────────────────────────────────┤
│                    Graph                                 │
│  Neo4j │ Amazon Neptune │ ArangoDB │ JanusGraph        │
├─────────────────────────────────────────────────────────┤
│                    Time-Series                           │
│  InfluxDB │ TimescaleDB │ Prometheus │ QuestDB         │
├─────────────────────────────────────────────────────────┤
│                    Search                                │
│  Elasticsearch │ OpenSearch │ Meilisearch │ Typesense  │
└─────────────────────────────────────────────────────────┘
```

## Skill Categories

### Fundamentals
Core database concepts every developer should know:
- Database types and their trade-offs
- ACID properties and transactions
- CAP theorem implications
- Normalization forms (1NF through BCNF)

### SQL
Structured Query Language mastery:
- SQL fundamentals (CRUD operations)
- Advanced query techniques
- Joins explained with diagrams
- Window functions for analytics
- CTEs and subqueries

### PostgreSQL
Deep dive into the world's most advanced open-source database:
- PostgreSQL-specific features
- Index types (B-tree, GIN, GiST, BRIN)
- JSON/JSONB operations
- Full-text search capabilities

### NoSQL
Non-relational database patterns:
- MongoDB document modeling
- Redis data structures and patterns
- DynamoDB single-table design
- When to use NoSQL vs SQL

### Design
Data modeling and schema design:
- Schema design principles
- Entity-relationship modeling
- Relationship types and implementation
- Strategic denormalization

### Migrations
Safe database evolution:
- Migration strategies
- Zero-downtime migrations
- Data migration patterns

### Optimization
Performance tuning techniques:
- Query optimization
- Indexing strategies
- EXPLAIN ANALYZE interpretation
- Connection pooling

### Operations
Database administration:
- Backup and recovery
- Replication strategies
- Sharding patterns
- Monitoring and alerting

## Decision Matrix: Choosing the Right Database

| Use Case | Recommended | Alternative | Rationale |
|----------|-------------|-------------|-----------|
| General purpose | PostgreSQL | MySQL | Versatile, ACID, JSON support |
| Simple web app | MySQL | SQLite | Wide hosting support |
| High-speed caching | Redis | Memcached | Data structures, persistence |
| Flexible documents | MongoDB | CouchDB | Schema-less, horizontal scale |
| Analytics/OLAP | ClickHouse | BigQuery | Column-oriented, fast aggregations |
| Complex relationships | Neo4j | ArangoDB | Native graph queries |
| Time-series data | TimescaleDB | InfluxDB | Time-based partitioning |
| Full-text search | Elasticsearch | Meilisearch | Inverted index, relevance |
| Global distribution | CockroachDB | Spanner | Geo-partitioning |
| Embedded/Edge | SQLite | DuckDB | Zero configuration |

## Database Selection Flowchart

```
Start: What's your primary need?
│
├─> Structured data with relationships?
│   ├─> Complex queries needed? → PostgreSQL
│   ├─> Simple CRUD, wide hosting? → MySQL
│   └─> Embedded/serverless? → SQLite
│
├─> Flexible schema/documents?
│   ├─> Horizontal scaling? → MongoDB
│   └─> Real-time sync? → Firestore
│
├─> High-speed caching?
│   ├─> Data structures needed? → Redis
│   └─> Simple key-value? → Memcached
│
├─> Analytics/reporting?
│   ├─> Real-time analytics? → ClickHouse
│   └─> Time-series data? → TimescaleDB
│
├─> Graph relationships?
│   └─> → Neo4j or Amazon Neptune
│
└─> Full-text search?
    └─> → Elasticsearch or Meilisearch
```

## Quick Reference

### ACID Properties
- **A**tomicity: All or nothing transactions
- **C**onsistency: Valid state transitions only
- **I**solation: Concurrent transaction separation
- **D**urability: Committed data persists

### CAP Theorem
Pick two of three (in partition scenario):
- **C**onsistency: Every read gets latest write
- **A**vailability: Every request gets response
- **P**artition tolerance: System works despite network splits

### Normal Forms Quick Guide
- **1NF**: Atomic values, no repeating groups
- **2NF**: 1NF + no partial dependencies
- **3NF**: 2NF + no transitive dependencies
- **BCNF**: 3NF + every determinant is a candidate key

## Common Patterns

### Read-Heavy Workloads
```
┌─────────────┐     ┌─────────────┐
│   Primary   │────▶│   Replica   │◀── Reads
│  (Writes)   │     │   (Reads)   │
└─────────────┘     └─────────────┘
                    ┌─────────────┐
               ────▶│   Replica   │◀── Reads
                    │   (Reads)   │
                    └─────────────┘
```

### Caching Strategy
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    App      │────▶│   Cache     │────▶│  Database   │
│             │     │   (Redis)   │     │   (PGSQL)   │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │
       └───────────────────┘
         Cache miss: query DB, populate cache
```

### Event Sourcing
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Events    │────▶│   Event     │────▶│  Projected  │
│   (append)  │     │   Store     │     │   Views     │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Files in This Skill

```
database/
├── _index.md                    # This file
├── fundamentals/
│   ├── database-types.md        # Database paradigms comparison
│   ├── acid-properties.md       # Transaction guarantees
│   ├── cap-theorem.md           # Distributed system trade-offs
│   └── normalization.md         # Data normalization forms
├── sql/
│   ├── sql-fundamentals.md      # Basic SQL operations
│   ├── advanced-queries.md      # Complex query patterns
│   ├── joins-explained.md       # Join types with diagrams
│   ├── window-functions.md      # Analytics functions
│   └── cte-subqueries.md        # CTEs and subqueries
├── postgresql/
│   ├── postgres-features.md     # PostgreSQL capabilities
│   ├── indexes.md               # Index types and usage
│   ├── json-operations.md       # JSON/JSONB handling
│   └── full-text-search.md      # FTS configuration
├── nosql/
│   ├── mongodb-basics.md        # MongoDB fundamentals
│   ├── redis-patterns.md        # Redis data patterns
│   ├── dynamodb-modeling.md     # DynamoDB design
│   └── when-to-use.md           # NoSQL vs SQL decision
├── design/
│   ├── schema-design.md         # Schema principles
│   ├── data-modeling.md         # ER modeling
│   ├── relationships.md         # Relationship types
│   └── denormalization.md       # Strategic denorm
├── migrations/
│   ├── migration-strategies.md  # Migration approaches
│   ├── zero-downtime.md         # Online migrations
│   └── data-migration.md        # Data movement
├── optimization/
│   ├── query-optimization.md    # Query tuning
│   ├── indexing-strategies.md   # Index design
│   ├── explain-analyze.md       # Query plans
│   └── connection-pooling.md    # Pool management
└── operations/
    ├── backup-recovery.md       # Backup strategies
    ├── replication.md           # Replication setup
    ├── sharding.md              # Horizontal scaling
    └── monitoring.md            # DB observability
```

## Related Skills

- **Backend Development**: Database integration patterns
- **API Design**: Data access layer design
- **Security**: Database security, encryption
- **DevOps**: Database deployment, automation
