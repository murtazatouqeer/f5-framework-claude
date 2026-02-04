---
name: chaos-engineering
description: Chaos engineering principles and practices
category: devops/reliability
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Chaos Engineering

## Overview

Chaos engineering is the discipline of experimenting on a system to build
confidence in the system's capability to withstand turbulent conditions
in production.

## Chaos Engineering Principles

```
┌─────────────────────────────────────────────────────────────────┐
│                Chaos Engineering Principles                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Build a Hypothesis Around Steady State                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Define what "normal" looks like in measurable terms      │   │
│  │ Examples: Error rate < 0.1%, Latency p99 < 500ms        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  2. Vary Real-World Events                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Inject failures that actually happen in production       │   │
│  │ Examples: Server crashes, network partitions, disk full │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  3. Run Experiments in Production                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Production has unique characteristics                    │   │
│  │ Start small, increase blast radius gradually            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  4. Automate Experiments                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Run experiments continuously to detect regressions       │   │
│  │ Integrate into CI/CD pipeline                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  5. Minimize Blast Radius                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Start with smallest possible experiment                  │   │
│  │ Have kill switch ready, monitor closely                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Chaos Experiment Types

```
┌─────────────────────────────────────────────────────────────────┐
│                   Chaos Experiment Categories                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Infrastructure                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Kill EC2 instances                                     │   │
│  │ • Terminate containers/pods                              │   │
│  │ • Fill disk space                                        │   │
│  │ • Exhaust CPU/memory                                     │   │
│  │ • Stop dependent services                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Network                                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Add latency between services                           │   │
│  │ • Drop packets                                           │   │
│  │ • Partition network segments                             │   │
│  │ • Corrupt network data                                   │   │
│  │ • Limit bandwidth                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Application                                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Inject exceptions                                      │   │
│  │ • Add response delays                                    │   │
│  │ • Return error codes                                     │   │
│  │ • Corrupt data                                           │   │
│  │ • Kill processes                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  State                                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Database failover                                      │   │
│  │ • Cache invalidation                                     │   │
│  │ • Queue backup                                           │   │
│  │ • Clock skew                                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Chaos Tools

### Chaos Monkey (AWS)

```yaml
# chaosmonkey-config.yaml
simianarmy:
  calendar:
    isMonkeyTime: true
    openHour: 9
    closeHour: 15
    timezone: America/Los_Angeles

  chaos:
    enabled: true
    leashed: false
    burnMoney: false
    terminateOndemand:
      enabled: true
      probability: 1.0
      defaultProbability: 1.0

    asgEnabled: true

    notification:
      sourceEmail: chaos@example.com
      receiverEmail: oncall@example.com

    filter:
      enabled: true
      excludedGroups:
        - database-asg
        - critical-services-asg
```

### Litmus Chaos (Kubernetes)

```yaml
# litmus-chaos-experiment.yaml
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: pod-delete-chaos
  namespace: production
spec:
  engineState: active
  appinfo:
    appns: production
    applabel: app=api-server
    appkind: deployment
  chaosServiceAccount: litmus-admin
  experiments:
    - name: pod-delete
      spec:
        components:
          env:
            - name: TOTAL_CHAOS_DURATION
              value: '60'
            - name: CHAOS_INTERVAL
              value: '10'
            - name: FORCE
              value: 'false'
            - name: PODS_AFFECTED_PERC
              value: '50'

---
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosExperiment
metadata:
  name: pod-network-latency
  namespace: production
spec:
  definition:
    scope: Namespaced
    permissions:
      - apiGroups: [""]
        resources: ["pods"]
        verbs: ["create", "delete", "get", "list", "patch", "update"]
    image: litmuschaos/go-runner:latest
    args:
      - -c
      - ./experiments -name pod-network-latency
    command:
      - /bin/bash
    env:
      - name: NETWORK_INTERFACE
        value: eth0
      - name: NETWORK_LATENCY
        value: '2000'  # 2 seconds
      - name: TOTAL_CHAOS_DURATION
        value: '120'
      - name: CONTAINER_RUNTIME
        value: containerd
```

### Chaos Toolkit

```json
{
  "version": "1.0.0",
  "title": "API Resilience Test",
  "description": "Verify API handles database failures gracefully",
  "tags": ["database", "resilience"],

  "steady-state-hypothesis": {
    "title": "API is healthy",
    "probes": [
      {
        "type": "probe",
        "name": "api-responds-normally",
        "tolerance": {
          "type": "jsonpath",
          "path": "$.status",
          "expect": "healthy"
        },
        "provider": {
          "type": "http",
          "url": "http://api.example.com/health",
          "method": "GET",
          "timeout": 5
        }
      },
      {
        "type": "probe",
        "name": "error-rate-normal",
        "tolerance": {
          "type": "range",
          "range": [0, 0.01]
        },
        "provider": {
          "type": "python",
          "module": "chaosprometheus.probes",
          "func": "query_instant",
          "arguments": {
            "query": "sum(rate(http_requests_total{status=~'5..'}[5m])) / sum(rate(http_requests_total[5m]))"
          }
        }
      }
    ]
  },

  "method": [
    {
      "type": "action",
      "name": "kill-database-primary",
      "provider": {
        "type": "python",
        "module": "chaosaws.rds.actions",
        "func": "reboot_db_instance",
        "arguments": {
          "db_instance_identifier": "prod-db-primary",
          "force_failover": true
        }
      },
      "pauses": {
        "after": 30
      }
    }
  ],

  "rollbacks": [
    {
      "type": "action",
      "name": "verify-database-healthy",
      "provider": {
        "type": "python",
        "module": "chaosaws.rds.probes",
        "func": "instance_status",
        "arguments": {
          "db_instance_identifier": "prod-db-primary"
        }
      }
    }
  ]
}
```

### Gremlin

```yaml
# gremlin-scenario.yaml
name: "Multi-Service Resilience Test"
description: "Test system resilience to cascading failures"
hypothesis: "System maintains 99.9% availability during cascading failures"

stages:
  - name: "Stage 1: Single Service Failure"
    attacks:
      - target:
          type: kubernetes
          namespace: production
          deployment: payment-service
        attack:
          type: process_killer
          process: java
          interval: 30
          count: 1
    duration: 5m
    success_criteria:
      - metric: error_rate
        threshold: 0.01
        comparison: less_than

  - name: "Stage 2: Network Degradation"
    attacks:
      - target:
          type: kubernetes
          namespace: production
          labels:
            tier: backend
        attack:
          type: latency
          ms: 500
          percent: 10
    duration: 10m
    success_criteria:
      - metric: p99_latency
        threshold: 2000
        comparison: less_than

  - name: "Stage 3: Resource Exhaustion"
    attacks:
      - target:
          type: kubernetes
          namespace: production
          deployment: api-gateway
        attack:
          type: cpu
          percent: 80
          cores: 2
    duration: 5m
    success_criteria:
      - metric: availability
        threshold: 99.5
        comparison: greater_than

abort_conditions:
  - metric: error_rate
    threshold: 0.10
    duration: 2m
  - metric: availability
    threshold: 95
    duration: 1m
```

## Experiment Design

### Experiment Template

```yaml
# chaos-experiment-template.yaml
experiment:
  id: "CE-001"
  name: "Database Failover Resilience"
  owner: "platform-team"
  created: "2024-01-15"

hypothesis:
  statement: >
    When the primary database fails, the application will failover
    to the replica within 30 seconds and maintain normal operation
    with no more than 5 seconds of errors.

  steady_state:
    - name: "API availability"
      metric: "sum(rate(http_requests_total{status!~'5..'}[1m])) / sum(rate(http_requests_total[1m]))"
      expected: "> 0.999"
    - name: "Database connections"
      metric: "pg_stat_activity_count{state='active'}"
      expected: "> 0"

method:
  action: "Force database failover"
  tool: "AWS RDS API"
  command: |
    aws rds reboot-db-instance \
      --db-instance-identifier prod-db \
      --force-failover
  duration: "5 minutes"

blast_radius:
  services_affected:
    - "api-gateway"
    - "order-service"
    - "user-service"
  users_affected: "< 1% (canary traffic only)"

rollback_procedure:
  - "Automatic failback not needed (RDS manages)"
  - "Manual intervention if replica promotion fails"
  - "Restore from snapshot if both fail"

success_criteria:
  - "Failover completes within 30 seconds"
  - "Error rate spike lasts < 5 seconds"
  - "No data loss detected"
  - "Connections re-establish automatically"

abort_conditions:
  - "Error rate > 10% for > 2 minutes"
  - "Data inconsistency detected"
  - "Replica fails to promote"

pre_experiment_checklist:
  - "[ ] Stakeholders notified"
  - "[ ] On-call aware and available"
  - "[ ] Monitoring dashboards ready"
  - "[ ] Rollback plan documented"
  - "[ ] Blast radius confirmed minimal"

post_experiment:
  - "Document results in runbook"
  - "Update SLO documentation if needed"
  - "Create tickets for improvements"
  - "Share learnings with team"
```

### GameDay Planning

```yaml
# gameday-plan.yaml
gameday:
  title: "Q1 Resilience GameDay"
  date: "2024-02-15"
  duration: "4 hours"
  facilitator: "Jane Smith"

participants:
  - team: "platform"
    role: "Execute experiments"
  - team: "product"
    role: "Monitor user impact"
  - team: "support"
    role: "Handle customer queries"

objectives:
  - "Test multi-region failover"
  - "Validate runbook accuracy"
  - "Train new team members"
  - "Identify improvement areas"

schedule:
  - time: "09:00"
    activity: "Kickoff and safety briefing"
  - time: "09:30"
    activity: "Experiment 1: Kill primary region"
  - time: "10:30"
    activity: "Experiment 2: Network partition"
  - time: "11:30"
    activity: "Experiment 3: Cascading failure"
  - time: "12:30"
    activity: "Debrief and lessons learned"

experiments:
  - id: 1
    name: "Primary region failure"
    hypothesis: "Traffic fails over to secondary within 60 seconds"
    blast_radius: "10% of traffic (canary)"
    abort_condition: "Error rate > 20%"

  - id: 2
    name: "Network partition"
    hypothesis: "Services degrade gracefully with cached data"
    blast_radius: "Single service"
    abort_condition: "Data inconsistency detected"

  - id: 3
    name: "Cascading failure"
    hypothesis: "Circuit breakers prevent cascade"
    blast_radius: "Backend tier"
    abort_condition: "Multiple services fail simultaneously"

safety_measures:
  - "Kill switch in place for all experiments"
  - "Real-time monitoring on big screen"
  - "Direct line to NOC"
  - "Customer communication prepared"

communication_plan:
  internal:
    channel: "#gameday-2024q1"
    updates: "Every 15 minutes"
  external:
    status_page: "Scheduled maintenance banner"
    support: "Scripted responses ready"
```

## CI/CD Integration

```yaml
# .github/workflows/chaos-tests.yaml
name: Chaos Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:
    inputs:
      experiment:
        description: 'Experiment to run'
        required: true
        type: choice
        options:
          - pod-kill
          - network-latency
          - cpu-stress

jobs:
  chaos-test:
    runs-on: ubuntu-latest
    environment: chaos-testing

    steps:
      - uses: actions/checkout@v4

      - name: Setup Chaos Toolkit
        run: |
          pip install chaostoolkit chaostoolkit-kubernetes

      - name: Configure kubectl
        uses: azure/setup-kubectl@v3
        with:
          version: 'v1.28.0'

      - name: Run Chaos Experiment
        env:
          KUBECONFIG: ${{ secrets.KUBECONFIG }}
        run: |
          chaos run experiments/${{ github.event.inputs.experiment || 'pod-kill' }}.json \
            --journal-path results/journal.json

      - name: Check Results
        run: |
          chaos verify results/journal.json

      - name: Upload Results
        uses: actions/upload-artifact@v4
        with:
          name: chaos-results
          path: results/

      - name: Notify on Failure
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Chaos experiment failed: ${{ github.event.inputs.experiment }}",
              "channel": "#reliability"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

## Observability During Chaos

```typescript
// chaos-observer.ts
import { PrometheusDriver } from 'prometheus-query';

interface ChaosMetrics {
  errorRate: number;
  latencyP99: number;
  availability: number;
  activeConnections: number;
}

class ChaosObserver {
  private prometheus: PrometheusDriver;
  private baselineMetrics: ChaosMetrics;

  constructor(prometheusUrl: string) {
    this.prometheus = new PrometheusDriver({
      endpoint: prometheusUrl,
    });
  }

  async captureBaseline(): Promise<void> {
    this.baselineMetrics = await this.getCurrentMetrics();
    console.log('Baseline captured:', this.baselineMetrics);
  }

  async getCurrentMetrics(): Promise<ChaosMetrics> {
    const [errorRate, latency, availability, connections] = await Promise.all([
      this.queryMetric('sum(rate(http_requests_total{status=~"5.."}[1m])) / sum(rate(http_requests_total[1m]))'),
      this.queryMetric('histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[1m])) by (le))'),
      this.queryMetric('avg_over_time(up{job="api"}[1m])'),
      this.queryMetric('sum(pg_stat_activity_count{state="active"})'),
    ]);

    return {
      errorRate: errorRate * 100,
      latencyP99: latency * 1000,
      availability: availability * 100,
      activeConnections: connections,
    };
  }

  async shouldAbort(): Promise<{ abort: boolean; reason?: string }> {
    const current = await this.getCurrentMetrics();

    if (current.errorRate > 10) {
      return { abort: true, reason: `Error rate ${current.errorRate}% exceeds 10%` };
    }

    if (current.availability < 95) {
      return { abort: true, reason: `Availability ${current.availability}% below 95%` };
    }

    if (current.latencyP99 > 5000) {
      return { abort: true, reason: `P99 latency ${current.latencyP99}ms exceeds 5s` };
    }

    return { abort: false };
  }

  private async queryMetric(query: string): Promise<number> {
    const result = await this.prometheus.instantQuery(query);
    return parseFloat(result.result[0]?.value.value || '0');
  }
}
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│              Chaos Engineering Best Practices                    │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Start small - single service, minimal traffic                │
│ ☐ Define clear hypothesis and success criteria                  │
│ ☐ Always have a kill switch ready                               │
│ ☐ Run experiments during business hours initially              │
│ ☐ Notify stakeholders before experiments                        │
│ ☐ Monitor continuously during experiments                       │
│ ☐ Document everything - findings, failures, learnings          │
│ ☐ Fix issues before expanding blast radius                      │
│ ☐ Automate experiments after manual validation                  │
│ ☐ Integrate chaos testing into CI/CD pipeline                   │
│ ☐ Build resilience incrementally                                │
│ ☐ Share learnings across teams                                  │
└─────────────────────────────────────────────────────────────────┘
```
