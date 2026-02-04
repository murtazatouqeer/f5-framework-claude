# Microservices Example

Complete microservices architecture example with Docker Compose.

## Architecture

```
                    ┌─────────────┐
                    │   Gateway   │ :8080
                    │  (Node.js)  │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│  User Service  │ │Product Service │ │ Order Service  │
│    (Node.js)   │ │   (Node.js)    │ │   (Node.js)    │
│     :3001      │ │     :3002      │ │     :3003      │
└────────┬───────┘ └────────┬───────┘ └────────┬───────┘
         │                  │                  │
         ▼                  ▼                  ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│   PostgreSQL   │ │    MongoDB     │ │   PostgreSQL   │
│    (users)     │ │   (products)   │ │    (orders)    │
└────────────────┘ └────────────────┘ └────────────────┘

Shared Infrastructure:
- Redis (caching)
- RabbitMQ (messaging)
```

## Quick Start

```bash
# Copy environment file
cp .env.example .env

# Edit with your passwords
vim .env

# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

## Services

| Service | Port | Database | Description |
|---------|------|----------|-------------|
| Gateway | 8080 | - | API Gateway with rate limiting |
| User Service | 3001 | PostgreSQL | User management |
| Product Service | 3002 | MongoDB | Product catalog |
| Order Service | 3003 | PostgreSQL | Order processing |

## Endpoints

### Gateway
- `GET /health` - Health check
- `POST /api/users/*` - Proxy to User Service
- `GET /api/products/*` - Proxy to Product Service
- `POST /api/orders/*` - Proxy to Order Service

### User Service
- `POST /users` - Create user
- `GET /users/:id` - Get user
- `PUT /users/:id` - Update user
- `DELETE /users/:id` - Delete user

### Product Service
- `GET /products` - List products
- `GET /products/:id` - Get product
- `POST /products` - Create product
- `PUT /products/:id` - Update product

### Order Service
- `POST /orders` - Create order
- `GET /orders/:id` - Get order
- `GET /orders/user/:userId` - Get user orders

## Monitoring

### RabbitMQ Management
- URL: http://localhost:15672
- User: rabbit
- Password: (from .env)

### Health Checks
```bash
# Check all services
docker compose ps

# Check specific service
curl http://localhost:8080/health
curl http://localhost:3001/health
curl http://localhost:3002/health
curl http://localhost:3003/health
```

## Scaling

```bash
# Scale specific service
docker compose up -d --scale user-service=3

# Scale multiple services
docker compose up -d --scale user-service=3 --scale product-service=2
```

## Development

```bash
# Start with dev profile
docker compose --profile dev up -d

# Rebuild specific service
docker compose build user-service
docker compose up -d user-service

# View service logs
docker compose logs -f user-service
```

## Network Isolation

- `public`: External access (gateway only)
- `services`: Inter-service communication
- `user-network`: User service + database
- `product-network`: Product service + database
- `order-network`: Order service + database

## Volumes

| Volume | Purpose |
|--------|---------|
| user_db_data | User database persistence |
| product_db_data | Product database persistence |
| order_db_data | Order database persistence |
| redis_data | Cache persistence |
| rabbitmq_data | Message queue persistence |
