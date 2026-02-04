---
name: load-balancing
description: Load balancing strategies and configurations
category: performance/scaling
applies_to: backend
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Load Balancing

## Overview

Load balancing distributes incoming traffic across multiple servers to ensure
high availability, reliability, and optimal resource utilization.

## Load Balancing Algorithms

```
┌─────────────────────────────────────────────────────────────────┐
│                Load Balancing Algorithms                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Round Robin          Least Connections      Weighted            │
│  ┌───┐ ┌───┐ ┌───┐   ┌───┐ ┌───┐ ┌───┐    ┌───┐ ┌───┐ ┌───┐   │
│  │ 1 │→│ 2 │→│ 3 │   │ 5 │ │ 2 │ │ 8 │    │3x │ │2x │ │1x │   │
│  └───┘ └───┘ └───┘   └───┘ └───┘ └───┘    └───┘ └───┘ └───┘   │
│    ↑_____________│     ↑         ↓          50%   33%   17%     │
│                      choose                                      │
│                                                                  │
│  IP Hash             Random              Response Time           │
│  hash(IP) % n        rand() % n         fastest server wins     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## NGINX Load Balancing

### Basic Configuration

```nginx
# /etc/nginx/nginx.conf

upstream api_servers {
    # Round robin (default)
    server api1.example.com:3000;
    server api2.example.com:3000;
    server api3.example.com:3000;
}

upstream api_weighted {
    # Weighted round robin
    server api1.example.com:3000 weight=5;
    server api2.example.com:3000 weight=3;
    server api3.example.com:3000 weight=2;
}

upstream api_least_conn {
    # Least connections
    least_conn;
    server api1.example.com:3000;
    server api2.example.com:3000;
    server api3.example.com:3000;
}

upstream api_ip_hash {
    # IP hash (sticky sessions)
    ip_hash;
    server api1.example.com:3000;
    server api2.example.com:3000;
    server api3.example.com:3000;
}

server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://api_servers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeouts
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### Health Checks and Failover

```nginx
upstream api_servers {
    server api1.example.com:3000 max_fails=3 fail_timeout=30s;
    server api2.example.com:3000 max_fails=3 fail_timeout=30s;
    server api3.example.com:3000 max_fails=3 fail_timeout=30s;
    server backup.example.com:3000 backup;  # Backup server

    # Keep connections alive to upstream
    keepalive 32;
}

# Active health checks (NGINX Plus or OpenResty)
upstream api_servers {
    zone api_servers 64k;
    server api1.example.com:3000;
    server api2.example.com:3000;

    # Active health check
    health_check interval=5s fails=3 passes=2;
}

# Health check location
location /health {
    proxy_pass http://api_servers/health;
    health_check;
}
```

### Rate Limiting

```nginx
# Define rate limit zone
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

server {
    location /api/ {
        # Rate limit: 10 req/s with burst of 20
        limit_req zone=api_limit burst=20 nodelay;

        # Connection limit: 10 concurrent connections per IP
        limit_conn conn_limit 10;

        proxy_pass http://api_servers;
    }

    # Different limits for different endpoints
    location /api/heavy/ {
        limit_req zone=api_limit burst=5 nodelay;
        proxy_pass http://api_servers;
    }
}
```

## HAProxy Configuration

### Basic Setup

```haproxy
# /etc/haproxy/haproxy.cfg

global
    maxconn 50000
    log stdout format raw local0
    stats socket /var/run/haproxy.sock mode 660 level admin

defaults
    mode http
    log global
    option httplog
    option dontlognull
    option http-server-close
    option forwardfor except 127.0.0.0/8
    option redispatch
    retries 3
    timeout http-request 10s
    timeout queue 60s
    timeout connect 5s
    timeout client 60s
    timeout server 60s
    timeout http-keep-alive 10s
    timeout check 10s
    maxconn 10000

frontend http_front
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/combined.pem
    http-request redirect scheme https unless { ssl_fc }

    # Route based on path
    acl is_api path_beg /api
    acl is_static path_beg /static

    use_backend api_servers if is_api
    use_backend static_servers if is_static
    default_backend web_servers

backend api_servers
    balance roundrobin
    option httpchk GET /health
    http-check expect status 200

    server api1 api1.example.com:3000 check inter 5s fall 3 rise 2
    server api2 api2.example.com:3000 check inter 5s fall 3 rise 2
    server api3 api3.example.com:3000 check inter 5s fall 3 rise 2

backend web_servers
    balance leastconn
    cookie SERVERID insert indirect nocache

    server web1 web1.example.com:8080 check cookie web1
    server web2 web2.example.com:8080 check cookie web2

backend static_servers
    balance source
    server static1 static1.example.com:80 check
    server static2 static2.example.com:80 check

# Stats page
listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 10s
    stats auth admin:password
```

### Advanced HAProxy Features

```haproxy
# Rate limiting with stick tables
frontend http_front
    bind *:80

    # Track request rates
    stick-table type ip size 100k expire 30s store http_req_rate(10s)
    http-request track-sc0 src

    # Deny if rate > 100 requests per 10 seconds
    http-request deny deny_status 429 if { sc_http_req_rate(0) gt 100 }

    # Slow down if rate > 50 requests per 10 seconds
    http-request tarpit if { sc_http_req_rate(0) gt 50 }

backend api_servers
    # Slow start (gradually increase traffic to new servers)
    server api1 api1.example.com:3000 check slowstart 60s

    # Connection limits per server
    server api2 api2.example.com:3000 check maxconn 1000

    # Agent health checks (server reports its own health)
    server api3 api3.example.com:3000 check agent-check agent-port 8080

# Circuit breaker pattern
backend api_servers
    # Mark server as down after 3 failed checks
    option httpchk GET /health
    default-server inter 5s fall 3 rise 2

    # Queue requests when all servers are at max connections
    option redispatch
    retries 3

    server api1 api1.example.com:3000 check maxconn 500
    server api2 api2.example.com:3000 check maxconn 500
```

## AWS Application Load Balancer

### Terraform Configuration

```hcl
# alb.tf

resource "aws_lb" "api" {
  name               = "api-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = aws_subnet.public[*].id

  enable_deletion_protection = true

  access_logs {
    bucket  = aws_s3_bucket.logs.bucket
    prefix  = "alb-logs"
    enabled = true
  }

  tags = {
    Environment = "production"
  }
}

resource "aws_lb_target_group" "api" {
  name     = "api-targets"
  port     = 3000
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher            = "200"
    path               = "/health"
    port               = "traffic-port"
    protocol           = "HTTP"
    timeout            = 5
    unhealthy_threshold = 3
  }

  stickiness {
    type            = "lb_cookie"
    cookie_duration = 86400
    enabled         = true
  }

  deregistration_delay = 30

  tags = {
    Name = "api-target-group"
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.api.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.api.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

# Path-based routing
resource "aws_lb_listener_rule" "api_v2" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api_v2.arn
  }

  condition {
    path_pattern {
      values = ["/api/v2/*"]
    }
  }
}

# Weighted routing (canary deployments)
resource "aws_lb_listener_rule" "canary" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 200

  action {
    type = "forward"

    forward {
      target_group {
        arn    = aws_lb_target_group.api.arn
        weight = 90
      }
      target_group {
        arn    = aws_lb_target_group.api_canary.arn
        weight = 10
      }
    }
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}
```

## Kubernetes Ingress

### NGINX Ingress Controller

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "5"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "60"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/use-regex: "true"
    # Rate limiting
    nginx.ingress.kubernetes.io/limit-rps: "100"
    nginx.ingress.kubernetes.io/limit-connections: "10"
    # Affinity (sticky sessions)
    nginx.ingress.kubernetes.io/affinity: "cookie"
    nginx.ingress.kubernetes.io/session-cookie-name: "SERVERID"
    nginx.ingress.kubernetes.io/session-cookie-max-age: "3600"
spec:
  tls:
  - hosts:
    - api.example.com
    secretName: api-tls
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /api/v2
        pathType: Prefix
        backend:
          service:
            name: api-v2
            port:
              number: 80
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web
            port:
              number: 80
```

### Service Configuration

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: api
  annotations:
    # For cloud load balancer integration
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-internal: "true"
spec:
  type: ClusterIP  # or LoadBalancer for external
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 3600
  ports:
  - port: 80
    targetPort: 3000
    protocol: TCP
  selector:
    app: api
```

## Application-Level Load Balancing

### Node.js Client-Side Load Balancing

```typescript
interface ServerInstance {
  url: string;
  weight: number;
  healthy: boolean;
  activeConnections: number;
  lastCheck: Date;
}

class LoadBalancer {
  private servers: ServerInstance[] = [];
  private currentIndex = 0;
  private healthCheckInterval: NodeJS.Timeout | null = null;

  constructor(
    serverUrls: string[],
    private algorithm: 'round-robin' | 'least-conn' | 'weighted' = 'round-robin'
  ) {
    this.servers = serverUrls.map(url => ({
      url,
      weight: 1,
      healthy: true,
      activeConnections: 0,
      lastCheck: new Date(),
    }));

    this.startHealthChecks();
  }

  private startHealthChecks(): void {
    this.healthCheckInterval = setInterval(async () => {
      await Promise.all(
        this.servers.map(server => this.checkHealth(server))
      );
    }, 5000);
  }

  private async checkHealth(server: ServerInstance): Promise<void> {
    try {
      const response = await fetch(`${server.url}/health`, {
        timeout: 3000,
      });
      server.healthy = response.ok;
    } catch {
      server.healthy = false;
    }
    server.lastCheck = new Date();
  }

  getServer(): ServerInstance | null {
    const healthyServers = this.servers.filter(s => s.healthy);
    if (healthyServers.length === 0) return null;

    switch (this.algorithm) {
      case 'round-robin':
        return this.roundRobin(healthyServers);
      case 'least-conn':
        return this.leastConnections(healthyServers);
      case 'weighted':
        return this.weightedRoundRobin(healthyServers);
      default:
        return healthyServers[0];
    }
  }

  private roundRobin(servers: ServerInstance[]): ServerInstance {
    const server = servers[this.currentIndex % servers.length];
    this.currentIndex++;
    return server;
  }

  private leastConnections(servers: ServerInstance[]): ServerInstance {
    return servers.reduce((min, server) =>
      server.activeConnections < min.activeConnections ? server : min
    );
  }

  private weightedRoundRobin(servers: ServerInstance[]): ServerInstance {
    const totalWeight = servers.reduce((sum, s) => sum + s.weight, 0);
    let random = Math.random() * totalWeight;

    for (const server of servers) {
      random -= server.weight;
      if (random <= 0) return server;
    }

    return servers[0];
  }

  async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const server = this.getServer();
    if (!server) {
      throw new Error('No healthy servers available');
    }

    server.activeConnections++;

    try {
      const response = await fetch(`${server.url}${path}`, options);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response.json();
    } finally {
      server.activeConnections--;
    }
  }

  destroy(): void {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
    }
  }
}

// Usage
const lb = new LoadBalancer([
  'http://api1:3000',
  'http://api2:3000',
  'http://api3:3000',
], 'least-conn');

const data = await lb.request('/api/users');
```

## Health Check Endpoints

```typescript
import express from 'express';
import { PrismaClient } from '@prisma/client';
import { Redis } from 'ioredis';

const app = express();
const prisma = new PrismaClient();
const redis = new Redis(process.env.REDIS_URL!);

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  checks: {
    database: boolean;
    cache: boolean;
    memory: boolean;
  };
  uptime: number;
  timestamp: string;
}

// Simple health check (for load balancer)
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

// Detailed health check (for monitoring)
app.get('/health/detailed', async (req, res) => {
  const checks = {
    database: false,
    cache: false,
    memory: false,
  };

  // Database check
  try {
    await prisma.$queryRaw`SELECT 1`;
    checks.database = true;
  } catch (error) {
    console.error('Database health check failed:', error);
  }

  // Cache check
  try {
    await redis.ping();
    checks.cache = true;
  } catch (error) {
    console.error('Cache health check failed:', error);
  }

  // Memory check
  const memUsage = process.memoryUsage();
  const heapPercent = memUsage.heapUsed / memUsage.heapTotal * 100;
  checks.memory = heapPercent < 90;

  // Determine overall status
  const allHealthy = Object.values(checks).every(Boolean);
  const anyHealthy = Object.values(checks).some(Boolean);

  const status: HealthStatus = {
    status: allHealthy ? 'healthy' : anyHealthy ? 'degraded' : 'unhealthy',
    checks,
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
  };

  const httpStatus = status.status === 'unhealthy' ? 503 : 200;
  res.status(httpStatus).json(status);
});

// Readiness check (for Kubernetes)
app.get('/ready', async (req, res) => {
  try {
    await prisma.$queryRaw`SELECT 1`;
    await redis.ping();
    res.status(200).json({ ready: true });
  } catch (error) {
    res.status(503).json({ ready: false, error: (error as Error).message });
  }
});

// Liveness check (for Kubernetes)
app.get('/live', (req, res) => {
  // Basic check - process is alive and responding
  res.status(200).json({ alive: true });
});
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│              Load Balancing Checklist                            │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Choose appropriate algorithm for workload                     │
│ ☐ Implement health checks (active and passive)                  │
│ ☐ Configure appropriate timeouts                                │
│ ☐ Set up SSL/TLS termination                                    │
│ ☐ Enable connection keep-alive                                  │
│ ☐ Implement rate limiting                                       │
│ ☐ Configure session affinity if needed                          │
│ ☐ Set up graceful degradation                                   │
│ ☐ Monitor load balancer metrics                                 │
│ ☐ Plan for load balancer failover                               │
│ ☐ Document routing rules and configurations                     │
│ ☐ Test failover scenarios regularly                             │
└─────────────────────────────────────────────────────────────────┘
```
