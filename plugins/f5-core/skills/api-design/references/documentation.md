# API Documentation Reference

## OpenAPI 3.x Specification

### Basic Structure

```yaml
openapi: 3.1.0
info:
  title: Example API
  version: 1.0.0
  description: |
    Example REST API with comprehensive documentation.

    ## Authentication
    All endpoints require Bearer token authentication.
  contact:
    name: API Support
    email: api@example.com
    url: https://support.example.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://api.example.com/v1
    description: Production
  - url: https://staging-api.example.com/v1
    description: Staging
  - url: http://localhost:3000/v1
    description: Local development

tags:
  - name: users
    description: User management operations
  - name: orders
    description: Order processing

paths:
  # Endpoints defined here

components:
  # Reusable schemas, parameters, responses
```

### Path Definitions

```yaml
paths:
  /users:
    get:
      summary: List users
      description: Retrieve paginated list of users
      operationId: listUsers
      tags:
        - users
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/LimitParam'
        - name: status
          in: query
          schema:
            type: string
            enum: [active, inactive, suspended]
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserListResponse'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/RateLimited'

    post:
      summary: Create user
      operationId: createUser
      tags:
        - users
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUserRequest'
            examples:
              basic:
                summary: Basic user
                value:
                  name: John Doe
                  email: john@example.com
              admin:
                summary: Admin user
                value:
                  name: Admin User
                  email: admin@example.com
                  role: admin
      responses:
        '201':
          description: User created
          headers:
            Location:
              schema:
                type: string
              description: URL of created resource
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '400':
          $ref: '#/components/responses/BadRequest'
        '422':
          $ref: '#/components/responses/ValidationError'

  /users/{userId}:
    get:
      summary: Get user by ID
      operationId: getUser
      tags:
        - users
      parameters:
        - $ref: '#/components/parameters/UserIdParam'
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          $ref: '#/components/responses/NotFound'

    patch:
      summary: Update user
      operationId: updateUser
      tags:
        - users
      parameters:
        - $ref: '#/components/parameters/UserIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateUserRequest'
      responses:
        '200':
          description: User updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'

    delete:
      summary: Delete user
      operationId: deleteUser
      tags:
        - users
      parameters:
        - $ref: '#/components/parameters/UserIdParam'
      responses:
        '204':
          description: User deleted
```

### Component Schemas

```yaml
components:
  schemas:
    # Entity Schemas
    User:
      type: object
      required:
        - id
        - name
        - email
        - status
        - created_at
      properties:
        id:
          type: string
          format: ulid
          example: 01ARZ3NDEKTSV4RRFFQ69G5FAV
          readOnly: true
        name:
          type: string
          minLength: 1
          maxLength: 100
          example: John Doe
        email:
          type: string
          format: email
          example: john@example.com
        status:
          $ref: '#/components/schemas/UserStatus'
        role:
          $ref: '#/components/schemas/UserRole'
        created_at:
          type: string
          format: date-time
          readOnly: true
        updated_at:
          type: string
          format: date-time
          readOnly: true

    UserStatus:
      type: string
      enum: [active, inactive, suspended]
      default: active

    UserRole:
      type: string
      enum: [user, admin, moderator]
      default: user

    # Request Schemas
    CreateUserRequest:
      type: object
      required:
        - name
        - email
      properties:
        name:
          type: string
          minLength: 1
          maxLength: 100
        email:
          type: string
          format: email
        password:
          type: string
          format: password
          minLength: 8
          writeOnly: true
        role:
          $ref: '#/components/schemas/UserRole'

    UpdateUserRequest:
      type: object
      minProperties: 1
      properties:
        name:
          type: string
          minLength: 1
          maxLength: 100
        email:
          type: string
          format: email
        status:
          $ref: '#/components/schemas/UserStatus'

    # Response Schemas
    UserListResponse:
      type: object
      required:
        - data
        - meta
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/User'
        meta:
          $ref: '#/components/schemas/PaginationMeta'
        links:
          $ref: '#/components/schemas/PaginationLinks'

    PaginationMeta:
      type: object
      properties:
        total:
          type: integer
          example: 100
        page:
          type: integer
          example: 1
        limit:
          type: integer
          example: 20
        total_pages:
          type: integer
          example: 5

    PaginationLinks:
      type: object
      properties:
        self:
          type: string
          format: uri
        first:
          type: string
          format: uri
        prev:
          type: string
          format: uri
          nullable: true
        next:
          type: string
          format: uri
          nullable: true
        last:
          type: string
          format: uri

    # Error Schemas
    Error:
      type: object
      required:
        - type
        - title
        - status
      properties:
        type:
          type: string
          format: uri
          example: https://api.example.com/errors/validation
        title:
          type: string
          example: Validation Error
        status:
          type: integer
          example: 422
        detail:
          type: string
          example: One or more fields failed validation
        instance:
          type: string
          format: uri-reference
        errors:
          type: array
          items:
            $ref: '#/components/schemas/FieldError'

    FieldError:
      type: object
      required:
        - field
        - code
        - message
      properties:
        field:
          type: string
          example: email
        code:
          type: string
          example: INVALID_FORMAT
        message:
          type: string
          example: Must be a valid email address
```

### Parameters and Responses

```yaml
components:
  parameters:
    UserIdParam:
      name: userId
      in: path
      required: true
      schema:
        type: string
        format: ulid
      description: Unique user identifier

    PageParam:
      name: page
      in: query
      schema:
        type: integer
        minimum: 1
        default: 1
      description: Page number

    LimitParam:
      name: limit
      in: query
      schema:
        type: integer
        minimum: 1
        maximum: 100
        default: 20
      description: Items per page

    SortParam:
      name: sort
      in: query
      schema:
        type: string
        pattern: '^-?[a-z_]+$'
      description: Sort field (prefix with - for descending)
      example: -created_at

  responses:
    BadRequest:
      description: Bad request
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            type: https://api.example.com/errors/bad-request
            title: Bad Request
            status: 400
            detail: Request body is not valid JSON

    Unauthorized:
      description: Authentication required
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            type: https://api.example.com/errors/unauthorized
            title: Unauthorized
            status: 401
            detail: Authentication token is missing or invalid

    NotFound:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            type: https://api.example.com/errors/not-found
            title: Not Found
            status: 404
            detail: The requested resource was not found

    ValidationError:
      description: Validation error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            type: https://api.example.com/errors/validation
            title: Validation Error
            status: 422
            detail: One or more fields failed validation
            errors:
              - field: email
                code: INVALID_FORMAT
                message: Must be a valid email address

    RateLimited:
      description: Rate limit exceeded
      headers:
        X-RateLimit-Limit:
          schema:
            type: integer
          description: Request limit per hour
        X-RateLimit-Remaining:
          schema:
            type: integer
          description: Remaining requests
        X-RateLimit-Reset:
          schema:
            type: integer
          description: Unix timestamp when limit resets
        Retry-After:
          schema:
            type: integer
          description: Seconds until retry is allowed
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
```

### Security Schemes

```yaml
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT access token

    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
      description: API key for server-to-server communication

    OAuth2:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://auth.example.com/authorize
          tokenUrl: https://auth.example.com/token
          refreshUrl: https://auth.example.com/refresh
          scopes:
            read: Read access
            write: Write access
            admin: Admin access

# Apply security globally
security:
  - BearerAuth: []

# Or per-operation
paths:
  /users:
    get:
      security:
        - BearerAuth: []
        - ApiKeyAuth: []
```

## Code Generation

### TypeScript from OpenAPI

```typescript
// Using openapi-typescript
import { paths, components } from './api-types';

type User = components['schemas']['User'];
type CreateUserRequest = components['schemas']['CreateUserRequest'];

// Type-safe API client
async function createUser(data: CreateUserRequest): Promise<User> {
  const response = await fetch('/api/v1/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return response.json();
}
```

### Generate Types Script

```bash
# Install generator
npm install -D openapi-typescript

# Generate types
npx openapi-typescript openapi.yaml -o src/types/api.ts

# With options
npx openapi-typescript openapi.yaml \
  --output src/types/api.ts \
  --export-type \
  --immutable
```

### Validation with Zod

```typescript
import { z } from 'zod';

// Generate Zod schemas from OpenAPI
const UserSchema = z.object({
  id: z.string().ulid(),
  name: z.string().min(1).max(100),
  email: z.string().email(),
  status: z.enum(['active', 'inactive', 'suspended']),
  role: z.enum(['user', 'admin', 'moderator']).default('user'),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime().optional(),
});

const CreateUserRequestSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  password: z.string().min(8).optional(),
  role: z.enum(['user', 'admin', 'moderator']).optional(),
});

type User = z.infer<typeof UserSchema>;

// Validate request
function validateCreateUser(data: unknown): CreateUserRequest {
  return CreateUserRequestSchema.parse(data);
}
```

## Documentation Tools

### Swagger UI Setup

```typescript
import express from 'express';
import swaggerUi from 'swagger-ui-express';
import YAML from 'yamljs';

const app = express();
const spec = YAML.load('./openapi.yaml');

app.use('/docs', swaggerUi.serve, swaggerUi.setup(spec, {
  customCss: '.swagger-ui .topbar { display: none }',
  customSiteTitle: 'API Documentation',
  swaggerOptions: {
    persistAuthorization: true,
    displayRequestDuration: true,
    filter: true,
    tryItOutEnabled: true,
  },
}));
```

### Redoc Setup

```html
<!DOCTYPE html>
<html>
  <head>
    <title>API Documentation</title>
    <link href="https://fonts.googleapis.com/css?family=Roboto" rel="stylesheet">
    <style>
      body { margin: 0; padding: 0; }
    </style>
  </head>
  <body>
    <redoc spec-url="/openapi.yaml"></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
  </body>
</html>
```

### Stoplight Elements

```html
<!DOCTYPE html>
<html>
  <head>
    <title>API Documentation</title>
    <script src="https://unpkg.com/@stoplight/elements/web-components.min.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/@stoplight/elements/styles.min.css">
  </head>
  <body>
    <elements-api
      apiDescriptionUrl="/openapi.yaml"
      router="hash"
      layout="sidebar"
    />
  </body>
</html>
```

## API Changelog

### Changelog Format

```markdown
# API Changelog

## [2024-01-15] v1.2.0

### Added
- `GET /users/{id}/preferences` - Retrieve user preferences
- `PATCH /users/{id}/preferences` - Update user preferences
- Added `timezone` field to User schema

### Changed
- `POST /users` now returns `201` instead of `200`
- Increased rate limit from 100 to 200 requests/hour

### Deprecated
- `GET /users/{id}/settings` - Use `/users/{id}/preferences` instead
- `role` field on User - Will be replaced by `roles` array in v2.0

### Fixed
- Fixed pagination returning incorrect `total_pages`

## [2023-12-01] v1.1.0

### Added
- OAuth 2.0 authentication support
- `status` filter on `GET /users`
```

### Deprecation Headers

```yaml
# OpenAPI deprecation
paths:
  /users/{id}/settings:
    get:
      deprecated: true
      description: |
        **DEPRECATED**: Use `/users/{id}/preferences` instead.
        This endpoint will be removed on 2024-06-01.
      x-sunset: '2024-06-01'

# Response headers
headers:
  Deprecation:
    description: RFC 8594 deprecation date
    schema:
      type: string
    example: 'true'
  Sunset:
    description: Date when endpoint will be removed
    schema:
      type: string
      format: date-time
    example: 'Sat, 01 Jun 2024 00:00:00 GMT'
  Link:
    description: Link to successor endpoint
    schema:
      type: string
    example: '</api/v1/users/{id}/preferences>; rel="successor-version"'
```

## Best Practices

### Schema Design
- [ ] Use `$ref` for reusable components
- [ ] Add `example` values for all properties
- [ ] Use `format` for common types (email, uri, date-time)
- [ ] Define min/max constraints for strings and numbers
- [ ] Mark required fields explicitly
- [ ] Use `readOnly` and `writeOnly` appropriately

### Documentation Quality
- [ ] Write clear, concise descriptions
- [ ] Include request/response examples
- [ ] Document all error responses
- [ ] Explain rate limits and quotas
- [ ] Provide authentication instructions
- [ ] Include code samples for common operations

### Versioning Documentation
- [ ] Maintain changelog for all versions
- [ ] Use deprecation headers
- [ ] Provide migration guides
- [ ] Document breaking changes clearly
- [ ] Include sunset dates for deprecated features

### Tooling
- [ ] Generate types from OpenAPI spec
- [ ] Validate requests against schema
- [ ] Keep spec in sync with implementation
- [ ] Use linting tools (Spectral)
- [ ] Automate documentation deployment
