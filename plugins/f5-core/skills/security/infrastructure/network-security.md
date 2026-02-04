---
name: network-security
description: Network security and firewall configuration
category: security/infrastructure
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Network Security

## Overview

Network security protects data in transit and controls access
between network segments and services.

## Network Segmentation

```
┌─────────────────────────────────────────────────────────────┐
│                    Network Architecture                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐                                           │
│  │   Internet  │                                           │
│  └──────┬──────┘                                           │
│         │                                                   │
│  ┌──────┴──────┐                                           │
│  │   WAF/CDN   │  DMZ                                      │
│  └──────┬──────┘                                           │
│         │                                                   │
│  ┌──────┴──────┐                                           │
│  │ Load Balancer│                                          │
│  └──────┬──────┘                                           │
│         │                                                   │
│  ╔══════╧══════╗  Public Subnet                            │
│  ║  Web Tier   ║                                           │
│  ║ (Frontend)  ║                                           │
│  ╚══════╤══════╝                                           │
│         │                                                   │
│  ╔══════╧══════╗  Private Subnet                           │
│  ║  App Tier   ║                                           │
│  ║ (Backend)   ║                                           │
│  ╚══════╤══════╝                                           │
│         │                                                   │
│  ╔══════╧══════╗  Data Subnet                              │
│  ║ Data Tier   ║                                           │
│  ║ (Database)  ║                                           │
│  ╚═════════════╝                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Firewall Rules (iptables)

```bash
#!/bin/bash
# firewall-setup.sh

# Flush existing rules
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X

# Default policies - deny all
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH (limit rate)
iptables -A INPUT -p tcp --dport 22 -m state --state NEW \
  -m recent --set --name SSH
iptables -A INPUT -p tcp --dport 22 -m state --state NEW \
  -m recent --update --seconds 60 --hitcount 4 --name SSH -j DROP
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow application port (from specific IPs)
iptables -A INPUT -p tcp --dport 3000 -s 10.0.0.0/8 -j ACCEPT

# Drop invalid packets
iptables -A INPUT -m state --state INVALID -j DROP

# Protection against common attacks
# Syn flood
iptables -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 3 -j ACCEPT

# Ping flood
iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s -j ACCEPT

# Port scanning
iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP
iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP

# Log dropped packets
iptables -A INPUT -j LOG --log-prefix "IPTables-Dropped: " --log-level 4

# Save rules
iptables-save > /etc/iptables/rules.v4
```

## AWS Security Groups

```typescript
// terraform/security-groups.tf
// (Represented as TypeScript for documentation)

interface SecurityGroupRule {
  type: 'ingress' | 'egress';
  fromPort: number;
  toPort: number;
  protocol: string;
  cidrBlocks?: string[];
  securityGroups?: string[];
  description: string;
}

// Web tier security group
const webSecurityGroup: SecurityGroupRule[] = [
  {
    type: 'ingress',
    fromPort: 443,
    toPort: 443,
    protocol: 'tcp',
    cidrBlocks: ['0.0.0.0/0'],
    description: 'HTTPS from anywhere',
  },
  {
    type: 'ingress',
    fromPort: 80,
    toPort: 80,
    protocol: 'tcp',
    cidrBlocks: ['0.0.0.0/0'],
    description: 'HTTP from anywhere (redirect to HTTPS)',
  },
  {
    type: 'egress',
    fromPort: 0,
    toPort: 0,
    protocol: '-1',
    cidrBlocks: ['0.0.0.0/0'],
    description: 'All outbound traffic',
  },
];

// App tier security group
const appSecurityGroup: SecurityGroupRule[] = [
  {
    type: 'ingress',
    fromPort: 3000,
    toPort: 3000,
    protocol: 'tcp',
    securityGroups: ['web-sg'],
    description: 'App port from web tier only',
  },
  {
    type: 'egress',
    fromPort: 5432,
    toPort: 5432,
    protocol: 'tcp',
    securityGroups: ['db-sg'],
    description: 'PostgreSQL to database tier',
  },
  {
    type: 'egress',
    fromPort: 6379,
    toPort: 6379,
    protocol: 'tcp',
    securityGroups: ['redis-sg'],
    description: 'Redis to cache tier',
  },
  {
    type: 'egress',
    fromPort: 443,
    toPort: 443,
    protocol: 'tcp',
    cidrBlocks: ['0.0.0.0/0'],
    description: 'HTTPS for external APIs',
  },
];

// Database tier security group
const dbSecurityGroup: SecurityGroupRule[] = [
  {
    type: 'ingress',
    fromPort: 5432,
    toPort: 5432,
    protocol: 'tcp',
    securityGroups: ['app-sg'],
    description: 'PostgreSQL from app tier only',
  },
];
```

## Kubernetes Network Policies

```yaml
# Allow only specific ingress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    # Allow from ingress controller
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
        - podSelector:
            matchLabels:
              app.kubernetes.io/name: ingress-nginx
      ports:
        - protocol: TCP
          port: 3000
  egress:
    # Allow to database
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - protocol: TCP
          port: 5432
    # Allow to Redis
    - to:
        - podSelector:
            matchLabels:
              app: redis
      ports:
        - protocol: TCP
          port: 6379
    # Allow DNS
    - to:
        - namespaceSelector: {}
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
    # Allow external HTTPS
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except:
              - 10.0.0.0/8
              - 172.16.0.0/12
              - 192.168.0.0/16
      ports:
        - protocol: TCP
          port: 443
---
# Default deny all
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
```

## Service Mesh (Istio)

```yaml
# Istio Authorization Policy
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: api-auth-policy
  namespace: production
spec:
  selector:
    matchLabels:
      app: api
  action: ALLOW
  rules:
    # Allow from frontend
    - from:
        - source:
            principals: ["cluster.local/ns/production/sa/frontend"]
      to:
        - operation:
            methods: ["GET", "POST", "PUT", "DELETE"]
            paths: ["/api/*"]
    # Allow health checks
    - to:
        - operation:
            methods: ["GET"]
            paths: ["/health", "/ready"]
---
# Mutual TLS
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT
```

## DDoS Protection

```typescript
// middleware/ddos-protection.ts
import rateLimit from 'express-rate-limit';

// Connection rate limiting
export const connectionLimiter = rateLimit({
  windowMs: 1000, // 1 second
  max: 50, // 50 requests per second per IP
  message: 'Too many connections',
  standardHeaders: true,
});

// Slow requests detection
export function slowLorisProtection(timeout: number = 5000) {
  return (req: Request, res: Response, next: NextFunction) => {
    req.socket.setTimeout(timeout);

    req.socket.on('timeout', () => {
      req.socket.destroy();
    });

    next();
  };
}

// Request size limiting
app.use(express.json({ limit: '10kb' }));
app.use(express.urlencoded({ limit: '10kb', extended: false }));

// Nginx rate limiting
// limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
// limit_conn_zone $binary_remote_addr zone=conn:10m;
//
// server {
//   location /api/ {
//     limit_req zone=api burst=20 nodelay;
//     limit_conn conn 10;
//   }
// }
```

## VPN Configuration

```typescript
// WireGuard configuration example
interface WireGuardConfig {
  interface: {
    address: string;
    privateKey: string;
    listenPort?: number;
  };
  peers: Array<{
    publicKey: string;
    allowedIPs: string[];
    endpoint?: string;
  }>;
}

// Server config
const serverConfig: WireGuardConfig = {
  interface: {
    address: '10.0.0.1/24',
    privateKey: 'SERVER_PRIVATE_KEY',
    listenPort: 51820,
  },
  peers: [
    {
      publicKey: 'CLIENT_PUBLIC_KEY',
      allowedIPs: ['10.0.0.2/32'],
    },
  ],
};

// Client config
const clientConfig: WireGuardConfig = {
  interface: {
    address: '10.0.0.2/24',
    privateKey: 'CLIENT_PRIVATE_KEY',
  },
  peers: [
    {
      publicKey: 'SERVER_PUBLIC_KEY',
      allowedIPs: ['10.0.0.0/24', '192.168.1.0/24'],
      endpoint: 'vpn.example.com:51820',
    },
  ],
};
```

## Network Monitoring

```typescript
// services/network-monitor.service.ts
export class NetworkMonitorService {
  async detectAnomalies(): Promise<NetworkAnomaly[]> {
    const anomalies: NetworkAnomaly[] = [];

    // Check for unusual traffic patterns
    const trafficStats = await this.getTrafficStats();

    // Spike detection
    if (trafficStats.requestsPerSecond > trafficStats.avgRequestsPerSecond * 3) {
      anomalies.push({
        type: 'traffic_spike',
        severity: 'high',
        message: `Traffic spike detected: ${trafficStats.requestsPerSecond} req/s`,
      });
    }

    // Geographic anomaly
    const geoStats = await this.getGeoStats();
    const unusualCountries = geoStats.filter(
      g => !this.expectedCountries.includes(g.country) && g.percentage > 10
    );

    if (unusualCountries.length > 0) {
      anomalies.push({
        type: 'geo_anomaly',
        severity: 'medium',
        message: `Unusual traffic from: ${unusualCountries.map(c => c.country).join(', ')}`,
      });
    }

    return anomalies;
  }
}
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Least privilege | Minimal network access |
| Defense in depth | Multiple security layers |
| Micro-segmentation | Isolate workloads |
| Encrypt in transit | TLS everywhere |
| Monitor traffic | Detect anomalies |
| Regular audits | Review firewall rules |
