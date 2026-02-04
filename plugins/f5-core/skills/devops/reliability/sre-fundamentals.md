---
name: sre-fundamentals
description: Site Reliability Engineering principles and practices
category: devops/reliability
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# SRE Fundamentals

## Overview

Site Reliability Engineering (SRE) is a discipline that applies software
engineering principles to operations problems. It focuses on creating
scalable and reliable systems through automation, measurement, and
error budgets.

## SRE Principles

```
┌─────────────────────────────────────────────────────────────────┐
│                    SRE Core Principles                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Embrace Risk                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 100% reliability is not the goal - balance reliability   │   │
│  │ with velocity using error budgets                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  2. Service Level Objectives                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Define measurable targets for system behavior            │   │
│  │ SLI → SLO → SLA hierarchy                               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  3. Eliminate Toil                                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Automate repetitive, manual work                         │   │
│  │ Target: <50% time on toil, >50% on engineering          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  4. Monitoring & Alerting                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Measure what matters, alert on symptoms not causes       │   │
│  │ Every alert should be actionable                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  5. Release Engineering                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Frequent, small releases                                 │   │
│  │ Canary, blue-green, progressive rollouts                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  6. Simplicity                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Simple systems are more reliable                         │   │
│  │ Remove unnecessary complexity                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Service Level Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                 SLI → SLO → SLA Hierarchy                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SLI (Service Level Indicator)                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Quantitative measure of service behavior                 │   │
│  │ Example: Request latency, error rate, throughput         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          │                                       │
│                          ▼                                       │
│  SLO (Service Level Objective)                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Target value for an SLI                                  │   │
│  │ Example: 99.9% of requests < 200ms latency              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          │                                       │
│                          ▼                                       │
│  SLA (Service Level Agreement)                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Contract with consequences if SLO not met               │   │
│  │ Example: Credit if availability < 99.9%                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Error Budget = 100% - SLO Target                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 99.9% SLO = 0.1% error budget                           │   │
│  │ = 43.2 minutes/month of allowed downtime                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Defining SLIs

### Common SLI Types

```yaml
# sli-definitions.yaml
slis:
  availability:
    description: "Proportion of successful requests"
    formula: "successful_requests / total_requests"
    good_event: "HTTP status < 500"
    valid_event: "All HTTP requests"

  latency:
    description: "Proportion of fast requests"
    formula: "fast_requests / total_requests"
    good_event: "Response time < 200ms"
    valid_event: "All HTTP requests"
    threshold_percentiles: [50, 95, 99]

  throughput:
    description: "Rate of successful operations"
    formula: "successful_operations / time_period"
    unit: "requests per second"

  error_rate:
    description: "Proportion of failed requests"
    formula: "error_requests / total_requests"
    bad_event: "HTTP status >= 500"

  freshness:
    description: "Proportion of fresh data"
    formula: "fresh_data_requests / total_data_requests"
    good_event: "Data age < 60 seconds"

  correctness:
    description: "Proportion of correct responses"
    formula: "correct_responses / total_responses"
    verification: "Output validation check"
```

### SLI Implementation

```typescript
// sli-collector.ts
import { Counter, Histogram } from 'prom-client';

// Availability SLI
const requestTotal = new Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'path', 'status'],
});

const requestSuccess = new Counter({
  name: 'http_requests_success_total',
  help: 'Successful HTTP requests (non-5xx)',
  labelNames: ['method', 'path'],
});

// Latency SLI
const requestDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request latency',
  labelNames: ['method', 'path'],
  buckets: [0.01, 0.05, 0.1, 0.2, 0.5, 1, 2, 5],
});

// Express middleware
export function sliMiddleware(req, res, next) {
  const start = process.hrtime();

  res.on('finish', () => {
    const [seconds, nanoseconds] = process.hrtime(start);
    const duration = seconds + nanoseconds / 1e9;

    const labels = {
      method: req.method,
      path: req.route?.path || req.path,
      status: res.statusCode,
    };

    requestTotal.inc(labels);
    requestDuration.observe(
      { method: labels.method, path: labels.path },
      duration
    );

    if (res.statusCode < 500) {
      requestSuccess.inc({
        method: labels.method,
        path: labels.path,
      });
    }
  });

  next();
}
```

## Defining SLOs

### SLO Document

```yaml
# slo-document.yaml
service: api-gateway
owner: platform-team
slos:
  - name: availability
    description: "API should be available for requests"
    sli:
      type: availability
      good_events_query: |
        sum(rate(http_requests_success_total{service="api-gateway"}[5m]))
      total_events_query: |
        sum(rate(http_requests_total{service="api-gateway"}[5m]))
    target: 99.9
    window: 30d
    alerting:
      page_threshold: 99.5
      ticket_threshold: 99.8

  - name: latency_p99
    description: "99th percentile latency should be fast"
    sli:
      type: latency
      query: |
        histogram_quantile(0.99,
          sum(rate(http_request_duration_seconds_bucket{service="api-gateway"}[5m]))
          by (le)
        )
    target: 0.5  # 500ms
    window: 30d

  - name: latency_p50
    description: "Median latency should be very fast"
    sli:
      type: latency
      query: |
        histogram_quantile(0.50,
          sum(rate(http_request_duration_seconds_bucket{service="api-gateway"}[5m]))
          by (le)
        )
    target: 0.1  # 100ms
    window: 30d

error_budget:
  total_minutes_per_month: 43.2  # For 99.9% SLO
  notification_thresholds:
    - percentage: 50
      action: email_team
    - percentage: 75
      action: slack_channel
    - percentage: 90
      action: page_oncall
    - percentage: 100
      action: freeze_releases
```

### SLO-Based Alerts

```yaml
# prometheus-rules/slo-alerts.yaml
groups:
  - name: slo-alerts
    rules:
      # Fast burn alert (critical)
      - alert: HighErrorBudgetBurn
        expr: |
          (
            sum(rate(http_requests_success_total{service="api-gateway"}[5m]))
            /
            sum(rate(http_requests_total{service="api-gateway"}[5m]))
          ) < 0.99
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate burning error budget quickly"
          description: "Error rate is {{ $value | humanizePercentage }}"

      # Slow burn alert (warning)
      - alert: ErrorBudgetBurnWarning
        expr: |
          (
            sum(increase(http_requests_success_total{service="api-gateway"}[1h]))
            /
            sum(increase(http_requests_total{service="api-gateway"}[1h]))
          ) < 0.999
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Error budget consumption above normal"

      # Budget exhaustion prediction
      - alert: ErrorBudgetExhaustionPredicted
        expr: |
          predict_linear(
            slo:error_budget_remaining:ratio[6h],
            86400
          ) < 0
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Error budget predicted to exhaust within 24h"
```

## Error Budgets

### Error Budget Calculator

```typescript
// error-budget-calculator.ts
interface SLOConfig {
  target: number;        // e.g., 99.9
  windowDays: number;    // e.g., 30
}

interface ErrorBudgetStatus {
  totalBudgetMinutes: number;
  consumedMinutes: number;
  remainingMinutes: number;
  remainingPercentage: number;
  burnRate: number;
  projectedExhaustionDays: number | null;
}

function calculateErrorBudget(
  slo: SLOConfig,
  errorMinutes: number
): ErrorBudgetStatus {
  const totalMinutes = slo.windowDays * 24 * 60;
  const errorBudgetPercentage = 100 - slo.target;
  const totalBudgetMinutes = totalMinutes * (errorBudgetPercentage / 100);

  const consumedMinutes = errorMinutes;
  const remainingMinutes = Math.max(0, totalBudgetMinutes - consumedMinutes);
  const remainingPercentage = (remainingMinutes / totalBudgetMinutes) * 100;

  // Calculate burn rate (how fast we're consuming budget)
  const dailyBurnRate = consumedMinutes / slo.windowDays;
  const expectedDailyBudget = totalBudgetMinutes / slo.windowDays;
  const burnRate = dailyBurnRate / expectedDailyBudget;

  // Project when budget will exhaust
  const projectedExhaustionDays = burnRate > 1
    ? remainingMinutes / dailyBurnRate
    : null;

  return {
    totalBudgetMinutes,
    consumedMinutes,
    remainingMinutes,
    remainingPercentage,
    burnRate,
    projectedExhaustionDays,
  };
}

// Example usage
const apiGatewaySLO: SLOConfig = {
  target: 99.9,
  windowDays: 30,
};

const status = calculateErrorBudget(apiGatewaySLO, 30);
// totalBudgetMinutes: 43.2
// If 30 minutes consumed, remainingMinutes: 13.2
```

### Error Budget Policy

```yaml
# error-budget-policy.yaml
policy:
  name: error-budget-policy
  version: 1.0

  thresholds:
    - level: green
      remaining: "> 50%"
      actions:
        - "Normal development velocity"
        - "Feature work prioritized"
        - "Routine maintenance allowed"

    - level: yellow
      remaining: "25-50%"
      actions:
        - "Reduce risk of deployments"
        - "Increase testing coverage"
        - "Review recent incidents"
        - "Prioritize reliability improvements"

    - level: orange
      remaining: "10-25%"
      actions:
        - "Halt non-critical deployments"
        - "Focus on reliability"
        - "Incident review required for all outages"
        - "Production changes require extra approval"

    - level: red
      remaining: "< 10%"
      actions:
        - "FREEZE all non-emergency deployments"
        - "All hands on reliability"
        - "Executive escalation"
        - "Only hotfixes allowed"

  exhausted:
    actions:
      - "Complete deployment freeze"
      - "All engineering on reliability"
      - "Daily executive review"
      - "Customer communication required"
```

## Toil Elimination

```
┌─────────────────────────────────────────────────────────────────┐
│                    Toil Characteristics                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Toil is work that:                                              │
│                                                                  │
│  ✗ Manual         - Requires human intervention                 │
│  ✗ Repetitive     - Done over and over                          │
│  ✗ Automatable    - Could be done by a machine                  │
│  ✗ Tactical       - Interrupt-driven, not strategic             │
│  ✗ No value       - Doesn't improve service permanently         │
│  ✗ Scales linearly - Grows with service size                    │
│                                                                  │
│  Common Toil Examples:                                           │
│  • Manual deployments                                            │
│  • Manually rotating certificates                                │
│  • Manually scaling resources                                    │
│  • Copying logs for debugging                                    │
│  • Manually creating user accounts                               │
│  • Running recurring reports                                     │
│                                                                  │
│  Target: < 50% of SRE time on toil                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Toil Tracking

```yaml
# toil-tracker.yaml
toil_items:
  - id: TOIL-001
    name: "Manual certificate renewal"
    category: security
    frequency: monthly
    time_per_occurrence: 2h
    monthly_cost: 2h
    priority: high
    automation_effort: 1 week
    status: automated
    solution: "Implemented cert-manager with Let's Encrypt"

  - id: TOIL-002
    name: "Manual database backups verification"
    category: data
    frequency: daily
    time_per_occurrence: 30m
    monthly_cost: 15h
    priority: critical
    automation_effort: 2 days
    status: in_progress
    solution: "Automated backup verification with Slack alerts"

  - id: TOIL-003
    name: "User access provisioning"
    category: access
    frequency: weekly
    time_per_occurrence: 1h
    monthly_cost: 4h
    priority: medium
    automation_effort: 1 week
    status: not_started
    solution: "Self-service portal with LDAP integration"

metrics:
  total_toil_hours_monthly: 21h
  sre_capacity_hours: 160h
  toil_percentage: 13%
  target_percentage: 50%
  status: healthy
```

## On-Call Best Practices

```yaml
# oncall-runbook.yaml
oncall:
  rotation:
    type: weekly
    handoff_day: monday
    handoff_time: "10:00 UTC"
    overlap_hours: 2

  escalation:
    - level: 1
      timeout: 15m
      contacts:
        - primary_oncall
    - level: 2
      timeout: 15m
      contacts:
        - secondary_oncall
    - level: 3
      timeout: 30m
      contacts:
        - team_lead
    - level: 4
      timeout: 30m
      contacts:
        - engineering_manager
        - vp_engineering

  expectations:
    response_time: 15m
    acknowledgement_required: true
    documentation_required: true

  handoff_checklist:
    - "Review active incidents"
    - "Check error budget status"
    - "Review recent deployments"
    - "Check scheduled maintenance"
    - "Update contact information"
    - "Test paging system"

  post_incident:
    - "Document timeline"
    - "Create incident ticket"
    - "Schedule postmortem if warranted"
    - "Update runbooks if needed"
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                    SRE Best Practices                            │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Define SLIs that measure user experience                      │
│ ☐ Set SLOs based on user needs, not aspirations                │
│ ☐ Track and communicate error budget status                     │
│ ☐ Use error budgets to balance velocity and reliability         │
│ ☐ Automate toil - target <50% time on manual work              │
│ ☐ Make on-call sustainable and fair                            │
│ ☐ Every alert should be actionable                              │
│ ☐ Conduct blameless postmortems                                 │
│ ☐ Share learnings across teams                                  │
│ ☐ Measure and reduce MTTR                                       │
│ ☐ Practice incident response regularly                          │
│ ☐ Simplify systems to improve reliability                       │
└─────────────────────────────────────────────────────────────────┘
```
