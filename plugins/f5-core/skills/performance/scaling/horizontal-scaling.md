---
name: horizontal-scaling
description: Horizontal scaling strategies for distributed systems
category: performance/scaling
applies_to: backend
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Horizontal Scaling

## Overview

Horizontal scaling (scaling out) adds more instances to handle increased load,
providing better fault tolerance and theoretically unlimited scaling capacity.

## Scaling Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│                    Scaling Comparison                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Vertical (Scale Up)         Horizontal (Scale Out)             │
│  ┌─────────────┐            ┌───┐ ┌───┐ ┌───┐ ┌───┐            │
│  │             │            │   │ │   │ │   │ │   │            │
│  │   Bigger    │     vs     │ S │ │ S │ │ S │ │ S │            │
│  │   Server    │            │ 1 │ │ 2 │ │ 3 │ │ 4 │            │
│  │             │            │   │ │   │ │   │ │   │            │
│  └─────────────┘            └───┘ └───┘ └───┘ └───┘            │
│                                                                  │
│  • Limited ceiling           • Theoretically unlimited          │
│  • Single point of failure   • Fault tolerant                   │
│  • Simpler architecture      • More complex                     │
│  • Expensive at scale        • Cost-effective                   │
└─────────────────────────────────────────────────────────────────┘
```

## Stateless Application Design

### Making Applications Stateless

```typescript
// ❌ Bad - stateful server
class StatefulServer {
  private sessions = new Map<string, UserSession>();

  login(userId: string): string {
    const sessionId = generateId();
    this.sessions.set(sessionId, { userId, createdAt: new Date() });
    return sessionId;
  }

  getUser(sessionId: string): UserSession | undefined {
    return this.sessions.get(sessionId); // Only works on this instance
  }
}

// ✅ Good - stateless with external session store
import { Redis } from 'ioredis';

class StatelessServer {
  constructor(private redis: Redis) {}

  async login(userId: string): Promise<string> {
    const sessionId = generateId();
    await this.redis.setex(
      `session:${sessionId}`,
      3600, // 1 hour TTL
      JSON.stringify({ userId, createdAt: new Date() })
    );
    return sessionId;
  }

  async getUser(sessionId: string): Promise<UserSession | null> {
    const data = await this.redis.get(`session:${sessionId}`);
    return data ? JSON.parse(data) : null;
  }
}
```

### External State Management

```typescript
// Configuration for stateless services
interface StatelessConfig {
  // Session storage
  sessionStore: {
    type: 'redis' | 'dynamodb' | 'memcached';
    connection: string;
    ttl: number;
  };

  // File storage
  fileStorage: {
    type: 's3' | 'gcs' | 'azure-blob';
    bucket: string;
    region: string;
  };

  // Cache
  cache: {
    type: 'redis' | 'elasticache';
    cluster: string[];
  };
}

// Service using external state
class UserService {
  constructor(
    private db: PrismaClient,
    private redis: Redis,
    private s3: S3Client
  ) {}

  async uploadAvatar(userId: string, file: Buffer): Promise<string> {
    const key = `avatars/${userId}/${Date.now()}.jpg`;

    // Store in S3 (accessible from any instance)
    await this.s3.send(new PutObjectCommand({
      Bucket: process.env.S3_BUCKET,
      Key: key,
      Body: file,
      ContentType: 'image/jpeg',
    }));

    // Update database
    await this.db.user.update({
      where: { id: userId },
      data: { avatarUrl: `https://cdn.example.com/${key}` },
    });

    // Invalidate cache
    await this.redis.del(`user:${userId}`);

    return key;
  }
}
```

## Database Scaling

### Read Replicas

```typescript
// Prisma with read replicas
import { PrismaClient } from '@prisma/client';

const primaryDb = new PrismaClient({
  datasources: {
    db: { url: process.env.DATABASE_URL_PRIMARY },
  },
});

const replicaDb = new PrismaClient({
  datasources: {
    db: { url: process.env.DATABASE_URL_REPLICA },
  },
});

class DatabaseRouter {
  // Writes go to primary
  async write<T>(operation: () => Promise<T>): Promise<T> {
    return operation.call(primaryDb);
  }

  // Reads go to replica
  async read<T>(operation: () => Promise<T>): Promise<T> {
    return operation.call(replicaDb);
  }
}

// Usage
const router = new DatabaseRouter();

// Write to primary
await router.write(() =>
  primaryDb.user.create({ data: userData })
);

// Read from replica
const user = await router.read(() =>
  replicaDb.user.findUnique({ where: { id: userId } })
);
```

### Database Sharding

```typescript
// Horizontal sharding by user ID
class ShardedDatabase {
  private shards: PrismaClient[];

  constructor(shardUrls: string[]) {
    this.shards = shardUrls.map(url =>
      new PrismaClient({ datasources: { db: { url } } })
    );
  }

  private getShardIndex(userId: string): number {
    // Consistent hashing
    const hash = this.hashString(userId);
    return hash % this.shards.length;
  }

  private hashString(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) - hash) + str.charCodeAt(i);
      hash = hash & hash;
    }
    return Math.abs(hash);
  }

  getShard(userId: string): PrismaClient {
    return this.shards[this.getShardIndex(userId)];
  }

  async getUser(userId: string) {
    const shard = this.getShard(userId);
    return shard.user.findUnique({ where: { id: userId } });
  }

  async createUser(userId: string, data: CreateUserDto) {
    const shard = this.getShard(userId);
    return shard.user.create({ data: { id: userId, ...data } });
  }

  // Cross-shard query (expensive)
  async getAllUsers() {
    const results = await Promise.all(
      this.shards.map(shard => shard.user.findMany())
    );
    return results.flat();
  }
}
```

## Message Queue for Distributed Processing

### BullMQ Distributed Workers

```typescript
import { Queue, Worker } from 'bullmq';

// Queue (shared across all instances)
const emailQueue = new Queue('emails', {
  connection: {
    host: process.env.REDIS_HOST,
    port: 6379,
  },
});

// Worker (runs on each instance)
const worker = new Worker('emails', async (job) => {
  const { to, subject, body } = job.data;
  await sendEmail(to, subject, body);
}, {
  connection: {
    host: process.env.REDIS_HOST,
    port: 6379,
  },
  concurrency: 10, // Process 10 jobs concurrently per instance
});

// Producer (can run on any instance)
async function queueEmail(to: string, subject: string, body: string) {
  await emailQueue.add('send', { to, subject, body }, {
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 1000,
    },
  });
}
```

### Event-Driven Architecture

```typescript
import { Redis } from 'ioredis';

class EventBus {
  private publisher: Redis;
  private subscriber: Redis;
  private handlers = new Map<string, Function[]>();

  constructor(redisUrl: string) {
    this.publisher = new Redis(redisUrl);
    this.subscriber = new Redis(redisUrl);

    this.subscriber.on('message', (channel, message) => {
      const handlers = this.handlers.get(channel) || [];
      const data = JSON.parse(message);
      handlers.forEach(handler => handler(data));
    });
  }

  async publish(event: string, data: any): Promise<void> {
    await this.publisher.publish(event, JSON.stringify(data));
  }

  subscribe(event: string, handler: (data: any) => void): void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, []);
      this.subscriber.subscribe(event);
    }
    this.handlers.get(event)!.push(handler);
  }
}

// Usage across multiple instances
const eventBus = new EventBus(process.env.REDIS_URL!);

// All instances subscribe to events
eventBus.subscribe('user.created', async (user) => {
  await sendWelcomeEmail(user.email);
});

eventBus.subscribe('order.completed', async (order) => {
  await updateInventory(order.items);
  await notifyShipping(order);
});

// Any instance can publish events
await eventBus.publish('user.created', { id: '123', email: 'user@example.com' });
```

## Distributed Caching

### Redis Cluster

```typescript
import { Cluster } from 'ioredis';

const cluster = new Cluster([
  { port: 7000, host: 'redis-node-1' },
  { port: 7001, host: 'redis-node-2' },
  { port: 7002, host: 'redis-node-3' },
], {
  redisOptions: {
    password: process.env.REDIS_PASSWORD,
  },
  scaleReads: 'slave', // Read from replicas
});

class DistributedCache {
  constructor(private redis: Cluster) {}

  async get<T>(key: string): Promise<T | null> {
    const data = await this.redis.get(key);
    return data ? JSON.parse(data) : null;
  }

  async set(key: string, value: any, ttl: number = 3600): Promise<void> {
    await this.redis.setex(key, ttl, JSON.stringify(value));
  }

  async invalidate(pattern: string): Promise<void> {
    // Use SCAN to find keys (works with cluster)
    const keys: string[] = [];
    let cursor = '0';

    do {
      const [newCursor, foundKeys] = await this.redis.scan(
        cursor,
        'MATCH', pattern,
        'COUNT', 100
      );
      cursor = newCursor;
      keys.push(...foundKeys);
    } while (cursor !== '0');

    if (keys.length > 0) {
      await this.redis.del(...keys);
    }
  }
}
```

## Service Discovery

### Consul Integration

```typescript
import Consul from 'consul';

const consul = new Consul({
  host: process.env.CONSUL_HOST,
  port: 8500,
});

class ServiceRegistry {
  private serviceId: string;

  constructor(
    private serviceName: string,
    private port: number
  ) {
    this.serviceId = `${serviceName}-${process.env.HOSTNAME}-${port}`;
  }

  async register(): Promise<void> {
    await consul.agent.service.register({
      id: this.serviceId,
      name: this.serviceName,
      port: this.port,
      check: {
        http: `http://localhost:${this.port}/health`,
        interval: '10s',
        timeout: '5s',
      },
    });

    // Deregister on shutdown
    process.on('SIGTERM', () => this.deregister());
    process.on('SIGINT', () => this.deregister());
  }

  async deregister(): Promise<void> {
    await consul.agent.service.deregister(this.serviceId);
    process.exit(0);
  }

  async getServiceInstances(serviceName: string): Promise<ServiceInstance[]> {
    const result = await consul.health.service({
      service: serviceName,
      passing: true, // Only healthy instances
    });

    return result.map((entry: any) => ({
      id: entry.Service.ID,
      address: entry.Service.Address,
      port: entry.Service.Port,
    }));
  }
}

// Usage
const registry = new ServiceRegistry('api-service', 3000);
await registry.register();

// Find other services
const userServices = await registry.getServiceInstances('user-service');
```

## Kubernetes Horizontal Scaling

### Deployment Configuration

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-service
  template:
    metadata:
      labels:
        app: api-service
    spec:
      containers:
      - name: api
        image: api-service:latest
        ports:
        - containerPort: 3000
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: redis-url
        readinessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 15
          periodSeconds: 20
```

### Horizontal Pod Autoscaler

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-service
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 4
        periodSeconds: 15
      selectPolicy: Max
```

## Graceful Shutdown

```typescript
import { Server } from 'http';

function setupGracefulShutdown(
  server: Server,
  cleanup: () => Promise<void>
): void {
  let isShuttingDown = false;

  async function shutdown(signal: string): Promise<void> {
    if (isShuttingDown) return;
    isShuttingDown = true;

    console.log(`Received ${signal}, starting graceful shutdown...`);

    // Stop accepting new connections
    server.close(async () => {
      console.log('HTTP server closed');

      try {
        // Cleanup resources
        await cleanup();
        console.log('Cleanup completed');
        process.exit(0);
      } catch (error) {
        console.error('Cleanup failed:', error);
        process.exit(1);
      }
    });

    // Force shutdown after timeout
    setTimeout(() => {
      console.error('Forced shutdown after timeout');
      process.exit(1);
    }, 30000);
  }

  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));
}

// Usage
const server = app.listen(3000);

setupGracefulShutdown(server, async () => {
  // Close database connections
  await prisma.$disconnect();

  // Close Redis connections
  await redis.quit();

  // Drain job queues
  await worker.close();

  // Deregister from service discovery
  await registry.deregister();
});
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│              Horizontal Scaling Checklist                        │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Stateless application design                                  │
│ ☐ External session storage (Redis/DynamoDB)                     │
│ ☐ External file storage (S3/GCS)                                │
│ ☐ Database read replicas for read-heavy workloads               │
│ ☐ Message queues for async processing                           │
│ ☐ Distributed caching (Redis Cluster)                           │
│ ☐ Service discovery for dynamic routing                         │
│ ☐ Health checks and readiness probes                            │
│ ☐ Graceful shutdown handling                                    │
│ ☐ Sticky sessions only when necessary                           │
│ ☐ Connection pooling with appropriate limits                    │
│ ☐ Centralized logging and monitoring                            │
└─────────────────────────────────────────────────────────────────┘
```
