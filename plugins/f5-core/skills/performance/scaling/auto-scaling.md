---
name: auto-scaling
description: Auto-scaling strategies for dynamic workloads
category: performance/scaling
applies_to: backend
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Auto-Scaling

## Overview

Auto-scaling automatically adjusts compute capacity based on demand,
ensuring optimal performance while minimizing costs.

## Scaling Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│                  Auto-Scaling Strategies                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Reactive Scaling            Predictive Scaling                  │
│  ─────────────────          ──────────────────                   │
│  • Responds to metrics      • Uses ML/patterns                   │
│  • Slight lag time          • Scales in advance                  │
│  • Simple to implement      • Reduces cold starts                │
│                                                                  │
│  Scheduled Scaling           Target Tracking                     │
│  ─────────────────          ────────────────                     │
│  • Time-based rules         • Maintains target metric            │
│  • Predictable patterns     • Self-adjusting                     │
│  • Cost optimization        • AWS/GCP native                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Kubernetes Horizontal Pod Autoscaler

### Basic HPA

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 3
  maxReplicas: 50
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
```

### Advanced HPA with Custom Metrics

```yaml
# hpa-custom.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa-custom
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 3
  maxReplicas: 100
  metrics:
  # CPU utilization
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  # Custom metric: requests per second
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: 1000
  # External metric: queue depth
  - type: External
    external:
      metric:
        name: sqs_queue_depth
        selector:
          matchLabels:
            queue: orders
      target:
        type: AverageValue
        averageValue: 100
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # 5 minutes
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
      selectPolicy: Min  # Use most conservative policy
    scaleUp:
      stabilizationWindowSeconds: 0  # Scale up immediately
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 4
        periodSeconds: 15
      selectPolicy: Max  # Use most aggressive policy
```

### KEDA (Kubernetes Event-driven Autoscaling)

```yaml
# keda-scaledobject.yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: api-scaledobject
spec:
  scaleTargetRef:
    name: api
  pollingInterval: 30
  cooldownPeriod: 300
  minReplicaCount: 3
  maxReplicaCount: 100
  triggers:
  # Scale based on Prometheus metric
  - type: prometheus
    metadata:
      serverAddress: http://prometheus:9090
      metricName: http_requests_total
      threshold: '100'
      query: sum(rate(http_requests_total{deployment="api"}[2m]))
  # Scale based on Redis queue length
  - type: redis
    metadata:
      address: redis:6379
      listName: job_queue
      listLength: '50'
  # Scale based on AWS SQS
  - type: aws-sqs-queue
    metadata:
      queueURL: https://sqs.us-east-1.amazonaws.com/123456789/orders
      queueLength: '100'
      awsRegion: us-east-1
  # Scale based on cron schedule
  - type: cron
    metadata:
      timezone: UTC
      start: 0 8 * * *    # 8 AM UTC
      end: 0 20 * * *     # 8 PM UTC
      desiredReplicas: '10'
```

## AWS Auto Scaling

### EC2 Auto Scaling Group

```hcl
# asg.tf

resource "aws_launch_template" "api" {
  name_prefix   = "api-"
  image_id      = data.aws_ami.amazon_linux_2.id
  instance_type = "t3.medium"

  vpc_security_group_ids = [aws_security_group.api.id]

  user_data = base64encode(<<-EOF
    #!/bin/bash
    yum update -y
    amazon-linux-extras install docker -y
    service docker start
    $(aws ecr get-login --no-include-email --region ${var.region})
    docker run -d -p 3000:3000 ${var.ecr_repository_url}:latest
  EOF
  )

  iam_instance_profile {
    name = aws_iam_instance_profile.api.name
  }

  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "api-instance"
    }
  }
}

resource "aws_autoscaling_group" "api" {
  name                = "api-asg"
  vpc_zone_identifier = aws_subnet.private[*].id
  target_group_arns   = [aws_lb_target_group.api.arn]
  health_check_type   = "ELB"

  min_size         = 3
  max_size         = 50
  desired_capacity = 5

  launch_template {
    id      = aws_launch_template.api.id
    version = "$Latest"
  }

  # Warm pool for faster scaling
  warm_pool {
    pool_state                  = "Stopped"
    min_size                    = 2
    max_group_prepared_capacity = 10

    instance_reuse_policy {
      reuse_on_scale_in = true
    }
  }

  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 90
    }
  }

  tag {
    key                 = "Name"
    value               = "api-instance"
    propagate_at_launch = true
  }
}

# Target tracking scaling policy
resource "aws_autoscaling_policy" "cpu" {
  name                   = "cpu-target-tracking"
  autoscaling_group_name = aws_autoscaling_group.api.name
  policy_type           = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 70.0
  }
}

# Request count per target scaling
resource "aws_autoscaling_policy" "request_count" {
  name                   = "request-count-target-tracking"
  autoscaling_group_name = aws_autoscaling_group.api.name
  policy_type           = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ALBRequestCountPerTarget"
      resource_label        = "${aws_lb.api.arn_suffix}/${aws_lb_target_group.api.arn_suffix}"
    }
    target_value = 1000.0
  }
}

# Scheduled scaling
resource "aws_autoscaling_schedule" "scale_up" {
  scheduled_action_name  = "scale-up-business-hours"
  autoscaling_group_name = aws_autoscaling_group.api.name
  min_size              = 10
  max_size              = 50
  desired_capacity      = 15
  recurrence            = "0 8 * * MON-FRI"  # 8 AM weekdays
}

resource "aws_autoscaling_schedule" "scale_down" {
  scheduled_action_name  = "scale-down-night"
  autoscaling_group_name = aws_autoscaling_group.api.name
  min_size              = 3
  max_size              = 20
  desired_capacity      = 5
  recurrence            = "0 20 * * *"  # 8 PM daily
}
```

### ECS Service Auto Scaling

```hcl
# ecs-autoscaling.tf

resource "aws_appautoscaling_target" "ecs" {
  max_capacity       = 50
  min_capacity       = 3
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# CPU-based scaling
resource "aws_appautoscaling_policy" "cpu" {
  name               = "cpu-auto-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# Memory-based scaling
resource "aws_appautoscaling_policy" "memory" {
  name               = "memory-auto-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value       = 80
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# Custom metric scaling (SQS queue depth)
resource "aws_appautoscaling_policy" "queue" {
  name               = "queue-based-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace

  target_tracking_scaling_policy_configuration {
    customized_metric_specification {
      metric_name = "ApproximateNumberOfMessagesVisible"
      namespace   = "AWS/SQS"
      statistic   = "Average"
      dimensions {
        name  = "QueueName"
        value = aws_sqs_queue.orders.name
      }
    }
    target_value       = 100
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}
```

## Custom Metrics for Auto-Scaling

### Prometheus Metrics Exporter

```typescript
import promClient from 'prom-client';

// Custom metrics for scaling decisions
const httpRequestsTotal = new promClient.Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'path', 'status'],
});

const httpRequestDuration = new promClient.Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration in seconds',
  labelNames: ['method', 'path'],
  buckets: [0.1, 0.3, 0.5, 0.7, 1, 3, 5, 7, 10],
});

const activeConnections = new promClient.Gauge({
  name: 'active_connections',
  help: 'Number of active connections',
});

const queueDepth = new promClient.Gauge({
  name: 'job_queue_depth',
  help: 'Number of jobs in queue',
  labelNames: ['queue'],
});

// Middleware to collect metrics
function metricsMiddleware() {
  return (req: Request, res: Response, next: NextFunction) => {
    activeConnections.inc();
    const start = Date.now();

    res.on('finish', () => {
      activeConnections.dec();
      const duration = (Date.now() - start) / 1000;

      httpRequestsTotal.inc({
        method: req.method,
        path: req.route?.path || 'unknown',
        status: res.statusCode.toString(),
      });

      httpRequestDuration.observe(
        { method: req.method, path: req.route?.path || 'unknown' },
        duration
      );
    });

    next();
  };
}

// Update queue metrics periodically
async function updateQueueMetrics(): Promise<void> {
  const queues = ['orders', 'notifications', 'emails'];

  for (const queue of queues) {
    const depth = await redis.llen(`queue:${queue}`);
    queueDepth.set({ queue }, depth);
  }
}

setInterval(updateQueueMetrics, 10000);

// Metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', promClient.register.contentType);
  res.end(await promClient.register.metrics());
});
```

### CloudWatch Custom Metrics

```typescript
import { CloudWatch } from '@aws-sdk/client-cloudwatch';

const cloudwatch = new CloudWatch({ region: process.env.AWS_REGION });

async function publishCustomMetrics(): Promise<void> {
  const metrics = [
    {
      MetricName: 'RequestsPerSecond',
      Value: calculateRPS(),
      Unit: 'Count/Second',
      Dimensions: [
        { Name: 'ServiceName', Value: 'api' },
        { Name: 'Environment', Value: process.env.NODE_ENV! },
      ],
    },
    {
      MetricName: 'ActiveWebSockets',
      Value: getActiveWebSockets(),
      Unit: 'Count',
      Dimensions: [
        { Name: 'ServiceName', Value: 'api' },
      ],
    },
    {
      MetricName: 'CacheHitRate',
      Value: getCacheHitRate() * 100,
      Unit: 'Percent',
      Dimensions: [
        { Name: 'ServiceName', Value: 'api' },
      ],
    },
  ];

  await cloudwatch.putMetricData({
    Namespace: 'CustomApp',
    MetricData: metrics,
  });
}

// Publish metrics every minute
setInterval(publishCustomMetrics, 60000);
```

## Scaling Best Practices

### Graceful Scaling

```typescript
import { Server } from 'http';

class GracefulServer {
  private server: Server;
  private connections = new Set<any>();
  private isShuttingDown = false;

  constructor(app: Express) {
    this.server = app.listen(3000);

    this.server.on('connection', (conn) => {
      this.connections.add(conn);
      conn.on('close', () => this.connections.delete(conn));
    });
  }

  // Handle SIGTERM for graceful shutdown during scale-in
  async shutdown(): Promise<void> {
    if (this.isShuttingDown) return;
    this.isShuttingDown = true;

    console.log('Starting graceful shutdown...');

    // Stop accepting new connections
    this.server.close();

    // Wait for existing connections to complete
    const timeout = setTimeout(() => {
      console.log('Forcing shutdown after timeout');
      this.connections.forEach(conn => conn.destroy());
    }, 30000);

    // Wait for all connections to close
    await new Promise<void>((resolve) => {
      const check = setInterval(() => {
        if (this.connections.size === 0) {
          clearInterval(check);
          clearTimeout(timeout);
          resolve();
        }
      }, 100);
    });

    // Cleanup resources
    await this.cleanup();

    console.log('Graceful shutdown complete');
    process.exit(0);
  }

  private async cleanup(): Promise<void> {
    // Close database connections
    await prisma.$disconnect();

    // Close Redis connections
    await redis.quit();

    // Drain job queues
    await worker.close();
  }
}

// Setup signal handlers
const gracefulServer = new GracefulServer(app);

process.on('SIGTERM', () => gracefulServer.shutdown());
process.on('SIGINT', () => gracefulServer.shutdown());
```

### Pre-warming

```typescript
// Lambda pre-warming
import { Lambda } from '@aws-sdk/client-lambda';

const lambda = new Lambda({ region: process.env.AWS_REGION });

async function warmLambdas(): Promise<void> {
  const functions = ['api-handler', 'worker-handler'];
  const concurrency = 10; // Number of warm instances

  await Promise.all(
    functions.flatMap(functionName =>
      Array.from({ length: concurrency }, (_, i) =>
        lambda.invoke({
          FunctionName: functionName,
          InvocationType: 'RequestResponse',
          Payload: JSON.stringify({ warmup: true }),
        })
      )
    )
  );
}

// Warm every 5 minutes
setInterval(warmLambdas, 5 * 60 * 1000);
```

### Scaling Policies

```yaml
# scaling-config.yaml
scaling:
  # Scale-out: aggressive, respond quickly to demand
  scale_out:
    cpu_threshold: 70
    memory_threshold: 80
    request_rate_threshold: 1000  # per second
    cooldown: 60  # seconds
    increment: 2  # pods or instances

  # Scale-in: conservative, avoid flapping
  scale_in:
    cpu_threshold: 30
    memory_threshold: 40
    request_rate_threshold: 200
    cooldown: 300  # 5 minutes
    decrement: 1

  # Limits
  limits:
    min_instances: 3
    max_instances: 100
    max_scale_per_minute: 10

  # Predictive scaling
  predictive:
    enabled: true
    history_days: 14
    forecast_window: 2  # hours ahead
```

## Cost Optimization

### Spot Instances / Preemptible VMs

```hcl
# spot-instances.tf

resource "aws_launch_template" "api_spot" {
  name_prefix   = "api-spot-"
  image_id      = data.aws_ami.amazon_linux_2.id

  instance_market_options {
    market_type = "spot"
    spot_options {
      max_price          = "0.05"
      spot_instance_type = "one-time"
    }
  }
}

resource "aws_autoscaling_group" "api_mixed" {
  name                = "api-mixed-asg"
  vpc_zone_identifier = aws_subnet.private[*].id

  min_size         = 3
  max_size         = 50
  desired_capacity = 10

  mixed_instances_policy {
    instances_distribution {
      on_demand_base_capacity                  = 3  # Always have 3 on-demand
      on_demand_percentage_above_base_capacity = 20  # 20% on-demand, 80% spot
      spot_allocation_strategy                 = "capacity-optimized"
    }

    launch_template {
      launch_template_specification {
        launch_template_id = aws_launch_template.api.id
      }

      override {
        instance_type = "t3.medium"
      }
      override {
        instance_type = "t3a.medium"
      }
      override {
        instance_type = "t2.medium"
      }
    }
  }
}
```

### Reserved Capacity for Baseline

```hcl
# Savings Plans or Reserved Instances for baseline capacity
resource "aws_autoscaling_group" "api" {
  # ... configuration

  # Use reserved instances for minimum capacity
  min_size = 5  # Covered by reserved instances

  # Scale with on-demand/spot for variable load
  max_size = 50
}
```

## Monitoring Auto-Scaling

```typescript
// Monitor scaling events
import { AutoScaling } from '@aws-sdk/client-auto-scaling';

const autoscaling = new AutoScaling({ region: process.env.AWS_REGION });

async function getScalingActivities(): Promise<void> {
  const activities = await autoscaling.describeScalingActivities({
    AutoScalingGroupName: 'api-asg',
    MaxRecords: 10,
  });

  activities.Activities?.forEach(activity => {
    console.log({
      status: activity.StatusCode,
      cause: activity.Cause,
      startTime: activity.StartTime,
      endTime: activity.EndTime,
      description: activity.Description,
    });
  });
}

// Alert on scaling issues
async function checkScalingHealth(): Promise<void> {
  const group = await autoscaling.describeAutoScalingGroups({
    AutoScalingGroupNames: ['api-asg'],
  });

  const asg = group.AutoScalingGroups?.[0];
  if (!asg) return;

  // Check if scaling is stuck
  if (asg.DesiredCapacity !== asg.Instances?.length) {
    console.warn('Scaling in progress or stuck', {
      desired: asg.DesiredCapacity,
      actual: asg.Instances?.length,
    });
  }

  // Check for unhealthy instances
  const unhealthy = asg.Instances?.filter(i => i.HealthStatus !== 'Healthy');
  if (unhealthy?.length) {
    console.warn('Unhealthy instances detected', {
      count: unhealthy.length,
      instances: unhealthy.map(i => i.InstanceId),
    });
  }
}
```

## Best Practices Checklist

```
┌─────────────────────────────────────────────────────────────────┐
│              Auto-Scaling Checklist                              │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Define clear scaling metrics (CPU, memory, custom)            │
│ ☐ Set appropriate thresholds (not too sensitive)                │
│ ☐ Configure scale-out cooldown (short: 60s)                     │
│ ☐ Configure scale-in cooldown (long: 300s+)                     │
│ ☐ Implement graceful shutdown                                   │
│ ☐ Use warm pools or pre-warming for faster scaling              │
│ ☐ Set up predictive scaling for predictable patterns            │
│ ☐ Use spot/preemptible instances for cost savings               │
│ ☐ Maintain reserved capacity for baseline load                  │
│ ☐ Monitor scaling events and latency                            │
│ ☐ Test scaling behavior under load                              │
│ ☐ Document scaling policies and thresholds                      │
└─────────────────────────────────────────────────────────────────┘
```
