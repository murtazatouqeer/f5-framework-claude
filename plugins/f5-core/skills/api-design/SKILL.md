---
name: api-design
description: API design principles for REST, GraphQL, and gRPC
category: skill
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: true
context: inject
---

# API Design Skills

## Overview

API design knowledge for building clean, consistent, and developer-friendly APIs.
This domain covers REST, GraphQL, gRPC, documentation standards, and best practices.

## API Types Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        API Types Comparison                                  │
├──────────────┬──────────────┬──────────────┬──────────────┬─────────────────┤
│ Aspect       │ REST         │ GraphQL      │ gRPC         │ Best For        │
├──────────────┼──────────────┼──────────────┼──────────────┼─────────────────┤
│ Protocol     │ HTTP/1.1     │ HTTP/1.1     │ HTTP/2       │                 │
│ Format       │ JSON/XML     │ JSON         │ Protobuf     │                 │
│ Schema       │ Optional     │ Required     │ Required     │                 │
│              │ (OpenAPI)    │ (SDL)        │ (.proto)     │                 │
│ Caching      │ HTTP native  │ Complex      │ Manual       │                 │
│ Real-time    │ Polling/SSE  │ Subscriptions│ Streaming    │                 │
│ Learning     │ Easy         │ Medium       │ Hard         │                 │
├──────────────┼──────────────┼──────────────┼──────────────┼─────────────────┤
│ Use Cases    │ Public APIs  │ Flexible     │ Microservices│                 │
│              │ CRUD apps    │ Mobile apps  │ Low latency  │                 │
│              │ Web services │ Aggregation  │ High perf    │                 │
└──────────────┴──────────────┴──────────────┴──────────────┴─────────────────┘
```

## Categories

### REST
- REST principles and HATEOAS
- Resource naming conventions
- HTTP methods semantics
- Status codes usage
- Pagination strategies
- Filtering and sorting
- API versioning

### GraphQL
- Schema design
- Queries and mutations
- Resolvers
- Subscriptions
- N+1 problem solutions

### gRPC
- Protocol Buffers
- Service definitions
- Streaming patterns
- Error handling

### Documentation
- OpenAPI/Swagger
- API documentation best practices
- Examples and SDKs

### Patterns
- Request/Response design
- Error handling
- Authentication patterns
- Rate limiting
- Idempotency

### Best Practices
- API design guidelines
- Backwards compatibility
- API evolution strategies

## REST Maturity Model (Richardson)

```
┌─────────────────────────────────────────────────────────────────┐
│                   REST Maturity Model                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Level 3: Hypermedia Controls (HATEOAS)                         │
│           ├── Self-documenting APIs                              │
│           ├── Discoverability via links                          │
│           └── Decoupled client-server evolution                  │
│                        ↑                                         │
│  Level 2: HTTP Verbs + Status Codes                             │
│           ├── GET, POST, PUT, PATCH, DELETE                     │
│           ├── Proper status codes (200, 201, 404, etc.)         │
│           └── Safe and idempotent methods                        │
│                        ↑                                         │
│  Level 1: Resources                                              │
│           ├── Multiple URIs for different resources              │
│           ├── /users, /orders, /products                        │
│           └── Still using single HTTP verb                       │
│                        ↑                                         │
│  Level 0: The Swamp of POX                                      │
│           ├── Single URI for all operations                      │
│           ├── POST /api with action in body                     │
│           └── RPC-style over HTTP                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## API Design Decision Tree

```
┌─────────────────────────────────────────────────────────────────┐
│                 Which API Style to Choose?                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Start Here                                                      │
│      │                                                           │
│      ▼                                                           │
│  Public API for third parties?                                  │
│      │                                                           │
│      ├── Yes → REST (with OpenAPI)                              │
│      │         • Easy to understand                              │
│      │         • Good tooling                                    │
│      │         • HTTP caching                                    │
│      │                                                           │
│      └── No → Internal/Microservices?                           │
│               │                                                  │
│               ├── Yes → Need real-time?                         │
│               │         │                                        │
│               │         ├── Yes → gRPC streaming                │
│               │         │                                        │
│               │         └── No → High performance?              │
│               │                  │                               │
│               │                  ├── Yes → gRPC                 │
│               │                  └── No → REST                  │
│               │                                                  │
│               └── No → Mobile/Web frontend?                     │
│                        │                                         │
│                        ├── Multiple clients? → GraphQL          │
│                        ├── Complex queries? → GraphQL           │
│                        └── Simple CRUD? → REST                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Reference

### HTTP Methods

| Method | Idempotent | Safe | Cacheable | Request Body |
|--------|------------|------|-----------|--------------|
| GET    | Yes        | Yes  | Yes       | No           |
| POST   | No         | No   | No        | Yes          |
| PUT    | Yes        | No   | No        | Yes          |
| PATCH  | No*        | No   | No        | Yes          |
| DELETE | Yes        | No   | No        | Optional     |

### Common Status Codes

| Code | Name | Usage |
|------|------|-------|
| 200  | OK | Successful GET, PUT, PATCH |
| 201  | Created | Successful POST (resource created) |
| 204  | No Content | Successful DELETE |
| 400  | Bad Request | Invalid syntax, validation error |
| 401  | Unauthorized | Missing/invalid authentication |
| 403  | Forbidden | Valid auth, no permission |
| 404  | Not Found | Resource doesn't exist |
| 409  | Conflict | Resource conflict |
| 422  | Unprocessable | Semantic errors |
| 429  | Too Many Requests | Rate limited |
| 500  | Internal Error | Server error |

## Skills Index

### REST

| Skill | Description |
|-------|-------------|
| [rest-principles](rest/rest-principles.md) | Core REST constraints and design |
| [resource-naming](rest/resource-naming.md) | URI design and resource naming |
| [http-methods](rest/http-methods.md) | HTTP verb semantics |
| [status-codes](rest/status-codes.md) | HTTP status code usage |
| [pagination](rest/pagination.md) | Pagination strategies |
| [filtering-sorting](rest/filtering-sorting.md) | Query parameters design |
| [versioning](rest/versioning.md) | API versioning approaches |

### GraphQL

| Skill | Description |
|-------|-------------|
| [graphql-basics](graphql/graphql-basics.md) | GraphQL fundamentals |
| [schema-design](graphql/schema-design.md) | Type system and schema |
| [resolvers](graphql/resolvers.md) | Resolver patterns |
| [mutations](graphql/mutations.md) | Write operations |
| [subscriptions](graphql/subscriptions.md) | Real-time updates |

### gRPC

| Skill | Description |
|-------|-------------|
| [grpc-basics](grpc/grpc-basics.md) | gRPC fundamentals |
| [protobuf](grpc/protobuf.md) | Protocol Buffers |
| [streaming](grpc/streaming.md) | Streaming patterns |

### Documentation

| Skill | Description |
|-------|-------------|
| [openapi-swagger](documentation/openapi-swagger.md) | OpenAPI specification |
| [api-documentation](documentation/api-documentation.md) | Documentation best practices |
| [examples](documentation/examples.md) | Code examples and SDKs |

### Patterns

| Skill | Description |
|-------|-------------|
| [request-response](patterns/request-response.md) | Request/response design |
| [error-handling](patterns/error-handling.md) | Error handling patterns |
| [authentication](patterns/authentication.md) | Auth patterns |
| [rate-limiting](patterns/rate-limiting.md) | Rate limiting strategies |
| [idempotency](patterns/idempotency.md) | Idempotent operations |

### Best Practices

| Skill | Description |
|-------|-------------|
| [api-guidelines](best-practices/api-guidelines.md) | General API guidelines |
| [backwards-compatibility](best-practices/backwards-compatibility.md) | Maintaining compatibility |
| [api-evolution](best-practices/api-evolution.md) | Evolving APIs over time |
