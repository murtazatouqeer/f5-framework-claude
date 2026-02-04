# Go Service Requirements Specification (SRS) Template

## 1. Overview

### 1.1 Service Information
| Field | Value |
|-------|-------|
| Service Name | {{service_name}} |
| Version | 1.0.0 |
| Owner | {{team_name}} |
| Created | {{date}} |
| Last Updated | {{date}} |
| Language | Go 1.21+ |
| Framework | Gin / Chi / Echo / Fiber |

### 1.2 Purpose
{{Brief description of what this service does and why it exists}}

### 1.3 Scope
- **In Scope**: {{list of features included}}
- **Out of Scope**: {{list of features NOT included}}

---

## 2. Functional Requirements

### 2.1 Core Features

#### FR-001: {{Feature Name}}
| Attribute | Value |
|-----------|-------|
| Priority | High/Medium/Low |
| Status | Draft/Approved/Implemented |

**Description**: {{What the feature does}}

**Acceptance Criteria**:
- [ ] {{Criterion 1}}
- [ ] {{Criterion 2}}
- [ ] {{Criterion 3}}

**Business Rules**:
- BR-001: {{Rule description}}
- BR-002: {{Rule description}}

---

### 2.2 API Endpoints

#### {{Resource}} Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/{{resource}}s` | Create new {{resource}} | JWT |
| GET | `/api/v1/{{resource}}s` | List all with pagination | JWT |
| GET | `/api/v1/{{resource}}s/:id` | Get by ID | JWT |
| PUT | `/api/v1/{{resource}}s/:id` | Update {{resource}} | JWT |
| DELETE | `/api/v1/{{resource}}s/:id` | Delete {{resource}} | JWT + Admin |

#### Request/Response Specifications

**POST /api/v1/{{resource}}s**
```go
// Request
type Create{{Resource}}Request struct {
    Name        string `json:"name" binding:"required,max=255"`
    Description string `json:"description,omitempty" binding:"max=1000"`
    Status      string `json:"status" binding:"required,oneof=active inactive"`
}

// Response 201
type {{Resource}}Response struct {
    ID          string    `json:"id"`
    Name        string    `json:"name"`
    Description string    `json:"description,omitempty"`
    Status      string    `json:"status"`
    CreatedAt   time.Time `json:"created_at"`
    UpdatedAt   time.Time `json:"updated_at"`
}

// Error 400
type ValidationError struct {
    Code    string   `json:"code"`
    Message string   `json:"message"`
    Details []string `json:"details,omitempty"`
}
```

**GET /api/v1/{{resource}}s**
```go
// Query Parameters
type ListQuery struct {
    Page    int    `form:"page" binding:"min=1"`
    Limit   int    `form:"limit" binding:"min=1,max=100"`
    Search  string `form:"search"`
    Status  string `form:"status" binding:"omitempty,oneof=active inactive"`
    SortBy  string `form:"sort_by" binding:"omitempty,oneof=created_at updated_at name"`
    Order   string `form:"order" binding:"omitempty,oneof=asc desc"`
}

// Response 200
type PaginatedResponse struct {
    Data  []{{Resource}}Response `json:"data"`
    Meta  Meta                   `json:"meta"`
}

type Meta struct {
    Total      int64 `json:"total"`
    Page       int   `json:"page"`
    Limit      int   `json:"limit"`
    TotalPages int   `json:"total_pages"`
}
```

---

## 3. Data Model

### 3.1 Entity Definitions

#### {{EntityName}}
```go
type {{EntityName}} struct {
    ID          string     `json:"id" db:"id"`              // UUID, Primary Key
    Name        string     `json:"name" db:"name"`          // VARCHAR(255), NOT NULL, UNIQUE
    Description string     `json:"description" db:"description"` // TEXT, NULL
    Status      Status     `json:"status" db:"status"`      // VARCHAR(20), NOT NULL, DEFAULT 'active'
    CreatedAt   time.Time  `json:"created_at" db:"created_at"`
    UpdatedAt   time.Time  `json:"updated_at" db:"updated_at"`
    DeletedAt   *time.Time `json:"deleted_at,omitempty" db:"deleted_at"` // Soft delete
}

type Status string

const (
    StatusActive   Status = "active"
    StatusInactive Status = "inactive"
    StatusPending  Status = "pending"
)
```

### 3.2 Database Schema

```sql
CREATE TABLE {{table_name}} (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP,

    CONSTRAINT chk_status CHECK (status IN ('active', 'inactive', 'pending'))
);

CREATE INDEX idx_{{table_name}}_status ON {{table_name}}(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_{{table_name}}_created_at ON {{table_name}}(created_at);
CREATE INDEX idx_{{table_name}}_name_search ON {{table_name}} USING gin(name gin_trgm_ops);
```

### 3.3 Relationships

```
{{EntityA}} 1:N {{EntityB}}
{{EntityA}}.id = {{EntityB}}.{{entity_a}}_id
```

---

## 4. Non-Functional Requirements

### 4.1 Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time (p95) | < 100ms | Prometheus metrics |
| Throughput | 5000 req/s | Load test |
| Database Query Time (p95) | < 20ms | Query logs |
| Memory Usage | < 256MB | Container limits |
| CPU Usage | < 500m | Container limits |

### 4.2 Availability

| Metric | Target |
|--------|--------|
| Uptime | 99.9% |
| RTO | 5 minutes |
| RPO | 0 (no data loss) |

### 4.3 Security

- [ ] All endpoints require authentication (JWT)
- [ ] Admin endpoints require admin role
- [ ] Input validation on all requests
- [ ] SQL injection prevention (parameterized queries)
- [ ] Rate limiting: 1000 req/min per user
- [ ] Audit logging for mutations
- [ ] TLS 1.3 required
- [ ] CORS configuration

### 4.4 Scalability

- Horizontal scaling via Kubernetes
- Stateless service design
- Connection pooling for database (PGX pool)
- Redis caching for read-heavy endpoints
- Graceful shutdown handling

---

## 5. Integration Points

### 5.1 Internal Services

| Service | Protocol | Purpose |
|---------|----------|---------|
| Auth Service | gRPC | JWT validation |
| User Service | gRPC | User lookup |
| Notification Service | Kafka | Send notifications |

### 5.2 External Services

| Service | Protocol | Purpose |
|---------|----------|---------|
| {{External API}} | REST | {{Purpose}} |

### 5.3 Events

**Published Events**
| Event | Topic | Payload |
|-------|-------|---------|
| `{{resource}}.created` | `{{resource}}.events` | `{ id, name, timestamp }` |
| `{{resource}}.updated` | `{{resource}}.events` | `{ id, changes, timestamp }` |
| `{{resource}}.deleted` | `{{resource}}.events` | `{ id, timestamp }` |

**Consumed Events**
| Event | Topic | Action |
|-------|-------|--------|
| `user.deleted` | `user.events` | Cleanup user-owned data |

---

## 6. Technical Design

### 6.1 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    {{Service Name}}                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Handler    │──│   Service    │──│  Repository  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                 │                  │              │
│         ▼                 ▼                  ▼              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Middleware  │  │    Events    │  │   Entities   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
         │                  │                   │
         ▼                  ▼                   ▼
    ┌─────────┐      ┌───────────┐       ┌───────────┐
    │  Redis  │      │   Kafka   │       │ PostgreSQL│
    └─────────┘      └───────────┘       └───────────┘
```

### 6.2 Project Structure

```
{{service_name}}/
├── cmd/
│   └── api/
│       └── main.go               # Application entrypoint
├── internal/
│   ├── config/
│   │   └── config.go             # Configuration management
│   ├── domain/                   # Domain models and interfaces
│   │   ├── {{resource}}.go
│   │   └── errors.go
│   ├── handler/                  # HTTP handlers
│   │   ├── handler.go
│   │   ├── {{resource}}.go
│   │   └── middleware.go
│   ├── service/                  # Business logic
│   │   └── {{resource}}.go
│   ├── repository/               # Data access
│   │   ├── postgres/
│   │   │   └── {{resource}}.go
│   │   └── redis/
│   │       └── cache.go
│   └── pkg/                      # Internal shared packages
│       ├── logger/
│       ├── validator/
│       └── response/
├── pkg/                          # Public shared packages
├── migrations/
├── docs/
├── Makefile
├── Dockerfile
├── docker-compose.yml
└── go.mod
```

### 6.3 Dependencies

```go
module {{module}}

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/jmoiron/sqlx v1.3.5
    github.com/lib/pq v1.10.9
    github.com/redis/go-redis/v9 v9.4.0
    github.com/google/uuid v1.6.0
    github.com/go-playground/validator/v10 v10.17.0
    go.uber.org/zap v1.26.0
    github.com/golang-jwt/jwt/v5 v5.2.0
    github.com/spf13/viper v1.18.2
    github.com/stretchr/testify v1.8.4
)
```

---

## 7. Testing Requirements

### 7.1 Unit Tests
- [ ] Service methods (80% coverage)
- [ ] Input validation
- [ ] Business logic edge cases
- [ ] Error handling

### 7.2 Integration Tests
- [ ] Handler endpoints
- [ ] Database operations
- [ ] Cache operations
- [ ] Event publishing

### 7.3 E2E Tests
- [ ] Happy path flows
- [ ] Error scenarios
- [ ] Authentication/Authorization
- [ ] Rate limiting

### 7.4 Load Tests
- [ ] Sustained load (1000 req/s for 5 min)
- [ ] Spike test (10x normal load)
- [ ] Soak test (normal load for 1 hour)

---

## 8. Deployment

### 8.1 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection | Yes | - |
| `REDIS_URL` | Redis connection | Yes | - |
| `JWT_SECRET` | JWT signing key | Yes | - |
| `LOG_LEVEL` | Logging level | No | `info` |
| `PORT` | Server port | No | `8080` |
| `ENV` | Environment | No | `development` |

### 8.2 Health Checks

```go
// GET /health
type HealthResponse struct {
    Status  string            `json:"status"`
    Version string            `json:"version"`
    Checks  map[string]string `json:"checks"`
}

// GET /ready
type ReadyResponse struct {
    Status string `json:"status"`
}
```

### 8.3 Kubernetes Resources

```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "500m"

livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

## 9. Monitoring & Observability

### 9.1 Metrics (Prometheus)

```go
// Request metrics
http_requests_total{method, path, status}
http_request_duration_seconds{method, path}

// Business metrics
{{resource}}_created_total
{{resource}}_updated_total
{{resource}}_deleted_total

// Database metrics
db_queries_total{operation}
db_query_duration_seconds{operation}
db_connections_active
db_connections_idle

// Cache metrics
cache_hits_total
cache_misses_total
cache_latency_seconds
```

### 9.2 Logging (Structured)

```go
// Request log format
{
    "level": "info",
    "ts": "2024-01-15T10:30:00Z",
    "caller": "handler/{{resource}}.go:45",
    "msg": "request processed",
    "request_id": "uuid",
    "method": "POST",
    "path": "/api/v1/{{resource}}s",
    "status": 201,
    "latency_ms": 15,
    "user_id": "uuid"
}
```

### 9.3 Tracing (OpenTelemetry)

```go
// Span attributes
service.name: "{{service_name}}"
service.version: "1.0.0"
http.method: "POST"
http.url: "/api/v1/{{resource}}s"
http.status_code: 201
db.system: "postgresql"
db.operation: "INSERT"
```

### 9.4 Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| High Error Rate | > 1% 5xx in 5m | Critical |
| Slow Response | p95 > 200ms in 5m | Warning |
| DB Connection Pool | > 80% in 5m | Warning |
| Memory Usage | > 200MB | Warning |

---

## 10. Appendix

### 10.1 Glossary
| Term | Definition |
|------|------------|
| {{Term}} | {{Definition}} |

### 10.2 References
- [Go Project Layout](https://github.com/golang-standards/project-layout)
- [Effective Go](https://go.dev/doc/effective_go)
- [Uber Go Style Guide](https://github.com/uber-go/guide/blob/master/style.md)

### 10.3 Change Log
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | {{date}} | {{author}} | Initial version |
