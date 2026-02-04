---
name: openapi-swagger
description: OpenAPI specification and Swagger tools for API documentation
category: api-design/documentation
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# OpenAPI and Swagger

## Overview

OpenAPI Specification (OAS) is a standard for describing RESTful APIs. Swagger
is a set of tools that implements the OpenAPI specification, including editors,
code generators, and documentation UIs.

## OpenAPI 3.x Structure

```yaml
openapi: 3.1.0
info:
  title: My API
  description: API description with **markdown** support
  version: 1.0.0
  contact:
    name: API Support
    email: support@example.com
    url: https://example.com/support
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT
  termsOfService: https://example.com/terms

servers:
  - url: https://api.example.com/v1
    description: Production server
  - url: https://staging-api.example.com/v1
    description: Staging server
  - url: http://localhost:3000/v1
    description: Development server

tags:
  - name: users
    description: User management operations
  - name: orders
    description: Order processing operations

paths:
  # Path definitions...

components:
  schemas:
    # Schema definitions...
  securitySchemes:
    # Security definitions...
  parameters:
    # Reusable parameters...
  responses:
    # Reusable responses...

security:
  - bearerAuth: []
```

## Path Definitions

```yaml
paths:
  /users:
    get:
      tags:
        - users
      summary: List all users
      description: |
        Returns a paginated list of users.
        Supports filtering by status and role.
      operationId: listUsers
      parameters:
        - $ref: '#/components/parameters/PageSize'
        - $ref: '#/components/parameters/PageToken'
        - name: status
          in: query
          description: Filter by user status
          required: false
          schema:
            $ref: '#/components/schemas/UserStatus'
        - name: role
          in: query
          description: Filter by user role
          required: false
          schema:
            type: string
            enum: [user, admin, moderator]
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserListResponse'
              example:
                users:
                  - id: usr_001
                    name: John Doe
                    email: john@example.com
                    status: active
                next_page_token: abc123
                total_count: 150
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'

    post:
      tags:
        - users
      summary: Create a new user
      description: Creates a new user account
      operationId: createUser
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUserRequest'
            examples:
              basic:
                summary: Basic user creation
                value:
                  name: Jane Doe
                  email: jane@example.com
                  password: SecurePass123!
              withRole:
                summary: User with admin role
                value:
                  name: Admin User
                  email: admin@example.com
                  password: SecurePass123!
                  role: admin
      responses:
        '201':
          description: User created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserResponse'
          headers:
            Location:
              description: URL of the created resource
              schema:
                type: string
                format: uri
        '400':
          $ref: '#/components/responses/BadRequest'
        '409':
          description: Email already exists
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /users/{userId}:
    parameters:
      - $ref: '#/components/parameters/UserId'

    get:
      tags:
        - users
      summary: Get user by ID
      description: Returns a single user by their ID
      operationId: getUser
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserResponse'
        '404':
          $ref: '#/components/responses/NotFound'

    patch:
      tags:
        - users
      summary: Update user
      description: Partially updates an existing user
      operationId: updateUser
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateUserRequest'
      responses:
        '200':
          description: User updated successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '404':
          $ref: '#/components/responses/NotFound'

    delete:
      tags:
        - users
      summary: Delete user
      description: Deletes a user account
      operationId: deleteUser
      responses:
        '204':
          description: User deleted successfully
        '404':
          $ref: '#/components/responses/NotFound'
```

## Components

### Schemas

```yaml
components:
  schemas:
    # Base types
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
          description: Unique user identifier
          example: usr_abc123
          readOnly: true
        name:
          type: string
          description: User's full name
          minLength: 2
          maxLength: 100
          example: John Doe
        email:
          type: string
          format: email
          description: User's email address
          example: john@example.com
        status:
          $ref: '#/components/schemas/UserStatus'
        role:
          type: string
          enum: [user, admin, moderator]
          default: user
        profile:
          $ref: '#/components/schemas/Profile'
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
      description: Current status of the user account

    Profile:
      type: object
      properties:
        bio:
          type: string
          maxLength: 500
        avatar_url:
          type: string
          format: uri
        website:
          type: string
          format: uri

    # Request types
    CreateUserRequest:
      type: object
      required:
        - name
        - email
        - password
      properties:
        name:
          type: string
          minLength: 2
          maxLength: 100
        email:
          type: string
          format: email
        password:
          type: string
          format: password
          minLength: 8
          description: Must contain uppercase, lowercase, number, and special char
        role:
          type: string
          enum: [user, admin, moderator]
          default: user

    UpdateUserRequest:
      type: object
      properties:
        name:
          type: string
          minLength: 2
          maxLength: 100
        email:
          type: string
          format: email
        status:
          $ref: '#/components/schemas/UserStatus'
        profile:
          $ref: '#/components/schemas/Profile'

    # Response types
    UserResponse:
      type: object
      properties:
        user:
          $ref: '#/components/schemas/User'

    UserListResponse:
      type: object
      properties:
        users:
          type: array
          items:
            $ref: '#/components/schemas/User'
        next_page_token:
          type: string
          nullable: true
        total_count:
          type: integer

    # Error types
    Error:
      type: object
      required:
        - code
        - message
      properties:
        code:
          type: string
          description: Machine-readable error code
        message:
          type: string
          description: Human-readable error message
        details:
          type: array
          items:
            $ref: '#/components/schemas/ErrorDetail'

    ErrorDetail:
      type: object
      properties:
        field:
          type: string
        message:
          type: string
        code:
          type: string

    # Pagination
    PaginationMeta:
      type: object
      properties:
        page_size:
          type: integer
        page_token:
          type: string
          nullable: true
        next_page_token:
          type: string
          nullable: true
        total_count:
          type: integer
```

### Parameters

```yaml
components:
  parameters:
    UserId:
      name: userId
      in: path
      required: true
      description: User's unique identifier
      schema:
        type: string
        pattern: '^usr_[a-zA-Z0-9]+$'
      example: usr_abc123

    PageSize:
      name: page_size
      in: query
      description: Number of items per page
      required: false
      schema:
        type: integer
        minimum: 1
        maximum: 100
        default: 20

    PageToken:
      name: page_token
      in: query
      description: Token for pagination
      required: false
      schema:
        type: string

    SortBy:
      name: sort_by
      in: query
      description: Field to sort by
      required: false
      schema:
        type: string
        enum: [created_at, updated_at, name]
        default: created_at

    SortOrder:
      name: sort_order
      in: query
      description: Sort direction
      required: false
      schema:
        type: string
        enum: [asc, desc]
        default: desc
```

### Responses

```yaml
components:
  responses:
    BadRequest:
      description: Invalid request
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            code: INVALID_REQUEST
            message: The request body is invalid
            details:
              - field: email
                message: Must be a valid email address
                code: INVALID_FORMAT

    Unauthorized:
      description: Authentication required
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            code: UNAUTHORIZED
            message: Authentication credentials are missing or invalid

    Forbidden:
      description: Access denied
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            code: FORBIDDEN
            message: You don't have permission to access this resource

    NotFound:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            code: NOT_FOUND
            message: The requested resource was not found

    Conflict:
      description: Resource conflict
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            code: CONFLICT
            message: A resource with this identifier already exists

    TooManyRequests:
      description: Rate limit exceeded
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            code: RATE_LIMITED
            message: Too many requests. Please try again later.
      headers:
        X-RateLimit-Limit:
          schema:
            type: integer
          description: Request limit per hour
        X-RateLimit-Remaining:
          schema:
            type: integer
          description: Remaining requests in the current window
        X-RateLimit-Reset:
          schema:
            type: integer
          description: Unix timestamp when the rate limit resets

    InternalError:
      description: Internal server error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            code: INTERNAL_ERROR
            message: An unexpected error occurred
```

### Security Schemes

```yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT token authentication

    apiKey:
      type: apiKey
      in: header
      name: X-API-Key
      description: API key authentication

    oauth2:
      type: oauth2
      description: OAuth2 authentication
      flows:
        authorizationCode:
          authorizationUrl: https://auth.example.com/authorize
          tokenUrl: https://auth.example.com/token
          refreshUrl: https://auth.example.com/refresh
          scopes:
            read:users: Read user data
            write:users: Modify user data
            admin: Full administrative access
        clientCredentials:
          tokenUrl: https://auth.example.com/token
          scopes:
            read:users: Read user data
            write:users: Modify user data

    basicAuth:
      type: http
      scheme: basic
```

## Advanced Features

### Webhooks (OpenAPI 3.1)

```yaml
webhooks:
  userCreated:
    post:
      summary: User created event
      description: Triggered when a new user is created
      operationId: onUserCreated
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserCreatedEvent'
      responses:
        '200':
          description: Webhook received successfully

  orderCompleted:
    post:
      summary: Order completed event
      description: Triggered when an order is completed
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/OrderCompletedEvent'
      responses:
        '200':
          description: Webhook received successfully
```

### Links

```yaml
paths:
  /users/{userId}:
    get:
      operationId: getUser
      responses:
        '200':
          description: User found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
          links:
            GetUserOrders:
              operationId: getUserOrders
              parameters:
                userId: $response.body#/id
              description: Get orders for this user
            UpdateUser:
              operationId: updateUser
              parameters:
                userId: $response.body#/id

  /users/{userId}/orders:
    get:
      operationId: getUserOrders
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: User's orders
```

### Callbacks

```yaml
paths:
  /subscriptions:
    post:
      summary: Create subscription
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                callback_url:
                  type: string
                  format: uri
                events:
                  type: array
                  items:
                    type: string
      callbacks:
        onEvent:
          '{$request.body#/callback_url}':
            post:
              requestBody:
                content:
                  application/json:
                    schema:
                      type: object
                      properties:
                        event_type:
                          type: string
                        data:
                          type: object
              responses:
                '200':
                  description: Callback acknowledged
```

## Code Generation

### Generate TypeScript Client

```bash
# Using openapi-generator
npx @openapitools/openapi-generator-cli generate \
  -i api.yaml \
  -g typescript-fetch \
  -o ./src/api

# Using swagger-codegen
swagger-codegen generate \
  -i api.yaml \
  -l typescript-fetch \
  -o ./src/api

# Using orval (recommended for TypeScript)
npx orval --input api.yaml --output ./src/api
```

### Generate Go Server

```bash
# Using oapi-codegen
oapi-codegen -generate types,server,spec -package api api.yaml > api/api.gen.go

# Using go-swagger
swagger generate server -f api.yaml -t ./gen
```

### Orval Configuration

```javascript
// orval.config.js
module.exports = {
  petstore: {
    input: './api.yaml',
    output: {
      mode: 'tags-split',
      target: './src/api/generated.ts',
      schemas: './src/api/model',
      client: 'react-query',
      mock: true,
    },
    hooks: {
      afterAllFilesWrite: 'prettier --write',
    },
  },
};
```

## Swagger UI Configuration

```html
<!DOCTYPE html>
<html>
  <head>
    <title>API Documentation</title>
    <link
      rel="stylesheet"
      href="https://unpkg.com/swagger-ui-dist/swagger-ui.css"
    />
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist/swagger-ui-bundle.js"></script>
    <script>
      SwaggerUIBundle({
        url: '/api.yaml',
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
        plugins: [SwaggerUIBundle.plugins.DownloadUrl],
        layout: 'StandaloneLayout',
        // Customization
        defaultModelsExpandDepth: 2,
        defaultModelExpandDepth: 2,
        displayRequestDuration: true,
        filter: true,
        showExtensions: true,
        showCommonExtensions: true,
        // Try it out
        tryItOutEnabled: true,
        // OAuth configuration
        oauth2RedirectUrl: window.location.origin + '/oauth2-redirect.html',
        // Custom CSS
        customCss: '.swagger-ui .topbar { display: none }',
      });
    </script>
  </body>
</html>
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                OpenAPI Best Practices                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Use Semantic Versioning                                     │
│     └── Major.Minor.Patch in info.version                       │
│                                                                  │
│  2. Provide Examples                                            │
│     └── Include examples for all schemas and operations         │
│                                                                  │
│  3. Use $ref for Reusability                                    │
│     └── Define components once, reference everywhere            │
│                                                                  │
│  4. Document Error Responses                                    │
│     └── Include all possible error codes with examples          │
│                                                                  │
│  5. Add Descriptions                                            │
│     └── Describe every field, parameter, and operation          │
│                                                                  │
│  6. Use Tags for Organization                                   │
│     └── Group related operations logically                      │
│                                                                  │
│  7. Validate Your Spec                                          │
│     └── Use spectral or swagger-cli for linting                 │
│                                                                  │
│  8. Keep Spec in Sync                                           │
│     └── Generate from code or validate against code             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
