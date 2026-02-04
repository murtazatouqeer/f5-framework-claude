# NestJS Service Requirements Specification (SRS) Template

## 1. Overview

### 1.1 Service Information
| Field | Value |
|-------|-------|
| Service Name | {{service_name}} |
| Version | 1.0.0 |
| Owner | {{team_name}} |
| Created | {{date}} |
| Last Updated | {{date}} |

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
| POST | `/api/v1/{{resource}}` | Create new {{resource}} | JWT |
| GET | `/api/v1/{{resource}}` | List all with pagination | JWT |
| GET | `/api/v1/{{resource}}/:id` | Get by ID | JWT |
| PUT | `/api/v1/{{resource}}/:id` | Update {{resource}} | JWT |
| DELETE | `/api/v1/{{resource}}/:id` | Delete {{resource}} | JWT + Admin |

#### Request/Response Specifications

**POST /api/v1/{{resource}}**
```typescript
// Request
interface CreateRequest {
  name: string;        // Required, max 255 chars
  description?: string; // Optional, max 1000 chars
  status: 'active' | 'inactive';
}

// Response 201
interface CreateResponse {
  id: string;          // UUID
  name: string;
  description: string | null;
  status: string;
  createdAt: string;   // ISO 8601
  updatedAt: string;   // ISO 8601
}

// Error 400
interface ValidationError {
  statusCode: 400;
  message: string[];
  error: 'Bad Request';
}
```

---

## 3. Data Model

### 3.1 Entity Definitions

#### {{EntityName}}
```typescript
interface {{EntityName}} {
  id: string;           // UUID, Primary Key
  name: string;         // VARCHAR(255), NOT NULL, UNIQUE
  description: string;  // TEXT, NULL
  status: Status;       // ENUM, NOT NULL, DEFAULT 'active'
  createdAt: Date;      // TIMESTAMP, NOT NULL
  updatedAt: Date;      // TIMESTAMP, NOT NULL
  deletedAt: Date;      // TIMESTAMP, NULL (soft delete)
}

enum Status {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  PENDING = 'pending'
}
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

CREATE INDEX idx_{{table_name}}_status ON {{table_name}}(status);
CREATE INDEX idx_{{table_name}}_created_at ON {{table_name}}(created_at);
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
| API Response Time (p95) | < 200ms | DataDog APM |
| Throughput | 1000 req/s | Load test |
| Database Query Time | < 50ms | Query logs |

### 4.2 Availability

| Metric | Target |
|--------|--------|
| Uptime | 99.9% |
| RTO | 15 minutes |
| RPO | 0 (no data loss) |

### 4.3 Security

- [ ] All endpoints require authentication (JWT)
- [ ] Admin endpoints require admin role
- [ ] Input validation on all requests
- [ ] SQL injection prevention (TypeORM)
- [ ] Rate limiting: 100 req/min per user
- [ ] Audit logging for mutations

### 4.4 Scalability

- Horizontal scaling via Kubernetes
- Stateless service design
- Connection pooling for database
- Redis caching for read-heavy endpoints

---

## 5. Integration Points

### 5.1 Internal Services

| Service | Protocol | Purpose |
|---------|----------|---------|
| Auth Service | REST | JWT validation |
| User Service | REST | User lookup |
| Notification Service | Events | Send notifications |

### 5.2 External Services

| Service | Protocol | Purpose |
|---------|----------|---------|
| {{External API}} | REST | {{Purpose}} |

### 5.3 Events

**Published Events**
| Event | Payload | Trigger |
|-------|---------|---------|
| `{{resource}}.created` | `{ id, data }` | POST success |
| `{{resource}}.updated` | `{ id, changes }` | PUT success |
| `{{resource}}.deleted` | `{ id }` | DELETE success |

**Consumed Events**
| Event | Source | Action |
|-------|--------|--------|
| `user.deleted` | User Service | Cleanup user data |

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
│  │  Controller  │──│   Service    │──│  Repository  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                 │                  │              │
│         ▼                 ▼                  ▼              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    DTOs      │  │   Events     │  │   Entities   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
         │                  │                   │
         ▼                  ▼                   ▼
    ┌─────────┐      ┌───────────┐       ┌───────────┐
    │  Redis  │      │  RabbitMQ │       │ PostgreSQL│
    └─────────┘      └───────────┘       └───────────┘
```

### 6.2 Module Structure

```
src/modules/{{module}}/
├── {{module}}.module.ts
├── {{module}}.controller.ts
├── {{module}}.service.ts
├── dto/
│   ├── create-{{entity}}.dto.ts
│   ├── update-{{entity}}.dto.ts
│   └── {{entity}}-response.dto.ts
├── entities/
│   └── {{entity}}.entity.ts
├── events/
│   └── {{entity}}.events.ts
└── __tests__/
    ├── {{module}}.controller.spec.ts
    └── {{module}}.service.spec.ts
```

### 6.3 Dependencies

```json
{
  "dependencies": {
    "@nestjs/common": "^10.0.0",
    "@nestjs/typeorm": "^10.0.0",
    "typeorm": "^0.3.0",
    "pg": "^8.0.0",
    "class-validator": "^0.14.0",
    "class-transformer": "^0.5.0"
  }
}
```

---

## 7. Testing Requirements

### 7.1 Unit Tests
- [ ] Service methods (80% coverage)
- [ ] DTOs validation
- [ ] Business logic

### 7.2 Integration Tests
- [ ] Controller endpoints
- [ ] Database operations
- [ ] Event publishing

### 7.3 E2E Tests
- [ ] Happy path flows
- [ ] Error scenarios
- [ ] Authentication/Authorization

---

## 8. Deployment

### 8.1 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection | Yes |
| `REDIS_URL` | Redis connection | Yes |
| `JWT_SECRET` | JWT signing key | Yes |
| `LOG_LEVEL` | Logging level | No |

### 8.2 Health Checks

```typescript
// GET /health
{
  "status": "ok",
  "info": {
    "database": { "status": "up" },
    "redis": { "status": "up" }
  }
}
```

---

## 9. Monitoring & Observability

### 9.1 Metrics
- Request count by endpoint
- Response time histogram
- Error rate by type
- Database connection pool usage

### 9.2 Logging
- Request/Response logging (sanitized)
- Error stack traces
- Business event logging

### 9.3 Alerts
| Alert | Condition | Severity |
|-------|-----------|----------|
| High Error Rate | > 1% 5xx | Critical |
| Slow Response | p95 > 500ms | Warning |
| DB Connection Pool | > 80% | Warning |

---

## 10. Appendix

### 10.1 Glossary
| Term | Definition |
|------|------------|
| {{Term}} | {{Definition}} |

### 10.2 References
- [NestJS Documentation](https://docs.nestjs.com)
- [TypeORM Documentation](https://typeorm.io)

### 10.3 Change Log
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | {{date}} | {{author}} | Initial version |
