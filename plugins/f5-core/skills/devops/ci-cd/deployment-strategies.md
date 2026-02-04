---
name: deployment-strategies
description: Deployment strategies for safe and reliable releases
category: devops/ci-cd
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Deployment Strategies

## Overview

Deployment strategies determine how new versions of applications are released
to production, balancing speed, safety, and resource utilization.

## Strategy Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│              Deployment Strategy Comparison                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Strategy      │ Downtime │ Risk │ Rollback │ Resource Cost     │
│  ──────────────┼──────────┼──────┼──────────┼─────────────────  │
│  Recreate      │ Yes      │ High │ Slow     │ Low               │
│  Rolling       │ No       │ Med  │ Med      │ Low               │
│  Blue-Green    │ No       │ Low  │ Fast     │ High (2x)         │
│  Canary        │ No       │ Low  │ Fast     │ Medium            │
│  A/B Testing   │ No       │ Low  │ Fast     │ Medium            │
│  Shadow        │ No       │ None │ N/A      │ High              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Recreate Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                   Recreate Deployment                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Before:  [v1] [v1] [v1]   →   Shutdown: [ ] [ ] [ ]            │
│                                                                  │
│  Deploy:  [ ] [ ] [ ]      →   After:   [v2] [v2] [v2]          │
│                                                                  │
│  ⚠️ Causes downtime during deployment                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

```yaml
# Kubernetes Recreate Strategy
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 3
  strategy:
    type: Recreate
  template:
    spec:
      containers:
        - name: api
          image: api:v2
```

**Use cases:**
- Development/staging environments
- Stateful applications requiring clean restarts
- Major database schema changes

## Rolling Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                   Rolling Deployment                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: [v1] [v1] [v1]  →  [v2] [v1] [v1]                      │
│  Step 2: [v2] [v1] [v1]  →  [v2] [v2] [v1]                      │
│  Step 3: [v2] [v2] [v1]  →  [v2] [v2] [v2]                      │
│                                                                  │
│  ✅ Zero downtime                                                │
│  ⚠️ Mixed versions during rollout                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

```yaml
# Kubernetes Rolling Strategy
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Max pods above desired
      maxUnavailable: 0  # Always maintain full capacity
  template:
    spec:
      containers:
        - name: api
          image: api:v2
          readinessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
```

```typescript
// Health check endpoint for rolling deployments
app.get('/health', (req, res) => {
  const checks = {
    database: checkDatabase(),
    cache: checkCache(),
    dependencies: checkDependencies(),
  };

  const healthy = Object.values(checks).every(Boolean);

  res.status(healthy ? 200 : 503).json({
    status: healthy ? 'healthy' : 'unhealthy',
    checks,
    version: process.env.APP_VERSION,
  });
});
```

## Blue-Green Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                  Blue-Green Deployment                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│               Load Balancer                                      │
│                    │                                             │
│        ┌──────────┴──────────┐                                  │
│        │                     │                                   │
│        ▼                     ▼                                   │
│  ┌──────────┐          ┌──────────┐                             │
│  │  BLUE    │          │  GREEN   │                             │
│  │   v1     │  ──────► │   v2     │                             │
│  │ (active) │  switch  │ (staged) │                             │
│  └──────────┘          └──────────┘                             │
│                                                                  │
│  ✅ Instant rollback (switch back)                               │
│  ✅ Zero downtime                                                │
│  ⚠️ Requires 2x infrastructure                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Kubernetes Implementation

```yaml
# blue-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-blue
  labels:
    app: api
    version: blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
      version: blue
  template:
    metadata:
      labels:
        app: api
        version: blue
    spec:
      containers:
        - name: api
          image: api:v1

---
# green-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-green
  labels:
    app: api
    version: green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
      version: green
  template:
    metadata:
      labels:
        app: api
        version: green
    spec:
      containers:
        - name: api
          image: api:v2

---
# service.yaml - Switch by changing selector
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  selector:
    app: api
    version: blue  # Change to 'green' to switch
  ports:
    - port: 80
      targetPort: 8080
```

### Blue-Green with AWS ALB

```hcl
# Terraform blue-green with target groups
resource "aws_lb_listener_rule" "blue_green" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 100

  action {
    type = "forward"
    forward {
      target_group {
        arn    = aws_lb_target_group.blue.arn
        weight = var.blue_weight  # 100 or 0
      }
      target_group {
        arn    = aws_lb_target_group.green.arn
        weight = var.green_weight  # 0 or 100
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

## Canary Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                    Canary Deployment                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Load Balancer                                                   │
│       │                                                          │
│       ├─── 90% ──────► [v1] [v1] [v1] [v1] (Stable)            │
│       │                                                          │
│       └─── 10% ──────► [v2] (Canary)                            │
│                                                                  │
│  Progression:                                                    │
│  5% → 10% → 25% → 50% → 100%                                    │
│                                                                  │
│  ✅ Early detection of issues                                    │
│  ✅ Limited blast radius                                         │
│  ⚠️ Requires traffic splitting                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Kubernetes Canary with Istio

```yaml
# VirtualService for traffic splitting
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: api
spec:
  hosts:
    - api.example.com
  http:
    - match:
        - headers:
            x-canary:
              exact: "true"
      route:
        - destination:
            host: api
            subset: canary
    - route:
        - destination:
            host: api
            subset: stable
          weight: 90
        - destination:
            host: api
            subset: canary
          weight: 10

---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: api
spec:
  host: api
  subsets:
    - name: stable
      labels:
        version: v1
    - name: canary
      labels:
        version: v2
```

### Automated Canary Analysis

```yaml
# Flagger canary analysis
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: api
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  progressDeadlineSeconds: 600
  service:
    port: 80
    targetPort: 8080
  analysis:
    interval: 1m
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
      - name: request-success-rate
        thresholdRange:
          min: 99
        interval: 1m
      - name: request-duration
        thresholdRange:
          max: 500
        interval: 1m
    webhooks:
      - name: load-test
        url: http://flagger-loadtester/
        timeout: 5s
        metadata:
          cmd: "hey -z 1m -q 10 http://api-canary:8080/"
```

### Canary Deployment Script

```typescript
interface CanaryConfig {
  stages: number[];      // [5, 10, 25, 50, 100]
  interval: number;      // seconds between stages
  threshold: {
    errorRate: number;   // max error rate %
    latencyP99: number;  // max p99 latency ms
  };
}

async function canaryDeploy(
  newImage: string,
  config: CanaryConfig
): Promise<boolean> {
  for (const weight of config.stages) {
    console.log(`Setting canary weight to ${weight}%`);
    await setCanaryWeight(weight);

    // Wait for metrics to stabilize
    await sleep(config.interval * 1000);

    // Check metrics
    const metrics = await getCanaryMetrics();

    if (metrics.errorRate > config.threshold.errorRate) {
      console.error(`Error rate ${metrics.errorRate}% exceeds threshold`);
      await rollback();
      return false;
    }

    if (metrics.latencyP99 > config.threshold.latencyP99) {
      console.error(`P99 latency ${metrics.latencyP99}ms exceeds threshold`);
      await rollback();
      return false;
    }

    console.log(`Stage ${weight}% passed. Metrics:`, metrics);
  }

  // Promote canary to stable
  await promoteCanary();
  return true;
}
```

## A/B Testing Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                   A/B Testing Deployment                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Users are split based on criteria (user ID, region, etc.)      │
│                                                                  │
│       User Pool                                                  │
│           │                                                      │
│     ┌─────┴─────┐                                               │
│     │           │                                                │
│     ▼           ▼                                                │
│  [Variant A] [Variant B]                                        │
│  (Control)   (Test)                                             │
│     │           │                                                │
│     └─────┬─────┘                                               │
│           │                                                      │
│     Metrics Collection                                           │
│     - Conversion rate                                            │
│     - Engagement                                                 │
│     - Revenue                                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

```typescript
// A/B test routing middleware
interface ABTestConfig {
  name: string;
  variants: {
    name: string;
    weight: number;
    backend: string;
  }[];
}

function abTestMiddleware(config: ABTestConfig) {
  return (req: Request, res: Response, next: NextFunction) => {
    // Get or create user segment
    const userId = req.cookies.userId || generateUserId();
    const segment = hashUserId(userId) % 100;

    // Determine variant
    let cumulative = 0;
    for (const variant of config.variants) {
      cumulative += variant.weight;
      if (segment < cumulative) {
        req.abVariant = variant.name;
        req.abBackend = variant.backend;
        break;
      }
    }

    // Track assignment
    trackABAssignment(config.name, userId, req.abVariant);

    // Set cookie for consistent experience
    res.cookie('abTest_' + config.name, req.abVariant, {
      maxAge: 30 * 24 * 60 * 60 * 1000, // 30 days
    });

    next();
  };
}
```

## Shadow Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                    Shadow Deployment                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Traffic is duplicated to shadow environment                     │
│                                                                  │
│         Request                                                  │
│            │                                                     │
│     ┌──────┴──────┐                                             │
│     │             │ (mirrored)                                   │
│     ▼             ▼                                              │
│  [Production] [Shadow]                                          │
│  (Response)   (Discard)                                         │
│                                                                  │
│  ✅ Real production traffic testing                              │
│  ✅ Zero user impact                                             │
│  ⚠️ Double resource usage                                        │
│  ⚠️ Side effects must be handled                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

```yaml
# Istio traffic mirroring
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: api
spec:
  hosts:
    - api.example.com
  http:
    - route:
        - destination:
            host: api
            subset: production
          weight: 100
      mirror:
        host: api
        subset: shadow
      mirrorPercentage:
        value: 100.0
```

## Feature Flags

```typescript
// Feature flag integration with deployment
interface FeatureFlag {
  name: string;
  enabled: boolean;
  rolloutPercentage: number;
  targetUsers?: string[];
  targetRegions?: string[];
}

class FeatureFlagService {
  private flags: Map<string, FeatureFlag> = new Map();

  async isEnabled(
    flagName: string,
    context: { userId?: string; region?: string }
  ): Promise<boolean> {
    const flag = this.flags.get(flagName);
    if (!flag || !flag.enabled) return false;

    // Target specific users
    if (flag.targetUsers?.includes(context.userId!)) {
      return true;
    }

    // Target specific regions
    if (flag.targetRegions?.includes(context.region!)) {
      return true;
    }

    // Percentage rollout
    if (context.userId) {
      const hash = this.hashString(context.userId + flagName);
      return (hash % 100) < flag.rolloutPercentage;
    }

    return false;
  }

  private hashString(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) - hash) + str.charCodeAt(i);
      hash = hash & hash;
    }
    return Math.abs(hash);
  }
}

// Usage in code
app.get('/api/feature', async (req, res) => {
  const newFeatureEnabled = await featureFlags.isEnabled('new-checkout', {
    userId: req.user.id,
    region: req.region,
  });

  if (newFeatureEnabled) {
    return newCheckoutFlow(req, res);
  }

  return legacyCheckoutFlow(req, res);
});
```

## Rollback Strategies

```yaml
# Kubernetes rollback
# View rollout history
kubectl rollout history deployment/api

# Rollback to previous version
kubectl rollout undo deployment/api

# Rollback to specific revision
kubectl rollout undo deployment/api --to-revision=2
```

```typescript
// Automated rollback based on metrics
async function monitorAndRollback(
  deploymentName: string,
  metrics: MetricsConfig
): Promise<void> {
  const checkInterval = 30000; // 30 seconds

  const monitor = setInterval(async () => {
    const currentMetrics = await getMetrics(deploymentName);

    if (currentMetrics.errorRate > metrics.maxErrorRate) {
      console.error('Error rate threshold exceeded, initiating rollback');
      await rollback(deploymentName);
      clearInterval(monitor);
    }

    if (currentMetrics.p99Latency > metrics.maxLatency) {
      console.error('Latency threshold exceeded, initiating rollback');
      await rollback(deploymentName);
      clearInterval(monitor);
    }
  }, checkInterval);
}
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│              Deployment Strategy Checklist                       │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Define rollback criteria and procedures                       │
│ ☐ Implement health checks and readiness probes                  │
│ ☐ Set up monitoring and alerting                                │
│ ☐ Use progressive delivery (canary/blue-green)                  │
│ ☐ Automate deployment process                                   │
│ ☐ Test rollback procedures regularly                            │
│ ☐ Document deployment runbooks                                  │
│ ☐ Implement feature flags for safer releases                    │
│ ☐ Version database migrations                                   │
│ ☐ Maintain backward compatibility                               │
│ ☐ Set deployment windows for critical systems                   │
│ ☐ Communicate deployments to stakeholders                       │
└─────────────────────────────────────────────────────────────────┘
```
